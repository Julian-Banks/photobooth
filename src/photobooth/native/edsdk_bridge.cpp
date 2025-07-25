#include <EDSDK.h>
#include <EDSDKErrors.h>
#include <EDSDKTypes.h>
#include <iostream>
#include <thread>
#include <chrono>
#ifdef __APPLE__
#include <CoreFoundation/CoreFoundation.h>
#endif
#include <string>
#include <filesystem>

extern "C" {

namespace fs = std::filesystem;
static EdsUInt32 kSaveToCamera = kEdsSaveTo_Camera;
// ---- Global Camera Handle ----
EdsCameraRef camera = nullptr;
static bool sdk_initialized = false;

// g_download_path
#include <mutex>
static std::mutex g_download_mutex;
static std::string g_download_path;
static bool g_download_success = false;

// shutdown flag

//live view 
bool start_live_view();
bool stop_live_view();
// For simplicity: allocate a buffer in C++ and return a pointer + size
unsigned char* get_live_view_frame(int* out_size);
void free_live_view_frame(unsigned char* buffer);


// ---- Dummy Event Handlers (needed for macOS stability) ----
EdsError EDSCALLBACK handleObjectEvent(EdsObjectEvent event, EdsBaseRef object, EdsVoid* context) {
    std::lock_guard<std::mutex> lock(g_download_mutex);
    
    if (event == kEdsObjectEvent_DirItemCreated || event == kEdsObjectEvent_DirItemRequestTransfer) {
        EdsDirectoryItemRef dirItem = (EdsDirectoryItemRef)object;
        EdsDirectoryItemInfo itemInfo;
        EdsError err = EdsGetDirectoryItemInfo(dirItem, &itemInfo);
        if (err != EDS_ERR_OK) {
            std::cerr << "[edsdk_bridge] EdsGetDirectoryItemInfo failed: 0x" << std::hex << err << std::endl;
            EdsRelease(dirItem);
            return err;
        }
        EdsStreamRef stream = nullptr;
        err = EdsCreateFileStream(
            g_download_path.c_str(),
            kEdsFileCreateDisposition_CreateAlways,
            kEdsAccess_ReadWrite,
            &stream);
        if (err == EDS_ERR_OK) {
            err = EdsDownload(dirItem, (EdsUInt32)itemInfo.size, stream);
            if (err != EDS_ERR_OK) {
                std::cerr << "[edsdk_bridge] EdsDownload failed: 0x" << std::hex << err << std::endl;
            }
            if (err == EDS_ERR_OK) {
                EdsDownloadComplete(dirItem);
                g_download_success = true;
                std::cout << "[edsdk_bridge] Download success!\n";
            }
            EdsRelease(stream);
        } else {
            std::cerr << "[edsdk_bridge] EdsCreateFileStream failed: 0x" << std::hex << err << std::endl;
        }
        EdsRelease(dirItem);
        return err;
    }
    if (object) EdsRelease(object);
    return EDS_ERR_OK;
}
EdsError EDSCALLBACK handlePropertyEvent(EdsPropertyEvent, EdsPropertyID, EdsUInt32, EdsVoid*) { return EDS_ERR_OK; }
EdsError EDSCALLBACK handleStateEvent(EdsStateEvent, EdsUInt32, EdsVoid*) { return EDS_ERR_OK; }


void shutdown_camera();


// ---- Robust Camera Enumerator ----
static int internal_get_camera_count(int max_retries = 8, int delay_ms = 800) {
    EdsError err;
    EdsCameraListRef cameraList = nullptr;
    EdsUInt32 count = 0;

    for (int tries = 0; tries < max_retries; ++tries) {
        if (tries > 0)
            std::cout << "🔁 Retrying camera count (attempt " << (tries+1) << ")...\n";
        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));

        err = EdsGetCameraList(&cameraList);
        if (err != EDS_ERR_OK) {
            std::cerr << "❌ EdsGetCameraList failed: 0x" << std::hex << err << std::endl;
            continue;
        }

        err = EdsGetChildCount(cameraList, &count);
        EdsRelease(cameraList); // Release immediately, every loop!
        if (err == EDS_ERR_OK && count > 0) return static_cast<int>(count);
    }
    return 0;
}

 bool initialize_camera() {
    shutdown_camera();
    
    EdsError err;
    if (sdk_initialized) {
        std::cerr << "⚠️ SDK already initialized.\n";
        return camera != nullptr;
    }

    std::cout << "🛠 Initializing SDK...\n";
    err = EdsInitializeSDK();
    if (err != EDS_ERR_OK) {
        std::cerr << "❌ EdsInitializeSDK failed: 0x" << std::hex << err << std::endl;
        return false;
    }
    std::cout << "[edsdk_bridge] SDK initialised on thread "
          << std::this_thread::get_id() << '\n';
    sdk_initialized = true;
  
    
  #ifdef __APPLE__
      // Spin the CFRunLoop for half a second (like the Canon sample does)
      std::cout << "🔄 Spinning macOS runloop for 0.5s to allow camera enumeration...\n";
      CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.5, false);
  #endif
  
    // Wait for camera(s) to be enumerated (macOS especially)
    int count = internal_get_camera_count();
    if (count == 0) {
        std::cerr << "❌ No camera found after waiting. Check cable, power, permissions.\n";
        EdsTerminateSDK();
        sdk_initialized = false;
        return false;
    }
    std::cout << "✅ Found " << count << " camera(s)\n";

    EdsCameraListRef cameraList = nullptr;
    err = EdsGetCameraList(&cameraList);
    if (err != EDS_ERR_OK) {
        std::cerr << "❌ EdsGetCameraList (final) failed: 0x" << std::hex << err << std::endl;
        EdsTerminateSDK();
        sdk_initialized = false;
        return false;
    }

    err = EdsGetChildAtIndex(cameraList, 0, &camera);
    if (err != EDS_ERR_OK || !camera) {
        std::cerr << "❌ EdsGetChildAtIndex failed: 0x" << std::hex << err << std::endl;
        EdsRelease(cameraList);
        EdsTerminateSDK();
        sdk_initialized = false;
        return false;
    }

    // Register event handlers (macOS requires at least dummy handlers)
    EdsSetObjectEventHandler(camera, kEdsObjectEvent_All, handleObjectEvent, nullptr);
    EdsSetPropertyEventHandler(camera, kEdsPropertyEvent_All, handlePropertyEvent, nullptr);
    EdsSetCameraStateEventHandler(camera, kEdsStateEvent_All, handleStateEvent, nullptr);

    std::cout << "📷 Opening session...\n";
    err = EdsOpenSession(camera);
    if (err != EDS_ERR_OK) {
        std::cerr << "❌ EdsOpenSession failed: 0x" << std::hex << err << std::endl;
        EdsRelease(camera);
        camera = nullptr;
        EdsRelease(cameraList);
        EdsTerminateSDK();
        sdk_initialized = false;
        return false;
    }

    std::cout << "✅ Camera session opened.\n";
    EdsRelease(cameraList);
    return true;
}

int get_camera_count() {
    // Always reinitialize, since this is often called as a probe
    EdsError err;
    EdsUInt32 count = 0;

    // Don't double-init/terminate SDK if it's already open
    bool needs_cleanup = false;
    if (!sdk_initialized) {
        err = EdsInitializeSDK();
        if (err != EDS_ERR_OK) {
            std::cerr << "❌ EdsInitializeSDK failed: 0x" << std::hex << err << std::endl;
            return -1;
        }
        needs_cleanup = true;
    }

    count = internal_get_camera_count();
    std::cout << "📸 Camera count: " << count << std::endl;

    if (needs_cleanup) {
        EdsTerminateSDK();
    }
    return count;
}

bool capture_photo() {
    if (!camera) return false;
    EdsError a = EdsSendCommand(camera, kEdsCameraCommand_PressShutterButton, kEdsCameraCommand_ShutterButton_Completely);
    EdsError b = EdsSendCommand(camera, kEdsCameraCommand_PressShutterButton, kEdsCameraCommand_ShutterButton_OFF);
    return a == EDS_ERR_OK && b == EDS_ERR_OK;
}


static void pump_sdk_events(int ms)
{
#ifdef __APPLE__
    CFRunLoopRunInMode(kCFRunLoopDefaultMode, ms / 1000.0, false);
#else
    // EdsGetEvent has been available since EDSDK 13.13
    for (int i = 0; i < ms / 10; ++i) {
        EdsGetEvent();                 // swallow one batch of events
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
#endif
}

static bool find_latest(EdsDirectoryItemRef dir,
                        EdsDirectoryItemRef* latest,
                        EdsTime*            latestTime)
{
    EdsUInt32 childCount = 0;
    if (EdsGetChildCount(dir, &childCount) != EDS_ERR_OK) return false;

    for (EdsUInt32 i = 0; i < childCount; ++i) {
        EdsDirectoryItemRef child = nullptr;
        if (EdsGetChildAtIndex(dir, i, &child) != EDS_ERR_OK) continue;

        EdsDirectoryItemInfo info{};
        if (EdsGetDirectoryItemInfo(child, &info) != EDS_ERR_OK) {
            EdsRelease(child);
            continue;
        }

        if (info.isFolder) {
            find_latest(child, latest, latestTime);      // recurse
            EdsRelease(child);
        } else {                                         // regular file
          if (info.szFileName[0]) {
              std::string currentName = info.szFileName;
              std::string bestName    = *latest ? EdsDirectoryItemInfo{}.szFileName : "";

              if (*latest) {
                  EdsDirectoryItemInfo bestInfo;
                  EdsGetDirectoryItemInfo(*latest, &bestInfo);
                  bestName = bestInfo.szFileName;
              }

              if (currentName > bestName) {
                  if (*latest) EdsRelease(*latest);
                  *latest = child;
              } else {
                  EdsRelease(child);
              }
            } else {
                EdsRelease(child);
            }
        }
    }
    return *latest != nullptr;
}


extern "C" bool capture_to_card_and_fetch(const char* dest_path,
                                          int wait_ms /* e.g. 1200 */)
{
    if (!camera) {
        std::cerr << "❌ No camera connected\n";
        return false;
    }

    static bool saveModeSet = false;
    if (!saveModeSet) {
        EdsUInt32 saveTarget = kEdsSaveTo_Camera;
        EdsError setErr = EdsSetPropertyData(camera, kEdsPropID_SaveTo,
                                             0, sizeof(saveTarget), &saveTarget);
        if (setErr != EDS_ERR_OK) {
            std::cerr << "❌ Failed to set save mode to camera: 0x" << std::hex << setErr << '\n';
            return false;
        }
        saveModeSet = true;
        std::cout << "💾 Camera set to save to card\n";
    }

    // ───── STEP 1: Trigger capture ─────
    std::cout << "📸 Sending capture command...\n";
    if (EdsSendCommand(camera, kEdsCameraCommand_TakePicture, 0) != EDS_ERR_OK) {
        std::cerr << "❌ EdsSendCommand failed\n";
        return false;
    }

    // ───── STEP 2: Wait for write ─────
    std::cout << "⏳ Waiting " << wait_ms << "ms for camera to save file\n";
    pump_sdk_events(wait_ms);

    // ───── STEP 3: Find newest file on card ─────
    std::cout << "📂 Scanning volume for latest file\n";
    EdsVolumeRef volume = nullptr;
    if (EdsGetChildAtIndex(camera, 0, &volume) != EDS_ERR_OK) {
        std::cerr << "❌ Failed to access volume 0\n";
        return false;
    }

    // Use lexicographic filename comparison to find newest
    EdsDirectoryItemRef latest = nullptr;
    std::string latestName = "";

    EdsUInt32 itemCount = 0;
    if (EdsGetChildCount(volume, &itemCount) == EDS_ERR_OK) {
        for (EdsUInt32 i = 0; i < itemCount; ++i) {
            EdsDirectoryItemRef folder = nullptr;
            if (EdsGetChildAtIndex(volume, i, &folder) != EDS_ERR_OK)
                continue;

            EdsUInt32 subCount = 0;
            if (EdsGetChildCount(folder, &subCount) == EDS_ERR_OK) {
                for (EdsUInt32 j = 0; j < subCount; ++j) {
                    EdsDirectoryItemRef item = nullptr;
                    if (EdsGetChildAtIndex(folder, j, &item) != EDS_ERR_OK)
                        continue;

                    EdsDirectoryItemInfo info{};
                    if (EdsGetDirectoryItemInfo(item, &info) == EDS_ERR_OK && !info.isFolder) {
                        std::string name = info.szFileName;
                        if (name > latestName) {
                            if (latest) EdsRelease(latest);
                            latest = item;
                            latestName = name;
                        } else {
                            EdsRelease(item);
                        }
                    } else {
                        EdsRelease(item);
                    }
                }
            }

            EdsRelease(folder);
        }
    }

    EdsRelease(volume);

    if (!latest) {
        std::cerr << "❌ No file found on card\n";
        return false;
    }

    std::cout << "✅ Latest file: " << latestName << '\n';

    // ───── STEP 4: Download it ─────
    std::cout << "📥 Downloading to: " << dest_path << '\n';

    EdsStreamRef stream = nullptr;
    if (EdsCreateFileStream(dest_path,
                            kEdsFileCreateDisposition_CreateAlways,
                            kEdsAccess_ReadWrite,
                            &stream) != EDS_ERR_OK) {
        std::cerr << "❌ Failed to create output stream\n";
        EdsRelease(latest);
        return false;
    }

    EdsDirectoryItemInfo info{};
    EdsGetDirectoryItemInfo(latest, &info);

    bool ok = (EdsDownload(latest, info.size, stream) == EDS_ERR_OK) &&
              (EdsDownloadComplete(latest)             == EDS_ERR_OK);

    EdsRelease(stream);
    EdsRelease(latest);

    if (!ok) {
        std::cerr << "❌ Download failed\n";
        return false;
    }

    std::cout << "✅ Download complete!\n";
    return true;
}


bool capture_and_download(const char* local_path) {
std::cout << "[edsdk_bridge] capture on thread "
          << std::this_thread::get_id() << '\n';

  if (!camera) return false;
    {
        std::lock_guard<std::mutex> lock(g_download_mutex);
        g_download_path = local_path;
        g_download_success = false;
    }

    EdsError err = EdsSendCommand(camera, kEdsCameraCommand_TakePicture, 0);
    if (err != EDS_ERR_OK) return false;

for (int i = 0; i < 400; ++i) {
    {
        std::lock_guard<std::mutex> lock(g_download_mutex);
        if (g_download_success) {
            std::cout << "[edsdk_bridge] capture_and_download: detected success, returning true\n";
            return true;
        }
    }
#ifdef __APPLE__
    // Spin the run loop for 50ms to allow Canon events to be processed
    CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.05, false);
#else
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
#endif

}
  std::cout << "[edsdk_bridge] capture_and_download: timeout, returning false\n";
  return false;

}


bool set_iso(int iso_value) {
    if (!camera) return false;
    return EdsSetPropertyData(camera, kEdsPropID_ISOSpeed, 0, sizeof(iso_value), &iso_value) == EDS_ERR_OK;
}

static bool live_view_active = false;

bool start_live_view() {
    if (!camera) return false;
    // Enable PC Live View
    EdsUInt32 device = kEdsEvfOutputDevice_PC;
    EdsError err = EdsSetPropertyData(camera, kEdsPropID_Evf_OutputDevice, 0, sizeof(device), &device);
    live_view_active = (err == EDS_ERR_OK);
    return live_view_active;
}

bool stop_live_view() {
    if (!camera) return false;
    EdsUInt32 device = kEdsEvfOutputDevice_TFT; // Or 0?
    EdsError err = EdsSetPropertyData(camera, kEdsPropID_Evf_OutputDevice, 0, sizeof(device), &device);
    live_view_active = false;
    return (err == EDS_ERR_OK);
}

// Allocate and return a JPEG buffer for Python (caller must free)
// Returns a newly-allocated JPEG buffer for Python (caller must free with free_live_view_frame)
unsigned char* get_live_view_frame(int* out_size) {
    if (!camera) return nullptr;
    if (!live_view_active) start_live_view();

    EdsStreamRef stream = nullptr;
    EdsEvfImageRef evfImage = nullptr;

    // Create memory stream to receive image
    if (EdsCreateMemoryStream(0, &stream) != EDS_ERR_OK)
        return nullptr;
    if (EdsCreateEvfImageRef(stream, &evfImage) != EDS_ERR_OK) {
        EdsRelease(stream);
        return nullptr;
    }
    if (EdsDownloadEvfImage(camera, evfImage) != EDS_ERR_OK) {
        EdsRelease(evfImage);
        EdsRelease(stream);
        return nullptr;
    }

    // Get JPEG pointer and size
    EdsUInt64 size = 0;
    EdsGetLength(stream, &size);
    if (size == 0) {
        EdsRelease(evfImage);
        EdsRelease(stream);
        return nullptr;
    }
    unsigned char* ptr = nullptr;
    EdsGetPointer(stream, (EdsVoid**)&ptr);

    unsigned char* result = (unsigned char*)malloc(size);
    if (result && ptr) memcpy(result, ptr, size);
    *out_size = (int)size;

    EdsRelease(evfImage);
    EdsRelease(stream);
    return result;
}

// Free buffer from Python
void free_live_view_frame(unsigned char* buffer) {
    free(buffer);
}

void shutdown_camera() {
    std::cout << "[edsdk_bridge] Shutting down camera..." << std::endl;  
    if (camera) {
        EdsError close_err = EdsCloseSession(camera);
        std::cout << "[edsdk_bridge] EdsCloseSession: 0x" << std::hex << close_err << std::endl;
        EdsError rel_err = EdsRelease(camera);
        std::cout << "[edsdk_bridge] EdsRelease (camera): 0x" << std::hex << rel_err << std::endl;
        camera = nullptr;
    }
    if (sdk_initialized) {
        EdsError term_err = EdsTerminateSDK();
        std::cout << "[edsdk_bridge] EdsTerminateSDK: 0x" << std::hex << term_err << std::endl;
        sdk_initialized = false;
    }
}


} // extern "C"

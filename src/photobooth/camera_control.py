import ctypes
import os

lib_path = os.path.join(os.path.dirname(__file__), "native", "libedsdk.dylib")
edsdk = ctypes.CDLL(lib_path)

edsdk.initialize_camera.restype = ctypes.c_bool
edsdk.capture_photo.restype = ctypes.c_bool
edsdk.set_iso.argtypes = [ctypes.c_int]
edsdk.set_iso.restype = ctypes.c_bool
edsdk.shutdown_camera.restype = None
edsdk.capture_and_download.argtypes = [ctypes.c_char_p]
edsdk.capture_and_download.restype = ctypes.c_bool
edsdk.get_camera_count.restype = ctypes.c_int


def get_camera_count():
    return edsdk.get_camera_count()


def init_camera():
    return edsdk.initialize_camera()


def take_photo():
    return edsdk.capture_photo()


def capture_and_save(path):
    return edsdk.capture_and_download(path.encode("utf-8"))


def set_iso(iso):
    return edsdk.set_iso(iso)


def shutdown():
    edsdk.shutdown_camera()

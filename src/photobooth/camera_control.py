import ctypes
import os
import numpy as np
import cv2

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
edsdk.start_live_view.restype = ctypes.c_bool
edsdk.stop_live_view.restype = ctypes.c_bool

edsdk.get_live_view_frame.restype = ctypes.POINTER(ctypes.c_ubyte)
edsdk.get_live_view_frame.argtypes = [ctypes.POINTER(ctypes.c_int)]
edsdk.free_live_view_frame.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]


def get_camera_count():
    return edsdk.get_camera_count()


def init_camera():
    return edsdk.initialize_camera()


def take_photo():
    return edsdk.capture_photo()


def capture_and_save(path):
    return edsdk.capture_and_download(path.encode("utf-8"))


def start_live_view():
    return edsdk.start_live_view()


def stop_live_view():
    return edsdk.stop_live_view()


def get_live_view_frame():
    size = ctypes.c_int()
    ptr = edsdk.get_live_view_frame(ctypes.byref(size))
    if not ptr or size.value == 0:
        return None
    buf = ctypes.string_at(ptr, size.value)
    edsdk.free_live_view_frame(ptr)

    frame = cv2.imdecode(np.frombuffer(buf, dtype=np.uint8), cv2.IMREAD_COLOR)
    return frame


def set_iso(iso):
    return edsdk.set_iso(iso)


def shutdown():
    edsdk.shutdown_camera()

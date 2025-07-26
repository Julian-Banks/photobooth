import threading, queue, time, concurrent.futures
from photobooth import camera_control

_MAIN_THREAD_ID = threading.get_ident()
_command_queue = queue.Queue()


def camera_mainloop(shutdown_flag):
    camera_control.init_camera()
    camera_control.start_live_view()

    try:
        while not shutdown_flag.is_set():
            camera_control.spin_runloop_once(5)
            try:
                fn, args, fut = _command_queue.get_nowait()
                try:
                    fut.set_result(fn(*args))
                except Exception as e:
                    fut.set_exception(e)
            except queue.Empty:
                pass
    finally:
        camera_control.stop_live_view()
        camera_control.shutdown()


def _run_on_main(fn, *args):
    if threading.get_ident() == _MAIN_THREAD_ID:
        return fn(*args)
    fut = concurrent.futures.Future()
    _command_queue.put((fn, args, fut))
    return fut.result()


def capture_photo(save_path):
    return _run_on_main(camera_control.capture_and_save, save_path)


def get_live_view_frame():
    return _run_on_main(camera_control.get_live_view_frame)

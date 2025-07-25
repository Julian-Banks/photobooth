# photobooth/camera_singleton.py
import threading, queue, time
from photobooth import camera_control


class CameraWorker:
    """
    Owns the EDSDK session *and* the Core‑Foundation run‑loop.
    All public methods just marshal work onto this thread.
    """

    def __init__(self):
        self._req_q = queue.Queue()  # (cmd, arg, ret_q)
        self._th = threading.Thread(target=self._worker, daemon=True)
        self._ready = threading.Event()
        self._th.start()
        print("Initialising from camera workder")
        # wait until camera is initialised
        if not self._ready.wait(timeout=5):
            raise RuntimeError("Canon SDK not ready on camera thread")

    # ---------- public façade -------------------------------------------------
    def get_frame(self, timeout=1):
        return self._ask("frame", None, timeout)

    def capture_photo(self, save_path, timeout=10):
        return self._ask("capture", save_path, timeout)

    def shutdown(self):
        try:
            self._ask("shutdown", None, timeout=3)
        finally:
            self._th.join()

    # ---------- private helpers ----------------------------------------------
    def _ask(self, cmd, arg, timeout):
        ret_q = queue.Queue(maxsize=1)
        self._req_q.put((cmd, arg, ret_q))
        try:
            return ret_q.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(f"camera thread did not answer {cmd!r} in time")

    def _worker(self):
        print("[CameraWorker] starting on thread", threading.get_ident())
        # -------- Canon initialisation happens *here* -------------------------
        if not camera_control.init_camera():
            print("❌ Canon camera init failed")
            return
        if not camera_control.start_live_view():
            print("❌ Could not start live‑view")
            return
        self._ready.set()  # signal main thread we’re ready
        # ---------------------------------------------------------------------
        while True:
            try:
                cmd, arg, ret_q = self._req_q.get(timeout=0.05)
            except queue.Empty:
                # 50 ms tick → gives CFRunLoopRunInMode inside EDSDK a chance
                continue  # (live‑view is pulled on demand)
            try:
                if cmd == "frame":
                    ret_q.put(camera_control.get_live_view_frame())
                elif cmd == "capture":
                    ok = camera_control.capture_and_save(arg)
                    ret_q.put(ok)
                elif cmd == "shutdown":
                    camera_control.stop_live_view()
                    camera_control.shutdown()
                    ret_q.put(True)
                    break
            except Exception as exc:
                ret_q.put(exc)

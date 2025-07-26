from numpy import sign
from photobooth import (
    pose_detection,
    drawing,
    camera_control,
    camera,
    camera_singleton,
)
from flask import Flask, Response, render_template, session, request
import json
import time
import argparse
import os
from threading import Event
import signal
import threading

# from photobooth.camera_singleton import CameraWorker
# camera_worker = CameraWorker()

_shutdown_flag = Event()
capture_photo_event = Event()
live_stream_event = Event()
camera_initialised = Event()

app = Flask(
    __name__, static_folder='web/static', template_folder='web/templates'
)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')


@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/options')
def options():
    return render_template('options.html')


@app.route('/photobooth')
def photobooth():
    selected_filter = request.args.get('filter', 'none')
    session['selected_filter'] = selected_filter
    return render_template('index.html')


@app.route('/qrcode')
def qrcode():
    return render_template('qrcode.html')


@app.route('/stats_feed')
def stats_feed():
    def generate():
        while live_stream_event.is_set():
            stats = {
                "fps": pose_detection.DETECTION_STATE.fps,
                "model": ["lite", "full", "heavy"][app.config["MODEL"]],
                "numPoses": app.config["numPoses"],
            }
            json_data = json.dumps(stats)
            yield f"data: {json_data}\n\n"
            time.sleep(0.1)

    return Response(generate(), mimetype='text/event-stream')


@app.route('/video_feed')
def video_feed():
    selected_filter = session.get('selected_filter', 'none')
    return Response(
        main_loop(selected_filter),
        mimetype='multipart/x-mixed-replace; boundary=frame',
    )


@app.route('/capture_photo', methods=['POST'])
def trigger_photo():
    path = os.path.join(os.getcwd(), 'src', 'web', 'static', 'image2.jpg')
    camera_singleton.capture_photo(path)
    processed = drawing.process_still_image("blue")
    capture_photo_event.clear()
    live_stream_event.clear()
    return '', 204


def main_loop(filter='none'):

    print(f"selected_filter: {filter}")

    landmarker = pose_detection.setup_pose_landmarker(
        model=app.config['MODEL'],
        num_poses=app.config['numPoses'],
        enable_segmentation=True,  # app.config['BACKGROUND'],
    )
    try:
        live_stream_event.set()
        while live_stream_event.is_set():

            # frame = camera_control.get_live_view_frame()
            frame = camera_singleton.get_live_view_frame()
            if frame is None:
                time.sleep(0.5)
                continue

            pose_detection.detect_pose(landmarker=landmarker, frame=frame)

            frame = drawing.process_live_stream(
                frame, filter, app.config['WEBCAM']
            )

            MJPEG_stream = drawing.get_stream_frame(frame)
            yield MJPEG_stream
    finally:
        pass


def create_arg_parser():
    parser = argparse.ArgumentParser(description="Motion tracking overlay")
    parser.add_argument(
        "-l",
        "--landmark",
        type=int,
        default=12,
        help="Index of the pose landmark to track (12 for shoulder, 15 for wrist",
    )
    parser.add_argument(
        "-s",
        "--skeleton",
        action='store_true',
        help="Show the skeleton for motion tracking",
    )
    parser.add_argument(
        "-p",
        "--numPoses",
        type=int,
        default=1,
        help='Max number of poses that can be detected by the landmarker',
        required=False,
    )
    parser.add_argument(
        "-m",
        "--model",
        type=int,
        default=0,
        help="0 - Pose detector lite, 1 - pose detector full, 2 - pose detector heavy",
    )
    parser.add_argument(
        "-b",
        "--background",
        action='store_true',
        help="Remove the background and replace with image",
    )
    parser.add_argument(
        "-o",
        "--overlay",
        action='store_true',
        help="Add a front overlay",
    )
    parser.add_argument(
        "-pk",
        "--pikachu",
        action='store_true',
        help="Add an overlay of pickachu that tracks you!",
    )

    parser.add_argument(
        "-w",
        "--webcam",
        action='store_true',
        help="Include to use a webcam for the livestream instead of the canon sdk.",
    )
    return parser


def run_flask():
    app.run(
        host='0.0.0.0',
        port=8080,
        threaded=True,
        debug=False,
        use_reloader=False,
    )


def handle_shutdown(signum, frame):
    print(f"Recieved shutdown signal: {signum}")
    _shutdown_flag.set()


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


if __name__ == "__main__":
    parser = create_arg_parser()
    args = parser.parse_args()

    app.config['LANDMARK'] = args.landmark
    app.config['SKELETON'] = args.skeleton
    app.config['numPoses'] = args.numPoses
    app.config['MODEL'] = args.model
    app.config['BACKGROUND'] = args.background
    app.config['OVERLAY'] = args.overlay
    app.config['PIKACHU'] = args.pikachu
    app.config['WEBCAM'] = args.webcam

    threading.Thread(target=run_flask, daemon=True).start()
    _shutdown_flag.clear()
    camera_singleton.camera_mainloop(_shutdown_flag)

from photobooth import camera, pose_detection, drawing
from flask import Flask, Response, render_template

app = Flask(__name__,static_folder = 'web/static', template_folder ='web/templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(main_loop(), mimetype='mulitpart/x-mixed-replace; boundary=frame')

def main_loop():
    
    stream = camera.start_stream()
    landmarker = pose_detection.setup_pose_landmarker(model = 1, num_poses=1)
    
    run = True
    while run :
        ret,frame = stream.read()
        pose_detection.detect_pose(landmarker = landmarker, frame = frame)
        MJPEG_stream = drawing.get_stream_frame(frame)
        run = camera.display_stream(frame)
        yield MJPEG_stream
    
    camera.shutdown(stream)

    
if __name__ == "__main__":
    app.run(debug = True)


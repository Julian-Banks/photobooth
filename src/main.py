from photobooth import camera, pose_detection, drawing
from flask import Flask, Response, render_template
import json 
import time
import argparse

app = Flask(__name__,static_folder = 'web/static', template_folder ='web/templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats_feed')
def stats_feed():
    def generate():
        while True:
            stats ={
                "fps": pose_detection.DETECTION_STATE.fps,
                "model": ["lite","full","heavy"][app.config["MODEL"]],
                "numPoses": app.config["numPoses"]
            }
            json_data = json.dumps(stats)
            yield f"data: {json_data}\n\n"
            time.sleep(0.1)
    
    return Response(generate(), mimetype = 'text/event-stream')

@app.route('/video_feed')
def video_feed():
    return Response(main_loop(), mimetype='multipart/x-mixed-replace; boundary=frame')

def main_loop():
    print("starting stream")
    stream = camera.start_stream()
    print("loading landmarker")
    landmarker = pose_detection.setup_pose_landmarker(model = app.config['MODEL'], num_poses=app.config['numPoses'], enable_segmentation= app.config['BACKGROUND'])
    try: 
        run = True
        while run :
            ret,frame = stream.read()
            pose_detection.detect_pose(landmarker = landmarker, frame = frame)
            frame = drawing.process_image(frame, skeleton=app.config['SKELETON'], landmark_no= app.config['LANDMARK'], background = app.config['BACKGROUND'], overlay=app.config['OVERLAY'])
            MJPEG_stream = drawing.get_stream_frame(frame)
            #run = camera.display_stream(frame)
            yield MJPEG_stream
    finally:        
        camera.shutdown(stream)

def create_arg_parser():
    parser = argparse.ArgumentParser(description="Motion tracking overlay")
    parser.add_argument("-l","--landmark", type=int,default = 12, help = "Index of the pose landmark to track (12 for shoulder, 15 for wrist")
    parser.add_argument("-s","--skeleton", type=int, default = 0, help = "Show the skeleton for motion tracking with 1 (defualt) or 0 to hide it")
    parser.add_argument("-p","--numPoses", type=int, default = 1, help='Max number of poses that can be detected by the landmarker', required=False)
    parser.add_argument("-m","--model", type=int, default = 0, help= "0 - Pose detector lite, 1 - pose detector full, 2 - pose detector heavy")
    parser.add_argument("-b", "--background", type = int, default = 1, help = "0 - normal live stream background, 1 for remove background" )
    parser.add_argument("-o","--overlay", type= int, default=1, help = "0 - no front overlay, 1 for a static front overlay")
    return parser

    
if __name__ == "__main__":
    parser = create_arg_parser()  
    args = parser.parse_args()
    
    app.config['LANDMARK'] = args.landmark
    if args.skeleton == 1:
        app.config['SKELETON'] = True
    else:
        app.config['SKELETON'] = False
    
    app.config['numPoses'] = args.numPoses
    app.config['MODEL']    = args.model
    if args.background == 1: 
        app.config['BACKGROUND'] = True
    else: 
        app.config['BACKGROUND'] = False 
    if args.overlay ==1:
        app.config['OVERLAY'] = True
    else:
        app.config['OVERLAY'] = False

    app.run(debug = True, host ='0.0.0.0', port = '8080')
    
  

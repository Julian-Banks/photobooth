import camera
import pose_detection

def main_loop():
    run = True
    while run :
        ret,frame = stream.read()
        pose_detection.detect_pose(landmarker = landmarker, frame = frame)
        run = camera.display_stream(frame)
        
       
if __name__ == "__main__":
    stream = camera.start_stream()
    landmarker = pose_detection.setup_pose_landmarker(model = 1, num_poses=1)
    main_loop()
    camera.shutdown(stream)


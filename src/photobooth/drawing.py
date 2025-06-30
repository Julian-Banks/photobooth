import re
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
from photobooth.config import OVERLAY
import cv2
import numpy as np 


def get_stream_frame(frame):
    _, buffer = cv2.imencode('.jpg',frame)
    frame_bytes = buffer.tobytes()
    stream_frame = (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    return stream_frame

def get_overlay_image():
    overlay_image = cv2.imread(OVERLAY,cv2.IMREAD_UNCHANGED)
    scale_factor = 1/4.0
    overlay_image = cv2.resize(
        overlay_image,
        (0,0),
        fx=scale_factor,
        fy = scale_factor,
        interpolation = cv2.INTER_AREA, 
    )
    return overlay_image


def draw_overlay_image(frame, detection_result, landmark_no):
    threshold_visibility = 0.5 
    pose_landmarks_list = detection_result.pose_landmarks 
    frame = np.copy(frame)

    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]
        if len(pose_landmarks)>landmark_no:
            tracked_landmark = pose_landmarks[landmark_no]
            if (tracked_landmark.visibility > threshold_visibility):
                h,w,_ = frame.shape
                tracked_landmark_x = int(tracked_landmark.x*w)
                tracked_landmark_y = int(tracked_landmark.y*h)
                frame = overlay_image(frame,OVERLAY,tracked_landmark_x, tracked_landmark_y)
    return frame

def draw_landmarks():
    pass

def overlay_image(frame, overlay,x,y):
    h,w,_ = overlay.shape
    fh,fw,_ = frame.shape

    x1 = max(x-w//2,0)
    y1 = max(y-h//2,0)
    x2 = min(x1+w,fw)
    y2 = min(y1+h,fh)

    overlay_x1 = max(0, -(x-w//2))
    overlay_y1 = max(0, -(y-h//2))
    overlay_x2 = overlay_x1 + (x2-x1)
    overlay_y2 = overlay_y1 + (y2-y1)
    
    if overlay_y2 - overlay_y1 <= 0 or overlay_x2-overlay_x1 <= 0:
        return frame

    overlay_crop = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
    alpha_overlay = overlay_crop[:,:,3]/255.0
    alpha_frame = 1.0 - alpha_overlay

    for c in range(3):
        frame[y1:y2, x1:x2,c] = (
            alpha_overlay * overlay_crop[:,:,c] + alpha_frame*frame[y1,y2, x1,x2,c]
        )

    return frame 

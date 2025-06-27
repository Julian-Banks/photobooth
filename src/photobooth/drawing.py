from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
from config import OVERLAY
import cv2
import numpy as np 


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
                frame = overlay_image(frame,overlay_img,tracked_landmark_x, tracked_landmark_y)
    
    return frame

def draw_landmarks():
    pass

def overlay_image(frame, overlay,x,y):
    h,w,_ = overlay.shape
    fh,fw,_ = frame.shape

    x1 = max(x-w//2,0)
    y1 = max(y-h//2,0)
    x2 = min(x1+w,fw)
    y2 = min(y1+h,bh)

    overlay_x1 = max(0, -(x-w//2))
    overlay_y1 = max(0, -(y-h//2))
    overlay_x2 = overlay_x1 + (x2-x1)
    overlay_y2 = overlay_y1 + (y2-y1)

    
    

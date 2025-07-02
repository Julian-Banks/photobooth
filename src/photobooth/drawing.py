from os import get_exec_path, rename
import re
import mediapipe as mp 
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
from photobooth.config import OVERLAY
from photobooth.config import BACKGROUND
import cv2
import numpy as np
from photobooth.pose_detection import DETECTION_STATE, DetectionState


class SmoothedPoint:
    def __init__(self, alpha = 0.3):
        self.alpha = alpha
        self.prev_x = None
        self.prev_y = None

    def update(self,x,y):
        if self.prev_x is None or self.prev_y is None:
            self.prev_x, self.prev_y = x,y
        else:
            self.prev_x = self.alpha*x + (1-self.alpha)*self.prev_x
            self.prev_y = self.alpha*y + (1-self.alpha)*self.prev_y
        return int(self.prev_x), int(self.prev_y)

smooth_point = SmoothedPoint(alpha=0.25)

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

def get_background_image(frame):
    background_image = cv2.imread(BACKGROUND, cv2.IMREAD_UNCHANGED)
    h,w,_ = frame.shape
    background_image = cv2.resize(background_image, (w,h),interpolation = cv2.INTER_AREA)

    return background_image 

def process_image(frame, skeleton:bool = False, landmark_no = 12, background: bool = False):
    if DETECTION_STATE.result: 
        result = DETECTION_STATE.result

        if skeleton and result.pose_landmarks:
            frame = draw_landmarks_on_image(frame, result)
        
        if background and result.segmentation_masks:
            frame = draw_segmentation_on_image(frame, result)
        
        if result.pose_landmarks:
            frame = draw_overlay_image(frame, landmark_no, result)

    frame = cv2.flip(frame,1)
    return frame 

def draw_segmentation_on_image(frame, result):
    BG_COLOR = (192, 192, 192)        
    bg_image = np.zeros_like(frame, dtype = np.uint8)
    bg_image[:] = BG_COLOR

    background_image = get_background_image(frame)

    segmentation_mask = result.segmentation_masks[0].numpy_view()
    condition = np.repeat(segmentation_mask[:,:,np.newaxis], 3,axis= 2)>0.1 
    
    frame = np.where(condition,frame,background_image)
    return frame 

def draw_overlay_image(frame, landmark_no, result ):
    threshold_visibility = 0.5 
    pose_landmarks_list = result.pose_landmarks 
    frame = np.copy(frame)
    overlay_image = get_overlay_image()

    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]
        if len(pose_landmarks)>landmark_no:
            tracked_landmark = pose_landmarks[landmark_no]
            if (tracked_landmark.visibility > threshold_visibility):
                h,w,_ = frame.shape
                tracked_landmark_x = int(tracked_landmark.x*w)
                tracked_landmark_y = int(tracked_landmark.y*h)
                frame = overlay(frame,overlay_image,tracked_landmark_x, tracked_landmark_y)
    return frame

def draw_landmarks_on_image(frame, result):
    mp_frame = mp.Image(image_format = mp.ImageFormat.SRGB, data = frame) 
    pose_landmarks_list = result.pose_landmarks
    mp_frame = mp_frame.numpy_view()
    frame = np.copy(mp_frame)

    # Loop through the detected poses to visualize.
    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]
        # Draw the pose landmarks.
        pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        pose_landmarks_proto.landmark.extend([
        landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
        ])
        solutions.drawing_utils.draw_landmarks(
        frame,
        pose_landmarks_proto,
        solutions.pose.POSE_CONNECTIONS,
        solutions.drawing_styles.get_default_pose_landmarks_style())
    
    return frame


def overlay(frame, overlay,x,y):
    h,w = overlay.shape[:2]
    fh,fw = frame.shape[:2]

    x,y = smooth_point.update(x,y)
    
    #Top left of overlay 
    x1 = x - w//2 
    y1 = y - h//2 
    
    #overlay and frame bounds
    overlay_x1 = max(0, -x1)
    overlay_y1 = max(0, -y1)
    overlay_x2 = min(w,fw-x1)
    overlay_y2 = min(h, fh-y1)

    frame_x1 = max(0,x1)
    frame_y1 = max(0,y1)
    frame_x2 = frame_x1 + (overlay_x2 - overlay_x1)
    frame_y2 = frame_y1 + (overlay_y2 - overlay_y1)
    
    if overlay_y2 - overlay_y1 <= 0 or overlay_x2-overlay_x1 <= 0:
        return frame #completely out of bounds

    overlay_crop = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
    frame_crop = frame[frame_y1:frame_y2, frame_x1:frame_x2]
    
    if overlay_crop.shape[2] == 4:
        alpha_overlay = overlay_crop[:,:,3]/255.0
        alpha_overlay = alpha_overlay[:,:,np.newaxis] 
    else :
        alpha_overlay = np.ones_like(overlay_crop[:,:,:1])

    alpha_frame = 1.0 - alpha_overlay

    blended = (alpha_overlay*overlay_crop[:,:,:3]+alpha_frame*frame_crop).astype(np.uint8)
    frame[frame_y1:frame_y2, frame_x1:frame_x2] = blended
    return frame


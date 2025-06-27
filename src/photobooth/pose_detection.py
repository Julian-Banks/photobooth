import mediapipe as mp
import time
from mediapipe.tasks.python.vision import PoseLandmarkerOptions, PoseLandmarkerResult
import numpy as np
from config import POSE_FULL , POSE_HEAVY, POSE_LITE 



DETECTION_RESULT = None
COUNTER, FPS = 0,0
START_TIME = time.time()

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
PoseLandmarkerResult = mp.tasks.vision.PoseLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode


def setup_pose_landmarker(model:int, num_poses:int):
    match model: 
        case 0:
            model_path = POSE_LITE
        case 1: 
            model_path = POSE_FULL
        case 2:
            model_path = POSE_HEAVY
        case _:
            model_path = POSE_LITE
            raise RuntimeWarning("No pose detection model was selected. Defaulting to lite")
    
    options = PoseLandmarkerOptions(
        base_options = BaseOptions(model_asset_path = model_path),
        running_mode = VisionRunningMode.LIVE_STREAM,
        num_poses = num_poses,
        result_callback = detection_result,
    )
    landmarker = PoseLandmarker.create_from_options(options)
    return landmarker

def detect_pose(landmarker:PoseLandmarker, frame):
    #convert frame into right format for mediapipe. Settings from the example and I havne't had any issues so far.
    mp_frame = mp.Image(image_format = mp.ImageFormat.SRGB, data = frame)
    frame_timestamp_ms = time.monotonic_ns()//1000
    landmarker.detect_async(mp_frame, frame_timestamp_ms)

def detection_result(result:PoseLandmarkerResult, output_image:mp.Image, timestamp_ms:int):
    global FPS,COUNTER,START_TIME,DETECTION_RESULT

    if COUNTER%10==0:
        FPS = 10/(time.time()-START_TIME)
        START_TIME=time.time()

    DETECTION_RESULT = result
    COUNTER += 1


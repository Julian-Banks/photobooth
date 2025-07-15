import re
import mediapipe as mp
import time
from mediapipe.tasks.python.vision import (
    PoseLandmarkerOptions,
    PoseLandmarkerResult,
)
import numpy as np
from photobooth.config import POSE_FULL, POSE_HEAVY, POSE_LITE

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
PoseLandmarkerResult = mp.tasks.vision.PoseLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode


class DetectionState:
    def __init__(self):
        self.result = None
        self.counter = 0
        self.fps = 0
        self.start_time = time.time()
        self.output_image = None

    def update(self, result, output_image):
        if self.counter % 10 == 0:
            self.fps = round(10 / (time.time() - self.start_time), 2)
            self.start_time = time.time()
        self.result = result
        self.counter += 1
        self.output_image = output_image


DETECTION_STATE = DetectionState()


def setup_pose_landmarker(
    model: int, num_poses: int, enable_segmentation: bool
):
    match model:
        case 0:
            model_path = POSE_LITE
        case 1:
            model_path = POSE_FULL
            print(f"Loading model from {POSE_FULL}")
            print(f"Model exists? {POSE_FULL.exists()}")
        case 2:
            model_path = POSE_HEAVY
        case _:
            model_path = POSE_LITE
            raise RuntimeWarning(
                "No pose detection model was selected. Defaulting to lite"
            )

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        num_poses=num_poses,
        output_segmentation_masks=enable_segmentation,
        result_callback=detection_result,
    )
    landmarker = PoseLandmarker.create_from_options(options)
    return landmarker


def detect_pose(landmarker: PoseLandmarker, frame):
    # convert frame into right format for mediapipe. Settings from the example and I havne't had any issues so far.
    mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    frame_timestamp_ms = time.monotonic_ns() // 1000
    landmarker.detect_async(mp_frame, frame_timestamp_ms)


def detection_result(
    result: PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int
):
    DETECTION_STATE.update(result, output_image)

from cv2.dnn import imagesFromBlob
import mediapipe as mp
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import time
from photobooth.config import (
    OVERLAY,
    BACKGROUND,
    PATH_TO_SAVED_IMAGE,
    PATH_TO_SAVED_IMAGE_LOAD,
    ASSET,
    ASSET1,
)
import cv2
import numpy as np
from photobooth.pose_detection import DETECTION_STATE
import os

BACKGROUND_IMAGE = None
OVERLAY_IMAGE = None
ASSET_IMAGE = None
ASSET1_IMAGE = None


class SmoothedPoint:
    def __init__(self, alpha=0.3):
        self.alpha = alpha
        self.prev_x = None
        self.prev_y = None

    def update(self, x, y):
        if self.prev_x is None or self.prev_y is None:
            self.prev_x, self.prev_y = x, y
        else:
            self.prev_x = self.alpha * x + (1 - self.alpha) * self.prev_x
            self.prev_y = self.alpha * y + (1 - self.alpha) * self.prev_y
        return int(self.prev_x), int(self.prev_y)


smooth_point = SmoothedPoint(alpha=0.4)
smooth_point1 = SmoothedPoint(alpha=0.4)


def get_overlay_image(overlay):
    global OVERLAY_IMAGE
    if OVERLAY_IMAGE is None:
        path = os.path.join(OVERLAY, f"{overlay}.png")
        print(path)
        OVERLAY_IMAGE = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        OVERLAY_IMAGE = cv2.flip(OVERLAY_IMAGE, 1)
        if OVERLAY_IMAGE is None:
            print("Overlay image is none!!")
        else:
            print(f"image shape {OVERLAY_IMAGE.shape}")
    return OVERLAY_IMAGE


def get_background_image(background):
    global BACKGROUND_IMAGE
    if BACKGROUND_IMAGE is None:
        path = os.path.join(BACKGROUND_IMAGE, f"{background}.png")
        BACKGROUND_IMAGE = cv2.imread(BACKGROUND, cv2.IMREAD_UNCHANGED)
    return BACKGROUND_IMAGE


def get_stream_frame(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()
    stream_frame = (
        b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
    )
    return stream_frame


def get_asset():
    global ASSET_IMAGE
    if ASSET_IMAGE is None:
        asset = cv2.imread(ASSET, cv2.IMREAD_UNCHANGED)
        scale_factor = 1 / 4.0
        asset = cv2.resize(
            asset,
            (0, 0),
            fx=scale_factor,
            fy=scale_factor,
            interpolation=cv2.INTER_AREA,
        )
        ASSET_IMAGE = asset
    return ASSET_IMAGE


def get_saved_photo():
    image = cv2.imread(PATH_TO_SAVED_IMAGE_LOAD, cv2.IMREAD_UNCHANGED)
    # image = cv2.resize(
    #    image,
    #    (0, 0),
    #    fx=1080,
    #    fy=1920,
    #    interpolation=cv2.INTER_AREA,
    # )
    return image


def get_asset1():
    global ASSET1_IMAGE
    if ASSET1_IMAGE is None:
        asset = cv2.imread(ASSET1, cv2.IMREAD_UNCHANGED)
        scale_factor = 1 / 4.0
        asset = cv2.resize(
            asset,
            (0, 0),
            fx=scale_factor,
            fy=scale_factor,
            interpolation=cv2.INTER_AREA,
        )
        ASSET1_IMAGE = asset
    return ASSET1_IMAGE


def draw_overlay(frame, overlay):
    asset = get_overlay_image(overlay)  # shape (H, W, 4)
    fh, fw, _ = frame.shape

    # Resize overlay (and alpha) to *exactly* match frame (can distort)
    asset_resized = cv2.resize(asset, (fw, fh), interpolation=cv2.INTER_AREA)
    b, g, r, a = cv2.split(asset_resized)
    asset_rgb = cv2.merge([b, g, r])
    alpha_mask = a / 255.0

    # Blend overlay onto frame using the alpha mask
    inv_alpha_mask = 1.0 - alpha_mask

    # Ensure shape compatibility for broadcasting
    for c in range(3):
        frame[:, :, c] = (
            frame[:, :, c] * inv_alpha_mask + asset_rgb[:, :, c] * alpha_mask
        ).astype(np.uint8)

    return frame


def check_background_size(frame):
    background_image = get_background_image()
    h, w, _ = frame.shape
    bh, bw, _ = background_image.shape

    if bw != w or bh != h:
        global BACKGROUND_IMAGE
        BACKGROUND_IMAGE = cv2.resize(
            background_image, (w, h), interpolation=cv2.INTER_AREA
        )

    return BACKGROUND_IMAGE


def process_image_demo(
    frame,
    skeleton: bool = False,
    landmark_no=12,
    background: bool = False,
    overlay: bool = True,
    pickachu: bool = True,
):
    if DETECTION_STATE.result:
        result = DETECTION_STATE.result

        if skeleton and result.pose_landmarks:
            frame = draw_landmarks_on_image(frame, result)

        if background and result.segmentation_masks:
            frame = draw_segmentation_on_image(frame, result)

        if overlay:
            frame = draw_overlay(frame)

        if result.pose_landmarks:
            if pickachu:
                frame = draw_asset_image(0, frame, landmark_no, result)
            else:
                frame = draw_asset_image(1, frame, landmark_no, result)
    frame = cv2.flip(frame, 1)
    return frame


def resize_livestream(frame, target_height=1920, target_width=1080):
    src_h, src_w = frame.shape[:2]
    scale = max(target_width / src_w, target_height / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)

    # Resize first, with no distortion
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # Now crop to the center
    x_start = (new_w - target_width) // 2
    y_start = (new_h - target_height) // 2
    cropped = resized[
        y_start : y_start + target_height, x_start : x_start + target_width
    ]
    return cropped


def process_live_stream(frame, filter, size=None):
    # frame = cv2.rotate(frame, 90)\

    frame = resize_livestream(frame)

    overlay = filter  # do error checking here
    frame = motor_show(frame, overlay, size)

    frame = cv2.flip(frame, 1)
    return frame


def motor_show(frame, filter, size=None):
    frame = draw_overlay(frame, filter)
    return frame


def process_still_image(filter, size=None):
    image = get_saved_photo()
    image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    image = motor_show(image, filter)
    print("saving_image!")
    image = cv2.flip(image, 1)
    save_image(image, PATH_TO_SAVED_IMAGE)
    # think I should change filter and size to state values that can be more easily accessed.
    return True


def save_image(frame, path):

    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"Frame dtype: {frame.dtype}, shape: {frame.shape}")
    success = cv2.imwrite(path, frame)
    if success:
        print("Image saved successfully")
    if not success:
        print("Image not saved successfully!!!")


def draw_segmentation_on_image(frame, result):
    BG_COLOR = (192, 192, 192)
    bg_image = np.zeros_like(frame, dtype=np.uint8)
    bg_image[:] = BG_COLOR

    background_image = check_background_size(frame)

    segmentation_mask = result.segmentation_masks[0].numpy_view()
    condition = np.repeat(segmentation_mask[:, :, np.newaxis], 3, axis=2) > 0.1

    frame = np.where(condition, frame, background_image)
    return frame


def draw_asset_image(asset_no, frame, landmark_no, result):
    threshold_visibility = 0.5
    pose_landmarks_list = result.pose_landmarks
    frame = np.copy(frame)

    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]
        if len(pose_landmarks) > landmark_no:
            tracked_landmark = pose_landmarks[landmark_no]
            if tracked_landmark.visibility > threshold_visibility:
                h, w, _ = frame.shape
                tracked_landmark_x = int(tracked_landmark.x * w)
                tracked_landmark_y = int(tracked_landmark.y * h)
                frame = draw_asset(
                    asset_no, frame, tracked_landmark_x, tracked_landmark_y
                )
    return frame


def draw_landmarks_on_image(frame, result):
    mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    pose_landmarks_list = result.pose_landmarks
    mp_frame = mp_frame.numpy_view()
    frame = np.copy(mp_frame)

    # Loop through the detected poses to visualize.
    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]
        # Draw the pose landmarks.
        pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        pose_landmarks_proto.landmark.extend(
            [
                landmark_pb2.NormalizedLandmark(
                    x=landmark.x, y=landmark.y, z=landmark.z
                )
                for landmark in pose_landmarks
            ]
        )
        solutions.drawing_utils.draw_landmarks(
            frame,
            pose_landmarks_proto,
            solutions.pose.POSE_CONNECTIONS,
            solutions.drawing_styles.get_default_pose_landmarks_style(),
        )

    return frame


def draw_asset(asset_no, frame, x, y):

    if asset_no == 0:
        asset = get_asset()
        x, y = smooth_point.update(x, y)

    else:
        asset = get_asset1()
        x, y = smooth_point1.update(x, y)

    h, w = asset.shape[:2]
    fh, fw = frame.shape[:2]

    # Top left of overlay
    if asset_no == 1:
        x1 = x - w
        y1 = y - h
    else:
        x1 = x - w // 2
        y1 = y - h

    # overlay and frame bounds
    overlay_x1 = max(0, -x1)
    overlay_y1 = max(0, -y1)
    overlay_x2 = min(w, fw - x1)
    overlay_y2 = min(h, fh - y1)

    frame_x1 = max(0, x1)
    frame_y1 = max(0, y1)
    frame_x2 = frame_x1 + (overlay_x2 - overlay_x1)
    frame_y2 = frame_y1 + (overlay_y2 - overlay_y1)

    if overlay_y2 - overlay_y1 <= 0 or overlay_x2 - overlay_x1 <= 0:
        return frame  # completely out of bounds

    asset_crop = asset[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
    frame_crop = frame[frame_y1:frame_y2, frame_x1:frame_x2]

    if asset_crop.shape[2] == 4:
        alpha_overlay = asset_crop[:, :, 3] / 255.0
        alpha_overlay = alpha_overlay[:, :, np.newaxis]
    else:
        alpha_overlay = np.ones_like(asset_crop[:, :, :1])

    alpha_frame = 1.0 - alpha_overlay

    blended = (
        alpha_overlay * asset_crop[:, :, :3] + alpha_frame * frame_crop
    ).astype(np.uint8)
    frame[frame_y1:frame_y2, frame_x1:frame_x2] = blended
    return frame

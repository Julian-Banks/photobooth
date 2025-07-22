import re
import cv2
from fractions import Fraction


def test_stream(camera):
    cap = cv2.VideoCapture(camera)

    if not cap.isOpened():
        print("error: Could not open camera.")
        exit()

    print_camera_stats(camera=cap)
    cap = make_1080_1350(cap)
    print('After changin width & height')
    print_camera_stats(camera=cap)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("error: could not read frame")
            break
        cv2.imshow(f'Camera: {camera}', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


def get_available_cameras():
    available_cameras = []

    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
            test_stream(i)

    if available_cameras:
        print("available_cameras: ", available_cameras)
    else:
        print("No cameras found")
    return available_cameras


def print_camera_stats(camera):

    width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = camera.get(cv2.CAP_PROP_FPS)

    if height == 0:
        print("Invalid resolution reported.")
        aspect_ratio_str = "Unknown"
    else:
        aspect_ratio = Fraction(width, height).limit_denominator(100)
        aspect_ratio_str = (
            f"{aspect_ratio.numerator}:{aspect_ratio.denominator}"
        )

    print(f"Resolution   : {width} x {height}")
    print(f"Aspect Ratio : {aspect_ratio_str}")
    print(f"Frame Rate   : {fps:.2f} FPS")


def make_1080_1350(stream):
    stream.set(3, 1080)
    stream.set(4, 1350)
    return stream


# cameras = get_available_cameras()
test_stream(0)

import cv2
from fractions import Fraction


def start_stream():

    # Setup Stream options
    # size etc
    stream = cv2.VideoCapture(0)
    stream = make_1080_1350(stream=stream)
    if not stream.isOpened():
        raise RuntimeError("The Camera Stream has not opened!")

    return stream


def capture_image():
    pass


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


def display_stream(frame) -> bool:
    cv2.imshow("Photobooth", frame)
    if cv2.waitKey(1) == ord('q'):
        return False
    return True


def shutdown(stream):
    stream.release()
    cv2.destroyAllWindows()

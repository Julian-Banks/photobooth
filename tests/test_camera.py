import cv2
import time
from photobooth import camera_control
import os


def main():
    try:
        print("Initializing camera...")
        if camera_control.init_camera():
            # camera_control.shutdown()

            print("✅ Camera initialized. Starting live view...")
            window_name = "Live View (Press SPACE to capture, ESC to exit)"

            cap = cv2.VideoCapture(
                0
            )  # Placeholder; real EVF integration will go here

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Failed to get frame")
                    break

                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1)

                if key == 27:  # ESC to quit
                    break
                elif key == 32:  # Spacebar to capture
                    print("📸 Capturing photo...")
                    # camera_control.take_photo()

                    path = os.path.join(os.getcwd(), 'test_photos')
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    path = os.path.join(path, 'image.jpg')
                    saved = camera_control.capture_and_save(path)
                    time.sleep(1)
                    if saved:
                        print(f"Imaged saved to: {path}")
                        saved_image = cv2.imread(path)
                        cv2.imshow("Captured", saved_image)
                        cv2.waitKey(2000)
                        cv2.destroyWindow("Captured")
                    else:
                        print("image not saved... :(")
            print("Shutting down camera.")
            cap.release()
            cv2.destroyAllWindows()
        else:
            print("❌ Failed to initialize Canon camera.")
    finally:
        camera_control.shutdown()


if __name__ == "__main__":
    main()

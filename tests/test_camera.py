import cv2
import time
from photobooth import camera_control


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
                    camera_control.take_photo()
                    time.sleep(1)

                    print(
                        "Displaying placeholder image (replace with real download)..."
                    )
                    cv2.imshow("Captured", frame)
                    cv2.waitKey(2000)
                    cv2.destroyWindow("Captured")

            print("Shutting down camera.")
            cap.release()
            cv2.destroyAllWindows()
        else:
            print("❌ Failed to initialize Canon camera.")
    finally:
        camera_control.shutdown()


if __name__ == "__main__":
    main()

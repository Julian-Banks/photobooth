import cv2
import time
import numpy as np
from photobooth import camera_control
import os


def main():
    try:
        print("Initializing camera...")
        if camera_control.init_camera():
            if not camera_control.start_live_view():
                print("❌ Failed to start Canon live view.")
                camera_control.shutdown()
                return

            print("✅ Camera initialized. Starting live view...")
            window_name = "Live View (Press SPACE to capture, ESC to exit)"
            cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

            while True:
                # --- Get Canon live view frame as JPEG bytes ---
                frame = camera_control.get_live_view_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue

                if frame is None:
                    print("❌ Failed to decode live view frame")
                    time.sleep(0.1)
                    continue

                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1)

                if key == 27:  # ESC to quit
                    break
                elif key == 32:  # Spacebar to capture
                    start_time = time.time()
                    print("📸 Capturing photo...")
                    path = os.path.join(os.getcwd(), 'test_photos')
                    os.makedirs(path, exist_ok=True)
                    filename = os.path.join(path, 'image_saved.jpg')
                    saved = camera_control.capture_and_save(filename)
                    end_time = time.time()

                    if saved:
                        print(
                            f"Image saved to: {filename} in time :{end_time - start_time}"
                        )
                        saved_image = cv2.imread(filename)
                        if saved_image is not None:
                            cv2.imshow("Captured", saved_image)
                            cv2.waitKey(2000)
                            cv2.destroyWindow("Captured")
                        else:
                            print(
                                "Image saved but could not display it (read error)."
                            )
                    else:
                        print("Image not saved... :(")

                    start_time = time.time()
                    path = os.path.join(os.getcwd(), 'test_photos')
                    os.makedirs(path, exist_ok=True)
                    filename = os.path.join(path, 'image_fetched.jpg')
                    saved = camera_control.capture_to_card_and_fetch(
                        filename.encode(), 1000
                    )
                    end_time = time.time()
                    if saved:
                        print(
                            f"Image saved to: {filename} in time :{end_time - start_time}"
                        )
                        saved_image = cv2.imread(filename)
                        if saved_image is not None:
                            cv2.imshow("Captured", saved_image)
                            cv2.waitKey(2000)
                            cv2.destroyWindow("Captured")
                        else:
                            print(
                                "Image saved but could not display it (read error)."
                            )
                    else:
                        print("Image not saved... :(")

            print("Shutting down live view and camera.")
            camera_control.stop_live_view()
            cv2.destroyAllWindows()
        else:
            print("❌ Failed to initialize Canon camera.")
    finally:
        camera_control.shutdown()


if __name__ == "__main__":
    main()

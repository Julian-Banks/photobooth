import cv2

def  start_stream():

    #Setup Stream options
    #size etc 
    stream = cv2.VideoCapture(0)
    if not stream.isOpened():
        raise RuntimeError("The Camera Stream has not opened!")

    return stream

def display_stream(frame)-> bool:
    cv2.imshow("Photobooth", frame)
    if cv2.waitKey(1)==ord('q'):
        return False
    return True

def shutdown(stream):
    stream.release()
    cv2.destroyAllWindows()

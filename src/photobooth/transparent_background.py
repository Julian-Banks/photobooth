import cv2
import numpy as np
from transparent_background import Remover


def transparent_background(frame):
    remover = Remover()
    frame = remover.process(frame, type='rgba')
    del remover
    return frame

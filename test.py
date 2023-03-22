import cv2 as cv
import numpy as np


cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    cap.release()
    exit()

while True:
    ret, frame = cap.read()
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    
    cv.imshow("output", np.hstack([frame, hsv]))
    
    if cv.waitKey(1) == ord('q'):
        break

import cv2 as cv
import numpy as np
import const as c
from statistics import median

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

mouseX = None
mouseY = None
new = False
state = 0
data = [(), (), ()]

# Set to true if camera not connected
VIDEO = False
VIDEOFILE = 'video/combined.mp4'

# Determine mouse position
def mouse_press(event, x, y, flags, param):
    global mouseX, mouseY, new
    if event == cv.EVENT_LBUTTONDOWN:
        mouseX, mouseY = x, y
        new = True

# Calculate average HSV value of a pixel and its neighbours.
def avg_hsv(hsv, x, y):
    hue_avg, sat_avg, val_avg = 0, 0, 0
    try:
        ky = -1
        for kx in [-1, 0, 1, -1, 0, 1, -1, 0, 1]:
            j = 0
            hue_avg += int(hsv[y + ky][x + kx][j] / 9)
            j += 1
            sat_avg += int(hsv[y + ky][x + kx][j] / 9)
            j += 1
            val_avg += int(hsv[y + ky][x + kx][j] / 9)

            if kx == 1:
                ky += 1
    except IndexError:
        return None, None, None
    return hue_avg, sat_avg, val_avg


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    if VIDEO:
        cap = cv.VideoCapture(VIDEOFILE)
    else:
        cap = cv.VideoCapture(2, cv.CAP_DSHOW)

    if not cap.isOpened():
        print("Cannot open camera")
        cap.release()
        exit()

    # Resolution
    cap.set(cv.CAP_PROP_FRAME_WIDTH, c.WIDTH)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, c.HEIGHT)
    cap.set(cv.CAP_PROP_AUTO_EXPOSURE, 1)
    cv.namedWindow('output')
    cv.setMouseCallback('output', mouse_press)

    print("Started.\nPress Pink ball.")

    if c.CROP:
        crop_width = c.WIDTH - c.CROP_AMOUNT
        c.WIDTH -= c.CROP_AMOUNT * 2
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # if frame is read correctly ret is True
        if not ret:
            if VIDEO:
                cap.set(cv.CAP_PROP_POS_FRAMES, 0)  # this make the video loop
                continue
            print("Can't receive frame (stream end?). Exiting ...")
            exit()

        if c.CROP:
            frame = frame[:, c.CROP_AMOUNT:crop_width]

        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

        cv.line(frame, (0, 0), (c.WIDTH, c.HEIGHT), (200, 200, 200), 2)
        cv.line(frame, (0, c.HEIGHT), (c.WIDTH, 0), (200, 200, 200), 2)

        cv.imshow("output", np.hstack([frame]))

        if cv.waitKey(1) == ord('q'):
            break

        if new:
            new = False
            avg = avg_hsv(hsv, mouseX, mouseY)
            if avg[1] < 50:
                print("Please try again..")
                continue

            data[state] = (avg)
            if state == 0:
                print("Found pink at: x %d, y &d - hsv:" % mouseX, mouseY, avg_hsv(hsv, mouseX, mouseY))
                print("\nPlease find green")
            elif state == 1:
                print("Found green at: x %d, y &d - hsv:" % mouseX, mouseY, avg_hsv(hsv, mouseX, mouseY))
                print("\nPlease find orange")
            elif state == 2:
                print("Found orange at: x %d, y &d - hsv:" % mouseX, mouseY, avg_hsv(hsv, mouseX, mouseY))
                break
            else:
                break
            state += 1

    # When everything done, release the capture
    cap.release()
    cv.destroyAllWindows()

    if data != [(), (), ()]:
        np.savetxt("settings.csv",
                   data,
                   delimiter=", ",
                   fmt='% s')
        print("Saved 'settings.csv'")
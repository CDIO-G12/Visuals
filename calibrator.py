import cv2 as cv
import numpy as np
import const as c
import locator as l
import os

mouseX = None
mouseY = None
new = False
state = 0
data = [(), (), ()]

red = 0
orange = 20
green = 50

# Getting correct camera source
source = os.environ.get("SOURCE")
CAMERASOURCE = c.CAMERASOURCE
if source is not None:
    if source.lower() == "video":
        c.VIDEO = True
    else:
        CAMERASOURCE = int(source)

# Determine mouse position
def mouse_press(event, x, y, flags, param):
    global mouseX, mouseY, new
    if event == cv.EVENT_LBUTTONDOWN:
        mouseX, mouseY = x, y
        new = True

# Calculate average HSV value of a pixel and its neighbours.
def avg_hsv(hsv, x, y):
    hue_avg, sat_avg, val_avg = 0, 0, 0
    hues = []
    try:
        ky = -1
        for kx in [-1, 0, 1, -1, 0, 1, -1, 0, 1]:
            j = 0
            hues.append(hsv[y + ky][x + kx][j])
            j += 1
            sat_avg += int(hsv[y + ky][x + kx][j] / 9)
            j += 1
            val_avg += int(hsv[y + ky][x + kx][j] / 9)

            if kx == 1:
                ky += 1
    except IndexError:
        return None, None, None
    hue_avg = int(l.calculate_average_hue(hues))
    return hue_avg, sat_avg, val_avg


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    if c.VIDEO:
        cap = cv.VideoCapture(c.VIDEOFILE)
    else:
        cap = cv.VideoCapture(CAMERASOURCE, cv.CAP_DSHOW)

    if not cap.isOpened():
        print("Cannot open camera")
        cap.release()
        exit()

    # Resolution
    cap.set(cv.CAP_PROP_FRAME_WIDTH, c.WIDTH)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, c.HEIGHT)
    cap.set(cv.CAP_PROP_AUTO_EXPOSURE, 1)
    cap.set(cv.CAP_PROP_AUTOFOCUS, 0)
    if c.CONTRAST is not None:
        cap.set(cv.CAP_PROP_CONTRAST, c.CONTRAST)

    cv.namedWindow('output')
    cv.setMouseCallback('output', mouse_press)

    print("Started.\nPress Pink ball.")

    if c.CROP:
        # calculate new width
        crop_width_x = c.WIDTH - c.CROP_AMOUNT_X
        c.WIDTH -= c.CROP_AMOUNT_X * 2

        # calculate new height
        # crop_width_y = c.HEIGHT - c.CROP_AMOUNT_Y
        # c.HEIGHT -= c.CROP_AMOUNT_Y * 2
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # if frame is read correctly ret is True
        if not ret:
            if c.VIDEO:
                cap.set(cv.CAP_PROP_POS_FRAMES, 0)  # this make the video loop
                continue
            print("Can't receive frame (stream end?). Exiting ...")
            exit()

        if c.CROP:
            frame = frame[:, c.CROP_AMOUNT_X:crop_width_x]

        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

        cv.line(frame, (0, 0), (c.WIDTH, c.HEIGHT), (200, 200, 200), 2)
        cv.line(frame, (0, c.HEIGHT), (c.WIDTH, 0), (200, 200, 200), 2)
        cv.circle(frame, (50, 40), 3, (0, 0, 0), 2)
        cv.circle(frame, (c.WIDTH-50, 40), 3, (0, 0, 0), 2)
        cv.circle(frame, (50, c.HEIGHT - 40), 3, (0, 0, 0), 2)
        cv.circle(frame, (c.WIDTH-50, c.HEIGHT - 40), 3, (0, 0, 0), 2)

        cv.line(frame, (50, 40), (c.WIDTH-50, 40), (100, 100, 100), 1)
        cv.line(frame, (c.WIDTH-50, 40), (c.WIDTH-50, c.HEIGHT - 40), (100, 100, 100), 1)
        cv.line(frame, (c.WIDTH-50, c.HEIGHT - 40), (50, c.HEIGHT - 40), (100, 100, 100), 1)
        cv.line(frame, (50, c.HEIGHT - 40), (50, 40), (100, 100, 100), 1)


        cv.imshow("output", np.hstack([frame]))

        if cv.waitKey(1) == ord('q'):
            break

        if new:
            new = False
            avg = avg_hsv(hsv, mouseX, mouseY)
            """if avg[1] < 50:
                print("Please try again..")
                continue
            """

            data[state] = (avg)
            if state == 0:
                print("Found red at: x: ", mouseX, ", y: ", mouseY, " - hsv:", avg_hsv(hsv, mouseX, mouseY))
                print("\nPlease find green")
            elif state == 1:
                print("Found green at: x: ", mouseX, ", y: ", mouseY, " - hsv:", avg_hsv(hsv, mouseX, mouseY))
                print("\nPlease find orange")
            elif state == 2:
                print("Found orange at: x: ", mouseX, ", y: ", mouseY, " - hsv:", avg_hsv(hsv, mouseX, mouseY))
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
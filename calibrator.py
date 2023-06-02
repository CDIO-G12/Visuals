import cv2 as cv
import numpy as np

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

mouseX = None
mouseY = None
new = False
state = 0
data = [(), (), ()]

def mouse_press(event, x, y, flags, param):
    global mouseX, mouseY, new
    if event == cv.EVENT_LBUTTONDOWN:
        mouseX, mouseY = x, y
        new = True

def avg_hsv(hsv, x, y):
    hue_avg = int(hsv[y - 1][x - 1][0] / 4 + hsv[y][x - 1][0] / 4 + hsv[y - 1][x][0] / 4 + hsv[y][x][0] / 4)
    sat_avg = int(hsv[y - 1][x - 1][1] / 4 + hsv[y][x - 1][1] / 4 + hsv[y - 1][x][1] / 4 + hsv[y][x][1] / 4)
    val_avg = int(hsv[y - 1][x - 1][2] / 4 + hsv[y][x - 1][2] / 4 + hsv[y - 1][x][2] / 4 + hsv[y][x][2] / 4)
    return (hue_avg, sat_avg, val_avg)

VIDEO = False # Set to true if camera not connected
VIDEOFILE = 'video/combined.mp4'

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    if VIDEO:
        cap = cv.VideoCapture(VIDEOFILE)
    else:
        cap = cv.VideoCapture(1, cv.CAP_DSHOW)

    if not cap.isOpened():
        print("Cannot open camera")
        cap.release()
        exit()

    # Resolution
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 1024)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 768)
    cap.set(cv.CAP_PROP_AUTO_EXPOSURE, 1)
    cv.namedWindow('output')
    cv.setMouseCallback('output', mouse_press)

    print("Started.\nPress Pink ball.")

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

        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        cv.imshow("output", frame)

        if cv.waitKey(1) == ord('q'):
            break

        if new:
            new = False
            data[state] = (avg_hsv(hsv, mouseX, mouseY))
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

    np.savetxt("settings.csv",
               data,
               delimiter=", ",
               fmt='% s')
    print("Saved 'settings.csv'")
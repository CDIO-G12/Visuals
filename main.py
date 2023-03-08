import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np
import argparse

cap = cv.VideoCapture(0, cv.CAP_DSHOW)
# cap = cv.VideoCapture(2)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv.CAP_PROP_AUTO_EXPOSURE, 1)
# cap.set(cv.CAP_PROP_FPS, 20)

wall_defined = True
corner_defined = True
corner_UR = False
corner_UL = False
corner_LR = False
corner_LL = False

corner_arr = []
corner_LL_arr = []
corner_LR_arr = []
corner_UL_arr = []
corner_UR_arr = []

counter = 0


def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        return 0, 0
    #  print('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


# print line_intersection((A, B), (C, D))

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # Our operations on the frame come here
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray = cv.medianBlur(gray, 5)
    output = frame.copy()
    # frame = cv.medianBlur(frame,10)

    circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, 20, param1=75, param2=20, minRadius=2, maxRadius=10)
    # ensure at least some circles were found
    if circles is not None:
        # convert the (x, y) coordinates and radius of the circles to integers
        circles = np.round(circles[0, :]).astype("int")

        # loop over the (x, y) coordinates and radius of the circles
        for (x, y, r) in circles:
            # draw the circle in the output image, then draw a rectangle
            # corresponding to the center of the circle
            cv.circle(output, (x, y), r, (0, 255, 0), 4)
            # print(x,", ", y)
            cv.rectangle(output, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
    # show the output image
    # cv.imshow("output", np.hstack([frame, output]))
    else:
        cv.imshow("output", gray)

    lower = np.array([0, 0, 100], dtype="uint8")
    upper = np.array([110, 70, 255], dtype="uint8")
    mask = cv.inRange(frame, lower, upper)
    frame2 = cv.bitwise_and(frame, frame, mask=mask)
    gray = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)

    # cross_lower = np.array([0, 0, 100], dtype="uint8")
    # cross_upper = np.array([70, 60, 255], dtype="uint8")

    # cv.imshow("output", np.hstack(frame2))

    # cv.imshow("output", np.hstack([frame2]))
    # Use canny edge detection
    edges = cv.Canny(gray, 50, 150, apertureSize=3)
    # Apply HoughLinesP method to
    # to directly obtain line end points

    if wall_defined:
        wall_defined = False

        lines_list = []
        lines = cv.HoughLinesP(
            edges,  # Input edge image
            1,  # Distance resolution in pixels
            np.pi / 180,  # Angle resolution in radians
            threshold=30,  # Min number of votes for valid line
            minLineLength=5,  # Min allowed length of line
            maxLineGap=40  # Max allowed gap between line for joining them
        )

    if lines is not None:
        # Iterate over points
        for points in lines:
            # Extracted points nested in the list
            x1, y1, x2, y2 = points[0]
            # Draw the lines joining the points
            # On the original image
            cv.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Maintain a simples lookup list for points
            lines_list.append([(x1, y1), (x2, y2)])

    if corner_defined:
        #corner_defined = False
        for x in lines_list:
            for y in lines_list:
                if y != x:
                    # print("this is line1: ", x[0], x[1])
                    # print("this is line2: ", y[0], y[1])
                    intersect = line_intersection(x, y)
                    # print("intersects at: ", intersect)
                    if (640 >= intersect[0] >= 580 or 80 >= intersect[0] >= 0) \
                            and (480 >= intersect[1] >= 400 or 80 >= intersect[1] >= 0):
                        # cv.circle(output, (int(intersect[0]), int(intersect[1])), 5, (255, 0, 0), -1)
                        # corner_arr.append((int(intersect[0]), int(intersect[1])))
                        counter += 1

                        if (640 >= intersect[0] >= 580 and 480 >= intersect[1] >= 400 and not corner_LR):
                            corner_LR = True
                            corner_LR_arr.append((int(intersect[0]) - 20, int(intersect[1]) - 20))

                        if (640 >= intersect[0] >= 580 and 80 >= intersect[1] >= 0 and not corner_UR):
                            corner_UR = True
                            corner_UR_arr.append((int(intersect[0]) - 20, int(intersect[1]) + 10))

                        if (80 >= intersect[0] >= 0 and 80 >= intersect[1] >= 0 and not corner_UL):
                            corner_UL = True
                            corner_UL_arr.append((int(intersect[0]) + 20, int(intersect[1]) + 10))

                        if (80 >= intersect[0] >= 0 and 480 >= intersect[1] >= 400 and not corner_LL):
                            corner_LL = True
                            corner_LL_arr.append((int(intersect[0]) + 20, int(intersect[1]) - 20))

    if corner_defined and corner_LR and corner_LL and corner_UL and corner_UR:
        corner_defined = False
        avg = np.mean(corner_LR_arr, axis=(0))
        avg = (int(avg[0]), int(avg[1]))

        corner_arr.append(avg)
        print(avg)
        avg = np.mean(corner_UR_arr, axis=(0))
        avg = (int(avg[0]), int(avg[1]))

        corner_arr.append(avg)
        print(avg)
        avg = np.mean(corner_UL_arr, axis=(0))
        avg = (int(avg[0]), int(avg[1]))

        corner_arr.append(avg)
        print(avg)
        avg = np.mean(corner_LL_arr, axis=(0))
        avg = (int(avg[0]), int(avg[1]))

        corner_arr.append(avg)
        print(avg)

    for x in corner_arr:
        cv.circle(output, x, 5, (255, 0, 0), -1)
    cv.imshow("output", np.hstack([frame, output]))

    # Display the resulting frame
    # cv.imshow('frame', gray)
    if cv.waitKey(1) == ord('q'):
        break
# When everything done, release the capture
cap.release()

cv.destroyAllWindows()

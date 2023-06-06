import math

import numpy as np
import cv2 as cv


class Borders:
    def __init__(self):
        self.corners = [] * 4

    def find_barriers(self, frame, hsv):
        self.corners = [None] * 4
        corner_LL_arr = []
        corner_LR_arr = []
        corner_UL_arr = []
        corner_UR_arr = []

        lower = np.array([0, 120, 50], dtype="uint8")
        upper = np.array([10, 255, 255], dtype="uint8")
        mask1 = cv.inRange(hsv, lower, upper)

        lower = np.array([170, 120, 50], dtype="uint8")
        upper = np.array([180, 255, 255], dtype="uint8")
        mask2 = cv.inRange(hsv, lower, upper)
        mask = mask1 | mask2
        frame2 = cv.bitwise_and(frame, frame, mask=mask)
        # red_edges = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)
        redEdges = frame2

        resized = frame2
        # resized = cv.resize(resized, (512, 384))
        cv.imshow("test", resized)

        resized = cv.resize(redEdges, (512, 384))
        cv.imshow("test", resized)

        # Use canny edge detection
        edges = cv.Canny(redEdges, 50, 150, apertureSize=3)
        # Apply HoughLinesP method to
        # to directly obtain line end points

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
                #cv.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Maintain a simples lookup list for points
                lines_list.append([(x1, y1), (x2, y2)])

        upper = 100
        left = 200
        right = 890
        lower = 570
        interval = 100

        cross_array = []
        min_X = None
        max_X = None
        min_Y = None
        max_Y = None

        for x in lines_list:
            for y in lines_list:
                if y == x:
                    continue

                intersect = line_intersection(x, y)

                if right >= intersect[0] >= (right - interval) and lower >= intersect[1] >= (lower - interval):
                    corner_LR_arr.append((int(intersect[0]), int(intersect[1])))

                elif right >= intersect[0] >= (right - interval) and upper >= intersect[1] >= 0:
                    corner_UR_arr.append((int(intersect[0]), int(intersect[1])))

                elif left >= intersect[0] >= (left-interval) and upper >= intersect[1] >= 0:
                    corner_UL_arr.append((int(intersect[0]), int(intersect[1])))

                elif left >= intersect[0] >= (left-interval) and lower >= intersect[1] >= (lower - interval):
                    corner_LL_arr.append((int(intersect[0]), int(intersect[1])))

                if 700 >= x[0][0] >= 300 and 500 >= x[0][1] >= 200 \
                        and 700 >= y[0][0] >= 300 and 500 >= y[0][1] >= 200 and False:

                    avg = None
                    if math.dist(x[0], y[0]) <= 15:
                        avg = np.mean([x[0], y[0]], axis=(0))
                        #cv.circle(frame, (int(avg[0]), int(avg[1])), 5, (255, 0, 255), -1)
                    if math.dist(x[1], y[1]) <= 15:
                        avg = np.mean([x[1], y[1]], axis=(0))
                        #cv.circle(frame, (int(avg[0]), int(avg[1])), 5, (255, 0, 0), -1)

                    if avg:
                        if min_X > avg[0] or not min_X:
                            min_X = avg[0]



        if min_X:
            cv.circle(frame, (int(min_X[0]), int(min_X[1])), 5, (255, 0, 0), -1)




        #Tilføjede dette Yrray for at undgå IndexError: list index out of range.
        avg_corners = [] * 4

        meanUL = None
        meanUR = None
        meanLL = None
        meanLR = None


        offset = 15
        if corner_UL_arr:
            meanUL = np.mean(corner_UL_arr, axis=(0))
            self.corners[0] = (int(meanUL[0]) + offset, int(meanUL[1]) + offset)
        else:
            avg = None

        if corner_UR_arr:
            meanUR = np.mean(corner_UR_arr, axis=(0))
            self.corners[1] = (int(meanUR[0]) - offset, int(meanUR[1])+offset)
        else:
            avg = None

        if corner_LR_arr:
            meanLR = np.mean(corner_LR_arr, axis=(0))
            self.corners[2] =(int(meanLR[0])-offset, int(meanLR[1])-offset)
        else:
            avg = None

        if corner_LL_arr:
            meanLL = np.mean(corner_LL_arr, axis=(0))
            self.corners[3] = (int(meanLL[0])+offset, int(meanLL[1])-offset)
        else:
            avg = None

        goal = (0, 0)
        #goal_arr = []

        if meanLL is not None and meanLR is not None and meanUR is not None and meanUL is not None:
            holeL = (int(meanUL[0]), int((meanLL[1] - meanUL[1]) / 2 + meanUL[1]))
            goal = holeL
            #holeR = (int(meanUR[0]), int((meanLR[1] - meanUR[1]) / 2 + meanUR[1]))
            #goal_arr.append(holeL)
            #goal_arr.append(holeR)

        return self.corners, goal

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

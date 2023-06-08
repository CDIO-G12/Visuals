import math
import const as c
import numpy as np
import cv2 as cv


class Borders:
    def __init__(self):
        self.corners = [] * 4
        self.cross_array = [] * 4

    def check_point_in_cross(self, avg):
        # min X
        if self.cross_array[0] is None or self.cross_array[0][0] > avg[0]:
            self.cross_array[0] = avg
        # max X
        if self.cross_array[1] is None or self.cross_array[1][0] < avg[0]:
            self.cross_array[1] = avg
        # min Y
        if self.cross_array[2] is None or self.cross_array[2][1] > avg[1]:
            self.cross_array[2] = avg
        # max Y
        if self.cross_array[3] is None or self.cross_array[3][1] < avg[1]:
            self.cross_array[3] = avg

    def find_barriers(self, frame, hsv):
        self.corners = [None] * 4
        self.cross_array = [None] * 4
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
        # directly obtain line end points

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

        upper = 0.17*c.HEIGHT
        left = 0.2*c.WIDTH
        right = 0.89*c.WIDTH
        lower = 0.98*c.HEIGHT
        interval = 100

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

                if 0.7*c.WIDTH >= x[0][0] >= 0.3*c.WIDTH and 0.65*c.HEIGHT >= x[0][1] >= 0.25*c.HEIGHT \
                        and 0.7*c.WIDTH >= y[0][0] >= 0.3*c.WIDTH and 0.65*c.HEIGHT >= y[0][1] >= 0.25*c.HEIGHT:

                    points = {0: [x[0], y[0]], 1: [x[1], y[1]]}
                    for key, value in points.items():
                        if math.dist(value[0], value[1]) <= 15:
                            avg = np.mean(value, axis=0)
                            self.check_point_in_cross(avg)

        for point in self.cross_array:
            if point is not None:
                cv.circle(frame, (int(point[0]), int(point[1])), 5, (255, 0, 0), -1)

        meanUL = None
        meanUR = None
        meanLL = None
        meanLR = None

        corner_dict = {'UL': corner_UL_arr, 'UR': corner_UR_arr, 'LR': corner_LR_arr, 'LL': corner_LL_arr}
        offset = 15

        for i, corner in enumerate(['UL', 'UR', 'LR', 'LL']):
            mean = np.mean(corner_dict[corner], axis=0) if corner_dict[corner] else None
            if mean is not None:
                x = int(mean[0]) + offset if i in [0, 3] else int(mean[0]) - offset
                y = int(mean[1]) + offset if i in [0, 1] else int(mean[1]) - offset
                self.corners[i] = (x, y)

        goal = (0, 0)
        # goal_arr = []

        if meanLL is not None and meanLR is not None and meanUR is not None and meanUL is not None:
            holeL = (int(meanUL[0]), int((meanLL[1] - meanUL[1]) / 2 + meanUL[1]))
            goal = holeL
            # holeR = (int(meanUR[0]), int((meanLR[1] - meanUR[1]) / 2 + meanUR[1]))
            # goal_arr.append(holeL)
            # goal_arr.append(holeR)

        return self.corners, goal, self.cross_array

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

import numpy as np
import cv2 as cv


class borders:

    def __init__(self):
        self.corners = []

    def find_barriers(self, frame):

        goal_arr = []
        corner_arr = []
        corner_LL_arr = []
        corner_LR_arr = []
        corner_UL_arr = []
        corner_UR_arr = []

        lower = np.array([0, 0, 100], dtype="uint8")
        upper = np.array([110, 70, 255], dtype="uint8")
        mask = cv.inRange(frame, lower, upper)
        frame2 = cv.bitwise_and(frame, frame, mask=mask)
        redEdges = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)

        # cv.imshow("output", np.hstack([frame2]))
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
                #cv.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Maintain a simples lookup list for points
                lines_list.append([(x1, y1), (x2, y2)])

        for x in lines_list:
            for y in lines_list:
                if y != x:
                    # print("this is line1: ", x[0], x[1])
                    # print("this is line2: ", y[0], y[1])
                    intersect = line_intersection(x, y)
                    # print("intersects at: ", intersect)
                    if (170 >= intersect[0] >= 130 or 890 >= intersect[0] >= 840) \
                            and (40 >= intersect[1] >= 0 or 570 >= intersect[1] >= 540):
                        # cv.circle(output, (int(intersect[0]), int(intersect[1])), 5, (255, 0, 0), -1)
                        # corner_arr.append((int(intersect[0]), int(intersect[1])))
                        if (890 >= intersect[0] >= 840 and 570 >= intersect[1] >= 540):
                            corner_LR_arr.append((int(intersect[0]) - 20, int(intersect[1]) - 20))

                        if (890 >= intersect[0] >= 840 and 40 >= intersect[1] >= 0):
                            corner_UR_arr.append((int(intersect[0]) - 20, int(intersect[1]) + 10))

                        if (170 >= intersect[0] >= 130 and 40 >= intersect[1] >= 0):
                            corner_UL_arr.append((int(intersect[0]) + 20, int(intersect[1]) + 10))

                        if (170 >= intersect[0] >= 130 and 570 >= intersect[1] >= 540):
                            corner_LL_arr.append((int(intersect[0]) + 20, int(intersect[1]) - 20))

        if corner_UL_arr is not None:
            meanUL = np.mean(corner_UL_arr, axis=(0))
            avg = (int(meanUL[0]), int(meanUL[1]))
            self.corners[0] = avg

        if corner_UR_arr is not None:
            meanUR = np.mean(corner_UR_arr, axis=(0))
            avg = (int(meanUR[0]), int(meanUR[1]))
            self.corners[1] = avg

        if corner_LL_arr is not None:
            meanLL = np.mean(corner_LL_arr, axis=(0))
            avg = (int(meanLL[0]), int(meanLL[1]))
            self.corners[2] = avg

        if corner_LR_arr is not None:
            meanLR = np.mean(corner_LR_arr, axis=(0))
            print(len(meanLR))
            avg = (int(meanLR[0]), int(meanLR[1]))
            self.corners[3] = avg

        holeL = (meanLL[1]) / 2
        goal_arr.append((int(meanUL[0]), int(holeL)))
        goal_arr.append((int(meanUL[0]), int(holeL) + 30))
        # print("HoleL: ", int(holeL), int(meanUL[0]))
        holeR = (meanLR[1]) / 2
        goal_arr.append((int(meanUR[0]), int(holeR)))
        goal_arr.append((int(meanUR[0]), int(holeR) + 50))
        # print("HoleR: ", int(holeR), int(meanUR[0]))

        return self.corners



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
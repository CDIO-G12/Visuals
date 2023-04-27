import numpy as np
import cv2 as cv


class borders:
    def __init__(self):
        self.corners = [] * 4

    def find_barriers(self, frame, hsv):
        self.corners = [None] * 4
        corner_LL_arr = []
        corner_LR_arr = []
        corner_UL_arr = []
        corner_UR_arr = []


        lower = np.array([0, 70, 50], dtype="uint8")
        upper = np.array([10, 255, 255], dtype="uint8")
        mask1 = cv.inRange(hsv, lower, upper)

        lower = np.array([170, 70, 50], dtype="uint8")
        upper = np.array([180, 255, 255], dtype="uint8")
        mask2 = cv.inRange(hsv, lower, upper)
        mask = mask1 | mask2
        frame2 = cv.bitwise_and(frame, frame, mask=mask)
        redEdges = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)

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
                #cv.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Maintain a simples lookup list for points
                lines_list.append([(x1, y1), (x2, y2)])

        upper = 40
        left = 200
        right = 890
        lower = 570
        interval = 100

        for x in lines_list:
            for y in lines_list:
                if y != x:
                    intersect = line_intersection(x, y)

                    if right >= intersect[0] >= (right - interval) and lower >= intersect[1] >= (lower - interval):
                        corner_LR_arr.append((int(intersect[0]) - 20, int(intersect[1]) - 20))

                    if right >= intersect[0] >= (right - interval) and upper >= intersect[1] >= 0:
                        corner_UR_arr.append((int(intersect[0]) - 20, int(intersect[1]) + 20))

                    if left >= intersect[0] >= 0 and upper >= intersect[1] >= 0:
                        corner_UL_arr.append((int(intersect[0]) + 20, int(intersect[1]) + 20))

                    if left >= intersect[0] >= 0 and lower >= intersect[1] >= (lower - interval):
                        corner_LL_arr.append((int(intersect[0]) + 20, int(intersect[1]) - 20))


        counter = 0
        #Denne kode er ugudeligt dårlig, og fuldstændigt fortabt. Skal cleanes up og gøres mere overskueligt.

        #while self.corners.count(None) <= 4:

        #Tilføjede dette array for at undgå IndexError: list index out of range.
        avg_corners = [] * 4

        if corner_UL_arr is not None and len(corner_UL_arr) > 0:
            meanUL = np.mean(corner_UL_arr, axis=(0))
            avg = (int(meanUL[0]), int(meanUL[1]))
            self.corners[0] = avg
            #self.corners[0] =avg
        else:
            avg = None

        if corner_UR_arr is not None and len(corner_UR_arr) > 0:
            meanUR = np.mean(corner_UR_arr, axis=(0))
            avg = (int(meanUR[0]), int(meanUR[1]))
            self.corners[1] = avg
            #self.corners.append(avg)
        else:
            avg = None

        if corner_LL_arr is not None and len(corner_LL_arr) > 0:
            meanLL = np.mean(corner_LL_arr, axis=(0))
            avg = (int(meanLL[0]), int(meanLL[1]))
            self.corners[2] = avg
            #self.corners.append(avg)
        else:
            avg = None

        if corner_LR_arr is not None and len(corner_LR_arr) > 0:
            meanLR = np.mean(corner_LR_arr, axis=(0))
            avg = (int(meanLR[0]), int(meanLR[1]))
            self.corners[3] = avg
            #self.corners.append(avg)
        else:
            avg = None

        """
        holeL = (meanLL[1]) / 2
        goal_arr.append((int(meanUL[0]), int(holeL)))
        goal_arr.append((int(meanUL[0]), int(holeL) + 30))
        # print("HoleL: ", int(holeL), int(meanUL[0]))
        holeR = (meanLR[1]) / 2
        goal_arr.append((int(meanUR[0]), int(holeR)))
        goal_arr.append((int(meanUR[0]), int(holeR) + 50))
        # print("HoleR: ", int(holeR), int(meanUR[0]))
        """

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
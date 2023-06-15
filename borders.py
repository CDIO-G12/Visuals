import math
import const as c
import numpy as np
import cv2 as cv


class Borders:
    def __init__(self):
        self.corners = [] * 4
        self.cross_array = [] * 4
        self.old_cross_array = [] * 4
        self.old_corners = [] * 4

# Determine position of the cross in the middle of the field.
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

    """""
    def borders_close_enough(self):
        if self.old_corners is None:
            return False

        for (x1, y1) in self.corners:
            match = False
            for (x2, y2) in self.old_corners:
                dist = np.abs(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
                if 10 >= dist:
                    match = True
                    break
            if not match:
                return False

        return True
    """

    def borders_close_enough(self): # TODO: check if this works, reliably. Samuel pointed out that sometimes a corners is detected in (0, 0).
        if self.old_corners is None:
            return False

        for (x1, y1) in self.corners:
            if all(np.abs(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5) > 10 for (x2, y2) in self.old_corners):
                return False

        return True

    def crosses_close_enough(self): # TODO: Make this work reliably.
        if self.old_cross_array is None:
            return False
        if any(x is None for x in self.cross_array):
            return False
        for (x1, y1) in self.cross_array:
            match = False
            for (x2, y2) in self.old_cross_array:
                dist = np.abs(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
                if 10 >= dist:
                    match = True
                    break
            if not match:
                return False

        return True

    # # calculate the position of the barriers.
    def find_barriers(self, frame, hsv):
        self.corners = [None] * 4
        self.cross_array = [None] * 4
        corner_LL_arr = []
        corner_LR_arr = []
        corner_UL_arr = []
        corner_UR_arr = []

        #frame = cv.medianBlur(frame, 11)
        #Initialize the upper and lower boundaries of the "orange" in the HSV color space
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


        new_width = int(c.WIDTH/4)
        new_height = int(c.HEIGHT/3)
        cropped_cross = redEdges[new_height:new_height*2, new_width:new_width*3]
        # Use canny edge detection
        edges = cv.Canny(redEdges, 50, 150, apertureSize=3)
        cross_edges = cv.Canny(cropped_cross, 50, 150, apertureSize=3)

        # Apply HoughLinesP method to
        # directly obtain line end points

        lines_list_borders = []
        lines_list_cross = []

        lines_for_borders = cv.HoughLinesP(
            edges,  # Input edge image
            1,  # Distance resolution in pixels
            np.pi / 180,  # Angle resolution in radians
            threshold=30,  # Min number of votes for valid line
            minLineLength=100,  # Min allowed length of line
            maxLineGap=20  # Max allowed gap between line for joining them
        )

        lines_for_cross = cv.HoughLinesP(
            cross_edges,  # Input edge image
            1,  # Distance resolution in pixels
            np.pi / 180,  # Angle resolution in radians
            threshold=40,  # Min number of votes for valid line
            minLineLength=50,  # Min allowed length of line
            maxLineGap=40  # Max allowed gap between line for joining them
        )

        if lines_for_borders is not None:
            # Iterate over points
            for points in lines_for_borders:
                # Extracted points nested in the list
                x1, y1, x2, y2 = points[0]
                # Draw the lines joining the points
                # On the original image
                cv.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Maintain a simples lookup list for points
                lines_list_borders.append([(x1, y1), (x2, y2)])

        if lines_for_cross is not None:
            # Iterate over points
            for points in lines_for_cross:
                # Extracted points nested in the list
                x1, y1, x2, y2 = points[0]
                # Draw the lines joining the points
                # On the original image
                x1 += new_width
                x2 += new_width
                y1 += new_height
                y2 += new_height
                # cv.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Maintain a simples lookup list for points
                lines_list_cross.append([(x1, y1), (x2, y2)])

        # Determine offsets
        upper = 0.025*c.HEIGHT
        lower = 1*c.HEIGHT
        left = 0.025*c.WIDTH 
        right = 0.98*c.WIDTH
        interval = 50
        offset = 20

        # Where borderlines intersect, draw edges.
        for x in lines_list_borders:
            for y in lines_list_borders:
                if y == x:
                    continue
                intersect = line_intersection(x, y)
                if right >= intersect[0] >= (right - interval) and lower >= intersect[1] >= (lower - interval):
                    corner_LR_arr.append((int(intersect[0]), int(intersect[1])))

                elif right >= intersect[0] >= (right - interval) and (upper+interval) >= intersect[1] >= upper:
                    corner_UR_arr.append((int(intersect[0]), int(intersect[1])))

                elif (left+interval) >= intersect[0] >= left and (upper+interval) >= intersect[1] >= upper:
                    corner_UL_arr.append((int(intersect[0]), int(intersect[1])))

                elif (left+interval) >= intersect[0] >= left and lower >= intersect[1] >= (lower - interval):
                    corner_LL_arr.append((int(intersect[0]), int(intersect[1])))

        for x in lines_list_cross:
            for y in lines_list_cross:
                if y == x:
                    continue
                points = {0: [x[0], y[0]], 1: [x[1], y[1]]}
                for key, value in points.items():
                    if math.dist(value[0], value[1]) <= offset:
                        avg = np.mean(value, axis=0)
                        self.check_point_in_cross(avg)

        """
        if self.cross_array and self.crosses_close_enough():
            self.cross_array = self.old_cross_array
        elif self.cross_array:
            self.old_cross_array = self.cross_array
        """

        # Calculate the average of the corners.
        corner_dict = {'UL': corner_UL_arr, 'UR': corner_UR_arr, 'LR': corner_LR_arr, 'LL': corner_LL_arr}

        for i, corner in enumerate(['UL', 'UR', 'LR', 'LL']):
            # print(corner, len(corner_dict[corner]))
            mean = np.mean(corner_dict[corner], axis=0) if corner_dict[corner] else None
            if mean is not None:
                x = int(mean[0]) + offset if i in [0, 3] else int(mean[0]) - offset
                y = int(mean[1]) + offset if i in [0, 1] else int(mean[1]) - offset
                self.corners[i] = (x, y)

        if all(self.corners) and self.borders_close_enough():
            self.corners = self.old_corners
        elif all(self.corners):
            self.old_corners = self.corners

        # Calculate the position of the goal.
        goal = (0, 0)
        if self.corners[0] is not None and self.corners[3] is not None:
            holeL = (int(self.corners[0][0]), int((self.corners[3][1] - self.corners[0][1]) / 2 + self.corners[0][1]))
            goal = holeL
            #print(self.corners[0], self.corners[3], goal)

        return self.corners, goal, self.cross_array

 
# Function to find the intersection of two lines. # find reference
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

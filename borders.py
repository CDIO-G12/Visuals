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
        # Checks all points for the cross and places them in the array based on their x and y values
        # At the end we should have an array with 4 points of the cross, in pairs.
        # min X
        if self.cross_array[0] is None or self.cross_array[0][0] >= avg[0]:
            self.cross_array[0] = avg
        # max X
        elif self.cross_array[1] is None or self.cross_array[1][0] <= avg[0]:
            self.cross_array[1] = avg
        # min Y
        elif self.cross_array[2] is None or self.cross_array[2][1] >= avg[1]:
            self.cross_array[2] = avg
        # max Y
        elif self.cross_array[3] is None or self.cross_array[3][1] <= avg[1]:
            self.cross_array[3] = avg

    # Funktion to check if we need to update the location of the borders
    def borders_close_enough(self):
        if self.old_corners is None:    # We update if there are no saved corners
            return False

        for (x1, y1) in self.corners:   # Checks if all corners are within 10 pixels of previous location
            if all(np.abs(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5) > 10 for (x2, y2) in self.old_corners):
                return False

        return True     # No update needed

    # Funktion to check if we need to update the cross points
    def crosses_close_enough(self):

        for i in range(4):
            dist = np.abs(((self.old_cross_array[i][0] - self.cross_array[i][0]) ** 2 + (self.old_cross_array[i][1] - self.cross_array[i][1]) ** 2) ** 0.5)
            if dist < 5 or dist > 50:   # If we have moved less than 5 or more than 50 then we dont need to update
                return False

        return True

    # # calculate the position of the barriers.
    def find_barriers(self, frame, hsv):
        # setting arrays to None
        self.corners = [None] * 4
        self.cross_array = [None] * 4

        # Making arrays for corners
        corner_LL_arr = []
        corner_LR_arr = []
        corner_UL_arr = []
        corner_UR_arr = []

        # New resolution for the cropped view we will be using
        new_width = int(c.WIDTH/5)
        new_height = int(c.HEIGHT/6)

        # Initialize the upper and lower boundaries of the "red" in the HSV color space
        # Since red has a hue around 0 we need two masks.
        # First mask
        lower = np.array([0, 170, 170], dtype="uint8")
        upper = np.array([5, 255, 255], dtype="uint8")
        mask1 = cv.inRange(hsv, lower, upper)

        # Second mask
        lower = np.array([175, 170, 170], dtype="uint8")
        upper = np.array([180, 255, 255], dtype="uint8")
        mask2 = cv.inRange(hsv, lower, upper)

        # Combine masks and then with fram
        mask = mask1 | mask2
        redEdges = cv.bitwise_and(frame, frame, mask=mask)

        # Gray scaling and making a cropped view for the cross
        gray_edges = cv.cvtColor(redEdges, cv.COLOR_BGR2GRAY)   # Apply gray scale to our image.
        cropped_edges = gray_edges[new_height:new_height * 5, new_width:new_width * 4]  # Crop the image, to fit to our borders.
        cropped_cross = cv.GaussianBlur(cropped_edges, (3, 3), 0)    # Apply Gaussian blur to our cropped image.

        # Apply Gaussian blur to our image.
        redEdges = cv.GaussianBlur(redEdges, (5, 5), 0)

        # Use canny edge detection
        edges = cv.Canny(redEdges, 50, 150, apertureSize=3)
        edges = cv.GaussianBlur(edges, (5, 5), 0)

        # Arrays for the lines found for the borders and cross
        lines_list_borders = []  # Array containing our lines, for our borders.
        lines_list_cross = []   # Array containing our lines, for our cross.

        # Determine offsets to differentiate between the different border corners
        upper = 0.025 * c.HEIGHT
        lower = 1 * c.HEIGHT
        left = 0.025 * c.WIDTH
        right = 0.98 * c.WIDTH
        interval = 50
        offset = 20

        # Apply HoughLinesP method to
        # directly obtain line end points

        # Determine the line-values for the borders.
        lines_for_borders = cv.HoughLinesP(
            edges,  # Input edge image
            1,  # Distance resolution in pixels
            np.pi / 180,  # Angle resolution in radians
            threshold=30,  # Min number of votes for valid line
            minLineLength=200,  # Min allowed length of line
            maxLineGap=20  # Max allowed gap between line for joining them
        )

        # Draw lines for the borders, on the image.
        if lines_for_borders is not None:
            # Iterate over points
            for points in lines_for_borders:
                # Extracted points nested in the list
                x1, y1, x2, y2 = points[0]
                # Draw the lines joining the points
                # On the original image
                # cv.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Maintain a simples lookup list for points
                lines_list_borders.append([(x1, y1), (x2, y2)])

        # Determine the line-values for the cross, for each case.
        # First if the cross is 90 degrees, and second if the cross is 45 degrees.
        threshold_arr = [80, 70]
        minLineLength_arr = [90, 70]
        maxLineGap_arr = [40, 50]

        for i in range(2):
            self.cross_array = [None] * 4
            lines_for_cross = cv.HoughLinesP(
                cropped_cross,  # Input edge image
                1,  # Distance resolution in pixels
                np.pi / 180,  # Angle resolution in radians
                threshold=threshold_arr[i],  # Min number of votes for valid line
                minLineLength=minLineLength_arr[i],  # Min allowed length of line
                maxLineGap=maxLineGap_arr[i]  # Max allowed gap between line for joining them
            )

            # Draw lines for the cross, on the image.
            if lines_for_cross is not None:
                distances = np.linalg.norm(lines_for_cross[:, 0, :2] - lines_for_cross[:, 0, 2:], axis=1)
                keep = distances <= 120
                lines_for_cross = lines_for_cross[keep]
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
                    cv.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    # Maintain a simples lookup list for points
                    lines_list_cross.append([(x1, y1), (x2, y2)])

            # Average out point on cross.
            for x in lines_list_cross:
                for y in lines_list_cross:
                    if y == x:
                        continue
                    # Look at the points in pairs x[0], y[0] and x[1], y[1]
                    points = {0: [x[0], y[0]], 1: [x[1], y[1]]}
                    for key, value in points.items():
                        # If the difference is low enough it must be an arm of the cross
                        if math.dist(value[0], value[1]) <= offset:
                            avg = np.mean(value, axis=0)    # Get the mean
                            # Insert into array using the functions
                            self.check_point_in_cross((int(avg[0]), int(avg[1])))
            if not all(self.cross_array):  # Checks if the first values for houghlinesP was good enough
                break

        # Check if all elements of self.cross_array are True using all() and that the cross hasn't moved.
        if all(self.cross_array) and (len(self.old_cross_array) < 1 or self.crosses_close_enough()):
            self.old_cross_array = self.cross_array
        else:
            self.cross_array = self.old_cross_array

        # Where borderlines intersect, draw edges.
        for x in lines_list_borders:
            for y in lines_list_borders:
                if y == x:
                    continue
                intersect = line_intersection(x, y)  # Do line intersection
                if intersect == (0, 0):  # If lines don't intersect
                    continue

                # Checks for which corner the intersection is in
                if right >= intersect[0] >= (right - interval) and lower >= intersect[1] >= (lower - interval):
                    corner_LR_arr.append((int(intersect[0]), int(intersect[1])))

                elif right >= intersect[0] >= (right - interval) and (upper+interval) >= intersect[1] >= upper:
                    corner_UR_arr.append((int(intersect[0]), int(intersect[1])))

                elif (left+interval) >= intersect[0] >= left and (upper+interval) >= intersect[1] >= upper:
                    corner_UL_arr.append((int(intersect[0]), int(intersect[1])))

                elif (left+interval) >= intersect[0] >= left and lower >= intersect[1] >= (lower - interval):
                    corner_LL_arr.append((int(intersect[0]), int(intersect[1])))

        # Calculate the average of the corners.
        corner_dict = {'UL': corner_UL_arr, 'UR': corner_UR_arr, 'LR': corner_LR_arr, 'LL': corner_LL_arr}

        for i, corner in enumerate(['UL', 'UR', 'LR', 'LL']):
            # print(corner, len(corner_dict[corner]))
            mean = np.mean(corner_dict[corner], axis=0) if corner_dict[corner] else None
            if mean is not None:
                # Offsets so we hit the actual corner
                x = int(mean[0]) + offset if i in [0, 3] else int(mean[0]) - offset
                y = int(mean[1]) + offset if i in [0, 1] else int(mean[1]) - offset
                self.corners[i] = (x, y)

        # Check if all elements of self.corners are True using all().
        # In which case save the old corners.
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

 
# Function to find the intersection of two lines.
# https://stackoverflow.com/questions/20677795/how-do-i-compute-the-intersection-point-of-two-lines
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

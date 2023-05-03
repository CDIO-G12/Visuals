import numpy as np
import cv2 as cv


class Borders:
    def __init__(self):
        self.corners = [] * 4

    def find_barriers(self, frame, hsv):
        #frame = cv.medianBlur(frame, 5)

        lower = np.array([0, 120, 50], dtype="uint8")
        upper = np.array([10, 255, 255], dtype="uint8")
        mask1 = cv.inRange(hsv, lower, upper)

        lower = np.array([170, 120, 50], dtype="uint8")
        upper = np.array([180, 255, 255], dtype="uint8")
        mask2 = cv.inRange(hsv, lower, upper)
        mask = mask1 | mask2
        frame2 = cv.bitwise_and(frame, frame, mask=mask)
        red_edges = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)

        resized = red_edges
        #resized = cv.resize(resized, (512, 384))
        cv.imshow("test", resized)

        # Start from the 1/3 down and find first red line
        # [y, x]
        current_pos = [int(len(frame)/3), int(len(frame[0])/2)]

        found = False
        while is_not_red(red_edges, current_pos) and is_not_red(red_edges, (current_pos[1], current_pos[0+3])):
            current_pos[0] -= 2
        cv.circle(resized, (current_pos[1], current_pos[0]), 5, (255, 0, 0), -1)
        current_pos[0] += 30

        while is_not_red(red_edges, current_pos) and is_not_red(red_edges, (current_pos[1-3], current_pos[0])):
            current_pos[1] += 2
        print(red_edges[current_pos[1]][current_pos[0]])
        current_pos[1] -= 10
        while is_not_red(red_edges, current_pos) and is_not_red(red_edges, (current_pos[1], current_pos[0+3])):
            current_pos[0] -= 2
        current_pos[1] += 10
        cv.circle(resized, (current_pos[1], current_pos[0]), 5, (255, 0, 0), -1)


        cv.circle(resized, (current_pos[1], current_pos[0]), 5, (255, 0, 0), -1)

        cv.imshow("test", resized)

        return self.corners, None


def is_not_red(frame, pos):
    if pos[1] >= len(frame)-4 or pos[0] >= len(frame[0])-4 or pos[1] < 3 or pos[0] < 3:
        return False

    try:
        return frame[pos[1]][pos[0]] < 80
    except IndexError:
        return False

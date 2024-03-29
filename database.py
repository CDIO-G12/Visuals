import utils as u
import numpy as np
import cv2 as cv
import locator as l
import const as c

LEFT = (0, 0)
RIGHT = (0, 0)
UP = (0, 0)
DOWN = (0, 0)


# Funktion to get the placement of the cross, settings file filled using the calibrator file
def read_settings_corners():
    global LEFT, RIGHT, UP, DOWN

    try:
        arr = np.loadtxt("settings.csv",
                         delimiter=",", dtype=int)

        i = 0
        for line in arr:
            if i == 3:
                LEFT = (line[3], line[4])
            elif i == 4:
                RIGHT = (line[3], line[4])
            elif i == 5:
                UP = (line[3], line[4])
            elif i == 6:
                DOWN = (line[3], line[4])
                break
            i += 1

        print("Got LRUD values from Settings.csv")
    except FileNotFoundError:
        pass



# Init databese
class Database:
    def __init__(self):
        read_settings_corners()
        self.balls = []
        self.robot = []
        self.robot_pos = None
        self.pixel_dist = 0
        self.orange = None
        self.robot_square = []
        self.oldGoal = [0, 0]
        self.sendBalls = 8
        self.corners = []
        self.cross = [LEFT, RIGHT, UP, DOWN]

    # Check position of balls, robot, orange, corners, crosses and goal and send to MM (MiddleMan).
    def check_and_send(self, s, balls, robot, orange, corner_array, cross_array, goal):

        if self.robot is not robot and robot is not None:
            self.robot = robot
            robot_pos = l.getAngleMidpointAndDist(robot)
            if robot_pos != self.robot_pos:
                self.robot_pos = robot_pos
                success = u.send(s, ("r/%d/%d/%d" % (self.robot_pos[0], self.robot_pos[1], self.robot_pos[2])))
                if not success:
                    return False
                if abs(self.pixel_dist- self.robot_pos[3]) > 0:
                    self.pixel_dist = self.robot_pos[3]
                    success = u.send(s, ("p/d/%f" % self.pixel_dist))
                    if not success:
                        return False

        if balls is None:
            balls = []
        # Send balls to MM
        if self.sendBalls >= 2:
            self.sendBalls = 0
            if not np.array_equal(self.balls, balls):
                self.balls = balls
                success = u.send(s, "b/r/r")
                if not success:
                    return False
                for (x, y) in balls:
                    success = u.send(s, ("b/%d/%d" % (x, y)))
                    if not success:
                        return False
                success = u.send(s, "b/d/d")
                if not success:
                    return False
        self.sendBalls += 1

        # Send orange to MM
        if self.orange is not None and orange is not None:
            if (orange == [0, 0] and self.orange == [0, 0]) or orange != [0, 0]:
                success = u.send(s, "o/%d/%d" % (orange[0], orange[1]))
                if not success:
                    return False
        self.orange = orange

        if corner_array is None and cross_array is None and goal is None:
            return True

        if goal is not None:
            if abs(self.oldGoal[0] - goal[0]) > 2 and (abs(self.oldGoal[1] - goal[1])) > 2:
                self.oldGoal = goal
                u.send(s, "g/%d/%d" % (goal[0], goal[1]))

        if len(corner_array) == 4 and self.corners is not corner_array:
            self.corners = corner_array
            counter = 0
            for corner in corner_array:
                if corner is None:
                    continue
                u.send(s, "c/%d/%d/%d" % (counter, corner[0], corner[1]))
                counter += 1

        if len(cross_array) != 4:
            cross_array = self.cross
            self.cross = []

        if len(cross_array) == 4 and self.cross is not cross_array:
            self.cross = cross_array
            counter = 0
            for corner in cross_array:
                if corner is None:
                    continue
                u.send(s, "m/%d/%d/%d" % (counter, corner[0], corner[1]))
                counter += 1
        return True

    # Highlight balls, robot, orange, corners, crosses and goal.
    def highlight(self, frame):

        if self.orange is not None and self.orange != (0, 0):
            cv.circle(frame, self.orange, 3, (0, 0, 0), 2)

        for ball in self.balls:
            cv.circle(frame, ball, 3, (40, 140, 0), 2)

        if self.cross is not None:
            for point in self.cross:
                cv.circle(frame, point, 1, (255, 255, 0), 1)

        if self.robot_pos is None:
            return
        pos = self.robot_pos

        if c.draw_robot:
            cv.circle(frame, (self.robot[0][0], self.robot[0][1]), 4, (187, 255, 0), 2)
            cv.circle(frame, (self.robot[1][0], self.robot[1][1]), 4, (170, 0, 255), 2)
            cv.rectangle(frame, (pos[0] - 2, pos[1] - 2), (pos[0] + 2, pos[1] + 2), (255, 255, 255), -1)

            coords = l.make_robot_square(self.robot)
            cv.circle(frame, coords[2], 4, (170, 0, 255), 2)
            cv.circle(frame, coords[3], 4, (187, 255, 0), 2)
            cv.line(frame, coords[0], coords[1], (255, 255, 255), 3)
            cv.line(frame, coords[1], coords[2], (255, 255, 255), 3)
            cv.line(frame, coords[2], coords[3], (255, 255, 255), 3)
            cv.line(frame, coords[0], coords[3], (255, 255, 255), 3)
        else:
            cv.circle(frame, (self.robot[0][0], self.robot[0][1]), 1, (187, 255, 0), 1)
            cv.circle(frame, (self.robot[1][0], self.robot[1][1]), 1, (170, 0, 255), 1)
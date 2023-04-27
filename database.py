import utils as u
import numpy as np
import cv2 as cv
import locator as l


class Database:
    def __init__(self):
        self.balls = []
        self.robot = []
        self.robot_pos = []
        self.pixel_dist = 0
        self.orange = (0, 0)

    def check_and_send(self, s, balls, robot, orange):
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

        if self.robot is not robot:
            self.robot = robot
            self.robot_pos = l.getAngleMidpointAndDist(robot)
            success = u.send(s, ("r/%d/%d/%d" % (self.robot_pos[0], self.robot_pos[1], self.robot_pos[2])))
            if not success:
                return False
            if self.pixel_dist != self.robot_pos[3]:
                self.pixel_dist = self.robot_pos[3]
                success = u.send(s, ("p/d/%f" % self.pixel_dist))
                if not success:
                    return False

        if self.orange is not orange:
            self.orange = orange
            success = u.send(s, "o/%d/%d" % (orange[0], orange[1]))
            if not success:
                return False

        return True

    def highlight(self, frame):
        pos = self.robot_pos
        cv.rectangle(frame, (pos[0] - 2, pos[1] - 2), (pos[0] + 2, pos[1] + 2), (255, 255, 255), -1)
        cv.rectangle(frame, (pos[0] - 50, pos[1] - 50), (pos[0] + 50, pos[1] + 50), (255, 255, 255), 2)
        cv.rectangle(frame, (pos[0] - 50, pos[1] - 50), (pos[0] + 50, pos[1] + 50), (255, 255, 255), 2)

        if self.orange is not (0, 0):
            cv.circle(frame, (self.orange[0], self.orange[1]), 3, (0, 0, 255), 2)

        for ball in self.balls:
            cv.circle(frame, (ball[0], ball[1]), 3, (255, 0, 255), 2)
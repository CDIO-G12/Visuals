import argparse
import math
import numpy as np

PINK = 160
GREEN = 82
ORANGE = 30


class Locator:
    def __init__(self):
        self.balancer = 0
        self.best = None
        self.circles = []
        self.last_robot = [[0, 0], [0, 0]]
        self.export = None

    def locate(self, hsv, circles, find_orange=True, ball_count=10):
        distances = ([])
        circles = np.round(circles[0, :]).astype("int")
        new_circles = []

        notBalls = []
        i = -1
        for (x, y, r) in circles:
            i += 1
            hsv_avg = int(hsv[y-1][x-1][0]/4 + hsv[y][x-1][0]/4 + hsv[y-1][x][0]/4 + hsv[y][x][0]/4)

            if hsv[y][x][2] < 150 or r < 6:
                notBalls.append((x, y))
                continue

            new_circles.append((x, y))

            if hsv[y][x][1] < 40:
                continue

            p_dist = hsv_distance_from_hue(hsv_avg, PINK) + ((255-hsv[y][x][1])/100)
            g_dist = hsv_distance_from_hue(hsv_avg, GREEN) + ((255-hsv[y][x][1])/100)
            if find_orange is True:
                o_dist = hsv_distance_from_hue(hsv_avg, ORANGE) + ((255-hsv[y][x][1])/100)
            else:
                o_dist = 9999

            m = min(p_dist, g_dist, o_dist)
            if m == p_dist:
                distances.append((0, m, (x, y)))
            elif m == g_dist:
                distances.append((1, m, (x, y)))
            else:
                distances.append((2, m, (x, y)))
            # print((x, y), (hsv_avg, hsv[y][x][1], hsv[y][x][2]), (p_dist, g_dist, o_dist))

        best_val = [9999, 9999, 9999]
        best_ball = [(0, 0), (0, 0), None]
        for dist in distances:
            type = dist[0]
            if dist[1] < best_val[type]:
                best_val[type] = dist[1]
                best_ball[type] = dist[2]

        orange = None
        if find_orange and best_ball[2] is not None:
            orange = best_ball[2]
            new_circles.remove(best_ball[2])

        robot = [best_ball[0], best_ball[1]]
        if best_ball[0] in new_circles:
            new_circles.remove(best_ball[0])
        if best_ball[1] in new_circles:
            new_circles.remove(best_ball[1])

        if robot != self.last_robot:
            temp = robot
            robot = self.last_robot
            self.last_robot = temp
        else:
            self.last_robot = robot

        if new_circles == self.best:
            self.balancer += 1
        else:
            self.balancer = 0

        if self.balancer > 2:
            self.circles = new_circles
            self.export = new_circles

        self.best = new_circles

        if self.export is None:
            self.export = new_circles

        return self.export, robot, orange




def hsv_distance_from_hue(hsv_hue, hue):
    dist = min(abs(hsv_hue - hue), abs(hsv_hue - (hue - 180)))
    return dist

def is_ball(hsv, sat):
    #print(hsv)
    return hsv[1] < 20 and hsv[2] > 200

def is_orange_ball(hsv):
    threshold_range = 20
    orange = 30
    return (orange - threshold_range) < hsv[0] < (orange + threshold_range) and hsv[1] > 50 and hsv[2] > 150

# pink
def is_robot_left(hsv):
    threshold_range = 10
    pink = 160
    return (pink - threshold_range) < hsv[0] < (pink + threshold_range) and hsv[1] > 80 and hsv[2] > 127

# green
def is_robot_right(hsv):
    threshold_range = 20
    green = 82
    #print(hsv)
    return (green - threshold_range) < hsv[0] < (green + threshold_range) and hsv[1] > 60 and hsv[2] > 127


def getAngleMidpointAndDist(robot_pos):
    myradians = math.atan2(robot_pos[0][1]-robot_pos[1][1], robot_pos[0][0]-robot_pos[1][0])
    mydegrees = int(math.degrees(myradians))
    middlex = int((robot_pos[0][0]+robot_pos[1][0])/2)
    middley = int((robot_pos[0][1]+robot_pos[1][1])/2)
    dist = math.sqrt(math.pow(robot_pos[0][0]-robot_pos[1][0], 2)+math.pow(robot_pos[0][1]-robot_pos[1][1], 2))
    return middlex, middley, mydegrees, dist


def is_robot(frame):
    #print(frame)
    return frame[0] < 160 and frame[1] > 180 and frame[2] > 230

import argparse
import math
import numpy as np

PINK = 160
GREEN = 82
ORANGE = 30


class locator:
    def __init__(self):
        self.balancer = 0
        self.best = None
        self.circles = []
        self.export_best = [[0, 0], [0, 0]]
        self.indexes = []

    def locate(self, hsv, circles, find_orange=True, ball_count=10):
        distances = ([], [], [])
        circles = np.round(circles[0, :]).astype("int")

        for (x, y, r) in circles:
            hsv_avg = int(hsv[y-1][x-1][0]/4 + hsv[y][x-1][0]/4 + hsv[y-1][x][0]/4 + hsv[y][x][0]/4)
            p_dist = hsv_distance_from_hue(hsv_avg, PINK) #* ((255-hsv[y][x][1]))
            g_dist = hsv_distance_from_hue(hsv_avg, GREEN) #* ((255-hsv[y][x][1]))
            o_dist = hsv_distance_from_hue(hsv_avg, ORANGE) #* ((255-hsv[y][x][1]))

            if hsv[y][x][1] < 40:
                p_dist = 99999
                g_dist = 99999
                o_dist = 99999

            distances[0].append(p_dist)
            distances[1].append(g_dist)
            if find_orange:
                distances[2].append(o_dist)

            #print((x, y), (hsv_avg, hsv[y][x][1], hsv[y][x][2]), (p_dist, g_dist, o_dist))


        best = []
        indexes = []
        for dist_list in distances:
            smallest = min(dist_list)
            index = dist_list.index(smallest)
            (x, y, r) = circles[index]
            best.append([x, y])
            indexes.append(index)

        if find_orange:
            if best[2] in best[0:1]:
                #print("or", str(best))
                find_orange = False


        if best == self.best:
            self.balancer += 1
        else:
            self.balancer = 0

        if self.balancer > 5:
            self.export_best = best
            self.indexes = indexes
            self.circles = circles
        self.best = best

        new_circles = []
        for i in range(len(self.circles)):
            if i not in self.indexes:
                (x, y, r) = self.circles[i]
                new_circles.append((x, y))


        orange = [0, 0]
        if len(self.export_best) > 2 and find_orange:
            orange = self.export_best[2]

        return new_circles, [self.export_best[0], self.export_best[1]], orange




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

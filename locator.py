import math
import numpy as np
import const as c
from statistics import median
from shapely.geometry import Point, Polygon

PINK = 180
GREEN = 50
ORANGE = 20
MIN_SAT = 50
MIN_VAL = 75

# Function to get settings values from our calibrator.
def read_settings():
    global PINK, GREEN, ORANGE, MIN_SAT, MIN_VAL

    try:
        arr = np.loadtxt("settings.csv",
                         delimiter=",", dtype=int)
        sat = 200
        val = 200
        i = 0
        for line in arr:
            if line[1] < sat:
                sat = line[1]
            if line[2] < val:
                val = line[2]

            if i == 0:
                PINK = line[0]
            elif i == 1:
                GREEN = line[0]
            elif i == 2:
                ORANGE = line[0]
                break
            i += 1
        MIN_SAT = sat
        if MIN_SAT < 50:
            MIN_SAT = 50
        MIN_VAL = int(val*0.7)
        if MIN_VAL < 50:
            MIN_VAL = 50

        MIN_VAL = 75
        MIN_SAT = 20
        print("Got PGO values from Settings.csv")
    except FileNotFoundError:
        pass


# Calculate the position of the robot.
def calculate_robot_position(robot):
    # Constants
    robot_dist_cm = 18.5  # cm distance between circles on robot
    cam_height = c.CAM_HEIGHT  # Camera height in cm, from ground
    robot_height = 9.5  # Robot height in cm, from ground

    # Calculate pixel ratio
    if robot is None:
        return robot

    pd = getPixelDist(robot)
    if pd == 0:
        print(robot)
    pixel_ratio = robot_dist_cm / pd

    x_axis = c.WIDTH / 2
    y_axis = c.HEIGHT / 2
    mid_point = (x_axis, y_axis)

    # Calculate robot positions
    for i in range(2):
        hyp = getPixelDist([mid_point, robot[i]]) * pixel_ratio
        angle = np.arctan(cam_height / hyp)
        dx = 0.70 * robot_height / np.tan(angle)

        p_help = (x_axis, robot[i][1])
        katete = getPixelDist([p_help, mid_point]) * pixel_ratio
        new_angle = np.arcsin(katete/hyp)
        y_diff = (np.sin(new_angle) * dx)/pixel_ratio
        x_diff = (np.cos(new_angle) * dx)/pixel_ratio

        x_direction = -1 if robot[i][0] > x_axis else 1
        y_direction = -1 if robot[i][1] > y_axis else 1
        new_x = int(robot[i][0] + (x_direction * x_diff))
        new_y = int(robot[i][1] + (y_direction * y_diff))
        robot[i] = (new_x, new_y)

    return robot


# Draw the square around the robot. Effectively works as a bounding box for the robot.
def make_robot_square(robot):
    mydegrees = getAngle(robot) + 90
    gx = int(robot[1][0] + (100 * np.cos(mydegrees * np.pi / 180)))
    gy = int(robot[1][1] + (100 * np.sin(mydegrees * np.pi / 180)))

    px = int(robot[0][0] + (100 * np.cos(mydegrees * np.pi / 180)))
    py = int(robot[0][1] + (100 * np.sin(mydegrees * np.pi / 180)))
    coords = [robot[0], robot[1], (gx, gy), (px, py)]
    return coords


def calculate_average_hue(hue_values):
    sum_angle = 0
    count = 0

    for hue in hue_values:
        angle = (hue * 2) * (2 * math.pi) / 360
        sum_angle += angle
        count += 1

    average_angle = sum_angle / count
    average_hue = average_angle * 360 / (2 * math.pi)

    if average_hue < 0:
        average_hue += 360
    elif average_hue >= 360:
        average_hue -= 360

    return int(average_hue/2)

class Locator:
    def __init__(self):
        self.old_orange = None
        self.orange_balancer = 0
        self.balancer = 0
        self.best = None
        self.circles = []
        self.last_robot = None
        self.export = None
        read_settings()

    def locate(self, hsv, circles, area_border, find_orange=True, ball_count=10):
        min_sat = 60
        distances = ([])
        circles = np.round(circles[0, :]).astype("int")  # convert circles to ints
        new_circles = []

        i = -1
        # Loop through all circles
        for (x, y, r) in circles:
            i += 1

            hue_avg, sat_avg, val_avg = 0, 0, 0
            hues = []
            try:
                ky = -1
                for kx in [-1, 0, 1, -1, 0, 1, -1, 0, 1]:
                    j = 0
                    hues.append(hsv[y + ky][x + kx][j])
                    j += 1
                    sat_avg += int(hsv[y + ky][x + kx][j] / 9)
                    j += 1
                    val_avg += int(hsv[y + ky][x + kx][j] / 9)

                    if kx == 1:
                        ky += 1
            except IndexError:
                continue
            hue_avg = calculate_average_hue(hues)  # calculate average hue for the circle

            # print((x, y, r), (hue_avg, sat_avg, val_avg))

            # Determine if a ball has been seen inside the robot
            if self.last_robot is not None:
                coords = make_robot_square(self.last_robot)
                poly = Polygon(coords)
                p = Point(x, y)
                if p.within(poly):
                    #print("Ball inside robot")
                    continue

            # Determine if a ball is seen outside borders
            if area_border is not None:
                p = Point(x, y)
                if not p.within(area_border):
                    pass
                    #continue

            new_circles.append((x, y))

            # White ball found
            if sat_avg < min_sat:
                continue



            # Calculate distance to the different colours, effectively determining which
            # ball is the best match for the different coloured balls
            p_dist = hsv_distance_from_hue(hue_avg, PINK) + ((255-sat_avg)/10)
            g_dist = hsv_distance_from_hue(hue_avg, GREEN) + ((255-sat_avg)/10)
            if find_orange:  # If we have not found an orange ball yet
                o_dist = hsv_distance_from_hue(hue_avg, ORANGE) + ((255-sat_avg)/10)
            else:
                o_dist = 9999

            # Calculating which dist is smallest, so that we can determine which colour it fits best
            m = min(p_dist, g_dist, o_dist)
            # Appends to list with index based on the colour it fits the best
            if m == p_dist:
                distances.append((0, m, (x, y)))
            elif m == g_dist:
                distances.append((1, m, (x, y)))
            else:
                #print((x, y), (hue_avg, hsv[y][x][1], hsv[y][x][2]), (p_dist, g_dist, o_dist))
                distances.append((2, m, (x, y)))

        best_val = [9999, 9999, 9999]

        best_ball = [(0, 0), (0, 0), None]

        for dist in distances:
            ball_type = dist[0]
            if dist[1] < best_val[ball_type]:
                best_val[ball_type] = dist[1]
                best_ball[ball_type] = dist[2]

        orange = (0, 0)

        if best_ball[2] is None:
            self.orange_balancer += 1
        else:
            self.orange_balancer = 0

        if find_orange:
            if best_ball[2] is not None:
                self.old_orange = best_ball[2]
                orange = best_ball[2]
                new_circles.remove(best_ball[2])
            elif self.orange_balancer < 3:
                orange = self.old_orange

        robot = None

        # Calculate the best candidates for the pink and green ball, and calculate the robot position
        # with respect to perspective distortion.
        if best_ball[0] != (0, 0) and best_ball[1] != (0, 0) and is_close(best_ball[0], best_ball[1], 300):
            """if self.last_robot is None:  # If we have not seen a robot yet
                robot = [best_ball[0], best_ball[1]]
                self.last_robot = robot
            elif self.robot_pos_stabilizer([best_ball[0], best_ball[1]]):
                robot = [best_ball[0], best_ball[1]]
                self.last_robot = robot
            else:
                robot = self.last_robot
            """
            robot = [best_ball[0], best_ball[1]]
            if c.PERSPECTIVE_OFFSET and robot is not None:
                robot = calculate_robot_position(robot)

        if best_ball[0] in new_circles:
            new_circles.remove(best_ball[0])
        if best_ball[1] in new_circles:
            new_circles.remove(best_ball[1])


        if self.balls_close_enough(new_circles):
            self.balancer += 1
        else:
            self.balancer = 0

        if self.balancer > 3:
            self.circles = new_circles
            self.export = new_circles

        self.best = new_circles

        if self.export is None:
            self.export = new_circles

        return self.export, robot, orange

    # Determine whether the new circles are close enough to the old circles
    # to be considered the same.
    def balls_close_enough(self, new_circles):
        if self.best is None:
            return True

        for (x1, y1) in new_circles:
            match = False
            for (x2, y2) in self.best:
                dist = np.abs(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
                if 5 >= dist:
                    match = True
                    break
            if not match:
                return False

        return True

    # If the position of the robot's balls (hehe) differs too much from the previous position, return false.
    def robot_pos_stabilizer(self, robot_pos):

        if robot_pos is None:
            return False

        for (x1, y1) in self.last_robot:
            match = False
            for (x2, y2) in robot_pos:
                dist = np.abs(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)
                if 50 >= dist:
                    match = True
                    break
            if not match:
                return False
        return True

# Determine whether two points are close enough to be considered the same.
def hsv_distance_from_hue(hsv_hue, hue):
    dist = min(abs(hsv_hue - hue), abs(hsv_hue - (hue - 180)))
    return dist

# Determine whether ball is white.
def is_ball(hsv, sat):
    #print(hsv)
    return hsv[1] < 20 and hsv[2] > 200


# Determine whether ball is orange.
def is_orange_ball(hsv):
    threshold_range = 20
    orange = 30
    return (orange - threshold_range) < hsv[0] < (orange + threshold_range) and hsv[1] > 50 and hsv[2] > 150


# Track position of pink guide circle.
def is_robot_left(hsv):
    threshold_range = 10
    pink = 160
    return (pink - threshold_range) < hsv[0] < (pink + threshold_range) and hsv[1] > 80 and hsv[2] > 127


# Track position of green guide circle.
def is_robot_right(hsv):
    threshold_range = 20
    green = 82
    #print(hsv)
    return (green - threshold_range) < hsv[0] < (green + threshold_range) and hsv[1] > 60 and hsv[2] > 127


# Calculate the angle and position of the robot based on the position of the balls
def getAngleMidpointAndDist(robot_pos):
    myradians = math.atan2(robot_pos[0][1]-robot_pos[1][1], robot_pos[0][0]-robot_pos[1][0])
    mydegrees = int(math.degrees(myradians))
    middlex = int((robot_pos[0][0]+robot_pos[1][0])/2)
    middley = int((robot_pos[0][1]+robot_pos[1][1])/2)
    dist = getPixelDist(robot_pos)
    return middlex, middley, mydegrees, dist


# Calculate angle.
def getAngle(point_array):
    myradians = math.atan2(point_array[0][1] - point_array[1][1], point_array[0][0] - point_array[1][0])
    return int(math.degrees(myradians))

# Calculate distance between two points in pixels.
def getPixelDist(robot_pos):
    return math.sqrt(math.pow(robot_pos[0][0] - robot_pos[1][0], 2) + math.pow(robot_pos[0][1] - robot_pos[1][1], 2))


# Check if the robot is in the correct position.
def is_robot(frame):
    return frame[0] < 160 and frame[1] > 180 and frame[2] > 230

# See if point1 is close to point2
def is_close(point1, point2, thresh=5):
    x = abs(point1[0] - point2[0])
    y = abs(point1[1] - point2[1])
    dist = math.sqrt(x**2 + y**2)
    return dist < thresh

def gen_mask(frame, hue):
    lower_hue = hue - 10
    upper_hue = hue + 10

    if lower_hue < 0 or upper_hue > 100:
        lower = np.array([0, MIN_SAT, 50], dtype="uint8")
        upper = np.array([10, 255, 255], dtype="uint8")
        mask1 = cv.inRange(frame, lower, upper)

        lower = np.array([170, MIN_SAT, 50], dtype="uint8")
        upper = np.array([180, 255, 255], dtype="uint8")
        mask2 = cv.inRange(frame, lower, upper)
        mask = mask1 | mask2
        return mask
    else:
        lower = np.array([lower_hue, MIN_SAT, MIN_VAL], dtype="uint8")
        upper = np.array([upper_hue, 255, 255], dtype="uint8")
        mask = cv.inRange(frame, lower, upper)
        return mask






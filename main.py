import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np
from time import sleep
import argparse
import socket
import select
import math
import borders



VIDEO = False # Set to true if camera not connected
#HOST = "localhost"  # The server's hostname or IP address
HOST = "192.168.0.102"  # The server's hostname or IP address
PORT = 8888  # The port used by the server

wall_defined = True
corner_defined = True

corner_array = []

drawPoints = []
guideCorners = [(), (), (), ()]

WHITE = 180


def checkData(s):
    try:
        readable = [s]
        r, w, e = select.select(readable, [], [], 0)
        for rs in r:  # iterate through readable sockets
            # read from a client
            data = rs.recv(1024)
            if not data:
                readable.remove(rs)
                rs.close()
            else:
                return data
    except ValueError or ConnectionResetError:
        return None
    return None

def send(s, package):
    try:
        package += "\n"
        #print(package)
        s.sendall(package.encode())
    except:
        s.close()
        return False
    return True

def is_ball_old(frame):
    return frame[0] > WHITE and frame[1] > WHITE and frame[2] > WHITE

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
    return (middlex, middley, mydegrees, dist)

def is_robot(frame):
    #print(frame)
    return frame[0] < 160 and frame[1] > 180 and frame[2] > 230

#Fix this function
def is_close(old, new):
    return new < old + 2 and new > old - 2





# print line_intersection((A, B), (C, D))
pixelDist = 0
ballsToFind = 2
countBalls = 0
saturation = 5
edges_sent = False
ballFound = True
lastHsvNumber = 0
oldOrange = (0, 0)
border_i = 0
dump_frame = 1
oldGoal = None

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
        except:
            sleep(0.5)
            continue
        print("Got new connection!\n")

        borderInstance = borders.borders()

        if VIDEO:
            cap = cv.VideoCapture('video/videotest1.mp4')
        else:
            cap = cv.VideoCapture(0, cv.CAP_DSHOW)

        if not cap.isOpened():
            print("Cannot open camera")
            cap.release()
            exit()

        #Resolution
        cap.set(cv.CAP_PROP_FRAME_WIDTH, 1024)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, 768)
        cap.set(cv.CAP_PROP_AUTO_EXPOSURE, 1)
        # cap.set(cv.CAP_PROP_FPS, 20)

        circles_backup = []
        robot = [0, 0, 0]

        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            # if frame is read correctly ret is True
            if not ret:
                if VIDEO:
                    cap.set(cv.CAP_PROP_POS_FRAMES, 0) # this make the video loop
                    continue
                print("Can't receive frame (stream end?). Exiting ...")
                exit()

            if dump_frame >= 5:
                dump_frame = 0
                continue
            dump_frame += 1

            # Our operations on the frame come here
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            gray = cv.medianBlur(gray, 5)
            output = frame.copy()
            # frame = cv.medianBlur(frame,10)

            lower = np.array([100, 60, 0], dtype="uint8")
            upper = np.array([140, 180, 255], dtype="uint8")
            mask = cv.bitwise_not(cv.inRange(hsv, lower, upper))
            frame = cv.bitwise_and(frame, frame, mask=mask)

            cv.imshow("masked", frame)

            if border_i <= 0:
                border_i = 10
                corner_array, goal = borderInstance.find_barriers(frame, hsv)
                if goal is not oldGoal:
                    oldGoal = goal
                    send(s, "g/%d/%d" % (goal[0], goal[1]))
                cv.rectangle(output, (goal[0] - 2, goal[1] - 2), (goal[0] + 2, goal[1] + 2), (255, 255, 255), -1)


            for x in corner_array:
                cv.circle(output, x, 5, (255, 0, 0), -1)
                cv.imshow("output", frame)

                counter = 0
                if corner_array:
                    edges_sent = True
                    #print("Corners: ")
                    for corner in corner_array:
                        if corner is None:
                            continue
                        send(s, "c/%d/%d/%d" % (counter, corner[0], corner[1]))
                        #print(corner)
                        counter += 1
            border_i -= 1

            temp_circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, 5, param1=75, param2=20, minRadius=2, maxRadius=10)
            # ensure at least some circles were found

            sleep(0.01)

            found_robot = [False, False]
            robot_l_r = [[0, 0], [0, 0]]

            circles = []

            if temp_circles is not None and len(temp_circles) > 0:
                if countBalls != len(temp_circles):  # if we have lost a ball
                    diff = countBalls - len(temp_circles)
                    if diff < 0:
                        countBalls = 0
                    else:
                        countBalls -= diff

                # convert the (x, y) coordinates and radius of the circles to integers
                temp_circles = np.round(temp_circles[0, :]).astype("int")
                # loop over the (x, y) coordinates and radius of the circles
                for (x, y, r) in temp_circles:

                    if not ballFound and countBalls < ballsToFind and lastHsvNumber > 150:
                        saturation += 5
                        print("Sat: ", saturation)
                    ballFound = False
                    if not is_ball(hsv[y][x], saturation):
                        if is_orange_ball(hsv[y][x]):
                            cv.rectangle(output, (x - 2, y - 2), (x + 2, y + 2), (255, 255, 0), -1)
                            ballFound = True
                            if not np.array_equal(oldOrange, (x,y)):
                                send(s, "o/%d/%d" % (x, y))
                                #print("New orange position")
                            oldOrange = (x,y)
                        elif is_robot_right(hsv[y][x]):
                            cv.rectangle(output, (x - 2, y - 2), (x + 2, y + 2), (0, 0, 255), -1)
                            found_robot[1] = True
                            robot_l_r[1] = (x,y)
                            ballFound = True
                        elif is_robot_left(hsv[y][x]):
                            cv.rectangle(output, (x - 2, y - 2), (x + 2, y + 2), (0, 255, 0), -1)
                            found_robot[0] = True
                            robot_l_r[0] = (x,y)
                            ballFound = True
                        else:
                            print("Circle not known: ", hsv[y][x])

                        lastHsvNumber = hsv[y][x][2]
                        continue
                    
                    countBalls += 1
                    ballFound = True
                    circles.append((x,y,r))
                    # draw the circle in the output image, then draw a rectangle
                    # corresponding to the center of the circle
                    cv.circle(output, (x, y), r, (0, 255, 0), 4)
                    # print(x,", ", y)
                    cv.rectangle(output, (x - 2, y - 2), (x + 2, y + 2), (0, 128, 255), -1)
                
                if found_robot[0] and found_robot[1]:
                    pos = getAngleMidpointAndDist(robot_l_r)
                    cv.rectangle(output, (pos[0] - 2, pos[1] - 2), (pos[0] + 2, pos[1] + 2), (255, 255, 255), -1)
                    cv.rectangle(output, (pos[0] - 50, pos[1] - 50), (pos[0] + 50, pos[1] + 50), (255, 255, 255), 2)
                    cv.rectangle(output, (pos[0] - 50, pos[1] - 50), (pos[0] + 50, pos[1] + 50), (255, 255, 255), 2)
                    if robot[0] != pos[0] and robot[1] != pos[1] and robot[2] != pos[2]:
                        success = send(s, ("r/%d/%d/%d" % (pos[0], pos[1], pos[2])))
                        if not success:
                            break
                        robot[0] = pos[0] #x
                        robot[1] = pos[1] #y
                        robot[2] = pos[2] #r
                        #print("Send: " + ("r/%d/%d/%d" % (pos[0], pos[1], pos[2])))
                    if pixelDist != pos[3]:
                        pixelDist = pos[3]
                        success = send(s, ("p/d/%f" % pixelDist))
                        if not success:
                            break

            # show the output image
            # cv.imshow("output", np.hstack([frame, output]))
            else:
                cv.imshow("output", gray)

            if circles is None:
                continue
            if not np.array_equal(circles, circles_backup):
                circles_backup = circles
                success = send(s, "b/r/r")
                if not success:
                    break
                for circle in circles:
                    success = send(s, ("b/%d/%d" % (circle[0], circle[1])))
                    if not success:
                        break
                success = send(s, "b/d/d")
                if not success:
                    break

            data = checkData(s)
            if data is not None:
                drawPoints = []
                spl = data.decode().split("\n")
                for parts in spl:
                    innerSplit = parts.split("/")
                    try:
                        if innerSplit[0] == "gc" and len(innerSplit) > 3:
                            innerSplit = [int(i) for i in innerSplit[1:]]
                            guideCorners[innerSplit[0]] = (innerSplit[1], innerSplit[2])

                        if len(innerSplit) < 5:
                            continue
                        innerSplit = [int(i) for i in innerSplit]
                        drawPoints.append((innerSplit[0], innerSplit[1], (innerSplit[2], innerSplit[3], innerSplit[4])))
                    except ValueError:
                        pass

            if drawPoints is not None and drawPoints is not []:
                for point in drawPoints:
                    cv.rectangle(output, (point[0] - 10, point[1] - 10), (point[0] + 10, point[1] + 10), point[2], 1)

            if len(guideCorners) == 4 and guideCorners[0] != ():
                cv.line(output, guideCorners[0], guideCorners[1], (200, 200, 200), 1)
                cv.line(output, guideCorners[1], guideCorners[2], (200, 200, 200), 1)
                cv.line(output, guideCorners[2], guideCorners[3], (200, 200, 200), 1)
                cv.line(output, guideCorners[3], guideCorners[0], (200, 200, 200), 1)


            # resized = cv.resize(np.hstack([output]), (512, 384))
            cv.imshow("output", np.hstack([output]))
            #cv.imshow("gray", gray)
            

            # Display the resulting frame
            #cv.imshow('frame', gray)
            if cv.waitKey(1) == ord('q'):
                exit(0)
        s.close()
        print("Lost connection.")

    # When everything done, release the capture
    cap.release()

    cv.destroyAllWindows()

import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np
from time import sleep
import argparse
import socket
import math
import borders





HOST = "localhost"  # The server's hostname or IP address
#HOST = "192.168.0.102"  # The server's hostname or IP address
PORT = 8888  # The port used by the server

wall_defined = True
corner_defined = True

corner_array = []
circles_backup = []

 
WHITE = 180

def send(s, package):
    #print(package)
    try:
        s.sendall(package.encode())
    except:
        s.close()
        return False
    return True

def is_ball_old(frame):
    return frame[0] > WHITE and frame[1] > WHITE and frame[2] > WHITE

def is_ball(hsv, sat):
    #print(hsv)
    return hsv[1] < sat and hsv[2] > 150

def orange_ball(hsv):
    threshold_range = 20
    # print(hsv, hsv_red)
    return (hsv[0] > (30 - threshold_range) or hsv[0] < (30 + threshold_range)) and hsv[1] > 60 and hsv[2] > 150

# pink
def is_robot_left(hsv):
    threshold_range = 20
    #print(hsv, hsv_red)
    return (hsv[0] > (160- threshold_range) or hsv[0] < (160+ threshold_range)) and hsv[1] > 100 and hsv[2] > 150

# green
def is_robot_right(hsv):
    threshold_range = 20
    green = np.uint8([[[200,255,0 ]]])
    hsv_green = cv.cvtColor(green,cv.COLOR_BGR2HSV)
    return hsv[0] > (hsv_green[0][0][0] - threshold_range) and hsv[0] < (hsv_green[0][0][0] + threshold_range) and hsv[1] > 35 and hsv[2] > 127

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
robot = [0,0,0]
pixelDist = 0
ballsToFind = 4
countBalls = 0
saturation = 5
edges_sent = False
ballFound = True
lastHsvNumber = 0
oldOrange = (0, 0)

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
        except:
            sleep(0.5)
            continue
        print("Got new connection!\n")

        borderInstance = borders.borders()


        cap = cv.VideoCapture(1, cv.CAP_DSHOW)
        #cap = cv.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open camera")
            cap.release()
            exit()

        #Resolution
        cap.set(cv.CAP_PROP_FRAME_WIDTH, 1024)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, 768)
        cap.set(cv.CAP_PROP_AUTO_EXPOSURE, 1)
        # cap.set(cv.CAP_PROP_FPS, 20)

        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            # if frame is read correctly ret is True
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                exit()
            # Our operations on the frame come here
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            gray = cv.medianBlur(gray, 5)
            output = frame.copy()
            # frame = cv.medianBlur(frame,10)

            corner_array = borderInstance.find_barriers(frame)

            for x in corner_array:
                cv.circle(output, x, 5, (255, 0, 0), -1)


            counter = 1
            if corner_array is not None and not edges_sent:
                edges_sent = True
                for x in corner_array:
                    send(s, "c/%d/%d/%d" % (counter, x[0], x[1]))
                    counter += 1
                    sleep(0.001)




            temp_circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, 5, param1=75, param2=20, minRadius=2, maxRadius=10)
            sleep(0.10)
            # ensure at least some circles were found

            found_robot = [False, False]
            robot_l_r = [[0, 0], [0, 0]]

            circles = []



            if temp_circles is not None:

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
                        if orange_ball(hsv[y][x]):
                            cv.rectangle(output, (x - 2, y - 2), (x + 2, y + 2), (0, 255, 0), -1)
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
                        sleep(0.001)
                    if pixelDist != pos[3]:
                        pixelDist = pos[3]
                        #s.sendall((b"p/d/%f" % pixelDist))
                        sleep(0.001)
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
                #s.sendall("b/r/r".encode())
                for circle in circles:
                    success = send(s, ("b/%d/%d" % (circle[0], circle[1])))
                    if not success:
                        break
                    #s.sendall((b"b/%d/%d" % (circle[0], circle[1])))
                    sleep(0.1)
                success = send(s, "b/d/d")
                if not success:
                    break
                #print("send new coordinates" + str(circles))


            
            cv.imshow("output", np.hstack([frame, output]))
            #cv.imshow("gray", gray)
            

            # Display the resulting frame
            # cv.imshow('frame', gray)
            if cv.waitKey(1) == ord('q'):
                break

    # When everything done, release the capture
    cap.release()

    cv.destroyAllWindows()

import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np
from time import sleep
import argparse
import socket
import math


HOST = "localhost"  # The server's hostname or IP address
#HOST = "192.168.0.102"  # The server's hostname or IP address
PORT = 8888  # The port used by the server

wall_defined = True
corner_defined = True
corner_UR = False
corner_UL = False
corner_LR = False
corner_LL = False

goal_arr = []
corner_arr = []
corner_LL_arr = []
corner_LR_arr = []
corner_UL_arr = []
corner_UR_arr = []
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
    print(hsv)
    return  hsv[1] < sat and hsv[2] > 150

# red
def is_robot_left(hsv):
    threshold_range = 40
    red = np.uint8([[[0,0,255 ]]])
    hsv_red = cv.cvtColor(red,cv.COLOR_BGR2HSV)
    #print(hsv, hsv_red)
    return (hsv[0] > (180- 10) or hsv[0] < (hsv_red[0][0][0] + threshold_range)) and hsv[1] > 50 and hsv[2] > 127

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
#def is_close(old, new):
#    return new < old + 2 and new > old - 2

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

def find_barriers():
    lower = np.array([0, 0, 100], dtype="uint8")
    upper = np.array([110, 70, 255], dtype="uint8")
    mask = cv.inRange(frame, lower, upper)
    frame2 = cv.bitwise_and(frame, frame, mask=mask)
    redEdges = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)

    # cv.imshow("output", np.hstack([frame2]))
    # Use canny edge detection
    edges = cv.Canny(redEdges, 50, 150, apertureSize=3)
    # Apply HoughLinesP method to
    # to directly obtain line end points
    lines_list = []
    lines = cv.HoughLinesP(
        edges,  # Input edge image
        1,  # Distance resolution in pixels
        np.pi / 180,  # Angle resolution in radians
        threshold=30,  # Min number of votes for valid line
        minLineLength=5,  # Min allowed length of line
        maxLineGap=40  # Max allowed gap between line for joining them
    )

    if lines is not None:
        # Iterate over points
        for points in lines:
            # Extracted points nested in the list
            x1, y1, x2, y2 = points[0]
            # Draw the lines joining the points
            # On the original image
            cv.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Maintain a simples lookup list for points
            lines_list.append([(x1, y1), (x2, y2)])

    for x in lines_list:
        for y in lines_list:
            if y != x:
                # print("this is line1: ", x[0], x[1])
                # print("this is line2: ", y[0], y[1])
                intersect = line_intersection(x, y)
                # print("intersects at: ", intersect)
                if (170 >= intersect[0] >= 130 or 890 >= intersect[0] >= 840) \
                        and (40 >= intersect[1] >= 0 or 570 >= intersect[1] >= 540):
                    #cv.circle(output, (int(intersect[0]), int(intersect[1])), 5, (255, 0, 0), -1)
                    #corner_arr.append((int(intersect[0]), int(intersect[1])))
                    if (890 >= intersect[0] >= 840 and 570 >= intersect[1] >= 540):
                        corner_LR_arr.append((int(intersect[0]) - 20, int(intersect[1]) - 20))

                    if (890 >= intersect[0] >= 840 and 40 >= intersect[1] >= 0):
                        corner_UR_arr.append((int(intersect[0]) - 20, int(intersect[1]) + 10))

                    if (170 >= intersect[0] >= 130 and 40 >= intersect[1] >= 0):
                        corner_UL_arr.append((int(intersect[0]) + 20, int(intersect[1]) + 10))

                    if (170 >= intersect[0] >= 130 and 570 >= intersect[1] >= 540):
                        corner_LL_arr.append((int(intersect[0]) + 20, int(intersect[1]) - 20))


    meanUL = np.mean(corner_UL_arr, axis=(0))
    avg = (int(meanUL[0]), int(meanUL[1]))
    corner_arr.append(avg)

    meanUR = np.mean(corner_UR_arr, axis=(0))
    avg = (int(meanUR[0]), int(meanUR[1]))
    corner_arr.append(avg)

    meanLL = np.mean(corner_LL_arr, axis=(0))
    avg = (int(meanLL[0]), int(meanLL[1]))
    corner_arr.append(avg)

    meanLR = np.mean(corner_LR_arr, axis=(0))
    avg = (int(meanLR[0]), int(meanLR[1]))
    corner_arr.append(avg)




    holeL = (meanLL[1])/2
    goal_arr.append((int(meanUL[0]), int(holeL)))
    goal_arr.append((int(meanUL[0]), int(holeL) + 30))
    print("HoleL: ", int(holeL), int(meanUL[0]))
    holeR = (meanLR[1])/2
    goal_arr.append((int(meanUR[0]), int(holeR)))
    goal_arr.append((int(meanUR[0]), int(holeR) + 50))
    print("HoleR: ", int(holeR), int(meanUR[0]))





    for x in corner_arr:
        cv.circle(output, x, 5, (255, 0, 0), -1)




# print line_intersection((A, B), (C, D))
robot = [0,0,0]
pixelDist = 0
ballsToFind = 5
countBalls = 0
saturation = 5
edges_sent = False
ballFound = True
lastHsvNumber = 0
while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
        except:
            sleep(0.5)
            continue
        print("Got new connection!\n")
        
        cap = cv.VideoCapture(0, cv.CAP_DSHOW)
        #cap = cv.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open camera")
            cap.release()
            exit()

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


            find_barriers()

            counter = 1
            if corner_arr is not None and not edges_sent:
                edges_sent = True
                for x in corner_arr:
                    send(s, "c/%d/%d/%d" % (counter, x[0], x[1]))
                    counter += 1
                    sleep(0.001)




            temp_circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, 5, param1=75, param2=20, minRadius=2, maxRadius=10)
            sleep(0.10)
            # ensure at least some circles were found

            found_robot = [False, False]
            robot_l_r = [[0, 0], [0, 0]]

            circles = []
            if countBalls != len(temp_circles): # if we have lost a ball
                countBalls = 0

            if temp_circles is not None:
                # convert the (x, y) coordinates and radius of the circles to integers
                temp_circles = np.round(temp_circles[0, :]).astype("int")
                # loop over the (x, y) coordinates and radius of the circles
                for (x, y, r) in temp_circles:
                    print("Sat: ", saturation)

                    if not ballFound and countBalls < ballsToFind and lastHsvNumber > 150:
                        saturation += 5
                    ballFound = False
                    if not is_ball(hsv[y][x], saturation):
                        if is_robot_right(hsv[y][x]):
                            cv.rectangle(output, (x - 2, y - 2), (x + 2, y + 2), (0, 0, 255), -1)
                            found_robot[1] = True
                            robot_l_r[1] = (x,y)
                            ballFound = True
                        elif is_robot_left(hsv[y][x]):
                            cv.rectangle(output, (x - 2, y - 2), (x + 2, y + 2), (0, 255, 0), -1)
                            found_robot[0] = True
                            robot_l_r[0] = (x,y)
                            ballFound = True

                        lastHsvNumber = hsv[y][x][2]

                        print("HSV: ", hsv[y][x])
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
            else:
                success = send(s, "b/r/r")
                if not success:
                    break
                #s.sendall("b/r/r".encode())
                for circle in circles:
                    success = send(s, ("b/%d/%d" % (circle[0], circle[1])))
                    if not success:
                        break
                    #s.sendall((b"b/%d/%d" % (circle[0], circle[1])))
                    sleep(0.001)
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

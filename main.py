import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np
from time import sleep
import socket
import borders as borders
import database as db
import locator as l
import utils as u
import os

VIDEO = False # Set to true if camera not connected
VIDEOFILE = 'video/combined.mp4'
CAMERASOURCE = 0
#HOST = "localhost"  # The server's hostname or IP address
HOST = "192.168.0.102"  # The server's hostname or IP address
PORT = 8888  # The port used by the server

wall_defined = True
corner_defined = True

corner_array = []

drawPoints = []
ballOrder = []
guideCorners = [(), (), (), ()]

WHITE = 180




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

print("Waiting on MiddleMan")
source = os.environ.get("SOURCE")
if source is not None:
    if source.lower() == "video":
        VIDEO = True
    else:
        VIDEO = False
        CAMERASOURCE = int(source)


while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
        except ConnectionRefusedError:
            sleep(0.5)
            continue
        print("Got new connection!\n")

        if VIDEO:
            cap = cv.VideoCapture(VIDEOFILE)
        else:
            cap = cv.VideoCapture(CAMERASOURCE, cv.CAP_DSHOW)

        if not cap.isOpened():
            print("Cannot open camera")
            cap.release()
            exit()

        # Resolution
        cap.set(cv.CAP_PROP_FRAME_WIDTH, 1024)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, 768)
        cap.set(cv.CAP_PROP_AUTO_EXPOSURE, 1)
        # cap.set(cv.CAP_PROP_FPS, 20)

        borderInstance = borders.Borders()
        database = db.Database()
        locator = l.Locator()

        circles_backup = []

        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            # if frame is read correctly ret is True
            if not ret:
                if VIDEO:
                    cap.set(cv.CAP_PROP_POS_FRAMES, 0)  # this make the video loop
                    continue
                print("Can't receive frame (stream end?). Exiting ...")
                exit()

            # Our operations on the frame come here
            hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            gray = cv.medianBlur(gray, 5)


            output = frame.copy()

            lower = np.array([0, 0, 0], dtype="uint8")
            upper = np.array([255, 255, 180], dtype="uint8")
            mask = cv.bitwise_not(cv.inRange(hsv, lower, upper))
            frame = cv.bitwise_and(frame, frame, mask=mask)

            if border_i <= 0:
                border_i = 10
                corner_array, goal = borderInstance.find_barriers(output, hsv)
                if goal is not None:
                    if goal is not oldGoal:
                        oldGoal = goal
                        u.send(s, "g/%d/%d" % (goal[0], goal[1]))
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
                        u.send(s, "c/%d/%d/%d" % (counter, corner[0], corner[1]))
                        #print(corner)
                        counter += 1
            border_i -= 1

            temp_circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, 5, param1=75, param2=20, minRadius=2, maxRadius=10)
            # ensure at least some circles were found


            #sleep(0.01)

            found_robot = [False, False]
            robot_l_r = [[0, 0], [0, 0]]

            orange = None
            robot = None
            circles = None

            if temp_circles is not None and len(temp_circles) > 0:
                circles, robot, orange = locator.locate(hsv, temp_circles)

            # show the output image
            # cv.imshow("output", np.hstack([frame, output]))
            else:
                cv.imshow("output", gray)

            if circles is None:
                continue

            success = database.check_and_send(s, circles, robot, orange)
            if not success:
                break
            database.highlight(output)

            data = u.check_data(s)  # read from middleman
            if data is not None:
                first = True
                spl = data.decode().split("\n")
                for parts in spl:

                    innerSplit = parts.split("/")

                    try:
                        if innerSplit[0] == "check" and len(innerSplit) > 2:
                            innerSplit = [int(i) for i in innerSplit[1:]]
                            if u.check_for_ball(hsv[innerSplit[1]][innerSplit[2]]):
                                u.send(s, "f/t/0")
                            else:
                                u.send(s, "f/f/0")
                            continue

                        if innerSplit[0] == "b" and len(innerSplit) > 2:
                            if first:
                                ballOrder = []
                                first = False
                            innerSplit = [int(i) for i in innerSplit[1:]]
                            ballOrder.append((innerSplit[0], (innerSplit[1], innerSplit[2] + 15)))
                            continue

                        if innerSplit[0] == "gc" and len(innerSplit) > 3:
                            innerSplit = [int(i) for i in innerSplit[1:]]
                            guideCorners[innerSplit[0]] = (innerSplit[1], innerSplit[2])

                        if len(innerSplit) < 5:
                            continue
                        if first:
                            drawPoints = []
                            first = False
                        innerSplit = [int(i) for i in innerSplit]
                        # x/y/r/g/b
                        drawPoints.append((innerSplit[0], innerSplit[1], (innerSplit[2], innerSplit[3], innerSplit[4])))
                    except ValueError:
                        pass

            if drawPoints is not None and drawPoints is not []:
                for point in drawPoints:
                    cv.rectangle(output, (point[0] - 10, point[1] - 10), (point[0] + 10, point[1] + 10), point[2], 1)

            if ballOrder is not None and ballOrder is not []:
                for ball in ballOrder:
                    cv.putText(output, str(ball[0]), ball[1], cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
                               cv.LINE_AA)

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


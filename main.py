import datetime

import cv2 as cv
import numpy as np
from time import sleep
from shapely.geometry import Point, Polygon
import socket
import borders as borders
import database as db
import locator as l
import utils as u
import os
import const as c


# booleans
exclamation = False

# arrays from class borders
corner_array = []
cross_array = []

# arrays from class locator
drawPoints = []
ballOrder = []
guideCorners = [(), (), (), ()]

# variable to keep track of how often we calculate borders and middle cross
border_i = 0


print("Waiting on MiddleMan")

# Getting correct camera source
source = os.environ.get("SOURCE")
VIDEO = False
CAMERASOURCE = c.CAMERASOURCE
if source is not None:
    if source.lower() == "video":
        VIDEO = True
    else:
        CAMERASOURCE = int(source)


# funktion to check if robot is outside of border, returns true if robot is outside.
def emergency(pPoint, gPoint, area_border):
    p1 = Point(pPoint)
    p2 = Point(gPoint)
    if p1.within(area_border) and p2.within(area_border):
        return False
    else:
        return True

# Crop funktion to crop the sides off the video
ORIGINAL_WIDTH = c.WIDTH
if c.CROP:  # check boolean
    # calculate new width
    crop_width = c.WIDTH - c.CROP_AMOUNT
    c.WIDTH -= c.CROP_AMOUNT * 2



# Main loop
while True:
    # Connecting to middle man
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((c.HOST, c.PORT))
        except ConnectionRefusedError or TimeoutError:
            sleep(0.5)
            continue
        print("Got new connection!\n")

        cv.namedWindow('output')

        # If statement to decide wether to use a videofile or live camera
        if c.VIDEO or VIDEO:
            cap = cv.VideoCapture(c.VIDEOFILE)
            c.CROP = True
        else:
            cap = cv.VideoCapture(CAMERASOURCE, cv.CAP_DSHOW)

        # Error handling for opening camera
        if not cap.isOpened():
            print("Cannot open camera")
            cap.release()
            exit()

        # Resolution
        cap.set(cv.CAP_PROP_FRAME_WIDTH, ORIGINAL_WIDTH)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, c.HEIGHT)
        cap.set(cv.CAP_PROP_AUTO_EXPOSURE, 1)
        cap.set(cv.CAP_PROP_AUTOFOCUS, 0)
        if c.CONTRAST is not None:
            cap.set(cv.CAP_PROP_CONTRAST, c.CONTRAST)

        # Frame
        frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

        # If expected resolution does not match actual resolution of camera, would effect calculations
        if not VIDEO and (frame_width != ORIGINAL_WIDTH or frame_height != c.HEIGHT):
            print("Error: Wrong resolution, got: " + str(frame_width) + "x" + str(frame_height) + ", expected: " + str(ORIGINAL_WIDTH) + "x" + str(c.HEIGHT))
            exit()

        # Creating instances of other classes
        borderInstance = borders.Borders()
        database = db.Database()
        locator = l.Locator()

        # Define the codec and create VideoWriter object.The output is stored in 'output.avi' file.
        if c.RECORD:
            # Using datetime to create unique file names
            out_c = cv.VideoWriter('recordings/outputCLEAN-' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.avi',
                                 cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (frame_width, frame_height))
            out = cv.VideoWriter('recordings/output-' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.avi',
                                 cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (frame_width, frame_height))
        else:
            out_c = cv.VideoWriter('recordings/outputCLEAN.avi', cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (c.WIDTH, c.HEIGHT))
            out = cv.VideoWriter('recordings/output.avi', cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (c.WIDTH, c.HEIGHT))

        find_orange = True

        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            # if frame is read correctly ret is True
            if not ret:
                if VIDEO:
                    cap.set(cv.CAP_PROP_POS_FRAMES, 0)  # this make the video loop, sets frame to 0
                    continue
                print("Can't receive frame (stream end?). Exiting ...")
                exit()

            if c.CROP:  # Changes frames resolution to cropped resolution
                frame = frame[:, c.CROP_AMOUNT:crop_width]

            # Our operations on the frame come here
            hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            gray = cv.GaussianBlur(gray, (5, 5), 0)


            output = frame.copy()
            out_c.write(output)

            picFrame = frame
            # define colour borders for our mask
            lower = np.array([0, 0, 0], dtype="uint8")
            upper = np.array([255, 255, 180], dtype="uint8")
            mask = cv.bitwise_not(cv.inRange(hsv, lower, upper))
            frame = cv.bitwise_and(frame, frame, mask=mask)

            area_border = None

            # Determines how often we detect borders and cross, every 'x' amount of frame
            if border_i <= 0:
                border_i = 1    # resets counter until next detection
                corner_array, goal, cross_array = borderInstance.find_barriers(output, hsv)  # call to bordersclass
                if goal is not None:  # show goal if found
                    cv.rectangle(output, (goal[0] - 2, goal[1] - 2), (goal[0] + 2, goal[1] + 2), (255, 255, 255), -1)

                for x in corner_array:  # show corners found
                    cv.circle(output, x, 5, (255, 0, 0), -1)

                for point in cross_array:  # show cross points found
                    if point is not None:
                        cv.circle(output, (int(point[0]), int(point[1])), 5, (255, 0, 0), -1)

                if all(corner_array):  # if 4 corners are found we create a polygon to use for checking.
                    area_border = Polygon(corner_array)
            else:   # else set all to None so that we ignore them
                corner_array = None
                cross_array = None
                goal = None
            border_i -= 1  # decrement counter for checking borders...

            # ensure at least some circles were found
            found_robot = [False, False]
            robot_l_r = [[0, 0], [0, 0]]

            # checks if we have found any circles

            circles, robot, orange = locator.locate(hsv, gray, frame, area_border, find_orange)
            if circles is None and robot is None and orange is None:
                continue

            cv.imshow("output", output)

            # Check if robot is inside our borders
            if robot is not None and not [(0, 0), (0, 0)] and False:  # only check if currently have some coordinates
                robot_outline = l.make_robot_square(robot)  # Calculating outline of robot

                # If statement only prints once everytime robot goes outside borders.
                if emergency(robot_outline[2], robot_outline[3], area_border) and not exclamation:
                    exclamation = True
                    u.send(s, '!')
                    print("!")
                if not emergency(robot_outline[2], robot_outline[3], area_border) and exclamation:
                    exclamation = False
                    print("good to go")

            if circles is None:
                continue

            # send data to middleman.
            success = database.check_and_send(s, circles, robot, orange, corner_array, cross_array, goal)
            if not success:
                break
            database.highlight(output)

            # read from middleman
            data = u.check_data(s)
            if data is not None:
                first = True
                spl = data.decode().split("\n")
                for parts in spl:
                    if parts.startswith("no"):
                        find_orange = False
                        continue

                    innerSplit = parts.split("/")  # Segments messages into parts, seperated by '/'

                    try:
                        # Check to see if a ball is present or not.
                        if innerSplit[0] == "check" and len(innerSplit) > 2:
                            innerSplit = [int(i) for i in innerSplit[1:]]
                            if u.check_for_ball(hsv[innerSplit[1]][innerSplit[2]]):
                                u.send(s, "f/t/0")
                            else:
                                u.send(s, "f/f/0")
                            continue

                        # Send ball order to middleman.
                        if innerSplit[0] == "b" and len(innerSplit) > 2:
                            if first:
                                ballOrder = []
                                first = False
                            innerSplit = [int(i) for i in innerSplit[1:]]
                            ballOrder.append((innerSplit[0], (innerSplit[1], innerSplit[2] + 15)))
                            continue

                        # Send guide corners to middleman.
                        if innerSplit[0] == "gc" and len(innerSplit) > 3:
                            innerSplit = [int(i) for i in innerSplit[1:]]
                            guideCorners[innerSplit[0]] = (innerSplit[1], innerSplit[2])

                        # Draw square highlighting of balls.
                        if len(innerSplit) < 5:
                            continue
                        if first:
                            drawPoints = []
                            first = False
                        innerSplit = [int(i) for i in innerSplit]
                        # x/y/r/g/b
                        drawPoints.append((innerSplit[0], innerSplit[1], (innerSplit[2], innerSplit[3], innerSplit[4])))
                    except ValueError or IndexError:
                        pass

            # Draw square around target balls.
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



            # Write the frame into the file 'output.avi'
            out.write(output)

            # Compress output and send stream to middleman.
            if border_i == 9 and c.STREAM:
                resized = cv.resize(output, (512, 384))
                _, img_encoded = cv.imencode(".jpg", resized)
                u.send(s, img_encoded.tobytes(), False)

            # Display the resulting frame
            cv.imshow("output", output)

            # Functionality for closing program and saving frames.
            k = cv.waitKey(1)
            if k == ord('q'):
                exit(0)
            elif k == ord(' '):
                # SPACE pressed
                img_name = "opencv_frame_{}.png".format(1)
                cv.imwrite(img_name, picFrame)
                print("{} written!".format(img_name))

        s.close()
        print("Lost connection.")

        cv.destroyAllWindows()
        out.release()

    # When everything done, release the capture
    cap.release()



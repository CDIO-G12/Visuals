import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np
import argparse

cap = cv.VideoCapture(0, cv.CAP_DSHOW)
#cap = cv.VideoCapture(2)
if not cap.isOpened():
	print("Cannot open camera")
	exit()
while True:
	# Capture frame-by-frame
	ret, frame = cap.read()
	# if frame is read correctly ret is True
	if not ret:
		print("Can't receive frame (stream end?). Exiting ...")
		break
	# Our operations on the frame come here
	gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
	gray = cv.medianBlur(gray,5)
	output = frame.copy()
	#frame = cv.medianBlur(frame,10)

	circles = cv.HoughCircles(gray,cv.HOUGH_GRADIENT,1,20,param1=75,param2=20,minRadius=3,maxRadius=10)
   # ensure at least some circles were found
	if circles is not None:
		# convert the (x, y) coordinates and radius of the circles to integers
		circles = np.round(circles[0, :]).astype("int")
		# loop over the (x, y) coordinates and radius of the circles
		for (x, y, r) in circles:
			# draw the circle in the output image, then draw a rectangle
			# corresponding to the center of the circle
			cv.circle(output, (x, y), r, (0, 255, 0), 4)
			cv.rectangle(output, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)
		# show the output image
		cv.imshow("output", np.hstack([frame, output]))
	else:
		cv.imshow("output", gray)


	
	lower = np.array([0, 0, 100], dtype = "uint8")
	upper = np.array([50, 50, 255], dtype = "uint8")
	mask = cv.inRange(frame, lower, upper)
	frame2 = cv.bitwise_and(frame, frame, mask = mask)
	gray = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)
	
	#cv.imshow("output", np.hstack([frame2]))
	# Use canny edge detection
	edges = cv.Canny(gray,50,150,apertureSize=3)
	# Apply HoughLinesP method to 
	# to directly obtain line end points
	lines_list =[]
	lines = cv.HoughLinesP(
				edges, # Input edge image
				1, # Distance resolution in pixels
				np.pi/180, # Angle resolution in radians
				threshold=100, # Min number of votes for valid line
				minLineLength=75, # Min allowed length of line
				maxLineGap=50 # Max allowed gap between line for joining them
				)
	
	if lines is not None:
		# Iterate over points
		for points in lines:
			# Extracted points nested in the list
			x1,y1,x2,y2=points[0]
			# Draw the lines joing the points
			# On the original image
			cv.line(output,(x1,y1),(x2,y2),(0,255,0),2)
			# Maintain a simples lookup list for points
			lines_list.append([(x1,y1),(x2,y2)])
		cv.imshow("output", np.hstack([frame, output]))


	# Display the resulting frame
	# cv.imshow('frame', gray)
	if cv.waitKey(1) == ord('q'):
		break
# When everything done, release the capture
cap.release()

cv.destroyAllWindows()
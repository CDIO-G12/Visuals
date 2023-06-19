
STREAM = False  # Set variable 'STREAM' to 'TRUE' to stream video
RECORD = True  # Set variable 'RECORD' to 'TRUE' to record video
VIDEO = False # Set env variable 'SOURCE' to 'VIDEO' if camera is not connected

draw_robot = True  # Set to true if robot should be drawn

VIDEOFILE = 'video/outputCLEAN.avi'  # Define which video file to use
CAMERASOURCE = 0

#WIDTH = 800
#HEIGHT = 600

WIDTH = 1920
HEIGHT = 1080

#WIDTH = 1280
#HEIGHT = 720
CONTRAST = None

CROP = True  # Crop the output image.
CROP_AMOUNT = 150  #Amount of pixels to crop from each side.

CAM_HEIGHT = 150  # Height of the camera in cm.
BORDER = 1  # Border around the image.

PERSPECTIVE_OFFSET = True  # Rectify the image for perspective offset.

HOST = "localhost"  # The server's hostname or IP address
#HOST = "192.168.0.102"  # The server's hostname or IP address
#HOST = "192.168.0.103"  # The Mark's hostname or IP address
PORT = 8888  # The port used by the server


STREAM = False  # Set variable 'STREAM' to 'TRUE' to stream video
RECORD = False  # Set variable 'RECORD' to 'TRUE' to record video
VIDEO = False   # Set env variable 'SOURCE' to 'VIDEO' if camera is not connected

draw_robot = True  # Set to true if robot should be drawn

VIDEOFILE = 'video/outputCLEAN3.avi'  # Define which video file to use
CAMERASOURCE = 0    #   Define which camera to use.

# Define the resolution of the camera.
WIDTH = 1280
HEIGHT = 720
CONTRAST = None # Set the contrast of the camera. default = None.

CROP = True  # Crop the output image.
CROP_AMOUNT_X = 150  #Amount of pixels to crop from each side.
#CROP_AMOUNT_Y = 100  #Amount of pixels to crop from each top.

CAM_HEIGHT = 150  # Height of the camera in cm.
ROBOT_HEIGHT = 15.5  # Height of the tracking point in cm.
TRACKING_DISTANCE = 20.5 # Distance between the tracking points in cm.
CAM_HEIGHT = 150  # Height of the camera in cm.
BORDER = 3 # How often the border will

PERSPECTIVE_OFFSET = True  # Rectify the image for perspective offset.

CROSS_BOOL = True   # Draw cross on the image.
HOST = "localhost"  # The server's hostname or IP address
#HOST = "192.168.0.102"  # The server's hostname or IP address
#HOST = "192.168.0.103"  # The Mark's hostname or IP address
PORT = 8888  # The port used by the server

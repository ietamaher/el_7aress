import sys
from PyQt5.QtCore import QThread, pyqtSignal
import jetson_inference
import jetson_utils
import time
import numpy as np
from jetson_utils import cudaImage, cudaToNumpy
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.Qt import Qt

class VideoFeedThread(QThread):
    frameCaptured = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.isRunning = True
        self.camera = jetson_utils.videoSource("/dev/video1")  # Adjust for your camera /dev/video1")#
        #self.parent.enableDetection.connect(self.handle_enableDetection, Qt.DirectConnection)
        self.enable_detection = 0 
        self.net = jetson_inference.detectNet("ssd-mobilenet-v2", threshold=0.5)  # Adjust


    def handle_enableDetection(self, value):
        self.enable_detection = value
        print(value)


    def run(self):

        while self.isRunning:
            # Capture the frame
            frame = self.camera.Capture()
            if frame is None:
                print("Failed to capture frame from camera")
                continue

            # Desired dimensions and aspect ratio
            desired_width = 800
            desired_height = 600
            desired_aspect = desired_width / desired_height

            # Original dimensions
            orig_width = frame.width
            orig_height = frame.height

            # Calculate crop dimensions to maintain aspect ratio
            if orig_width / orig_height > desired_aspect:
                # Original is too wide
                crop_width = int(orig_height * desired_aspect)
                crop_height = orig_height
                x_offset = int((orig_width - crop_width) / 2)
                y_offset = 0
            else:
                # Original is too tall
                crop_width = orig_width
                crop_height = int(orig_width / desired_aspect)
                x_offset = 0
                y_offset = int((orig_height - crop_height) / 2)


            # Compute the ROI as (left, top, right, bottom)
            crop_roi = (x_offset, y_offset, x_offset + crop_width, y_offset + crop_height)

            # Allocate the output image, with the cropped size
            cropped_frame = jetson_utils.cudaAllocMapped(width=crop_width,
                                                        height=crop_height,
                                                        format=frame.format)

            # Crop the image to the ROI
            jetson_utils.cudaCrop(frame, cropped_frame, crop_roi)

            # Allocate the output image for resizing
            resized_frame = jetson_utils.cudaAllocMapped(width=desired_width,
                                                        height=desired_height,
                                                        format=frame.format)

            # Resize the cropped image to the desired dimensions
            jetson_utils.cudaResize(cropped_frame, resized_frame)

            # Perform object detection (if necessary)
            if (self.enable_detection):
                detections = self.net.Detect(resized_frame, overlay="none" )
                # Populate the detections message.
                for single_detection in detections:


                    center_x = single_detection.Center[0] 
                    center_y = single_detection.Center[1]
                    width = single_detection.Width
                    height = single_detection.Height
                    x1 = center_x - width / 2
                    x2 = center_x + width / 2
                    y1 = center_y - height / 2
                    y2 = center_y + height / 2


                    jetson_utils.cudaDrawLine(resized_frame, (int(x1), int(y1)), (int(x2), int(y1)), tuple([230, 0, 0, 100]), 2)
                    jetson_utils.cudaDrawLine(resized_frame, (int(x1), int(y1)), (int(x1), int(y2)), tuple([230, 0, 0, 100]), 2)
                    jetson_utils.cudaDrawLine(resized_frame, (int(x1), int(y2)), (int(x2), int(y2)), tuple([230, 0, 0, 100]), 2)
                    jetson_utils.cudaDrawLine(resized_frame, (int(x2), int(y1)), (int(x2), int(y2)), tuple([230, 0, 0, 100]), 2)
			    

 
                #print("Network ", self.net.GetNetworkFPS(),  " FPS")

            mapped_array = cudaToNumpy(resized_frame)
            self.frameCaptured.emit(resized_frame)
            time.sleep(0.03)

    def stop(self):
        self.isRunning = False
        self.wait()

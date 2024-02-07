import time
from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor, QFont , QPainter, QPen ,  QPainterPath, QTransform, QBrush

from PyQt5.QtCore import QThread, pyqtSignal, QTimer 
from PyQt5.Qt import Qt, QMetaObject, Q_ARG
from VideoFeedThread import VideoFeedThread
from PyQt5.QtWidgets import QLabel, QApplication, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QPainter, QPen, QTransform
from PyQt5.QtCore import Qt

from DDS.Query_msg import Query_msg
from DDS.Response_msg import Response_msg, Response_msgPubSubType
from DDS.JoystickData import JoystickData, JoystickDataPubSubType
import math
from dds_threads import MotorSubscriberThread, PLCSubscriberThread
from dds_threads import JoySubscriberThread
from dds_threads import PublisherThread, PLC_PublisherThread
from dds_threads import ActionData, fireActionData

from UI.ControlPanel import ControlPanel
from UI.VideoWidget import VideoWidget
from UI.VideOvelay import VideOvelay
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')



class MainWindow(QMainWindow):
    updateAzimuthSignal = pyqtSignal(int)
    enableDetection = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Setup the layout and video label
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.setGeometry(100, 100, 800, 600)

        self.controlPanel = ControlPanel(self)
        #self.videoOverlay = VideOvelay(self)

        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)  # Set all margins to zero
        self.layout.setSpacing(0)  # Set the spacing to zero        
        self.videoWidget = VideoWidget(self)
        self.layout.addWidget(self.videoWidget)
        self.centralWidget.setLayout(self.layout)


        # Layout setup
        self.videoThread = VideoFeedThread()
        self.videoThread.frameCaptured.connect(self.videoWidget.setVideoFrame)
        self.videoThread.start()
        self.enableDetection.connect(self.videoThread.handle_enableDetection)

        # Initialize subscriber threads for different topics
        self.motor_subscriber_thread = MotorSubscriberThread("ResponseTopic")
        self.motor_subscriber_thread.motor_data_received_signal.connect(self.update_motor_data_ui)
        self.motor_subscriber_thread.start()

        # Initialize subscriber threads for different topics
        self.plc_subscriber_thread = PLCSubscriberThread("PLC_ResponseTopic")
        self.plc_subscriber_thread.plc_data_received_signal.connect(self.update_plc_data_ui)
        self.plc_subscriber_thread.start()        
        
        # Initialize subscriber threads for different topics
        self.Joystick_subscriber_thread = JoySubscriberThread("JoystickTopic")

        # Connect signals from subscriber threads to slots in MainWindow
        self.Joystick_subscriber_thread.Joy_data_received_signal.connect(self.update_Joy_data_ui)

        # Start subscriber threads
        self.Joystick_subscriber_thread.start()


        # Initialize and start the publisher thread
        self.dds_publisher_thread = PublisherThread("QueryTopic")
        self.dds_publisher_thread.start()

        # Initialize and start the publisher thread
        self.plc_dds_publisher_thread = PLC_PublisherThread("PLC_QueryTopic")
        self.plc_dds_publisher_thread.start()

        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.updateUI)
        self.updateTimer.start(100)  # Update UI every 100 ms

        self.speed = 0 
        self.latest_speed = 0
        self.mot1_speed = 5000
        self.mapped_speed = 0 
        self.direction= 0x4000  

        self.latestAzimuth = 0
        self.increment = 0
        self.last_button_fire_value = 0
        self.button_fire_value   = 0
        # Set stylesheet for labels with the object name "specialLabel"
        self.setStyleSheet("""
            QLabel {
                font-family: Courier;
                font-size: 12pt;
                font-weight : 600;           
                color: rgb(230,0,0);
             }
        """)   

        self.initLabels()     
        # Load the image
        pixmap = QPixmap('imgs/reticle_hud.png')  # Update this to the path of your image

        # Create a QLabel to display the image
        self.hud_label = QLabel(self)
        self.hud_label.setPixmap(pixmap)   
        # Set the window size and position
        self.hud_label.resize(300, 300)  # Set the size of the window
        self.hud_label.move(250, 150)    # Set the position of the window on the screen



    def updateUI(self):
        pass

    def update_motor_data_ui(self, data):
        self.latestAzimuth = data.data()[4]  # Example: extract azimuth from data
        #logging.debug(f"Data updateUI received #{self.increment} at {datetime.now()}")
        self.increment += 1
        #self.updateAzimuthSignal.emit(self.latestAzimuth)
        self.updateAzimuthLabel(self.latestAzimuth)


        #self.videoOverlay.updateAzimuthSignal.emit(azimuth)
         
        #print(f"Received data: {data.data()[4]}, {data.data()[5]}, {data.data()[6]}, {data.data()[7]}")
    def update_plc_data_ui(self, data):
        #self.latestAzimuth = data.data()[4]  # Example: extract azimuth from data
        #logging.debug(f"Data updateUI received #{self.increment} at {datetime.now()}")
        #self.increment += 1
        #self.updateAzimuthSignal.emit(self.latestAzimuth)
        #self.updateAzimuthLabel(self.latestAzimuth)


        #self.videoOverlay.updateAzimuthSignal.emit(azimuth)
         
        print(f"Received data: {data.data()[0]}, {data.data()[1]}, {data.data()[2]}, {data.data()[3]} {data.data()[4]}, {data.data()[5]}, {data.data()[6]}, {data.data()[7]}")


    def update_Joy_data_ui(self, data):
        # Assuming buttonStates, axisStates, and hatStates are accessible through getters or direct attributes
        button_states = list(data.buttonStates())  # Convert sequence to list
        axis_states = list(data.axisStates())      # Convert sequence to list
        hat_states = list(data.hatStates())        # Convert sequence to list

        #print("Button States:", button_states)
        #print("Axis States:", axis_states)
        #print("Hat States:", hat_states)
        self.button_spd_plus_value = button_states[1]
        self.button_spd_minus_value = button_states[0] 
        self.button_burst_mode_value = button_states[6]
        self.button_track_value = button_states[3] 
        self.button_detect_value = button_states[2]  
        self.button_stab_value = button_states[7] 

        self.button_fire_value = button_states[4]

        # Burst mode button
        if self.button_burst_mode_value == 1 and self.last_button_burst_mode_value == 0:
            # Cycle through burst modes
            self.current_burst_mode_index = (self.current_burst_mode_index + 1) % len(self.burst_modes)
            self.updateBurstModeLabel()
            print(f"Burst mode set to: {self.burst_modes[self.current_burst_mode_index]}")
            action_data = fireActionData(command_type="mode", target="plc1", parameters={"val": self.current_burst_mode_index})
            self.publish_plc_action(action_data) 
        self.last_button_burst_mode_value = self.button_burst_mode_value

        # Track button
        if self.button_track_value == 1 and self.last_button_track_value == 0:
            # Toggle track state
            self.track_state = 'ON' if self.track_state == 'OFF' else 'OFF'
            self.updateTrackLabel()

            print(f"Track set to: {self.track_state}")

        self.last_button_track_value = self.button_track_value

        # Detect button
        if self.button_detect_value == 1 and self.last_button_detect_value == 0:
            # Toggle detect state
            self.detect_state = 'ON' if self.detect_state == 'OFF' else 'OFF'
            self.updateDetectLabel()
            if (self.detect_state == 'ON'):
                self.enableDetection.emit(1)
            else:
                self.enableDetection.emit(0)

            print(f"Detect set to: {self.detect_state}")

        self.last_button_detect_value = self.button_detect_value

        # Stab button
        if self.button_stab_value == 1 and self.last_button_stab_value == 0:
            # Toggle detect state
            self.stab_state = 'ON' if self.stab_state == 'OFF' else 'OFF'
            self.updateStabLabel()
            print(f"Stab set to: {self.stab_state}")

        self.last_button_stab_value = self.button_stab_value

        if (self.button_spd_plus_value == 1 and (self.last_button_spd_plus_value == 0)):
            self.speed += 1000
            self.updateSpeedLabel()
            print(self.speed)

        self.last_button_spd_plus_value = self.button_spd_plus_value

        if (self.button_spd_minus_value == 1 and (self.last_button_spd_minus_value == 0)):
            self.speed -=  1000
            self.updateSpeedLabel()            
            print(self.speed)

        self.speed = max(0, min(self.speed, 10000)) 

        self.last_button_spd_minus_value = self.button_spd_minus_value

 

        axis_4_value = axis_states[4]  # Get the value of axis 4
        mot1_speed = 0
        # Map the axis 4 value to a desired speed or intensity for the motor
        # This mapping depends on how you want the joystick input to control the speed
        if (axis_4_value >= 0.3):
            mot1_speed = self.speed
            self.direction= 0x4000  
        elif (axis_4_value <= -0.3):
            mot1_speed = self.speed
            self.direction= 0x8000             
        else:
            mot1_speed = 0
            self.direction= 0             
        time.sleep(0.01)

        if  (mot1_speed != self.latest_speed):
            #print('speed change', self.mot1_speed)
            print(self.direction, mot1_speed)
            action_data = ActionData(command_type="move_forward", target="motor1", parameters={"direction": self.direction, "speed": mot1_speed})
            
            self.publish_action(action_data) 
            self.latest_speed = mot1_speed    

        if (self.button_fire_value != self.last_button_fire_value):
            action_data = fireActionData(command_type="fire", target="plc1", parameters={"val": self.button_fire_value})
            self.publish_plc_action(action_data) 
            self.last_button_fire_value = self.button_fire_value  

    def publish_action(self, action_data):
        # Assuming you have initialized and started a PublisherThread named self.dds_publisher_thread
        self.dds_publisher_thread.enqueue_action(action_data)
        #print('cmd to move')

    def publish_plc_action(self, action_data):
        # Assuming you have initialized and started a PublisherThread named self.dds_publisher_thread
        self.plc_dds_publisher_thread.enqueue_action(action_data)
        #print('cmd to move')


    def updateVideoFeed(self, frame):
        # Convert the captured frame to QImage and then to QPixmap
        height, width, channel = frame.shape
        bytesPerLine = channel * width
        qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)#.rgbSwapped()
        #qImg = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)#.rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
      
        self.videoLabel.setPixmap(pixmap)

    def closeEvent(self, event):
        self.videoThread.stop()
        super().closeEvent(event)

    def updateAzimuthLabel(self, steps):
        self.steps = steps
        azimuth = round((steps * 0.009) % 360 , 1) # Convert steps to angle and wrap around at 360            
        self.display_azimuth_text.setText(f"Az:{azimuth}")   

    def updateTrackLabel(self):         
        self.display_track_text.setText(f"TRACK:{self.track_state}")  

    def updateDetectLabel(self):         
        self.display_detection_text.setText(f"DETECT:{self.detect_state}")  

    def updateBurstModeLabel(self):         
        self.display_burst_mode_text.setText(f"MODE:{self.burst_modes[self.current_burst_mode_index]}")  

    def updateStabLabel(self):         
        self.display_stab_text.setText(f"STAB:{self.stab_state}")  

    def updateSpeedLabel(self):         
        self.display_speed_text.setText(f"SPEED:{self.speed/100}%")  

    def initLabels(self):
        self.steps = 0  # Total steps taken by the motor
        self.azimuth = 0  # Initial azimuth value
        self.elevation = 0.0
        self.lrf = 0.0
        self.lrf_rdy = 'OFF'

        self.fov = 45.0
        self.speed_ = 10
 
        self.gun_ready = 'READY'
        self.gun_charged = 'CHARGED'
        self.gun_armed = 'ARMED'
        self.ammunition_low = 'AMMUNITION LOW'
        self.ammunition_ready = 'AMMUNITION READY' 


        # Initial states and modes
        self.last_button_burst_mode_value = 0
        self.last_button_track_value = 0
        self.last_button_detect_value = 0
        self.last_button_stab_value = 0


        self.burst_modes = ['SINGLE SHOT', 'BURST SHORT', 'BURST FULL']
        self.current_burst_mode_index = 0  # Start with the first mode
        self.track_state = 'OFF'
        self.detect_state = 'OFF'
        self.stab_state = 'OFF'


        text = "SENSOR MODE: TRACKING"
        display_azimuth_text = f"Az:{self.azimuth}°" #takes "azimuth" value
        display_elevation_text = f"El:{self.elevation}°" #takes elevation value

        display_lrf_text = f"LRF:{self.lrf}m {self.lrf_rdy}" #takes LRF value if LRF button pressed 
        display_track_text = f"TRACK:{self.track_state}" #takes "ON" or   "OFF" based on tracking active or none
        display_stab_text = f"STAB:{self.stab_state}" #takes "ON" or   "OFF" based on stabilization active or none
        display_detection_text = f"DETECT:{self.detect_state}" #takes "ON" or   "OFF" based on detection active
        display_camFOV_text = f"FOV:{self.fov}°" #takes fov of active camera
        display_speed_text = f"SPEED:{self.speed/100}%"  #takes speed percent based on actual speed and max speed ratio

        display_burst_mode_text = f"MODE:{self.burst_modes[self.current_burst_mode_index]}" #takes "BURST  FULL" or  "BURST  SHORT" or "SINGLE SHOT"
        display_gun_state_ready_text = f"{self.gun_ready}"    #takes "CAHEGED" or  nothing
        display_gun_state_charged_text = f"{self.gun_charged}"   #takes "CHARED" or  nothing
        display_gun_state_armed_text = f"{self.gun_armed}"   #takes "ARMED" or  nothing

 
        display_gun_ammunition_low_text = f"{self.ammunition_low}" #takes "AMMUNITION LOW" or  nothing
        display_gun_ammunition_ready_text = f"{self.ammunition_ready}" #takes "AMMUNITION READY" or  nothing

        line1_y = 20
        line2_y = 540
        line3_y = 570


        self.display_azimuth_text = QLabel(display_azimuth_text, self)
        self.display_azimuth_text.move(690, 100) 
        self.display_azimuth_text.resize(300, 20)
        self.display_elevation_text = QLabel(display_elevation_text, self)
        self.display_elevation_text.move(680, 200) 
        self.display_elevation_text.resize(300, 20)
        self.display_camFOV_text = QLabel(display_camFOV_text, self)
        self.display_camFOV_text.move(680, 220) 
        self.display_camFOV_text.resize(300, 20)
        self.display_speed_text = QLabel(display_speed_text, self)
        self.display_speed_text.move(680, 240) 
        self.display_speed_text.resize(300, 20)

        self.display_lrf_text = QLabel(display_lrf_text, self)
        self.display_lrf_text.move(20, line1_y) 
        self.display_lrf_text.resize(150, 20)
        self.display_track_text = QLabel(display_track_text, self)
        self.display_track_text.move(170, line1_y) 
        self.display_track_text.resize(110, 20)
        self.display_stab_text = QLabel(display_stab_text, self)
        self.display_stab_text.move(280, line1_y) 
        self.display_stab_text.resize(120, 20)
        self.display_detection_text = QLabel(display_detection_text, self)
        self.display_detection_text.move(400, line1_y) 
        self.display_detection_text.resize(120, 20)


        self.display_burst_mode_text = QLabel(display_burst_mode_text, self)
        self.display_burst_mode_text.move(20, line2_y) 
        self.display_burst_mode_text.resize(300, 20) 
        self.display_gun_state_ready_text = QLabel(display_gun_state_ready_text, self)
        self.display_gun_state_ready_text.move(20, line3_y) 
        self.display_gun_state_ready_text.resize(300, 20) 
        self.display_gun_state_charged_text = QLabel(display_gun_state_charged_text, self)
        self.display_gun_state_charged_text.move(150, line3_y) 
        self.display_gun_state_charged_text.resize(300, 20) 
        self.display_gun_state_armed_text = QLabel(display_gun_state_armed_text, self)
        self.display_gun_state_armed_text.move(250, line3_y) 
        self.display_gun_state_armed_text.resize(300, 20) 
        self.display_gun_ammunition_low_text = QLabel(display_gun_ammunition_low_text, self)
        self.display_gun_ammunition_low_text.move(600, line2_y) 
        self.display_gun_ammunition_low_text.resize(300, 20) 
        self.display_gun_ammunition_ready_text = QLabel(display_gun_ammunition_ready_text, self)
        self.display_gun_ammunition_ready_text.move(600, line3_y) 
        self.display_gun_ammunition_ready_text.resize(300, 20)             

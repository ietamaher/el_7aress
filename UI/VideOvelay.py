from PyQt5.QtWidgets import  QWidget
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from PyQt5.QtGui import QImage, QPixmap, QPalette, QColor, QFont , QPainter, QPen ,  QPainterPath, QTransform, QBrush
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint, QSize,  QPointF, QRectF
import math
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class VideoProcessingThread(QThread):
    updateOverlaySignal = pyqtSignal(str)  # Signal to emit overlay text
    updateAzimuthSignal = pyqtSignal(int)


    def run(self):
        while True:
            # Your video processing logic here
            overlayText = "Your overlay text"
            self.updateOverlaySignal.emit(overlayText)
            # Implement appropriate sleep or wait mechanism to control the update rate


class VideOvelay(QWidget):
    updateAzimuthSignal = pyqtSignal(int) 
    def __init__(self, parent=None):
        super(VideOvelay, self).__init__(parent)
        self.setPalette(QPalette(QColor(255, 255, 255, 0)))  # Transparent background
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Pass through mouse events
        self.steps = 0  # Total steps taken by the motor
        self.azimuth = 0  # Initial azimuth value
        self.elevation = 0.0
        self.lrf = 0.0
        self.lrf_rdy = 'Off'
        self.track_on_off = 'Off'
        self.stab_on_off = 'Off'
        self.auto_detect_on_off = 'Off'
        self.fov = 45.0
        self.speed_ = 10
        self.burst_mode = 'Single Shot'
        self.gun_ready = 'READY'
        self.gun_charged = 'CHARGED'
        self.gun_armed = 'ARMED'
        self.ammunition_low = 'AMMUNITION LOW'
        self.ammunition_ready = 'AMMUNITION READY'
        self.increment = 0


        self.updateAzimuthSignal.connect(self.setAzimuth)
        # Set the size of the overlay to match the parent widget's size
        self.resize(parent.size())

    def paintEvent(self, event):
        # Create a QPainter instance
        print("paint event fired!!!!")
        #painter = QPainter(self)
        #painter.setRenderHint(QPainter.Antialiasing)
        center = QPointF(self.width() / 2, self.height() / 2)

        # Set colors
        borderColor = QColor(80, 0, 0)
        mainColor = QColor(200, 0, 0)
        textColor = QColor(0, 200, 0)
        borderWidth = 3

        # Drawing elements
        #self.drawCrosshairs(painter, center, borderColor, borderWidth)
        #self.drawCrosshairs(painter, center,  mainColor, 1)

        #self.drawCircleWithGraduations(painter, center, borderColor, borderWidth)
        #self.drawCircleWithGraduations(painter, center, mainColor, 1)

        #self.drawNeedle(painter, center, borderColor, borderWidth)
        #self.drawNeedle(painter, center, mainColor, 1)

        #self.drawText(painter, center, mainColor, borderColor)       
          
        # Finish painting
        painter.end()

    def draw_bracket(self, painter, pos, size, line_length, corner='topLeft'):
        """
        Draw a bracket at a specified position.
        pos: QPoint for the position of the top left corner.
        size: QSize for the width and height of the rectangle.
        line_length: Length of the lines composing the bracket.
        corner: String indicating the corner ('topLeft', 'topRight', 'bottomLeft', 'bottomRight')
        """
        if corner == 'topLeft':
            painter.drawLine(pos.x(), pos.y(), pos.x() + size.width(), pos.y())  # Top side
            painter.drawLine(pos.x(), pos.y(), pos.x(), pos.y() + size.height())  # Left side
        elif corner == 'topRight':
            painter.drawLine(pos.x(), pos.y(), pos.x() - size.width(), pos.y())  # Top side
            painter.drawLine(pos.x(), pos.y(), pos.x(), pos.y() + size.height())  # Right side
        elif corner == 'bottomLeft':
            painter.drawLine(pos.x(), pos.y(), pos.x() + size.width(), pos.y())  # Bottom side
            painter.drawLine(pos.x(), pos.y(), pos.x(), pos.y() - size.height())  # Left side
        elif corner == 'bottomRight':
            painter.drawLine(pos.x(), pos.y(), pos.x() - size.width(), pos.y())  # Bottom side
            painter.drawLine(pos.x(), pos.y(), pos.x(), pos.y() - size.height())  # Right side
            

    def drawCrosshairs(self, painter, center,  color, borderWidth):
        # Border pen for crosshairs
        borderPen = QPen(color, borderWidth)
        borderPen.setCapStyle(Qt.RoundCap)  # Set the cap style to round
        painter.setPen(borderPen)

        # Drawing the crosshairs with border and main line
        center_x = int(center.x())
        center_y = int(center.y())
        # Draw the horizontal line with notch
        painter.drawLine(center_x - 60, center_y, center_x - 15, center_y)  # Horizontal line
        painter.drawLine(center_x + 15, center_y, center_x + 60, center_y)  # Horizontal line
        radius = 1
        
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        painter.drawLine(center_x, center_y + 15 , center_x, center_y +30)  # Notch line
        
        bracket_size = QSize(30, 30)
        line_length = 20  # The length of the bracket lines
        self.draw_bracket(painter, QPoint(center_x - 100, center_y - 60), bracket_size, line_length, 'topLeft')
        self.draw_bracket(painter, QPoint(center_x + 100, center_y - 60), bracket_size, line_length, 'topRight')
        self.draw_bracket(painter, QPoint(center_x - 100, center_y + 60), bracket_size, line_length, 'bottomLeft')
        self.draw_bracket(painter, QPoint(center_x + 100, center_y + 60), bracket_size, line_length, 'bottomRight')

    def drawCircleWithGraduations(self, painter, center, color, borderWidth):
        pos_x = 100
        pox_y = 100
        borderPen = QPen(color, borderWidth)
        borderPen.setCapStyle(Qt.RoundCap)  # Set the cap style to round
        painter.setPen(borderPen)
        center = QPointF(self.width() - 80, 80)
        radius = 65  # Radius of the circle
 
        # Draw the graduated circle
        painter.drawEllipse(center, radius, radius)    

        # Draw the graduations every 30 degrees
        for angle in range(0, 360, 30):
            rad_angle = math.radians(angle)
            # Calculate the end point of the graduation mark on the circle's circumference
            mark_end = QPointF(
                center.x() + (radius-3) * math.cos(rad_angle),
                center.y() - (radius-3) * math.sin(rad_angle)  # Subtract because y-coordinates go down the screen
            )
            # Calculate the start point of the graduation mark slightly inside the circle's circumference
            inner_radius = radius -8  # 10 pixels inside the circle for the mark
            mark_start = QPointF(
                center.x() + inner_radius * math.cos(rad_angle),
                center.y() - inner_radius * math.sin(rad_angle)
            )
            painter.drawLine(mark_start, mark_end)

        borderPen = QPen(color, borderWidth + 2)
        borderPen.setCapStyle(Qt.RoundCap)  # Set the cap style to round
        painter.setPen(borderPen)

        # Draw the graduations every 30 degrees
        for angle in range(0, 360, 90):
            rad_angle = math.radians(angle)
            # Calculate the end point of the graduation mark on the circle's circumference
            mark_end = QPointF(
                center.x() + (radius-3) * math.cos(rad_angle),
                center.y() - (radius-3) * math.sin(rad_angle)  # Subtract because y-coordinates go down the screen
            )
            #print(center.x(), center.y())
            # Calculate the start point of the graduation mark slightly inside the circle's circumference
            inner_radius = radius -12  # 10 pixels inside the circle for the mark
            mark_start = QPointF(
                center.x() + inner_radius * math.cos(rad_angle),
                center.y() - inner_radius * math.sin(rad_angle)
            )
            painter.drawLine(mark_start, mark_end)           

    def drawNeedle(self, painter, center, color , borderWidth):
        # Drawing the needle with border and main line
        pos_x = 100
        pox_y = 100
        borderPen = QPen(color, borderWidth)
        borderPen.setCapStyle(Qt.RoundCap)  # Set the cap style to round
        painter.setPen(borderPen)
        center = QPointF(self.width() - 80, 80)

        radius = 60  # Radius of the circle        
        # Transform to rotate the painter's coordinate system
        transform = QTransform()
        transform.translate(center.x(),center.y())
        transform.rotate(self.azimuth)
        painter.setTransform(transform)

        # Draw the needle
        painter.drawLine(0, 0, 0, -(radius-10))  # Draw line from center to top (since we've rotated the coordinate system)

        # Reset transformation to draw the square at the base of the needle
        painter.resetTransform()

        # Calculate the top-left corner of the square relative to the center
        squareSize = 4  # Adjust size as needed
        topLeftX = center.x() - squareSize / 2
        topLeftY = center.y() - squareSize / 2

        # Define the rectangle representing the square
        rect = QRectF(topLeftX, topLeftY, squareSize, squareSize)

        # Set pen for the square
        squarePen = QPen(color, 1)  # Adjust color and thickness as needed
        painter.setPen(squarePen)
        # Set brush for filling the square
        squareBrush = QBrush(color)
        painter.setBrush(squareBrush)
        # Draw the rounded square
        cornerRadius = 1  # Adjust corner radius as needed
        painter.drawRoundedRect(rect, cornerRadius, cornerRadius) 


    def drawText(self, painter, center, mainColor, borderColor):
        # Set font for text
        # Define the font and text color
        font = QFont('New Courier', 13, QFont.Bold)
        font.setStyleHint(QFont.Monospace)
        painter.setFont(font)

       # Drawing text with border and main text
        text = "SENSOR MODE: TRACKING"
        display_azimuth_text = f"Az: {self.azimuth}°" #takes "azimuth" value
        display_elevation_text = f"El: {self.elevation}°" #takes elevation value

        display_lrf_text = f"LRF:{self.lrf}m {self.lrf_rdy}" #takes LRF value if LRF button pressed 
        display_track_text = f"TRACK:{self.track_on_off}" #takes "ON" or   "OFF" based on tracking active or none
        display_stab_text = f"STAB:{self.stab_on_off}" #takes "ON" or   "OFF" based on stabilization active or none
        display_detection_text = f" DETECT:{self.auto_detect_on_off}" #takes "ON" or   "OFF" based on detection active
        display_camFOV_text = f"FOV:{self.fov}°" #takes fov of active camera
        display_speed_text = f"SPEED:{self.speed_}%"  #takes speed percent based on actual speed and max speed ratio

        display_burst_mode_text = f"MODE:{self.burst_mode}" #takes "BURST  FULL" or  "BURST  SHORT" or "SINGLE SHOT"
        display_gun_state_ready_text = f"{self.gun_ready}"    #takes "CAHEGED" or  nothing
        display_gun_state_charged_text = f"{self.gun_charged}"   #takes "CHARED" or  nothing
        display_gun_state_armed_text = f"{self.gun_armed}"   #takes "ARMED" or  nothing

 
        display_gun_ammunition_low_text = f"{self.ammunition_low}" #takes "AMMUNITION LOW" or  nothing
        display_gun_ammunition_ready_text = f"{self.ammunition_ready}" #takes "AMMUNITION READY" or  nothing
 


        # Create a QPainterPath and add text to it
        path = QPainterPath()
        #path.addText(100, 100, font, text)  # Specify the position and font
        path.addText(690, 100, font, display_azimuth_text)  # Specify the position and font
        path.addText(680, 180, font, display_elevation_text)  # Specify the position and font
        path.addText(680, 200, font, display_camFOV_text)
        path.addText(680, 220, font, display_speed_text) 
        line1_y = 40
        line2_y = 550
        line3_y = 580
        path.addText(20, line1_y, font, display_lrf_text)
        path.addText(170, line1_y, font, display_track_text)
        path.addText(280, line1_y, font, display_stab_text)
        path.addText(400, line1_y, font, display_detection_text)

        path.addText(20, line2_y, font, display_burst_mode_text)
        path.addText(20, line3_y, font, display_gun_state_ready_text)
        path.addText(150, line3_y, font, display_gun_state_charged_text)
        path.addText(250, line3_y, font, display_gun_state_armed_text)
        path.addText(600, line2_y, font, display_gun_ammunition_low_text)     
        path.addText(600, line3_y, font, display_gun_ammunition_ready_text)     

        # Draw the outline (stroke) using a thick pen
        outline_pen = QPen(borderColor, 2)  # Outline thickness of 2
        outline_pen.setCapStyle(Qt.RoundCap)
        outline_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(outline_pen)
        painter.drawPath(path)

         # Draw the text itself with a smaller pen (the fill)
        text_pen = QPen(mainColor, 1)
        painter.setPen(text_pen)
        painter.fillPath(path, mainColor)    

    @pyqtSlot(int)
    def setAzimuth(self, steps):
        self.steps = steps
        self.azimuth = round((steps * 0.009) % 360 , 1) # Convert steps to angle and wrap around at 360        
        self.update()  # Trigger a repaint
        #logging.debug(f"Data AZIMUTH received #{self.increment} at {datetime.now()}")
        self.increment += 1


    def setElevation(self, value):
        self.elevation = round((value * 0.009) % 360 , 1) # Convert steps to angle and wrap around at 360        
        self.update()  # Trigger a repaint

    def setElevation(self, value):
        self.elevation = value
        self.update()  # Trigger a repaint

    def setLrf(self, value):
        self.lrf = value
        self.update()  # Trigger a repaint

    def setLrfRdy(self, status):
        self.lrf_rdy = status
        self.update()  # Trigger a repaint

    def setTrackOnOff(self, status):
        self.track_on_off = status
        self.update()  # Trigger a repaint

    def setStabOnOff(self, status):
        self.stab_on_off = status
        self.update()  # Trigger a repaint

    def setAutoDetectOnOff(self, status):
        self.auto_detect_on_off = status
        self.update()  # Trigger a repaint

    def setFov(self, value):
        self.fov = value
        self.update()  # Trigger a repaint

    def setSpeed(self, value):
        self.speed_ = value
        self.update()  # Trigger a repaint

    def setBurstMode(self, mode):
        self.burst_mode = mode
        self.update()  # Trigger a repaint

    def setGunReady(self, status):
        self.gun_ready = status
        self.update()  # Trigger a repaint

    def setGunCharged(self, status):
        self.gun_charged = status
        self.update()  # Trigger a repaint

    def setGunArmed(self, status):
        self.gun_armed = status
        self.update()  # Trigger a repaint

    def setAmmunitionLow(self, status):
        self.ammunition_low = status
        self.update()  # Trigger a repaint

    def setAmmunitionReady(self, status):
        self.ammunition_ready = status
        self.update()  # Trigger a repaint
                       
        
        

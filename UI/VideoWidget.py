import time
from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.Qt import Qt, QMetaObject, Q_ARG

class VideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Set all margins to zero
        self.layout.setSpacing(0)  # Set the spacing to zero
        self.videoLabel = QLabel("Video Feed Here")
        self.layout.addWidget(self.videoLabel)
    

    @pyqtSlot(object)
    def setVideoFrame(self, image):

        # Convert the captured frame to QImage and then to QPixmap
        height, width, channel = image.shape
        bytesPerLine = channel * width
        qImg = QImage(image, image.shape[1], image.shape[0], QImage.Format_RGB888)#.rgbSwapped()
        #qImg = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)#.rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
        self.videoLabel.setPixmap(pixmap.scaled(self.videoLabel.size(), Qt.KeepAspectRatio))

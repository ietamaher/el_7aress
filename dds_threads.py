from DDS.ResponseSubscriber import DDSSubscriber
from DDS.QueryPublisher import DDSPublisher
from DDS.PLC_QueryPublisher import PLCQueryPublisher
from DDS.PLC_ResponseSubscribe import PLC_DDSSubscriber
from DDS.JoySubscriber import JoyReader
from DDS.Query_msg import Query_msg
from DDS.Response_msg import Response_msg, Response_msgPubSubType
from DDS.JoystickData import JoystickData, JoystickDataPubSubType
from PyQt5.Qt import Qt, QMetaObject, Q_ARG
from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class dds_threads(QThread):
     def __init__(self):
        super().__init__()   


class PLCSubscriberThread(QThread):
    plc_data_received_signal = pyqtSignal(Response_msg)

    def __init__(self, topic_name):
        super().__init__()
        self.topic_name = topic_name
        self.subscriber = PLC_DDSSubscriber(self.topic_name)
        self.subscriber.plc_data_received.connect(self.handle_data_received,Qt.DirectConnection)
        self.increment = 0
    
    def run(self):
        print("running subscriber thread")
        self.exec_()

    def handle_data_received(self, data):
        self.increment += 1 
        self.plc_data_received_signal.emit(data)

    def stop(self):
        if self.subscriber:
            self.subscriber.delete()
        self.quit()
        self.wait()

class MotorSubscriberThread(QThread):
    motor_data_received_signal = pyqtSignal(Response_msg)

    def __init__(self, topic_name):
        super().__init__()
        self.topic_name = topic_name
        self.subscriber = DDSSubscriber(self.topic_name)
        self.subscriber.motor_data_received.connect(self.handle_data_received,Qt.DirectConnection)
        self.increment = 0
    
    def run(self):
        print("running subscriber thread")
        # The subscriber is already initialized, so just keep the thread running
        self.exec_()

    def handle_data_received(self, data):
        #logging.debug(f"Data RESPONSE THREAD  received #{self.increment} at  {datetime.now()}")
        self.increment += 1 
        self.motor_data_received_signal.emit(data)

    def stop(self):
        if self.subscriber:
            self.subscriber.delete()
        self.quit()
        self.wait()


class JoySubscriberThread(QThread):
    Joy_data_received_signal = pyqtSignal(JoystickData)

    def __init__(self, topic_name):
        super().__init__()
        self.topic_name = topic_name
        self.subscriber = JoyReader(self.topic_name)
        self.subscriber.Joy_data_received.connect(self.handle_data_received,Qt.DirectConnection)
    
    def run(self):
        print("running subscriber thread")
        # The subscriber is already initialized, so just keep the thread running
        self.exec_()

    def handle_data_received(self, data):
        #print("handle_data_received called .....")
        self.Joy_data_received_signal.emit(data)

    def stop(self):
        if self.subscriber:
            self.subscriber.delete()
        self.quit()
        self.wait()

class ActionData:
    def __init__(self, command_type, target, parameters=None):
        self.command_type = command_type  # e.g., "move", "stop", "set_speed", "set_angle"
        self.target = target  # e.g., "motor1", "PLC1"
        self.parameters = parameters or {}  # e.g., {"speed": 100, "angle": 45}

class fireActionData:
    def __init__(self, command_type, target, parameters=None):
        self.command_type = command_type  # e.g., "move", "stop", "set_speed", "set_angle"
        self.target = target  # e.g., "motor1", "PLC1"
        self.parameters = parameters or {}  # e.g., {"speed": 100, "angle": 45}

class PublisherThread(QThread):
    #query_data_received_signal = pyqtSignal(ActionData)
    def __init__(self, topic_name):
        super().__init__()
        self.topic_name = topic_name
        self.dds_publisher = None

    def run(self):
        self.dds_publisher = DDSPublisher(self.topic_name)
        self.dds_publisher.run()

    def enqueue_action(self, action_data):
        if self.dds_publisher:
            self.dds_publisher.enqueue_action(action_data)

class PLC_PublisherThread(QThread):
    #query_data_received_signal = pyqtSignal(ActionData)
    def __init__(self, topic_name):
        super().__init__()
        self.topic_name = topic_name
        self.dds_publisher = None

    def run(self):
        self.dds_publisher = PLCQueryPublisher(self.topic_name)
        self.dds_publisher.run()

    def enqueue_action(self, action_data):
        if self.dds_publisher:
            self.dds_publisher.enqueue_action(action_data)
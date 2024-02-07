"""
Query_msg Publisher
"""
from threading import Condition
import time
import sys
import  fastdds  # import DomainParticipantFactory, DomainParticipant, Publisher, Subscriber
from .Query_msg import Query_msg, Query_msgPubSubType
import queue
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QMetaObject, Q_ARG, Qt
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
class ActionData:
    def __init__(self, command_type, target, parameters=None):
        self.command_type = command_type  # e.g., "move", "stop", "set_speed", "set_angle"
        self.target = target  # e.g., "motor1", "PLC1"
        self.parameters = parameters or {}  # e.g., {"speed": 100, "angle": 45}


class WriterListener (fastdds.DataWriterListener) :
    def __init__(self, writer) :
        self._writer = writer
        super().__init__()


    def on_publication_matched(self, datawriter, info) :
        if (0 < info.current_count_change) :
            print ("Motor Publisher matched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader += 1
            self._writer._cvDiscovery.notify()
            self._writer._cvDiscovery.release()
        else :
            print ("Motor Publisher unmatched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader -= 1
            self._writer._cvDiscovery.notify()
            self._writer._cvDiscovery.release()


class DDSPublisher(QObject):
    query_data_received = pyqtSignal(ActionData)    
    def __init__(self, topic_name, parent=None):
        super().__init__(parent)
        self._matched_reader = 0
        self._cvDiscovery = Condition()
        self.index = 0

        # Initialize the participant
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant_qos = fastdds.DomainParticipantQos()
        self.participant_qos.name = "QueryResponse"
        factory.get_default_participant_qos(self.participant_qos)
        self.participant = factory.create_participant(0, self.participant_qos)        
        
        # Register the type
        self.topic_data_type = Query_msgPubSubType()
        self.topic_data_type.setName("Query_msg")
        self.type_support = fastdds.TypeSupport(self.topic_data_type)
        self.participant.register_type(self.type_support)
        
        self.topic_qos = fastdds.TopicQos()
        self.participant.get_default_topic_qos(self.topic_qos)
        self.topic = self.participant.create_topic("QueryTopic", self.topic_data_type.getName(), self.topic_qos)

        self.publisher_qos = fastdds.PublisherQos()
        self.participant.get_default_publisher_qos(self.publisher_qos)
        self.publisher = self.participant.create_publisher(self.publisher_qos)

        self.listener = WriterListener(self)
        self.writer_qos = fastdds.DataWriterQos()
        self.publisher.get_default_datawriter_qos(self.writer_qos)
        self.writer = self.publisher.create_datawriter(self.topic, self.writer_qos, self.listener)

        # Create the writer
        self.writer = self.publisher.create_datawriter(self.topic, fastdds.DATAWRITER_QOS_DEFAULT, None)
        self.action_queue = queue.Queue()
        self.query_data_received.connect(self.enqueue_action)

        self.increment = 0
        self.send = 0

    def publish_status_update(self):
        query = Query_msg()
        query.slave_id (2)
        query.func_code(2)  # Assuming 1 is the code for write
        query.write_addr(0)  # 0x0F8 Example write address
        query.write_num(0)  # Number of registers to write
        query.read_addr(0x0C4)
        query.read_num(15)

        self.writer.write(query)

    def wait_discovery(self) :
        self._cvDiscovery.acquire()
        print ("Motor Writer is waiting discovery...")
        self._cvDiscovery.wait_for(lambda : self._matched_reader != 0)
        self._cvDiscovery.release()
        print("Motor Writer discovery finished...")

    @pyqtSlot(ActionData)
    def enqueue_action(self, action_data):
        #print('im here ...', action_data.parameters['speed'])
        # Convert action_data to DDS message format and enqueue
        self.convert_to_dds_message(action_data)
        

    def convert_to_dds_message(self, action_data):
        dds_message = Query_msg()

        if (action_data.target == 'motor1'):
            dds_message.slave_id(1)
        else:
            dds_message.slave_id(2)
        speed = action_data.parameters['speed']
        direction = action_data.parameters["direction"]
        dds_message.func_code(1)
        self.send = 1
        if (speed > 0):

            dds_message.slave_id(2)  # Unit selection (Hex): Unit 1
            dds_message.func_code(1)  # Function code selection: 1 (Write)
            dds_message.write_addr(1152)  # Select starting address (Dec)
            dds_message.write_num(1)   # Write data size: 1 (1x32bit)
            data_values = [speed] + [0] * 63  # Fill remaining with zeros
            dds_message.data(data_values) 
            self.writer.write(dds_message)
            time.sleep(0.01)
            data_values = [0] * 64
            dds_message.slave_id(2)  # Unit selection (Hex): Unit 1/2
            dds_message.func_code(1)  # Function code selection: 1 (Write)
            dds_message.write_addr(124)  # Select starting address (Dec)
            dds_message.write_num(1)   # Write data size: 6 (1x32bit)
            data_values = [direction] + [0] * 63  # Fill remaining with zeros
            dds_message.data(data_values) 
            self.writer.write(dds_message)
            time.sleep(0.01)            

        else:

            dds_message.slave_id(2)  # Unit selection (Hex): Unit 1
            dds_message.func_code(1)  # Function code selection: 1 (Write)
            dds_message.write_addr(124)  # Select starting address (Dec): Operation data No.0 method (1800h)
            dds_message.write_num(1)   # Write data size: 6 (6x32bit)
            data_values = [32]+[0] * 63  # Fill remaining with zeros
            dds_message.data(data_values) 
            self.writer.write(dds_message)
            time.sleep(0.01)
            dds_message.slave_id(2)  # Unit selection (Hex): Unit 1
            dds_message.func_code(1)  # Function code selection: 1 (Write)
            dds_message.write_addr(124)  # Select starting address (Dec): Operation data No.0 method (1800h)
            dds_message.write_num(1)   # Write data size: 6 (6x32bit)
            data_values = [0] * 64  # Fill remaining with zeros
            dds_message.data(data_values) 
            self.writer.write(dds_message)
            time.sleep(0.01)
        
        self.send = 0

    def publish_action(self, action_data):
        #print("Publishing action ...")
        self.writer.write(action_data)

    def run(self):
        self.wait_discovery()
        while True:
            if (self.send):
                ##action_data = self.action_queue.get()
                #self.publish_action(action_data)
                time.sleep(0.01)
            else:
                self.publish_status_update()
                #logging.debug(f"Data QUERY DDS sent #{self.increment}at {datetime.now()}")
                self.increment += 1

                time.sleep(0.1)

    def delete(self):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)        
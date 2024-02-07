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
            print ("PLC Publisher matched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader += 1
            self._writer._cvDiscovery.notify()
            self._writer._cvDiscovery.release()
        else :
            print ("PLC Publisher unmatched subscriber {}".format(info.last_subscription_handle))
            self._writer._cvDiscovery.acquire()
            self._writer._matched_reader -= 1
            self._writer._cvDiscovery.notify()
            self._writer._cvDiscovery.release()

class PLCQueryPublisher(QObject):
    query_data_received = pyqtSignal(ActionData)    
    def __init__(self, topic_name, parent=None):
        super().__init__(parent)
        self._matched_reader = 0
        self._cvDiscovery = Condition()
        self.index = 0

        # Initialize the participant
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant_qos = fastdds.DomainParticipantQos()
        self.participant_qos.name = "PLC_Query_Response"
        factory.get_default_participant_qos(self.participant_qos)
        self.participant = factory.create_participant(0, self.participant_qos)        
        
        # Register the type
        self.topic_data_type = Query_msgPubSubType()
        self.topic_data_type.setName("Query_msg")
        self.type_support = fastdds.TypeSupport(self.topic_data_type)
        self.participant.register_type(self.type_support)
        
        self.topic_qos = fastdds.TopicQos()
        self.participant.get_default_topic_qos(self.topic_qos)
        self.topic = self.participant.create_topic(topic_name, self.topic_data_type.getName(), self.topic_qos)

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
        query.func_code(4)  # Assuming 1 is the code for write
        query.read_addr(0)
        query.read_num(13)

        self.writer.write(query)


    def wait_discovery(self) :
        self._cvDiscovery.acquire()
        print ("PLC Writer is waiting discovery...")
        self._cvDiscovery.wait_for(lambda : self._matched_reader != 0)
        self._cvDiscovery.release()
        print("PLC Writer discovery finished...")

    @pyqtSlot(ActionData)
    def enqueue_action(self, action_data):
        #print('im here ...', action_data.parameters['speed'])
        # Convert action_data to DDS message format and enqueue
        self.convert_to_dds_message(action_data)
        

    def convert_to_dds_message(self, action_data):
        dds_message = Query_msg()

        if (action_data.target == 'plc1'):
            dds_message.slave_id(1)
        else:
            dds_message.slave_id(2)
        val = action_data.parameters['val']

        self.send = 1
        if (action_data.command_type == "mode"):
                dds_message.slave_id(2)  # Unit selection (Hex): Unit 1
                dds_message.func_code(1)  # Function code selection: 1 (Write)
                dds_message.write_addr(0)  # Select starting address (Dec)
                dds_message.write_num(1)   # Write data size: 1 (1x32bit)
                data_values = [(val+1) * 300] + [0] * 63 # Fill remaining with zeros
                dds_message.data(data_values) 
                self.writer.write(dds_message)
                time.sleep(0.01) 
        else:    
            if (val > 0):

                dds_message.slave_id(2)  # Unit selection (Hex): Unit 1
                dds_message.func_code(3)  # Function code selection: 1 (Write)
                dds_message.write_addr(0)  # Select starting address (Dec)
                dds_message.write_num(7)   # Write data size: 1 (1x32bit)
                data_values = [1,1,1,1,1,1,1] + [0] * 57 # Fill remaining with zeros
                dds_message.data(data_values) 
                self.writer.write(dds_message)
                time.sleep(0.01)   

            else:

                dds_message.slave_id(2)  # Unit selection (Hex): Unit 1
                dds_message.func_code(3)  # Function code selection: 1 (Write)
                dds_message.write_addr(0)  # Select starting address (Dec)
                dds_message.write_num(7)   # Write data size: 1 (1x32bit)
                data_values = [0,0,0,0,0,0,0] + [0] * 57 # Fill remaining with zeros
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
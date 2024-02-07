import signal
from PyQt5.QtCore import QObject, pyqtSignal
import fastdds
from .JoystickData import JoystickData, JoystickDataPubSubType

class ReaderListener(fastdds.DataReaderListener):


    def __init__(self, callback):
        super().__init__()
        self.callback = callback # Store the reference to the subscriber

    def on_subscription_matched(self, datareader, info) :
        if (0 < info.current_count_change) :
            print ("Subscriber matched publisher {}".format(info.last_publication_handle))
        else :
            print ("Subscriber unmatched publisher {}".format(info.last_publication_handle))


    def on_data_available(self, reader):
        info = fastdds.SampleInfo()
        data = JoystickData()
        reader.take_next_sample(data, info)
        # Emit the signal with the received data
        self.callback(data)


class JoyReader(QObject):
    Joy_data_received = pyqtSignal(JoystickData)

    def __init__(self, topic_name):
        super().__init__()  # Initialize the QObject base class   
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant_qos = fastdds.DomainParticipantQos()
        factory.get_default_participant_qos(self.participant_qos)
        self.participant = factory.create_participant(0, self.participant_qos)

        self.topic_data_type = JoystickDataPubSubType()
        self.topic_data_type.setName("JoystickData")
        self.type_support = fastdds.TypeSupport(self.topic_data_type)
        self.participant.register_type(self.type_support)

        self.topic_qos = fastdds.TopicQos()
        self.participant.get_default_topic_qos(self.topic_qos)
        self.topic = self.participant.create_topic("JoystickTopic", self.topic_data_type.getName(), self.topic_qos)

        self.subscriber_qos = fastdds.SubscriberQos()
        self.participant.get_default_subscriber_qos(self.subscriber_qos)
        self.subscriber = self.participant.create_subscriber(self.subscriber_qos)

        self.listener = ReaderListener(self.data_callback)
        self.reader_qos = fastdds.DataReaderQos()
        self.subscriber.get_default_datareader_qos(self.reader_qos)
        self.reader = self.subscriber.create_datareader(self.topic, self.reader_qos, self.listener)


    def delete(self):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)


    def data_callback(self, data):
        #print("data_callback called .....")        
        self.Joy_data_received.emit(data)
 
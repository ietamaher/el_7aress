import signal
from PyQt5.QtCore import QObject, pyqtSignal
import fastdds
from .Response_msg import Response_msg, Response_msgPubSubType

class DDSSubscriber(QObject):
    motor_data_received = pyqtSignal(Response_msg)

    def __init__(self, topic_name):
        super().__init__()      
        # Initialize the participant
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant_qos = fastdds.DomainParticipantQos()
        factory.get_default_participant_qos(self.participant_qos)
        self.participant = factory.create_participant(0, self.participant_qos)        
         #self.participant = fastdds.DomainParticipantFactory.get_instance().create_participant(0)
        
        # Register the type
        self.topic_data_type = Response_msgPubSubType()
        self.topic_data_type.setName("Response_msg")
        self.type_support = fastdds.TypeSupport(self.topic_data_type)        
        self.participant.register_type(self.type_support)


        self.topic_qos = fastdds.TopicQos()
        self.participant.get_default_topic_qos(self.topic_qos)
        self.topic = self.participant.create_topic(topic_name, self.topic_data_type.getName(), self.topic_qos)

        self.subscriber_qos = fastdds.SubscriberQos()
        self.participant.get_default_subscriber_qos(self.subscriber_qos)
        self.subscriber = self.participant.create_subscriber(self.subscriber_qos)

        self.listener = ReaderListener(self.data_callback)
        self.reader_qos = fastdds.DataReaderQos()
        self.subscriber.get_default_datareader_qos(self.reader_qos)
        self.reader = self.subscriber.create_datareader(self.topic, self.reader_qos, self.listener)
        self.increment = 0

        
    def delete(self):
        factory = fastdds.DomainParticipantFactory.get_instance()
        self.participant.delete_contained_entities()
        factory.delete_participant(self.participant)

    def data_callback(self, data):
        #logging.debug(f"Data RESPONSE DDS Subscriber received #{self.increment} at  {datetime.now()}")
        self.motor_data_received.emit(data)


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
        data = Response_msg()
        reader.take_next_sample(data, info)
        self.callback(data)


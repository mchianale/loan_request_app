from confluent_kafka import Producer,  Consumer
from dotenv import load_dotenv
import os
import json
from .baseModels import LogEntry

load_dotenv()

KAFKA_BROKERS = os.environ['KAFKA_BROKERS']
PRODUCER_CONFIG = {
    'bootstrap.servers': KAFKA_BROKERS,
    'acks': 'all',  # Ensures all brokers acknowledge writes
    'retries': 5     # Retry in case of failure
}

class KafkaProducer:
    def __init__(self):
        self.producer = Producer(PRODUCER_CONFIG)
    
    async def send_log_async(self, logEntry : LogEntry, kafka_topic : str = "logs")->None:
        """Send logs asynchronously to Kafka."""
        kafka_key = logEntry.log_id
        # create item dict serializable
        logEntry: dict = logEntry.dict()
        logEntry["log_timestamp"] = logEntry["log_timestamp"].isoformat()
        logEntry["start_time"] = logEntry["start_time"].isoformat()
        logEntry["end_time"] = logEntry["end_time"].isoformat()
        # produce & flush
        self.producer.produce(kafka_topic,key=kafka_key, value=json.dumps(logEntry))
        self.producer.flush()  # Ensure messages are sent
        
    async def send_message_async(self, content : dict, kafka_topic: str)->None:
        """Send message to Kafka."""
        # produce & flush
        self.producer.produce(kafka_topic, value=json.dumps(content))
        self.producer.flush()

kafkaProducer : KafkaProducer = None
def init_kafka_producer():
    """
        Init our custom kafka producer
    """
    global kafkaProducer
    if kafkaProducer is None:
        try:
            kafkaProducer = KafkaProducer()
        except Exception as e:
            raise Exception(f"Failed to load kafka producer: {e}")

def get_kafka_producer()->KafkaProducer:
    """
        retrieve our kafka producer
    """
    if kafkaProducer is None:
        raise Exception("Kafka producer is not initialized. Ensure `init_kafka_producer()` is called at startup.")
    return kafkaProducer


def send_log_sync(logEntry : LogEntry, kafka_topic : str = "logs")->None:
    """Send logs synchronously to Kafka."""
    producer = Producer(PRODUCER_CONFIG)
    kafka_key = logEntry.log_id
    # create item dict serializable
    logEntry: dict = logEntry.dict()
    logEntry["log_timestamp"] = logEntry["log_timestamp"].isoformat()
    logEntry["start_time"] = logEntry["start_time"].isoformat()
    logEntry["end_time"] = logEntry["end_time"].isoformat()
    # produce & flush
    producer.produce(kafka_topic,key=kafka_key, value=json.dumps(logEntry))
    producer.flush()

 
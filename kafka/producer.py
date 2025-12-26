from confluent_kafka import Producer


class KafkaProducer:
    """
    Wrapper class for Kafka Producer with configuration and helper methods.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """
        Initialize the Kafka producer.

        Args:
            bootstrap_servers: Comma-separated list of Kafka broker addresses.
        """
        self.config = {
            "bootstrap.servers": bootstrap_servers,
        }
        self.producer = Producer(self.config)

    def produce(self, topic: str, value: bytes, callback=None):
        """
        Produce a message to a Kafka topic.

        Args:
            topic: The Kafka topic to send the message to.
            value: The message value as bytes.
            callback: Optional callback function for delivery reports.
        """
        self.producer.produce(topic=topic, value=value, callback=callback)

    def flush(self):
        """
        Flush will block until all buffered messages are sent to the broker.
        """
        self.producer.flush()


def delivery_report(err, msg):
    """
    Callback function to handle the delivery report.

    Args:
        err: Error information if delivery failed.
        msg: Message information if delivery succeeded.
    """
    if err is not None:
        print(f"❌ Delivery failed: {err}")
    else:
        print(f"✅ Delivered: {msg.value().decode('utf-8')}")
        print(
            f"✅ Topic: {msg.topic()}, Partition: {msg.partition()}, Offset: {msg.offset()}"
        )

from confluent_kafka import Consumer, KafkaError


class KafkaConsumer:
    """
    Wrapper class for Kafka Consumer.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "default-group",
        auto_offset_reset: str = "earliest",
    ):
        """
        Initialize the Kafka consumer.

        Args:
            bootstrap_servers: Comma-separated list of Kafka broker addresses.
            group_id: Consumer group identifier.
            auto_offset_reset: Where to start consuming (earliest/latest).
        """
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
        }
        self.consumer = Consumer(self.config)

    def subscribe(self, topics: list[str]):
        """
        Subscribe to a list of topics.

        Args:
            topics: List of topic names to subscribe to.
        """
        self.consumer.subscribe(topics)

    def poll(self, timeout: float = 1.0):
        """
        Poll for new messages.

        Args:
            timeout: Maximum time to block waiting for message (seconds).

        Returns:
            Message object or None if no message available.
        """
        return self.consumer.poll(timeout=timeout)

    def close(self):
        """
        Close the consumer and commit final offsets.
        """
        self.consumer.close()


def process_message(message, message_handler):
    """
    Process a Kafka message and handle errors.

    Args:
        message: The Kafka message object.
        message_handler: Callback function to process the message value.

    Returns:
        True if message processed successfully, False otherwise.
    """
    if message is None:
        return False

    if message.error():
        if message.error().code() == KafkaError._PARTITION_EOF:
            # End of partition event - not an error
            return False
        print(f"Message Error: {message.error()}")
        return False

    try:
        message_value = message.value().decode("utf-8")
        message_handler(message_value)
        return True
    except Exception as e:
        print(f"Error processing message: {e}")
        return False

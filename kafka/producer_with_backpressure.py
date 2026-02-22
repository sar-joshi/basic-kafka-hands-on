import time
from confluent_kafka import Producer, KafkaException


class KafkaProducerWithBackpressure:
    """
    Enhanced Kafka Producer with back pressure handling.

    Back pressure prevents the producer from overwhelming Kafka when the internal
    buffer is full or when the broker can't keep up with the message rate.
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        queue_buffering_max_messages: int = 100000,  # Max messages in buffer
        queue_buffering_max_kbytes: int = 1048576,  # Max buffer size (1GB)
        linger_ms: int = 10,  # Wait time to batch messages
    ):
        """
        Initialize the Kafka producer with back pressure configuration.

        Args:
            bootstrap_servers: Comma-separated list of Kafka broker addresses.
            queue_buffering_max_messages: Maximum number of messages in buffer.
            queue_buffering_max_kbytes: Maximum buffer size in kilobytes.
            linger_ms: Time to wait for batching messages (milliseconds).
        """
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            # Back pressure related configs
            "queue.buffering.max.messages": queue_buffering_max_messages,
            "queue.buffering.max.kbytes": queue_buffering_max_kbytes,
            "linger.ms": linger_ms,  # Allow some batching
            # Block if buffer is full (instead of throwing error)
            "queue.buffering.max.ms": 1000,  # Wait up to 1 second
        }
        self.producer = Producer(self.config)
        self.messages_in_flight = 0

    def produce_with_backpressure(
        self, topic: str, key: bytes = None, value: bytes = None, callback=None
    ):
        """
        Produce a message with back pressure handling.

        This method will:
        1. Try to produce the message
        2. If buffer is full, poll to trigger callbacks and free space
        3. Retry with exponential backoff if needed

        Args:
            topic: The Kafka topic to send the message to.
            key: Optional message key for partitioning.
            value: The message value as bytes.
            callback: Optional callback function for delivery reports.

        Raises:
            KafkaException: If message cannot be produced after retries.
        """
        max_retries = 5
        retry_delay = 0.1  # Start with 100ms

        for attempt in range(max_retries):
            try:
                # Try to produce the message
                self.producer.produce(
                    topic=topic, key=key, value=value, callback=callback
                )
                self.messages_in_flight += 1

                # Poll to trigger callbacks and free up buffer space
                # Non-blocking call (timeout=0)
                self.producer.poll(0)
                return  # Success!

            except BufferError:
                # Buffer is full - apply back pressure
                print(
                    f"⚠️  Buffer full! Applying back pressure (attempt {attempt + 1}/{max_retries})"
                )

                # Poll with longer timeout to process pending messages
                self.producer.poll(1.0)

                # Exponential backoff
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Double the delay each time
                else:
                    raise KafkaException(
                        "Failed to produce message after max retries - buffer exhausted"
                    )

            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                raise

    def produce_batch_with_backpressure(
        self, topic: str, messages: list, callback=None
    ):
        """
        Produce a batch of messages with back pressure handling.

        Args:
            topic: The Kafka topic to send messages to.
            messages: List of (key, value) tuples.
            callback: Optional callback function for delivery reports.
        """
        for i, (key, value) in enumerate(messages):
            self.produce_with_backpressure(
                topic=topic, key=key, value=value, callback=callback
            )

            # Poll every 10 messages to keep buffer from filling
            if i % 10 == 0:
                self.producer.poll(0)

        print(f"✅ Batch of {len(messages)} messages queued with back pressure")

    def flush(self, timeout: float = None):
        """
        Flush all buffered messages.

        Args:
            timeout: Maximum time to wait (seconds). None = wait forever.

        Returns:
            Number of messages still in queue (0 = all flushed successfully).
        """
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            print(f"⚠️  {remaining} messages remaining in buffer after flush")
        return remaining

    def get_queue_length(self):
        """
        Get the current number of messages in the producer queue.

        Returns:
            Number of messages waiting to be sent.
        """
        return len(self.producer)


def delivery_report_with_metrics(err, msg):
    """
    Enhanced delivery report callback with metrics tracking.

    Args:
        err: Error information if delivery failed.
        msg: Message information if delivery succeeded.
    """
    if err is not None:
        print(f"❌ Delivery failed: {err}")
    else:
        # Success - could increment metrics here
        print(
            f"✅ Delivered to {msg.topic()}[{msg.partition()}] at offset {msg.offset()}"
        )

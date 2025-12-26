from unittest.mock import Mock, patch
from kafka.consumer import KafkaConsumer, process_message
from confluent_kafka import KafkaError


class TestKafkaConsumer:
    """
    Test Kafka Consumer wrapper class.
    """

    @patch("kafka.consumer.Consumer")
    def test_consumer_initialization(self, mock_consumer_class):
        """
        Test that the Kafka consumer is initialized correctly.
        """
        consumer = KafkaConsumer(
            bootstrap_servers="localhost:9092",
            group_id="test-group",
            auto_offset_reset="earliest",
        )

        mock_consumer_class.assert_called_once_with(
            {
                "bootstrap.servers": "localhost:9092",
                "group.id": "test-group",
                "auto.offset.reset": "earliest",
            }
        )
        assert consumer.config["bootstrap.servers"] == "localhost:9092"
        assert consumer.config["group.id"] == "test-group"

    @patch("kafka.consumer.Consumer")
    def test_subscribe_to_topics(self, mock_consumer_class):
        """
        Test subscribing to topics.
        """
        mock_consumer_instance = Mock()
        mock_consumer_class.return_value = mock_consumer_instance

        consumer = KafkaConsumer()
        consumer.subscribe(topics=["orders", "payments"])

        mock_consumer_instance.subscribe.assert_called_once_with(["orders", "payments"])

    @patch("kafka.consumer.Consumer")
    def test_poll_for_messages(self, mock_consumer_class):
        """
        Test polling for messages.
        """
        mock_consumer_instance = Mock()
        mock_consumer_class.return_value = mock_consumer_instance

        # Create a mock message
        mock_message = Mock()
        mock_consumer_instance.poll.return_value = mock_message

        consumer = KafkaConsumer()
        message = consumer.poll(timeout=2.0)

        assert message == mock_message
        mock_consumer_instance.poll.assert_called_once_with(timeout=2.0)

    @patch("kafka.consumer.Consumer")
    def test_close_consumer(self, mock_consumer_class):
        """
        Test closing the consumer.
        """
        mock_consumer_instance = Mock()
        mock_consumer_class.return_value = mock_consumer_instance

        consumer = KafkaConsumer()
        consumer.close()

        mock_consumer_instance.close.assert_called_once()


class TestProcessMessage:
    """
    Test the process_message function.
    """

    def test_process_message_none(self):
        """
        Test processing when message is None (no message available).
        """
        result = process_message(None, lambda x: print(x))
        assert result is False

    def test_process_message_with_error(self, capsys):
        """
        Test processing a message with an error.
        """
        mock_message = Mock()
        mock_error = Mock()
        mock_error.code.return_value = KafkaError.BROKER_NOT_AVAILABLE
        mock_message.error.return_value = mock_error

        result = process_message(mock_message, lambda x: print(x))

        assert result is False
        captured = capsys.readouterr()
        assert "Message Error" in captured.out

    def test_process_message_partition_eof(self):
        """
        Test processing end of partition (not an error).
        """
        mock_message = Mock()
        mock_error = Mock()
        mock_error.code.return_value = KafkaError._PARTITION_EOF
        mock_message.error.return_value = mock_error

        result = process_message(mock_message, lambda x: print(x))

        # Should return False but not print error
        assert result is False

    def test_process_message_success(self):
        """
        Test successfully processing a message.
        """
        mock_message = Mock()
        mock_message.error.return_value = None
        mock_message.value.return_value = b'{"order_id": "123"}'

        processed_values = []

        def handler(value):
            processed_values.append(value)

        result = process_message(mock_message, handler)

        assert result is True
        assert processed_values == ['{"order_id": "123"}']

    def test_process_message_with_order_model(self, sample_order):
        """
        Test processing a message with Order model deserialization.
        """
        from models.order import Order

        mock_message = Mock()
        mock_message.error.return_value = None
        mock_message.value.return_value = sample_order.model_dump_json().encode("utf-8")

        orders_received = []

        def order_handler(message_value):
            order = Order.model_validate_json(message_value)
            orders_received.append(order)

        result = process_message(mock_message, order_handler)

        assert result is True
        assert len(orders_received) == 1
        assert orders_received[0].customer_name == sample_order.customer_name
        assert orders_received[0].item == sample_order.item

    def test_process_message_handler_exception(self, capsys):
        """
        Test processing a message when handler raises an exception.
        """
        mock_message = Mock()
        mock_message.error.return_value = None
        mock_message.value.return_value = b"test message"

        def failing_handler(value):
            raise ValueError("Handler failed!")

        result = process_message(mock_message, failing_handler)

        assert result is False
        captured = capsys.readouterr()
        assert "Error processing message" in captured.out
        assert "Handler failed!" in captured.out

    def test_process_multiple_messages(self, sample_order):
        """
        Test processing multiple messages in sequence.
        """
        from models.order import Order

        orders_received = []

        def order_handler(message_value):
            order = Order.model_validate_json(message_value)
            orders_received.append(order)

        # Simulate 3 messages
        for i in range(3):
            mock_message = Mock()
            mock_message.error.return_value = None
            mock_message.value.return_value = sample_order.model_dump_json().encode(
                "utf-8"
            )
            process_message(mock_message, order_handler)

        assert len(orders_received) == 3

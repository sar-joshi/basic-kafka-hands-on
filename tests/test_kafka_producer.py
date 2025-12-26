from unittest.mock import Mock, patch
from kafka.producer import KafkaProducer, delivery_report


class TestKafkaProducer:
    """
    Test Kafka Producer wrapper class.
    """

    @patch("kafka.producer.Producer")
    def test_producer_initialization(self, mock_producer):
        """
        Test that the Kafka producer is initialized correctly.
        """
        producer = KafkaProducer(bootstrap_servers="localhost:9092")

        mock_producer.assert_called_once_with({"bootstrap.servers": "localhost:9092"})
        assert producer.config == {"bootstrap.servers": "localhost:9092"}

    @patch("kafka.producer.Producer")
    def test_produce_single_message(self, mock_producer, sample_order):
        """
        Test that the Kafka producer can produce a single message.
        """
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance

        producer = KafkaProducer()

        order = sample_order.model_dump_json().encode("utf-8")

        producer.produce(topic="orders", value=order, callback=delivery_report)

        mock_producer_instance.produce.assert_called_once_with(
            topic="orders", key=None, value=order, callback=delivery_report
        )

    @patch("kafka.producer.Producer")
    def test_produce_multiple_messages_in_buffer(self, mock_producer, sample_order):
        """
        Test producing multiple messages that are held in buffer before flush.
        This tests the batching behavior of Kafka producers.
        """
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance

        producer = KafkaProducer()

        orders = [sample_order.model_dump_json().encode("utf-8") for _ in range(3)]

        # Produce all messages (they go into buffer)
        for order in orders:
            producer.produce(topic="orders", value=order, callback=delivery_report)

        # Verify produce was called 3 times (messages buffered)
        assert mock_producer_instance.produce.call_count == 3

        # Flush should be called once to send all buffered messages
        producer.flush()
        mock_producer_instance.flush.assert_called_once()

    @patch("kafka.producer.Producer")
    def test_verify_buffered_message_content(self, mock_producer):
        """
        Test that buffered messages contain correct data before flush.
        """
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance

        producer = KafkaProducer()

        from models.order import Order

        # Create test orders with specific data
        order1 = Order(customer_name="Alice", item="iPhone", quantity=1, price=999)
        order2 = Order(customer_name="Bob", item="iPad", quantity=2, price=599)

        # Produce messages
        producer.produce(
            topic="orders",
            value=order1.model_dump_json().encode("utf-8"),
            callback=delivery_report,
        )
        producer.produce(
            topic="orders",
            value=order2.model_dump_json().encode("utf-8"),
            callback=delivery_report,
        )

        # Get all the calls made to produce
        calls = mock_producer_instance.produce.call_args_list

        # Verify first call
        first_call = calls[0]
        assert first_call.kwargs["topic"] == "orders"
        assert b"Alice" in first_call.kwargs["value"]
        assert b"iPhone" in first_call.kwargs["value"]

        # Verify second call
        second_call = calls[1]
        assert second_call.kwargs["topic"] == "orders"
        assert b"Bob" in second_call.kwargs["value"]
        assert b"iPad" in second_call.kwargs["value"]

        # Both should use same callback
        assert first_call.kwargs["callback"] == delivery_report
        assert second_call.kwargs["callback"] == delivery_report

    @patch("kafka.producer.Producer")
    def test_produce_with_key(self, mock_producer, sample_order):
        """
        Test producing a message with a key for partitioning.
        """
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance

        producer = KafkaProducer()

        order_key = sample_order.customer_id.encode("utf-8")
        order_value = sample_order.model_dump_json().encode("utf-8")

        producer.produce(
            topic="orders",
            key=order_key,
            value=order_value,
            callback=delivery_report,
        )

        mock_producer_instance.produce.assert_called_once_with(
            topic="orders",
            key=order_key,
            value=order_value,
            callback=delivery_report,
        )

    @patch("kafka.producer.Producer")
    def test_produce_multiple_messages_with_same_key(self, mock_producer):
        """
        Test that messages with the same key maintain ordering (same partition).
        """
        mock_producer_instance = Mock()
        mock_producer.return_value = mock_producer_instance

        producer = KafkaProducer()

        from models.order import Order

        # Create multiple orders for the same customer
        customer_key = b"customer-123"
        orders = [
            Order(customer_name="Alice", item="iPhone", quantity=1, price=999),
            Order(customer_name="Alice", item="iPad", quantity=1, price=599),
            Order(customer_name="Alice", item="MacBook", quantity=1, price=2499),
        ]

        # Produce all messages with the same key
        for order in orders:
            producer.produce(
                topic="orders",
                key=customer_key,
                value=order.model_dump_json().encode("utf-8"),
                callback=delivery_report,
            )

        # Verify all 3 messages were sent with the same key
        assert mock_producer_instance.produce.call_count == 3

        calls = mock_producer_instance.produce.call_args_list
        for call in calls:
            assert call.kwargs["key"] == customer_key
            assert call.kwargs["topic"] == "orders"


class TestDeliveryReport:
    """
    Test the delivery report callback function.
    """

    def test_delivery_report_success(self, capsys):
        """
        Test delivery report for successful message delivery.
        """
        mock_msg = Mock()
        mock_msg.topic.return_value = "orders"
        mock_msg.partition.return_value = 0
        mock_msg.offset.return_value = 42
        mock_msg.value.return_value = b'{"order_id": "123"}'

        delivery_report(None, mock_msg)

        captured = capsys.readouterr()
        assert "✅ Delivered" in captured.out
        assert "orders" in captured.out
        assert "42" in captured.out

    def test_delivery_report_failure(self, capsys):
        """
        Test delivery report for failed message delivery.
        """
        delivery_report("Connection timeout", None)

        captured = capsys.readouterr()
        assert "❌ Delivery failed" in captured.out
        assert "Connection timeout" in captured.out

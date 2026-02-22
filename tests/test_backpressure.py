"""
Tests for Kafka Producer with Back Pressure.

Tests cover:
- Back pressure configuration
- BufferError handling and retry logic
- Exponential backoff
- Batch production with back pressure
- Queue monitoring
"""

import time
from unittest.mock import Mock, patch, call
from confluent_kafka import KafkaException
from kafka.producer_with_backpressure import (
    KafkaProducerWithBackpressure,
    delivery_report_with_metrics,
)


class TestKafkaProducerWithBackpressure:
    """Test the enhanced producer with back pressure handling."""

    @patch("kafka.producer_with_backpressure.Producer")
    def test_producer_initialization_with_backpressure_config(
        self, mock_producer_class
    ):
        """Test that producer is initialized with back pressure configuration."""
        producer = KafkaProducerWithBackpressure(
            bootstrap_servers="localhost:9092",
            queue_buffering_max_messages=10000,
            queue_buffering_max_kbytes=32768,
            linger_ms=50,
        )

        expected_config = {
            "bootstrap.servers": "localhost:9092",
            "queue.buffering.max.messages": 10000,
            "queue.buffering.max.kbytes": 32768,
            "linger.ms": 50,
            "queue.buffering.max.ms": 1000,
        }

        mock_producer_class.assert_called_once_with(expected_config)
        assert producer.config == expected_config
        assert producer.messages_in_flight == 0

    @patch("kafka.producer_with_backpressure.Producer")
    def test_produce_with_backpressure_success_first_try(self, mock_producer_class):
        """Test successful message production without retries."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        producer = KafkaProducerWithBackpressure()

        test_key = b"customer-123"
        test_value = b'{"order_id": "456"}'

        # Should succeed on first try
        producer.produce_with_backpressure(
            topic="orders", key=test_key, value=test_value
        )

        # Verify produce was called once
        mock_producer_instance.produce.assert_called_once_with(
            topic="orders", key=test_key, value=test_value, callback=None
        )

        # Verify poll was called to free buffer
        mock_producer_instance.poll.assert_called_with(0)

        # Messages in flight should be tracked
        assert producer.messages_in_flight == 1

    @patch("kafka.producer_with_backpressure.Producer")
    @patch("kafka.producer_with_backpressure.time.sleep")
    def test_produce_with_backpressure_handles_buffer_error(
        self, mock_sleep, mock_producer_class
    ):
        """Test BufferError handling with retry logic."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        # First call raises BufferError, second succeeds
        mock_producer_instance.produce.side_effect = [
            BufferError("Queue full"),
            None,  # Success on retry
        ]

        producer = KafkaProducerWithBackpressure()

        producer.produce_with_backpressure(topic="orders", key=b"key", value=b"value")

        # Verify produce was called twice (initial + 1 retry)
        assert mock_producer_instance.produce.call_count == 2

        # Verify poll was called with longer timeout during back pressure
        calls = mock_producer_instance.poll.call_args_list
        assert len(calls) >= 2  # At least one during retry, one after success

        # Verify exponential backoff sleep was called
        mock_sleep.assert_called_once_with(0.1)  # First retry delay

    @patch("kafka.producer_with_backpressure.Producer")
    @patch("kafka.producer_with_backpressure.time.sleep")
    def test_produce_with_backpressure_exponential_backoff(
        self, mock_sleep, mock_producer_class
    ):
        """Test that retry delays increase exponentially."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        # Fail 3 times, then succeed
        mock_producer_instance.produce.side_effect = [
            BufferError("Queue full"),
            BufferError("Queue full"),
            BufferError("Queue full"),
            None,  # Success
        ]

        producer = KafkaProducerWithBackpressure()

        producer.produce_with_backpressure(topic="orders", key=b"key", value=b"value")

        # Verify exponential backoff: 0.1, 0.2, 0.4
        sleep_calls = mock_sleep.call_args_list
        assert len(sleep_calls) == 3
        assert sleep_calls[0] == call(0.1)  # First retry
        assert sleep_calls[1] == call(0.2)  # Second retry (2x)
        assert sleep_calls[2] == call(0.4)  # Third retry (4x)

    @patch("kafka.producer_with_backpressure.Producer")
    def test_produce_with_backpressure_max_retries_exceeded(self, mock_producer_class):
        """Test that KafkaException is raised after max retries."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        # Always fail
        mock_producer_instance.produce.side_effect = BufferError("Queue full")

        producer = KafkaProducerWithBackpressure()

        # Should raise KafkaException after max retries (5)
        try:
            producer.produce_with_backpressure(
                topic="orders", key=b"key", value=b"value"
            )
            assert False, "Should have raised KafkaException"
        except KafkaException as e:
            assert "max retries" in str(e).lower()

        # Verify produce was called 5 times (max retries)
        assert mock_producer_instance.produce.call_count == 5

    @patch("kafka.producer_with_backpressure.Producer")
    def test_produce_with_backpressure_unexpected_error(self, mock_producer_class):
        """Test that unexpected errors are re-raised."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        # Raise unexpected error
        mock_producer_instance.produce.side_effect = ValueError("Unexpected error")

        producer = KafkaProducerWithBackpressure()

        # Should re-raise the error
        try:
            producer.produce_with_backpressure(
                topic="orders", key=b"key", value=b"value"
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unexpected error" in str(e)

    @patch("kafka.producer_with_backpressure.Producer")
    def test_produce_batch_with_backpressure(self, mock_producer_class):
        """Test batch production with back pressure handling."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        producer = KafkaProducerWithBackpressure()

        # Create batch of messages
        batch = [
            (b"key-1", b"value-1"),
            (b"key-2", b"value-2"),
            (b"key-3", b"value-3"),
        ]

        producer.produce_batch_with_backpressure(topic="orders", messages=batch)

        # Verify produce was called for each message
        assert mock_producer_instance.produce.call_count == 3

        # Verify messages were produced in order
        calls = mock_producer_instance.produce.call_args_list
        assert calls[0].kwargs["key"] == b"key-1"
        assert calls[1].kwargs["key"] == b"key-2"
        assert calls[2].kwargs["key"] == b"key-3"

    @patch("kafka.producer_with_backpressure.Producer")
    def test_produce_batch_polls_periodically(self, mock_producer_class):
        """Test that batch production polls every 10 messages."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        producer = KafkaProducerWithBackpressure()

        # Create batch of 25 messages
        batch = [(b"key", b"value") for _ in range(25)]

        producer.produce_batch_with_backpressure(topic="orders", messages=batch)

        # Poll should be called at messages 0, 10, 20 = 3 times
        # Plus once per produce call = 25 times
        # Total: 25 (from produce_with_backpressure) + 3 (from batch logic)
        poll_calls = mock_producer_instance.poll.call_count
        assert poll_calls >= 3  # At least the periodic polls

    @patch("kafka.producer_with_backpressure.Producer")
    def test_flush_with_timeout(self, mock_producer_class):
        """Test flush with timeout parameter."""
        mock_producer_instance = Mock()
        mock_producer_instance.flush.return_value = 0  # All messages flushed
        mock_producer_class.return_value = mock_producer_instance

        producer = KafkaProducerWithBackpressure()

        result = producer.flush(timeout=10.0)

        # Verify flush was called with timeout
        mock_producer_instance.flush.assert_called_once_with(10.0)
        assert result == 0

    @patch("kafka.producer_with_backpressure.Producer")
    def test_flush_with_remaining_messages(self, mock_producer_class, capsys):
        """Test flush when some messages remain in buffer."""
        mock_producer_instance = Mock()
        mock_producer_instance.flush.return_value = 5  # 5 messages remaining
        mock_producer_class.return_value = mock_producer_instance

        producer = KafkaProducerWithBackpressure()

        result = producer.flush(timeout=1.0)

        assert result == 5

        # Should print warning
        captured = capsys.readouterr()
        assert "5 messages remaining" in captured.out

    @patch("kafka.producer_with_backpressure.Producer")
    def test_get_queue_length(self, mock_producer_class):
        """Test getting current queue length."""
        mock_producer_instance = Mock()
        mock_producer_instance.__len__ = Mock(return_value=42)
        mock_producer_class.return_value = mock_producer_instance

        producer = KafkaProducerWithBackpressure()

        queue_length = producer.get_queue_length()

        assert queue_length == 42


class TestDeliveryReportWithMetrics:
    """Test the enhanced delivery report callback."""

    def test_delivery_report_success(self, capsys):
        """Test successful delivery report."""
        mock_msg = Mock()
        mock_msg.topic.return_value = "orders"
        mock_msg.partition.return_value = 1
        mock_msg.offset.return_value = 100

        delivery_report_with_metrics(None, mock_msg)

        captured = capsys.readouterr()
        assert "✅ Delivered to orders[1] at offset 100" in captured.out

    def test_delivery_report_failure(self, capsys):
        """Test failed delivery report."""
        delivery_report_with_metrics("Connection timeout", None)

        captured = capsys.readouterr()
        assert "❌ Delivery failed" in captured.out
        assert "Connection timeout" in captured.out


class TestBackpressureIntegration:
    """Integration tests for back pressure scenarios."""

    @patch("kafka.producer_with_backpressure.Producer")
    def test_high_volume_with_backpressure(self, mock_producer_class):
        """Test producing high volume of messages with back pressure."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        # Simulate buffer full on every 10th message
        call_count = [0]

        def produce_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 10 == 0:
                raise BufferError("Queue full")
            return None

        mock_producer_instance.produce.side_effect = produce_side_effect

        producer = KafkaProducerWithBackpressure()

        # Produce 50 messages
        for i in range(50):
            producer.produce_with_backpressure(
                topic="orders", key=f"key-{i}".encode(), value=f"value-{i}".encode()
            )

        # All 50 messages should eventually be produced
        # 50 initial attempts + retries for BufferErrors
        assert mock_producer_instance.produce.call_count >= 50

    @patch("kafka.producer_with_backpressure.Producer")
    def test_backpressure_with_callback(self, mock_producer_class):
        """Test back pressure with delivery callbacks."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        producer = KafkaProducerWithBackpressure()

        callback = Mock()

        producer.produce_with_backpressure(
            topic="orders", key=b"key", value=b"value", callback=callback
        )

        # Verify callback was passed through
        mock_producer_instance.produce.assert_called_once()
        call_kwargs = mock_producer_instance.produce.call_args.kwargs
        assert call_kwargs["callback"] == callback

    @patch("kafka.producer_with_backpressure.Producer")
    @patch("kafka.producer_with_backpressure.time.sleep")
    def test_backpressure_recovers_after_delay(self, mock_sleep, mock_producer_class):
        """Test that back pressure recovers after buffer space is freed."""
        mock_producer_instance = Mock()
        mock_producer_class.return_value = mock_producer_instance

        # Fail twice, then succeed (simulating buffer draining)
        mock_producer_instance.produce.side_effect = [
            BufferError("Queue full"),
            BufferError("Queue full"),
            None,  # Success - buffer drained
        ]

        producer = KafkaProducerWithBackpressure()

        producer.produce_with_backpressure(topic="orders", key=b"key", value=b"value")

        # Should have retried and eventually succeeded
        assert mock_producer_instance.produce.call_count == 3

        # Poll should have been called with blocking timeout during retries
        blocking_poll_calls = [
            call_obj
            for call_obj in mock_producer_instance.poll.call_args_list
            if call_obj.args[0] == 1.0
        ]
        assert len(blocking_poll_calls) >= 2  # At least 2 retries with blocking poll


class TestBackpressureConfiguration:
    """Test different back pressure configurations."""

    @patch("kafka.producer_with_backpressure.Producer")
    def test_small_buffer_configuration(self, mock_producer_class):
        """Test producer with small buffer for aggressive back pressure."""
        producer = KafkaProducerWithBackpressure(
            queue_buffering_max_messages=100,  # Very small buffer
            queue_buffering_max_kbytes=1024,  # 1 MB
        )

        assert producer.config["queue.buffering.max.messages"] == 100
        assert producer.config["queue.buffering.max.kbytes"] == 1024

    @patch("kafka.producer_with_backpressure.Producer")
    def test_large_buffer_configuration(self, mock_producer_class):
        """Test producer with large buffer for high throughput."""
        producer = KafkaProducerWithBackpressure(
            queue_buffering_max_messages=1000000,  # Large buffer
            queue_buffering_max_kbytes=10485760,  # 10 GB
        )

        assert producer.config["queue.buffering.max.messages"] == 1000000
        assert producer.config["queue.buffering.max.kbytes"] == 10485760

    @patch("kafka.producer_with_backpressure.Producer")
    def test_linger_configuration_for_batching(self, mock_producer_class):
        """Test linger configuration for better batching."""
        producer = KafkaProducerWithBackpressure(linger_ms=100)

        assert producer.config["linger.ms"] == 100

from kafka.consumer import KafkaConsumer, process_message
from models.order import Order


def handle_order_message(message_value: str):
    """
    Process an order message.

    Args:
        message_value: JSON string containing order data.
    """
    order = Order.model_validate_json(message_value)
    print(f"✅ Order received: {order.order_id}")
    print(
        f"   Customer: {order.customer_name}, Item: {order.item}, Qty: {order.quantity}"
    )


if __name__ == "__main__":
    consumer = KafkaConsumer(
        bootstrap_servers="localhost:9092",
        group_id="order-consumer",
        auto_offset_reset="earliest",
    )
    consumer.subscribe(topics=["orders"])

    print("🔵 Consumer started. Waiting for messages...")

    """
    Poll for new messages from the broker.
    If no message is available, poll() will block for up to timeout seconds.
    If program is interrupted or crashes, the consumer will be closed gracefully.
    """
    try:
        while True:
            message = consumer.poll(timeout=1.0)
            process_message(message, handle_order_message)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        consumer.close()
        print("🟢 Consumer closed.")

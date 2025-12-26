from kafka.producer import KafkaProducer, delivery_report
from models.order import Order

if __name__ == "__main__":
    # Initialize Kafka producer
    producer = KafkaProducer(bootstrap_servers="localhost:9092")

    # Create an order object
    order = Order(
        customer_name="John Doe",
        item="MacBook Pro",
        quantity=1,
        price=100,
    )

    """
    Producer buffer will hold the messages in memory before they are sent to the broker.
    This is to improve performance by batching messages together before sending them to the broker.
    """
    producer.produce(
        topic="orders",
        value=order.model_dump_json().encode("utf-8"),
        callback=delivery_report,
    )

    """
    Flush will block until all buffered messages are sent to the broker before exiting the program.
    If program crashes, the buffered messages are later sent when producer is reinitialized.
    """
    producer.flush()

"""
Order Producer with Back Pressure

This demonstrates how to produce high-volume messages with back pressure handling
to prevent overwhelming the Kafka cluster.
"""

import time
from kafka.producer_with_backpressure import (
    KafkaProducerWithBackpressure,
    delivery_report_with_metrics,
)
from models.order import Order


def simulate_high_volume_orders():
    """
    Simulate high-volume order production with back pressure.
    """
    # Initialize producer with back pressure configuration
    producer = KafkaProducerWithBackpressure(
        bootstrap_servers="localhost:9092",
        queue_buffering_max_messages=10000,  # Smaller buffer for demo
        linger_ms=10,  # Batch messages for 10ms
    )

    print("🚀 Starting high-volume order production with back pressure...")
    print(f"📊 Initial queue length: {producer.get_queue_length()}\n")

    customers = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
    items = ["iPhone", "iPad", "MacBook", "Apple Watch", "AirPods"]

    try:
        # Produce 100 orders rapidly
        for i in range(100):
            order = Order(
                customer_name=customers[i % len(customers)],
                item=items[i % len(items)],
                quantity=1,
                price=999.99 + i,
            )

            # Use customer_name as key for partitioning
            producer.produce_with_backpressure(
                topic="orders",
                key=order.customer_name.encode("utf-8"),
                value=order.model_dump_json().encode("utf-8"),
                callback=delivery_report_with_metrics,
            )

            # Show progress every 20 messages
            if (i + 1) % 20 == 0:
                queue_len = producer.get_queue_length()
                print(f"📈 Produced {i + 1} orders | Queue length: {queue_len}")

        print(f"\n✅ All orders queued! Final queue length: {producer.get_queue_length()}")

        # Flush all messages
        print("🔄 Flushing messages...")
        remaining = producer.flush(timeout=30)

        if remaining == 0:
            print("✅ All messages successfully sent!")
        else:
            print(f"⚠️  {remaining} messages could not be sent")

    except Exception as e:
        print(f"❌ Error: {e}")
        producer.flush()


def simulate_batch_production():
    """
    Demonstrate batch production with back pressure.
    """
    producer = KafkaProducerWithBackpressure(
        bootstrap_servers="localhost:9092",
        linger_ms=50,  # Wait longer for better batching
    )

    print("\n🚀 Batch production with back pressure...\n")

    # Create a batch of orders
    batch = []
    for i in range(50):
        order = Order(
            customer_name=f"Customer-{i}",
            item="Bulk Order Item",
            quantity=10,
            price=100.00,
        )
        key = order.customer_id.encode("utf-8")
        value = order.model_dump_json().encode("utf-8")
        batch.append((key, value))

    # Produce the batch with back pressure
    producer.produce_batch_with_backpressure(
        topic="orders", messages=batch, callback=delivery_report_with_metrics
    )

    # Flush
    producer.flush()
    print("✅ Batch production complete!")


if __name__ == "__main__":
    print("=" * 60)
    print("KAFKA PRODUCER WITH BACK PRESSURE DEMO")
    print("=" * 60)

    # Demo 1: High-volume production
    simulate_high_volume_orders()

    # Wait a bit
    time.sleep(2)

    # Demo 2: Batch production
    simulate_batch_production()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


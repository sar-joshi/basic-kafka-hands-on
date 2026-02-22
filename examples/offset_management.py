"""
Kafka Offset Management Examples

Demonstrates:
- Manual offset commit (at-least-once delivery)
- Auto-commit vs manual commit
- Resetting offsets to specific positions
- Monitoring consumer lag
- Handling consumer rebalancing

Run: python examples/offset_management.py
"""

from confluent_kafka import Consumer, KafkaError
from models.order import Order


def example_manual_commit():
    """
    Example 1: Manual Offset Commit (Recommended for Production)
    
    Commits offsets AFTER successful processing to ensure at-least-once delivery.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Manual Offset Commit (At-Least-Once Delivery)")
    print("=" * 70)
    
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "manual-commit-example",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,  # Manual control
    }
    
    consumer = Consumer(config)
    consumer.subscribe(["orders"])
    
    print("\n🔵 Consumer started with manual offset commit")
    print("📊 Delivery guarantee: At-Least-Once")
    print("⚙️  Press Ctrl+C to stop\n")
    
    processed_count = 0
    
    try:
        while True:
            message = consumer.poll(timeout=1.0)
            
            if message is None:
                continue
            
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                print(f"❌ Error: {message.error()}")
                continue
            
            try:
                # 1. Process the message
                order = Order.model_validate_json(message.value().decode("utf-8"))
                print(f"✅ Processed order: {order.order_id}")
                print(f"   Partition: {message.partition()}, Offset: {message.offset()}")
                
                processed_count += 1
                
                # 2. Commit offset AFTER successful processing
                consumer.commit(message=message)
                print(f"📍 Committed offset: {message.offset()}\n")
                
            except Exception as e:
                # Processing failed - DO NOT commit
                print(f"❌ Failed at offset {message.offset()}: {e}")
                print(f"   Will retry this message (not committing)\n")
                continue
                
    except KeyboardInterrupt:
        print(f"\n⚠️  Shutting down... Processed {processed_count} messages")
    finally:
        consumer.close()
        print("🟢 Consumer closed")


def example_auto_commit():
    """
    Example 2: Auto-Commit
    
    Kafka automatically commits offsets at regular intervals.
    Simpler but riskier - messages may be lost if consumer crashes.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Auto-Commit (Simple but Risky)")
    print("=" * 70)
    
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "auto-commit-example",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,           # Auto-commit enabled
        "auto.commit.interval.ms": 5000,      # Commit every 5 seconds
    }
    
    consumer = Consumer(config)
    consumer.subscribe(["orders"])
    
    print("\n🔵 Consumer started with auto-commit")
    print("⚠️  Risk: Messages may be lost if consumer crashes")
    print("⚙️  Press Ctrl+C to stop\n")
    
    try:
        while True:
            message = consumer.poll(timeout=1.0)
            
            if message is None:
                continue
            
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                print(f"❌ Error: {message.error()}")
                continue
            
            try:
                order = Order.model_validate_json(message.value().decode("utf-8"))
                print(f"✅ Processed: {order.order_id} (offset: {message.offset()})")
                
                # No explicit commit needed - auto-commit handles it
                # ⚠️ If crash happens here, message may be lost!
                
            except Exception as e:
                print(f"❌ Failed: {e}")
                
    except KeyboardInterrupt:
        print("\n⚠️  Shutting down...")
    finally:
        consumer.close()
        print("🟢 Consumer closed")


def example_commit_batch():
    """
    Example 3: Batch Commit
    
    Commits offsets every N messages for better performance.
    Good balance between reliability and performance.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Batch Commit (Performance Optimization)")
    print("=" * 70)
    
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "batch-commit-example",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    
    consumer = Consumer(config)
    consumer.subscribe(["orders"])
    
    print("\n🔵 Consumer started with batch commit")
    print("📊 Commits every 10 messages for better performance")
    print("⚙️  Press Ctrl+C to stop\n")
    
    BATCH_SIZE = 10
    processed_count = 0
    
    try:
        while True:
            message = consumer.poll(timeout=1.0)
            
            if message is None:
                continue
            
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                print(f"❌ Error: {message.error()}")
                continue
            
            try:
                order = Order.model_validate_json(message.value().decode("utf-8"))
                print(f"✅ Processed: {order.order_id} (offset: {message.offset()})")
                
                processed_count += 1
                
                # Commit every BATCH_SIZE messages
                if processed_count % BATCH_SIZE == 0:
                    consumer.commit(message=message)
                    print(f"📍 Batch commit at offset {message.offset()} ({processed_count} messages)\n")
                
            except Exception as e:
                print(f"❌ Failed: {e}")
                
    except KeyboardInterrupt:
        print(f"\n⚠️  Shutting down... Processed {processed_count} messages")
        # Commit any remaining messages
        consumer.commit()
        print("📍 Final commit")
    finally:
        consumer.close()
        print("🟢 Consumer closed")


def example_specific_offset():
    """
    Example 4: Seek to Specific Offset
    
    Demonstrates how to manually seek to a specific offset.
    Useful for reprocessing specific messages.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Seek to Specific Offset")
    print("=" * 70)
    
    from confluent_kafka import TopicPartition
    
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "seek-offset-example",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    
    consumer = Consumer(config)
    consumer.subscribe(["orders"])
    
    # Wait for assignment
    print("\n🔵 Waiting for partition assignment...")
    message = consumer.poll(timeout=5.0)
    
    if message:
        # Seek to offset 0 (beginning) on assigned partition
        partition = TopicPartition("orders", message.partition(), 0)
        consumer.seek(partition)
        print(f"📍 Seeked to offset 0 on partition {message.partition()}")
        print("⚙️  Processing from beginning...\n")
        
        count = 0
        try:
            while count < 5:  # Process only 5 messages for demo
                msg = consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    continue
                
                try:
                    order = Order.model_validate_json(msg.value().decode("utf-8"))
                    print(f"✅ Offset {msg.offset()}: {order.order_id}")
                    count += 1
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
        except KeyboardInterrupt:
            pass
    
    consumer.close()
    print("\n🟢 Consumer closed")


def example_monitor_lag():
    """
    Example 5: Monitor Consumer Lag
    
    Shows how to check consumer lag programmatically.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Monitor Consumer Lag")
    print("=" * 70)
    
    from confluent_kafka.admin import AdminClient
    
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "lag-monitor-example",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    
    consumer = Consumer(config)
    consumer.subscribe(["orders"])
    
    # Process a few messages
    print("\n🔵 Processing messages and monitoring lag...")
    
    try:
        for i in range(3):
            message = consumer.poll(timeout=2.0)
            
            if message and not message.error():
                order = Order.model_validate_json(message.value().decode("utf-8"))
                print(f"\n✅ Processed: {order.order_id}")
                
                # Get committed offset
                partitions = consumer.assignment()
                committed = consumer.committed(partitions, timeout=1.0)
                
                # Get high watermark (latest offset)
                low_high = consumer.get_watermark_offsets(
                    message.partition(),
                    timeout=1.0
                )
                
                if committed:
                    for partition in committed:
                        if partition.offset >= 0:
                            lag = low_high[1] - partition.offset
                            print(f"📊 Lag Stats:")
                            print(f"   Partition: {partition.partition}")
                            print(f"   Current offset: {message.offset()}")
                            print(f"   Committed offset: {partition.offset}")
                            print(f"   High watermark: {low_high[1]}")
                            print(f"   Lag: {lag} messages")
                
                consumer.commit(message=message)
                
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        print("\n🟢 Consumer closed")


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 70)
    print("KAFKA OFFSET MANAGEMENT EXAMPLES")
    print("=" * 70)
    
    print("\nAvailable examples:")
    print("  1. Manual Commit (at-least-once delivery)")
    print("  2. Auto-Commit (simple but risky)")
    print("  3. Batch Commit (performance optimization)")
    print("  4. Seek to Specific Offset (reprocess messages)")
    print("  5. Monitor Consumer Lag")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nEnter example number (1-5) or 'all': ")
    
    examples = {
        "1": example_manual_commit,
        "2": example_auto_commit,
        "3": example_commit_batch,
        "4": example_specific_offset,
        "5": example_monitor_lag,
    }
    
    if choice == "all":
        for func in examples.values():
            func()
    elif choice in examples:
        examples[choice]()
    else:
        print("❌ Invalid choice!")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE!")
    print("=" * 70)
    print("\n📚 For more info, see: docs/OFFSETS.md\n")

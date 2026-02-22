"""
Kafka Idempotent Processing Examples

Demonstrates different strategies for handling duplicate messages:
- Database unique constraint (recommended)
- In-memory deduplication
- Redis-based deduplication
- Transaction-based processing

Run: python examples/idempotent_processing.py
"""

from confluent_kafka import Consumer, KafkaError
from models.order import Order
from datetime import datetime, timedelta


def example_unique_constraint_simulation():
    """
    Example 1: Database Unique Constraint (Recommended)
    
    Simulates using a database unique constraint to prevent duplicates.
    In production, this would be a real database with PRIMARY KEY constraint.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Idempotent Processing with Unique Constraint")
    print("=" * 70)
    
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "idempotent-unique-constraint",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    
    consumer = Consumer(config)
    consumer.subscribe(["orders"])
    
    # Simulate database with set (in production: use real database)
    processed_orders = set()
    
    print("\n🔵 Consumer started with idempotent processing")
    print("💾 Using unique constraint pattern")
    print("⚙️  Press Ctrl+C to stop\n")
    
    processed_count = 0
    duplicate_count = 0
    
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
                
                # Simulate database INSERT with unique constraint
                if order.order_id in processed_orders:
                    # Duplicate! (would be IntegrityError in real database)
                    duplicate_count += 1
                    print(f"⏭️  DUPLICATE: Order {order.order_id} already processed")
                    print(f"   Offset: {message.offset()} (skipping)\n")
                else:
                    # Process the order
                    processed_orders.add(order.order_id)
                    processed_count += 1
                    print(f"✅ PROCESSED: Order {order.order_id}")
                    print(f"   Item: {order.item}, Price: ${order.price}")
                    print(f"   Offset: {message.offset()}\n")
                
                # Always commit offset (even for duplicates)
                consumer.commit(message=message)
                
            except Exception as e:
                print(f"❌ Failed: {e}\n")
                
    except KeyboardInterrupt:
        print(f"\n⚠️  Shutting down...")
    finally:
        consumer.close()
        print(f"\n📊 Statistics:")
        print(f"   ✅ Processed: {processed_count} unique orders")
        print(f"   ⏭️  Skipped: {duplicate_count} duplicates")
        print("🟢 Consumer closed")


def example_in_memory_deduplication():
    """
    Example 2: In-Memory Deduplication with Time Window
    
    Keeps recent order IDs in memory to detect duplicates within a time window.
    Suitable for high-throughput scenarios where strict deduplication isn't critical.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: In-Memory Deduplication (Time Window)")
    print("=" * 70)
    
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "idempotent-in-memory",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    
    consumer = Consumer(config)
    consumer.subscribe(["orders"])
    
    # In-memory cache with timestamps
    recent_orders = {}  # {order_id: timestamp}
    DEDUP_WINDOW = timedelta(minutes=5)  # 5-minute window
    
    print("\n🔵 Consumer started with in-memory deduplication")
    print("⏱️  Deduplication window: 5 minutes")
    print("⚙️  Press Ctrl+C to stop\n")
    
    processed_count = 0
    duplicate_count = 0
    
    try:
        while True:
            message = consumer.poll(timeout=1.0)
            
            if message is None:
                # Cleanup old entries
                current_time = datetime.now()
                expired_keys = [
                    order_id for order_id, timestamp in recent_orders.items()
                    if current_time - timestamp > DEDUP_WINDOW
                ]
                for key in expired_keys:
                    del recent_orders[key]
                
                if expired_keys:
                    print(f"🧹 Cleaned up {len(expired_keys)} expired entries")
                
                continue
            
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    continue
                print(f"❌ Error: {message.error()}")
                continue
            
            try:
                order = Order.model_validate_json(message.value().decode("utf-8"))
                current_time = datetime.now()
                
                # Check if recently processed
                if order.order_id in recent_orders:
                    time_since = current_time - recent_orders[order.order_id]
                    duplicate_count += 1
                    print(f"⏭️  DUPLICATE: Order {order.order_id}")
                    print(f"   Last seen: {time_since.total_seconds():.1f}s ago")
                    print(f"   Offset: {message.offset()}\n")
                else:
                    # Process and cache
                    recent_orders[order.order_id] = current_time
                    processed_count += 1
                    print(f"✅ PROCESSED: Order {order.order_id}")
                    print(f"   Cache size: {len(recent_orders)} entries")
                    print(f"   Offset: {message.offset()}\n")
                
                consumer.commit(message=message)
                
            except Exception as e:
                print(f"❌ Failed: {e}\n")
                
    except KeyboardInterrupt:
        print(f"\n⚠️  Shutting down...")
    finally:
        consumer.close()
        print(f"\n📊 Statistics:")
        print(f"   ✅ Processed: {processed_count} orders")
        print(f"   ⏭️  Duplicates: {duplicate_count}")
        print(f"   💾 Cache size: {len(recent_orders)} entries")
        print("🟢 Consumer closed")


def example_checksum_based_deduplication():
    """
    Example 3: Checksum-Based Deduplication
    
    Uses message content hash to detect duplicates even if order_id changes.
    Useful for detecting exact duplicate messages.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Checksum-Based Deduplication")
    print("=" * 70)
    
    import hashlib
    
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "idempotent-checksum",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    
    consumer = Consumer(config)
    consumer.subscribe(["orders"])
    
    # Store checksums of processed messages
    processed_checksums = set()
    
    def calculate_checksum(order: Order) -> str:
        """Calculate message checksum."""
        # Use relevant fields (not order_id which may differ)
        content = f"{order.customer_name}|{order.item}|{order.quantity}|{order.price}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    print("\n🔵 Consumer started with checksum deduplication")
    print("🔐 Detects duplicates by message content")
    print("⚙️  Press Ctrl+C to stop\n")
    
    processed_count = 0
    duplicate_count = 0
    
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
                checksum = calculate_checksum(order)
                
                if checksum in processed_checksums:
                    duplicate_count += 1
                    print(f"⏭️  DUPLICATE CONTENT: Order {order.order_id}")
                    print(f"   Checksum: {checksum}")
                    print(f"   Offset: {message.offset()}\n")
                else:
                    processed_checksums.add(checksum)
                    processed_count += 1
                    print(f"✅ PROCESSED: Order {order.order_id}")
                    print(f"   Checksum: {checksum}")
                    print(f"   {order.customer_name}: {order.item} x{order.quantity}")
                    print(f"   Offset: {message.offset()}\n")
                
                consumer.commit(message=message)
                
            except Exception as e:
                print(f"❌ Failed: {e}\n")
                
    except KeyboardInterrupt:
        print(f"\n⚠️  Shutting down...")
    finally:
        consumer.close()
        print(f"\n📊 Statistics:")
        print(f"   ✅ Unique messages: {processed_count}")
        print(f"   ⏭️  Duplicates: {duplicate_count}")
        print(f"   🔐 Checksums stored: {len(processed_checksums)}")
        print("🟢 Consumer closed")


def example_with_state_tracking():
    """
    Example 4: Idempotent Processing with State Tracking
    
    Tracks processing state to handle partial failures and retries.
    Useful for multi-step processing pipelines.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Idempotent Processing with State Tracking")
    print("=" * 70)
    
    config = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "idempotent-state-tracking",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    
    consumer = Consumer(config)
    consumer.subscribe(["orders"])
    
    # Track processing state
    processing_state = {}  # {order_id: {"status": "...", "step": N}}
    
    print("\n🔵 Consumer started with state tracking")
    print("📊 Tracks processing progress for multi-step operations")
    print("⚙️  Press Ctrl+C to stop\n")
    
    def process_order_steps(order: Order):
        """Simulate multi-step processing."""
        order_id = order.order_id
        
        # Check current state
        if order_id not in processing_state:
            processing_state[order_id] = {"status": "new", "step": 0}
        
        state = processing_state[order_id]
        
        # Step 1: Validate
        if state["step"] < 1:
            print(f"   Step 1: Validating order...")
            state["step"] = 1
            state["status"] = "validated"
        
        # Step 2: Reserve inventory
        if state["step"] < 2:
            print(f"   Step 2: Reserving inventory...")
            state["step"] = 2
            state["status"] = "reserved"
        
        # Step 3: Process payment
        if state["step"] < 3:
            print(f"   Step 3: Processing payment...")
            state["step"] = 3
            state["status"] = "completed"
        
        return state["status"] == "completed"
    
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
                
                state = processing_state.get(order.order_id)
                if state and state["status"] == "completed":
                    print(f"⏭️  ALREADY COMPLETED: Order {order.order_id}")
                    print(f"   State: {state}")
                    print(f"   Offset: {message.offset()}\n")
                else:
                    print(f"🔄 PROCESSING: Order {order.order_id}")
                    completed = process_order_steps(order)
                    
                    if completed:
                        print(f"✅ COMPLETED: Order {order.order_id}")
                        print(f"   All steps finished")
                        print(f"   Offset: {message.offset()}\n")
                
                consumer.commit(message=message)
                
            except Exception as e:
                print(f"❌ Failed: {e}\n")
                # State is preserved, will retry from last step
                
    except KeyboardInterrupt:
        print(f"\n⚠️  Shutting down...")
    finally:
        consumer.close()
        print(f"\n📊 Processing State:")
        for order_id, state in list(processing_state.items())[:5]:
            print(f"   {order_id}: {state}")
        print("🟢 Consumer closed")


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 70)
    print("KAFKA IDEMPOTENT PROCESSING EXAMPLES")
    print("=" * 70)
    
    print("\nAvailable examples:")
    print("  1. Unique Constraint Pattern (recommended)")
    print("  2. In-Memory Deduplication (time window)")
    print("  3. Checksum-Based Deduplication")
    print("  4. State Tracking (multi-step processing)")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nEnter example number (1-4) or 'all': ")
    
    examples = {
        "1": example_unique_constraint_simulation,
        "2": example_in_memory_deduplication,
        "3": example_checksum_based_deduplication,
        "4": example_with_state_tracking,
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
    print("\n💡 Key Takeaway: Always make processing idempotent!")
    print("📚 For more info, see README.md (Idempotent Processing section)\n")

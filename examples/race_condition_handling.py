"""
Kafka Race Condition Handling Examples

Demonstrates strategies for handling race conditions when multiple consumers
process the same topic:
- Simulated database transactions
- Lock-based coordination
- Compare-and-swap pattern
- Optimistic locking

Run: python examples/race_condition_handling.py
"""

import time
import threading
from confluent_kafka import Consumer, KafkaError, Producer
from models.order import Order
from typing import Dict, Optional


# Simulated database (in production: use real database)
simulated_db = {}
db_lock = threading.Lock()


def example_race_condition_problem():
    """
    Example 1: Demonstrating the Race Condition Problem
    
    Shows what happens when multiple consumers process the same message
    without proper synchronization.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Race Condition Problem (No Protection)")
    print("=" * 70)
    
    # Clear database
    simulated_db.clear()
    
    print("\n⚠️  Simulating race condition with 2 concurrent consumers")
    print("📊 Both try to increment the same counter\n")
    
    # Shared counter
    counter = {"value": 0}
    
    def unsafe_increment(consumer_id: int, iterations: int):
        """Unsafe increment - race condition!"""
        for i in range(iterations):
            # Read current value
            current = counter["value"]
            print(f"Consumer {consumer_id}: Read value = {current}")
            
            # Simulate processing delay
            time.sleep(0.001)
            
            # Write new value (RACE CONDITION HERE!)
            counter["value"] = current + 1
            print(f"Consumer {consumer_id}: Wrote value = {counter['value']}")
    
    # Run two consumers concurrently
    thread1 = threading.Thread(target=unsafe_increment, args=(1, 3))
    thread2 = threading.Thread(target=unsafe_increment, args=(2, 3))
    
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    print(f"\n❌ RACE CONDITION RESULT:")
    print(f"   Expected: 6 (3 + 3)")
    print(f"   Actual: {counter['value']}")
    print(f"   Lost updates: {6 - counter['value']}")


def example_lock_based_solution():
    """
    Example 2: Lock-Based Solution
    
    Uses a lock to prevent race conditions by serializing access.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Lock-Based Solution (Protected)")
    print("=" * 70)
    
    counter = {"value": 0}
    lock = threading.Lock()
    
    print("\n✅ Using lock to prevent race conditions\n")
    
    def safe_increment(consumer_id: int, iterations: int):
        """Safe increment with lock."""
        for i in range(iterations):
            with lock:  # Acquire lock
                current = counter["value"]
                print(f"Consumer {consumer_id}: Read value = {current} (locked)")
                
                time.sleep(0.001)
                
                counter["value"] = current + 1
                print(f"Consumer {consumer_id}: Wrote value = {counter['value']} (locked)")
            # Lock released here
    
    thread1 = threading.Thread(target=safe_increment, args=(1, 3))
    thread2 = threading.Thread(target=safe_increment, args=(2, 3))
    
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    print(f"\n✅ LOCK-BASED RESULT:")
    print(f"   Expected: 6")
    print(f"   Actual: {counter['value']}")
    print(f"   Lost updates: 0")


def example_database_transaction_pattern():
    """
    Example 3: Database Transaction Pattern
    
    Simulates using database transactions with proper isolation level.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Database Transaction Pattern")
    print("=" * 70)
    
    # Simulate inventory database
    inventory = {"product_123": {"quantity": 10, "version": 0}}
    inventory_lock = threading.Lock()
    
    print("\n📦 Initial inventory: 10 units")
    print("🛒 Two customers try to buy 6 units each")
    print("✅ Only one should succeed (insufficient stock for both)\n")
    
    def reserve_inventory(customer_id: int, product_id: str, quantity: int):
        """Reserve inventory with transaction protection."""
        with inventory_lock:  # Simulates database transaction
            print(f"Customer {customer_id}: Starting transaction...")
            
            # Read current stock
            if product_id not in inventory:
                print(f"Customer {customer_id}: ❌ Product not found")
                return False
            
            current_quantity = inventory[product_id]["quantity"]
            print(f"Customer {customer_id}: Current stock = {current_quantity}")
            
            # Check availability
            if current_quantity < quantity:
                print(f"Customer {customer_id}: ❌ Insufficient stock")
                return False
            
            # Simulate processing delay
            time.sleep(0.01)
            
            # Update stock
            inventory[product_id]["quantity"] = current_quantity - quantity
            inventory[product_id]["version"] += 1
            
            print(f"Customer {customer_id}: ✅ Reserved {quantity} units")
            print(f"Customer {customer_id}: New stock = {inventory[product_id]['quantity']}")
            return True
    
    # Two customers compete
    def customer_purchase(customer_id: int):
        success = reserve_inventory(customer_id, "product_123", 6)
        if success:
            print(f"Customer {customer_id}: 🎉 Purchase successful\n")
        else:
            print(f"Customer {customer_id}: 😞 Purchase failed\n")
    
    thread1 = threading.Thread(target=customer_purchase, args=(1,))
    thread2 = threading.Thread(target=customer_purchase, args=(2,))
    
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    print(f"📊 Final inventory: {inventory['product_123']['quantity']} units")
    print(f"✅ Race condition prevented!")


def example_optimistic_locking():
    """
    Example 4: Optimistic Locking (Compare-and-Swap)
    
    Uses version numbers to detect concurrent modifications.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Optimistic Locking (Version-Based)")
    print("=" * 70)
    
    # Database with version field
    orders_db = {}
    db_lock = threading.Lock()
    
    print("\n🔄 Using version numbers to detect conflicts")
    print("📝 Multiple updates to the same order\n")
    
    class OptimisticLockError(Exception):
        """Raised when version conflict detected."""
        pass
    
    def update_order_status(order_id: str, new_status: str, expected_version: int) -> bool:
        """Update order with optimistic locking."""
        with db_lock:
            # Read current state
            if order_id not in orders_db:
                orders_db[order_id] = {"status": "pending", "version": 0}
            
            current = orders_db[order_id]
            
            print(f"   Order {order_id}:")
            print(f"      Current: status={current['status']}, version={current['version']}")
            print(f"      Expected version: {expected_version}")
            
            # Check version
            if current["version"] != expected_version:
                print(f"      ❌ Version mismatch! Conflict detected")
                raise OptimisticLockError(
                    f"Version conflict: expected {expected_version}, "
                    f"got {current['version']}"
                )
            
            # Update with new version
            orders_db[order_id]["status"] = new_status
            orders_db[order_id]["version"] += 1
            
            print(f"      ✅ Updated: status={new_status}, version={orders_db[order_id]['version']}")
            return True
    
    def worker_update(worker_id: int, order_id: str):
        """Worker tries to update order."""
        try:
            # Read current version
            with db_lock:
                version = orders_db.get(order_id, {"version": 0})["version"]
            
            print(f"\nWorker {worker_id}: Reading order (version {version})")
            
            # Simulate processing delay
            time.sleep(0.02)
            
            # Try to update
            print(f"Worker {worker_id}: Attempting update...")
            update_order_status(order_id, f"processed_by_{worker_id}", version)
            print(f"Worker {worker_id}: ✅ Update successful")
            
        except OptimisticLockError as e:
            print(f"Worker {worker_id}: ❌ Update failed - {e}")
            print(f"Worker {worker_id}: 🔄 Should retry with new version")
    
    # Initialize order
    orders_db["order_1"] = {"status": "pending", "version": 0}
    
    # Two workers try to update
    thread1 = threading.Thread(target=worker_update, args=(1, "order_1"))
    thread2 = threading.Thread(target=worker_update, args=(2, "order_1"))
    
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    print(f"\n📊 Final state: {orders_db['order_1']}")
    print(f"✅ Optimistic locking detected conflict!")


def example_kafka_multiple_consumers():
    """
    Example 5: Multiple Consumers with Coordination
    
    Shows how multiple consumers can safely process messages with coordination.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Multiple Consumers with Coordination")
    print("=" * 70)
    
    # Shared state
    processed_orders = set()
    processing_lock = threading.Lock()
    
    print("\n👥 Simulating 2 consumers processing the same topic")
    print("🔐 Using lock to prevent duplicate processing\n")
    
    def consumer_worker(consumer_id: int, order_ids: list):
        """Simulated consumer with coordination."""
        for order_id in order_ids:
            with processing_lock:
                # Check if already processed (idempotent check)
                if order_id in processed_orders:
                    print(f"Consumer {consumer_id}: ⏭️  Order {order_id} already processed")
                    continue
                
                # Mark as processing
                processed_orders.add(order_id)
            
            # Process outside lock (allow concurrent processing of different orders)
            print(f"Consumer {consumer_id}: 🔄 Processing order {order_id}")
            time.sleep(0.01)  # Simulate work
            print(f"Consumer {consumer_id}: ✅ Completed order {order_id}")
    
    # Both consumers get the same orders (simulating rebalance or duplicate)
    orders = ["order_1", "order_2", "order_3", "order_2", "order_1"]  # Note duplicates
    
    thread1 = threading.Thread(target=consumer_worker, args=(1, orders[:3]))
    thread2 = threading.Thread(target=consumer_worker, args=(2, orders[3:]))
    
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    print(f"\n📊 Results:")
    print(f"   Total unique orders processed: {len(processed_orders)}")
    print(f"   Orders: {sorted(processed_orders)}")
    print(f"   ✅ No duplicates processed!")


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 70)
    print("KAFKA RACE CONDITION HANDLING EXAMPLES")
    print("=" * 70)
    
    print("\nAvailable examples:")
    print("  1. Race Condition Problem (demo)")
    print("  2. Lock-Based Solution")
    print("  3. Database Transaction Pattern")
    print("  4. Optimistic Locking (version-based)")
    print("  5. Multiple Consumers with Coordination")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nEnter example number (1-5) or 'all': ")
    
    examples = {
        "1": example_race_condition_problem,
        "2": example_lock_based_solution,
        "3": example_database_transaction_pattern,
        "4": example_optimistic_locking,
        "5": example_kafka_multiple_consumers,
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
    print("\n💡 Key Takeaways:")
    print("   1. Use database transactions for atomicity")
    print("   2. Use locks for simple coordination")
    print("   3. Use optimistic locking for high concurrency")
    print("   4. Always make processing idempotent")
    print("\n📚 For more info, see README.md (Idempotent Processing section)\n")

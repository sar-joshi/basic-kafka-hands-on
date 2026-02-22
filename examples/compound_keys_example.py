"""
Order Producer with Compound Partition Keys

This demonstrates how to use compound keys for better partition distribution.

Why Compound Keys?
- Simple customer_id can create hotspots (some customers are more active)
- Compound keys (customer_id + region/segment) distribute load more evenly
- Prevents partition skew and improves overall throughput
"""

from kafka.producer import KafkaProducer, delivery_report
from models.order import Order
from utils.partitioning import (
    create_region_based_key,
    create_segment_based_key,
    hash_partition_key,
    analyze_distribution,
)


def demo_simple_key_partitioning():
    """
    Demo 1: Simple key partitioning (baseline).
    
    Uses only customer_id as key - can lead to hotspots.
    """
    print("\n" + "=" * 70)
    print("DEMO 1: Simple Key Partitioning (Baseline)")
    print("=" * 70)

    producer = KafkaProducer(bootstrap_servers="localhost:9092")

    # Simulate orders from different customers
    customers = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
    items = ["iPhone", "iPad", "MacBook", "Apple Watch", "AirPods"]

    keys_generated = []

    for i in range(20):
        customer_name = customers[i % len(customers)]
        
        order = Order(
            customer_name=customer_name,
            item=items[i % len(items)],
            quantity=1,
            price=999.99 + i,
        )

        # Simple key: Just use customer_id
        simple_key = order.customer_id.encode("utf-8")
        keys_generated.append(order.customer_id)

        producer.produce(
            topic="orders",
            key=simple_key,
            value=order.model_dump_json().encode("utf-8"),
            callback=delivery_report,
        )

        if (i + 1) % 5 == 0:
            producer.poll(0)

    producer.flush()

    # Analyze distribution
    distribution = analyze_distribution(keys_generated, num_partitions=3)
    print(f"\n📊 Distribution Analysis:")
    print(f"   Partition Counts: {distribution['partition_counts']}")
    print(f"   Imbalance Ratio: {distribution['imbalance_ratio']:.2f}")
    print(f"   Is Balanced: {distribution['is_balanced']}")
    print("\n✅ Simple key demo complete")


def demo_region_based_partitioning():
    """
    Demo 2: Region-based compound key partitioning.
    
    Uses customer_id + region for better geographical distribution.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: Region-Based Compound Key Partitioning")
    print("=" * 70)

    producer = KafkaProducer(bootstrap_servers="localhost:9092")

    regions = ["us-west", "us-east", "eu-central", "ap-southeast", "sa-east"]
    customers = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
    items = ["iPhone", "iPad", "MacBook"]

    keys_generated = []

    for i in range(20):
        customer_name = customers[i % len(customers)]
        region = regions[i % len(regions)]
        
        order = Order(
            customer_name=customer_name,
            item=items[i % len(items)],
            quantity=1,
            price=999.99 + i,
        )

        # Compound key: customer_id + region
        compound_key = create_region_based_key(order.customer_id, region)
        keys_generated.append(compound_key)

        print(f"🔑 Order {i+1}: Key = {compound_key}")

        producer.produce(
            topic="orders",
            key=compound_key.encode("utf-8"),
            value=order.model_dump_json().encode("utf-8"),
            callback=delivery_report,
        )

        if (i + 1) % 5 == 0:
            producer.poll(0)

    producer.flush()

    # Analyze distribution
    distribution = analyze_distribution(keys_generated, num_partitions=3)
    print(f"\n📊 Distribution Analysis:")
    print(f"   Partition Counts: {distribution['partition_counts']}")
    print(f"   Imbalance Ratio: {distribution['imbalance_ratio']:.2f}")
    print(f"   Is Balanced: {distribution['is_balanced']}")
    print("\n✅ Region-based key demo complete")


def demo_segment_based_partitioning():
    """
    Demo 3: Segment-based compound key partitioning.
    
    Uses customer_id + segment (free/premium/enterprise) for even distribution
    when different segments have different activity levels.
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Segment-Based Compound Key Partitioning")
    print("=" * 70)

    producer = KafkaProducer(bootstrap_servers="localhost:9092")

    segments = ["free", "premium", "enterprise"]
    customers = ["Alice", "Bob", "Charlie", "Diana", "Eve"]

    keys_generated = []

    # Simulate: 60% free, 30% premium, 10% enterprise
    for i in range(30):
        customer_name = customers[i % len(customers)]
        
        if i < 18:  # 60%
            segment = "free"
        elif i < 27:  # 30%
            segment = "premium"
        else:  # 10%
            segment = "enterprise"

        order = Order(
            customer_name=customer_name,
            item="Subscription",
            quantity=1,
            price=9.99 if segment == "free" else (99.99 if segment == "premium" else 999.99),
        )

        # Compound key: customer_id + segment
        compound_key = create_segment_based_key(order.customer_id, segment)
        keys_generated.append(compound_key)

        print(f"🔑 Order {i+1}: Segment={segment:10s} Key={compound_key}")

        producer.produce(
            topic="orders",
            key=compound_key.encode("utf-8"),
            value=order.model_dump_json().encode("utf-8"),
            callback=delivery_report,
        )

        if (i + 1) % 10 == 0:
            producer.poll(0)

    producer.flush()

    # Analyze distribution
    distribution = analyze_distribution(keys_generated, num_partitions=3)
    print(f"\n📊 Distribution Analysis:")
    print(f"   Partition Counts: {distribution['partition_counts']}")
    print(f"   Imbalance Ratio: {distribution['imbalance_ratio']:.2f}")
    print(f"   Is Balanced: {distribution['is_balanced']}")
    print("\n✅ Segment-based key demo complete")


def demo_hash_based_partitioning():
    """
    Demo 4: Hash-based compound key partitioning.
    
    Uses hash of multiple attributes for compact, evenly-distributed keys.
    """
    print("\n" + "=" * 70)
    print("DEMO 4: Hash-Based Compound Key Partitioning")
    print("=" * 70)

    producer = KafkaProducer(bootstrap_servers="localhost:9092")

    regions = ["us-west", "us-east", "eu-central"]
    segments = ["free", "premium", "enterprise"]
    customers = ["Alice", "Bob", "Charlie", "Diana", "Eve"]

    keys_generated = []

    for i in range(20):
        customer_name = customers[i % len(customers)]
        region = regions[i % len(regions)]
        segment = segments[i % len(segments)]
        
        order = Order(
            customer_name=customer_name,
            item="Product",
            quantity=1,
            price=99.99,
        )

        # Hash-based key: hash(customer_id + region + segment)
        hash_key = hash_partition_key(order.customer_id, region, segment, hash_size=12)
        keys_generated.append(hash_key)

        print(f"🔑 Order {i+1}: Customer={customer_name:7s} Region={region:12s} "
              f"Segment={segment:10s} Hash={hash_key}")

        producer.produce(
            topic="orders",
            key=hash_key.encode("utf-8"),
            value=order.model_dump_json().encode("utf-8"),
            callback=delivery_report,
        )

        if (i + 1) % 5 == 0:
            producer.poll(0)

    producer.flush()

    # Analyze distribution
    distribution = analyze_distribution(keys_generated, num_partitions=3)
    print(f"\n📊 Distribution Analysis:")
    print(f"   Partition Counts: {distribution['partition_counts']}")
    print(f"   Imbalance Ratio: {distribution['imbalance_ratio']:.2f}")
    print(f"   Is Balanced: {distribution['is_balanced']}")
    print("\n✅ Hash-based key demo complete")


def compare_strategies():
    """
    Compare all partitioning strategies side by side.
    """
    print("\n" + "=" * 70)
    print("COMPARISON: All Partitioning Strategies")
    print("=" * 70)

    # Generate same set of customers with different key strategies
    customers = [f"customer-{i}" for i in range(100)]
    regions = ["us-west", "us-east", "eu-central", "ap-southeast"]
    segments = ["free", "premium", "enterprise"]

    # Strategy 1: Simple keys
    simple_keys = customers

    # Strategy 2: Region-based keys
    region_keys = [
        create_region_based_key(customers[i], regions[i % len(regions)])
        for i in range(100)
    ]

    # Strategy 3: Segment-based keys
    segment_keys = [
        create_segment_based_key(customers[i], segments[i % len(segments)])
        for i in range(100)
    ]

    # Strategy 4: Hash-based keys
    hash_keys = [
        hash_partition_key(customers[i], regions[i % len(regions)], segments[i % len(segments)])
        for i in range(100)
    ]

    # Analyze all strategies
    strategies = {
        "Simple": simple_keys,
        "Region-Based": region_keys,
        "Segment-Based": segment_keys,
        "Hash-Based": hash_keys,
    }

    print("\n📊 Distribution Comparison (100 keys, 3 partitions):\n")
    print(f"{'Strategy':<20} {'P0':>6} {'P1':>6} {'P2':>6} {'Imbalance':>12} {'Balanced':>10}")
    print("-" * 70)

    for strategy_name, keys in strategies.items():
        dist = analyze_distribution(keys, num_partitions=3)
        counts = dist['partition_counts']
        print(f"{strategy_name:<20} {counts[0]:>6} {counts[1]:>6} {counts[2]:>6} "
              f"{dist['imbalance_ratio']:>11.2f}  {str(dist['is_balanced']):>10}")

    print("\n💡 Key Insights:")
    print("   - All strategies provide reasonable distribution")
    print("   - Region/Segment keys help when activity varies by region/segment")
    print("   - Hash keys provide compact representation with good distribution")
    print("   - Choose based on your specific use case and access patterns")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("KAFKA COMPOUND PARTITION KEYS DEMONSTRATION")
    print("=" * 70)

    # Run all demos
    demo_simple_key_partitioning()
    demo_region_based_partitioning()
    demo_segment_based_partitioning()
    demo_hash_based_partitioning()
    compare_strategies()

    print("\n" + "=" * 70)
    print("ALL DEMOS COMPLETE!")
    print("=" * 70)
    print("\n📚 Next Steps:")
    print("   1. Check partition distribution: docker exec -it kafka kafka-topics --describe --topic orders --bootstrap-server localhost:9092")
    print("   2. Monitor consumer lag by partition")
    print("   3. Adjust strategy based on your traffic patterns\n")


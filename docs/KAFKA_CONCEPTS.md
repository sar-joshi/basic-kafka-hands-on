# Kafka Core Concepts

This guide covers the fundamental concepts you need to understand to work with Apache Kafka effectively.

## Table of Contents

1. [Topic Partitioning](#topic-partitioning)
2. [Message Ordering](#message-ordering)
3. [Partition Key Strategies](#partition-key-strategies)
4. [Best Practices](#best-practices)

## Topic Partitioning

### What is Topic Partitioning?

A Kafka **topic** is divided into multiple **partitions**. Think of partitions as separate "lanes" within a topic that allow parallel processing.

**Visual Structure:**
```
Topic: "orders"
┌─────────────────────────────────────────────────┐
│                                                 │
│  Partition 0: [msg1] [msg2] [msg3] [msg4] ...  │
│                                                 │
│  Partition 1: [msg5] [msg6] [msg7] [msg8] ...  │
│                                                 │
│  Partition 2: [msg9] [msg10] [msg11] ...       │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Why Use Partitions?

#### 1. Parallelism and Scalability
```
Producer 1 ──┐
             ├──→ Partition 0 ──→ Consumer A
Producer 2 ──┤
             ├──→ Partition 1 ──→ Consumer B
Producer 3 ──┤
             └──→ Partition 2 ──→ Consumer C
```
- Multiple consumers can read from different partitions simultaneously
- Increases throughput (more messages processed per second)
- Horizontal scaling by adding more partitions and consumers

#### 2. Load Distribution
- Messages are distributed across partitions
- Prevents any single partition from becoming a bottleneck
- Better resource utilization across the cluster

#### 3. Fault Tolerance
- Each partition can have replicas on different brokers
- If one broker fails, data remains available from replicas
- Ensures high availability and durability

### How Messages are Assigned to Partitions

Kafka uses three strategies to determine which partition a message goes to:

#### Strategy 1: Round-Robin (No Key)
```python
# Messages distributed evenly across partitions
producer.produce(topic="orders", value=message)
# Distribution: P0 → P1 → P2 → P0 → P1 → P2...
```
- **Use case:** When order doesn't matter
- **Advantage:** Even distribution across partitions

#### Strategy 2: Key-Based Partitioning (Recommended)
```python
# All messages with the same key go to the same partition
producer.produce(
    topic="orders",
    key="customer-123",  # Same key = Same partition
    value=message
)
```
- **Use case:** When you need ordering for related messages
- **Advantage:** Guarantees all messages with the same key are processed in order

#### Strategy 3: Explicit Partition Assignment
```python
# Directly specify which partition to use
producer.produce(topic="orders", partition=1, value=message)
```
- **Use case:** Custom partitioning logic
- **Advantage:** Full control over message placement

## Message Ordering

### Critical Rule

**Kafka guarantees message order within a partition, but NOT across partitions.**

#### Within a Single Partition ✅
```
Partition 0: [Order A: created] → [Order A: paid] → [Order A: shipped]
             ↑ Messages are always read in the order they were written
```

#### Across Multiple Partitions ❌
```
Partition 0: [Order A: created] [Order A: paid]
Partition 1: [Order B: created] [Order B: paid]
Partition 2: [Order C: created] [Order C: paid]

Consumer might read in any order across partitions:
[Order B: created] [Order A: created] [Order C: paid] [Order A: paid] ...
```

### Real-World Example: Order Processing

#### ❌ Problem: Without Keys (No Ordering)

```python
# Producer sends order status updates
order1 = Order(customer_id="Alice", item="iPhone", status="created")
order2 = Order(customer_id="Alice", item="iPhone", status="paid")
order3 = Order(customer_id="Alice", item="iPhone", status="shipped")

# Without keys - goes to random partitions
producer.produce(topic="orders", value=order1.model_dump_json().encode())
producer.produce(topic="orders", value=order2.model_dump_json().encode())
producer.produce(topic="orders", value=order3.model_dump_json().encode())
```

**Result:**
```
Partition 0: [Alice: shipped]    ← Wrong! Shipped before payment!
Partition 1: [Alice: created]
Partition 2: [Alice: paid]
```

#### ✅ Solution: With Keys (Ordering Guaranteed)

```python
# Use customer_id as key - ensures all of Alice's orders go to same partition
producer.produce(
    topic="orders",
    key=order.customer_id.encode("utf-8"),  # Key ensures ordering
    value=order1.model_dump_json().encode()
)
producer.produce(
    topic="orders",
    key=order.customer_id.encode("utf-8"),
    value=order2.model_dump_json().encode()
)
producer.produce(
    topic="orders",
    key=order.customer_id.encode("utf-8"),
    value=order3.model_dump_json().encode()
)
```

**Result:**
```
Partition 1: [Alice: created] → [Alice: paid] → [Alice: shipped] ✅
             ↑ Correct order maintained!
```

## Partition Key Strategies

### Implementing Key-Based Partitioning

Update your producer to support message keys:

**1. Update the producer wrapper:**
```python
# kafka/producer.py
def produce(self, topic: str, key: bytes = None, value: bytes = None, callback=None):
    """
    Produce a message to a Kafka topic.
    
    Args:
        topic: The Kafka topic to send the message to.
        key: Optional message key for partitioning.
        value: The message value as bytes.
        callback: Optional callback function for delivery reports.
    """
    self.producer.produce(topic=topic, key=key, value=value, callback=callback)
```

**2. Use keys in your application:**
```python
# order_producer.py
order = Order(
    customer_name="John Doe",
    item="MacBook Pro",
    quantity=1,
    price=100,
)

producer.produce(
    topic="orders",
    key=order.customer_id.encode("utf-8"),  # Ensures ordering per customer
    value=order.model_dump_json().encode("utf-8"),
    callback=delivery_report,
)
```

### Best Practices

| Scenario | Recommended Approach | Reason |
|----------|---------------------|---------|
| Order status updates | Use customer_id as key | Maintains order lifecycle sequence |
| User activity logs | Use user_id as key | Keeps user actions in order |
| IoT sensor data | Use device_id as key | Preserves time-series data order |
| General events (no ordering needed) | No key (round-robin) | Best load distribution |
| High-cardinality keys | Ensure even distribution | Prevents partition hotspots |

### Partitioning Quick Reference

```
┌─────────────────────────────────────────────────────────┐
│  Key Concept: Same Key → Same Partition → Ordered      │
└─────────────────────────────────────────────────────────┘

Producer sends messages with keys:
┌──────────────┐
│ Customer A:  │  Key: "A"  ──┐
│  - Order 1   │              │
│  - Order 2   │              ├──→ Partition 2: [A1][A2][A3] ✅
│  - Order 3   │              │    (All A's orders in order)
└──────────────┘              │
                              │
┌──────────────┐              │
│ Customer B:  │  Key: "B"  ──┼──→ Partition 0: [B1][B2] ✅
│  - Order 1   │              │    (All B's orders in order)
│  - Order 2   │              │
└──────────────┘              │
                              │
┌──────────────┐              │
│ Customer C:  │  Key: "C"  ──┘
│  - Order 1   │         └──────→ Partition 1: [C1] ✅
└──────────────┘                  (C's orders in order)

Consumer Group reads:
  Consumer 1 ← Partition 0 (B's orders)
  Consumer 2 ← Partition 1 (C's orders)
  Consumer 3 ← Partition 2 (A's orders)

Result: Each customer's orders processed in correct order! 🎯
```

## Monitoring Partition Distribution

Check how messages are distributed across partitions:

```bash
# Describe topic to see partition details
docker exec -it kafka kafka-topics --describe --topic orders --bootstrap-server localhost:9092

# Check consumer lag per partition
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group order-consumer
```

**Example Output:**
```
TOPIC    PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
orders   0          150             150             0
orders   1          148             148             0
orders   2          152             152             0
```
This shows relatively even distribution across partitions.

## Advanced Topics

For advanced partitioning strategies including compound keys, hash-based partitioning, and load distribution analysis, see:

- **[Compound Partition Keys Guide](PARTITIONING.md)** - Advanced strategies for better load distribution
- **[Compound Keys Examples](../examples/compound_keys_example.py)** - Interactive examples with 5 different strategies

## Key Takeaways

1. **Partitions enable scalability** - Multiple consumers process in parallel
2. **Use keys for ordering** - Same key → same partition → ordered messages
3. **No global ordering** - Only within a partition
4. **Choose wisely** - Simple keys vs compound keys based on your workload
5. **Monitor distribution** - Check for partition skew and hotspots

## Related Resources

- **[Understanding Offsets](OFFSETS.md)** - How Kafka tracks message consumption
- **[Back Pressure Guide](BACKPRESSURE.md)** - Managing high-volume production
- **[Examples](../examples/)** - Interactive demonstrations

---

**For hands-on practice, run:**
```bash
python order_producer.py  # Basic producer
python examples/compound_keys_example.py  # Advanced partitioning
```

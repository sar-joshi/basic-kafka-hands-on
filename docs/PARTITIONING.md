# Custom Partition Keys for Better Load Distribution

## Overview

This guide explains how to use compound partition keys to achieve better load distribution across Kafka partitions, preventing hotspots and improving overall throughput.

## The Problem: Simple Keys Can Create Hotspots

### Scenario: E-commerce Platform

Imagine you have an e-commerce platform with 1 million customers, but:
- 1000 "power users" generate 80% of all orders
- These users are concentrated in specific regions (e.g., US-West)
- Simple `customer_id` partitioning leads to uneven load

```python
# ❌ Simple partitioning - can create hotspots
producer.produce(
    topic="orders",
    key=customer_id.encode(),  # Power users overload specific partitions
    value=order.model_dump_json().encode(),
)
```

**Result:**
```
Partition 0: ▓▓▓▓▓▓▓▓▓▓ (90% load) ← Power users here!
Partition 1: ▓░░░░░░░░░ (10% load)
Partition 2: ▓░░░░░░░░░ ( 5% load)
```

## The Solution: Compound Keys

Use **multiple attributes** to create compound keys that distribute load more evenly:

```python
# ✅ Compound partitioning - better distribution
compound_key = create_region_based_key(customer_id, region)
producer.produce(
    topic="orders",
    key=compound_key.encode(),  # customer_id|region
    value=order.model_dump_json().encode(),
)
```

**Result:**
```
Partition 0: ▓▓▓▓▓▓░░░░ (35% load) ← More balanced!
Partition 1: ▓▓▓▓▓░░░░░ (30% load)
Partition 2: ▓▓▓▓▓░░░░░ (35% load)
```

## Partitioning Strategies

### 1. Region-Based Partitioning

**When to use:** Geographical distribution, multi-region deployments

```python
from utils.partitioning import create_region_based_key

# Combine customer_id + region
key = create_region_based_key("customer-123", "us-west")
# Result: "customer-123|us-west"
```

**Benefits:**
- Prevents regional hotspots
- Better distribution when some regions are more active
- Maintains order per customer within a region

**Example:**
```python
regions = ["us-west", "us-east", "eu-central", "ap-southeast"]

for order in orders:
    customer_region = get_customer_region(order.customer_id)
    key = create_region_based_key(order.customer_id, customer_region)
    
    producer.produce(
        topic="orders",
        key=key.encode("utf-8"),
        value=order.model_dump_json().encode("utf-8"),
    )
```

### 2. Segment-Based Partitioning

**When to use:** Different user tiers with varying activity levels

```python
from utils.partitioning import create_segment_based_key

# Combine customer_id + segment
key = create_segment_based_key("customer-123", "premium")
# Result: "customer-123|premium"
```

**Benefits:**
- Prevents premium users from overwhelming specific partitions
- Better distribution across user segments
- Useful for tiered services (free/premium/enterprise)

**Example:**
```python
for order in orders:
    customer_segment = get_customer_segment(order.customer_id)
    key = create_segment_based_key(order.customer_id, customer_segment)
    
    producer.produce(
        topic="orders",
        key=key.encode("utf-8"),
        value=order.model_dump_json().encode("utf-8"),
    )
```

### 3. Hash-Based Partitioning

**When to use:** Multiple attributes, need compact keys

```python
from utils.partitioning import hash_partition_key

# Hash multiple attributes
key = hash_partition_key("customer-123", "us-west", "premium", hash_size=8)
# Result: "a7f2c3d1" (8-character hash)
```

**Benefits:**
- Compact key representation
- Deterministic (same inputs = same hash)
- Even distribution with multiple attributes
- Prevents key size explosion

**Example:**
```python
for order in orders:
    region = get_customer_region(order.customer_id)
    segment = get_customer_segment(order.customer_id)
    
    # Hash combines all attributes
    key = hash_partition_key(
        order.customer_id,
        region,
        segment,
        hash_size=12
    )
    
    producer.produce(
        topic="orders",
        key=key.encode("utf-8"),
        value=order.model_dump_json().encode("utf-8"),
    )
```

### 4. Time-Bucketed Partitioning

**When to use:** Time-series data, analytics workloads

```python
from utils.partitioning import create_time_bucketed_key
from datetime import datetime

# Combine customer_id + time bucket
hour_bucket = datetime.now().strftime("%Y-%m-%d-%H")
key = create_time_bucketed_key("customer-123", hour_bucket)
# Result: "customer-123|2024-12-26-10"
```

**Benefits:**
- Parallel processing of different time periods
- Maintains order within time buckets
- Good for analytics and time-series data

### 5. Multi-Tenant Partitioning

**When to use:** SaaS applications with multiple tenants/organizations

```python
from utils.partitioning import create_multi_tenant_key

# Combine tenant_id + customer_id
key = create_multi_tenant_key("acme-corp", "customer-123")
# Result: "acme-corp|customer-123"
```

**Benefits:**
- Prevents one large tenant from dominating partitions
- Fair resource allocation across tenants
- Maintains order per customer within a tenant

## Analyzing Distribution

Use the built-in analysis tool to verify your partitioning strategy:

```python
from utils.partitioning import analyze_distribution, create_region_based_key

# Generate keys
keys = [
    create_region_based_key(f"customer-{i}", regions[i % len(regions)])
    for i in range(1000)
]

# Analyze distribution
result = analyze_distribution(keys, num_partitions=3)

print(f"Partition Counts: {result['partition_counts']}")
# Output: {0: 334, 1: 333, 2: 333}

print(f"Imbalance Ratio: {result['imbalance_ratio']:.2f}")
# Output: 1.00 (perfectly balanced)

print(f"Is Balanced: {result['is_balanced']}")
# Output: True (within 20% tolerance)
```

## Decision Guide

| Scenario | Recommended Strategy | Example |
|----------|---------------------|---------|
| **Geographic diversity** | Region-based | `customer\|us-west` |
| **Tiered users** | Segment-based | `customer\|premium` |
| **Multiple attributes** | Hash-based | `a7f2c3d1` |
| **Time-series data** | Time-bucketed | `customer\|2024-12-26-10` |
| **SaaS multi-tenant** | Multi-tenant | `tenant\|customer` |
| **Simple workload** | Simple ID | `customer-123` |

## Implementation Example

### Step 1: Choose Strategy

```python
from utils.partitioning import create_region_based_key
from kafka.producer import KafkaProducer
from models.order import Order

producer = KafkaProducer(bootstrap_servers="localhost:9092")
```

### Step 2: Apply to Producer

```python
def produce_order_with_partitioning(order: Order, region: str):
    """Produce an order with region-based partitioning."""
    
    # Create compound key
    partition_key = create_region_based_key(order.customer_id, region)
    
    # Produce with compound key
    producer.produce(
        topic="orders",
        key=partition_key.encode("utf-8"),
        value=order.model_dump_json().encode("utf-8"),
    )
    
    producer.poll(0)  # Back pressure handling
```

### Step 3: Verify Distribution

```bash
# Check partition distribution
docker exec -it kafka kafka-topics --describe \
  --topic orders \
  --bootstrap-server localhost:9092

# Monitor consumer lag by partition
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group order-consumer
```

## Testing Your Strategy

Run the comprehensive demo:

```bash
python order_producer_with_compound_keys.py
```

**Output:**
```
====================================================================
DEMO 1: Simple Key Partitioning (Baseline)
====================================================================
...
📊 Distribution Analysis:
   Partition Counts: {0: 8, 1: 7, 2: 5}
   Imbalance Ratio: 1.60
   Is Balanced: False

====================================================================
DEMO 2: Region-Based Compound Key Partitioning
====================================================================
...
📊 Distribution Analysis:
   Partition Counts: {0: 7, 1: 7, 2: 6}
   Imbalance Ratio: 1.17
   Is Balanced: True

====================================================================
COMPARISON: All Partitioning Strategies
====================================================================

Strategy              P0     P1     P2   Imbalance   Balanced
----------------------------------------------------------------------
Simple                  35     33     32        1.09       True
Region-Based            34     33     33        1.03       True
Segment-Based           35     32     33        1.09       True
Hash-Based              33     34     33        1.03       True
```

## Best Practices

### ✅ DO

1. **Analyze your traffic patterns**
   ```python
   # Profile your data before choosing a strategy
   customer_orders = count_orders_per_customer()
   regional_distribution = count_orders_per_region()
   ```

2. **Test distribution before production**
   ```python
   keys = generate_keys_from_production_sample()
   result = analyze_distribution(keys, num_partitions=N)
   assert result["is_balanced"], "Distribution not balanced!"
   ```

3. **Monitor partition skew in production**
   ```bash
   # Watch consumer lag per partition
   watch -n 5 'docker exec kafka kafka-consumer-groups ...'
   ```

4. **Use consistent key format**
   ```python
   # Always use the same separator and order
   key = create_compound_key(customer_id, region)  # ✅
   # NOT: create_compound_key(region, customer_id)  # ❌
   ```

### ❌ DON'T

1. **Don't mix partition strategies**
   ```python
   # Bad - inconsistent partitioning
   if condition:
       key = customer_id
   else:
       key = create_region_based_key(customer_id, region)
   ```

2. **Don't use too many attributes**
   ```python
   # Bad - unnecessarily complex
   key = f"{customer_id}|{region}|{segment}|{device}|{os}|{browser}"
   ```

3. **Don't forget to encode keys**
   ```python
   # Bad - will fail
   producer.produce(topic="orders", key=key)
   
   # Good
   producer.produce(topic="orders", key=key.encode("utf-8"))
   ```

4. **Don't change partitioning strategy mid-flight**
   - Causes message ordering issues
   - Deploy strategy changes carefully

## Performance Considerations

### Key Size Impact

| Strategy | Key Size | Network Overhead | Recommendation |
|----------|----------|------------------|----------------|
| Simple | 10-20 bytes | Low | Good for simple workloads |
| Region-based | 30-50 bytes | Medium | Good balance |
| Hash-based | 8-16 bytes | Low | Best for large scale |

### Partition Count Guidelines

```
Partitions = max(
    target_throughput_MB/s / broker_throughput_MB/s,
    num_consumers_in_largest_group
)

Example:
- Target: 100 MB/s
- Broker: 10 MB/s
- Max consumers: 20
- Partitions: max(100/10, 20) = 20 partitions
```

## Troubleshooting

### Problem: Partition Skew

**Symptoms:**
- Some partitions have much more data than others
- Consumer lag on specific partitions
- Uneven CPU usage across brokers

**Solutions:**
1. Analyze current distribution:
   ```python
   result = analyze_distribution(production_keys, num_partitions=N)
   print(f"Imbalance ratio: {result['imbalance_ratio']}")
   ```

2. Switch to compound keys with more attributes
3. Consider repartitioning (requires new topic)

### Problem: Too Many Small Partitions

**Symptoms:**
- High metadata overhead
- Slow rebalancing
- Wasted resources

**Solutions:**
1. Reduce partition count
2. Use hash-based keys for compact representation
3. Consolidate low-traffic topics

## Summary

**Key Takeaways:**

1. 🎯 **Choose strategy based on workload**
   - Geographic? → Region-based
   - Tiered users? → Segment-based
   - Multiple factors? → Hash-based

2. 📊 **Test before deploying**
   - Use `analyze_distribution()` to verify
   - Run load tests with production-like data

3. 🔍 **Monitor in production**
   - Watch for partition skew
   - Track consumer lag per partition
   - Adjust strategy if needed

4. ⚖️ **Balance complexity vs benefit**
   - Start simple, add complexity if needed
   - Don't over-engineer for small workloads

---

**Related Files:**
- `utils/partitioning.py` - Partitioning utilities
- `tests/test_partitioning.py` - Comprehensive tests
- `order_producer_with_compound_keys.py` - Demo and examples


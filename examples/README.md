# Kafka Examples

This directory contains comprehensive, production-ready examples demonstrating various Kafka concepts and patterns.

## 📁 Directory Structure

```
examples/
├── README.md                          # This file
├── offset_management.py               # Offset handling patterns
├── idempotent_processing.py          # Duplicate message handling
├── race_condition_handling.py        # Concurrent processing safety
├── backpressure_example.py           # Flow control strategies
└── compound_keys_example.py          # Partition key strategies
```

## 🚀 Quick Start

### Prerequisites

```bash
# 1. Start Kafka
docker compose up -d

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run producer to generate test data
python order_producer.py
```

### Running Examples

Each example is self-contained and interactive:

```bash
# List available examples in each file
python examples/offset_management.py

# Run specific example
python examples/offset_management.py 1

# Run all examples in a file
python examples/offset_management.py all
```

## 📚 Examples Overview

### 1. Offset Management (`offset_management.py`)

Learn how Kafka tracks message consumption and enables reliable processing.

**Examples:**
- ✅ Manual Commit (at-least-once delivery) - **Recommended for production**
- ✅ Auto-Commit (simple but risky)
- ✅ Batch Commit (performance optimization)
- ✅ Seek to Specific Offset (reprocess messages)
- ✅ Monitor Consumer Lag

**When to use:**
- You need reliable message processing
- Want to control exactly when offsets are committed
- Need to reprocess historical messages
- Monitoring consumer performance

**Run:**
```bash
python examples/offset_management.py 1  # Manual commit example
```

**Key Concepts:**
- Message offset vs Consumer offset
- `auto.offset.reset` configuration
- Commit strategies (manual vs auto)
- At-least-once vs at-most-once delivery

---

### 2. Idempotent Processing (`idempotent_processing.py`)

Handle duplicate messages safely using various deduplication strategies.

**Examples:**
- ✅ Unique Constraint Pattern (database-level) - **Recommended**
- ✅ In-Memory Deduplication (time window)
- ✅ Checksum-Based Deduplication (content hash)
- ✅ State Tracking (multi-step processing)

**When to use:**
- Using at-least-once delivery semantics
- Messages may be redelivered after failures
- Need to prevent duplicate processing
- Building reliable data pipelines

**Run:**
```bash
python examples/idempotent_processing.py 1  # Unique constraint
```

**Key Concepts:**
- Why duplicates happen (at-least-once delivery)
- Database unique constraints
- Time-window deduplication
- Processing state management

---

### 3. Race Condition Handling (`race_condition_handling.py`)

Prevent data corruption when multiple consumers process concurrently.

**Examples:**
- ⚠️  Race Condition Problem (demonstration)
- ✅ Lock-Based Solution
- ✅ Database Transaction Pattern
- ✅ Optimistic Locking (version-based)
- ✅ Multiple Consumers with Coordination

**When to use:**
- Multiple consumers in same consumer group
- Shared state across consumers
- Need to prevent concurrent modifications
- High-concurrency scenarios

**Run:**
```bash
python examples/race_condition_handling.py 1  # See the problem
python examples/race_condition_handling.py 2  # See the solution
```

**Key Concepts:**
- Race conditions in distributed systems
- Locking strategies (pessimistic vs optimistic)
- Database transaction isolation levels
- Compare-and-swap patterns

---

### 4. Back Pressure (`backpressure_example.py`)

Control message flow to prevent overwhelming the system.

**Examples:**
- ✅ Simple Key Partitioning (baseline)
- ✅ High-Volume Production with back pressure
- ✅ Batch Production
- ✅ Buffer monitoring

**When to use:**
- Producing messages faster than Kafka can accept
- Buffer filling up (`BufferError`)
- Need reliable high-throughput production
- System resource constraints

**Run:**
```bash
python examples/backpressure_example.py
```

**Key Concepts:**
- Producer buffer management
- `poll()` for callback triggers
- Exponential backoff on `BufferError`
- Queue length monitoring

**Related Documentation:**
- `docs/BACKPRESSURE.md` - Complete guide

---

### 5. Compound Partition Keys (`compound_keys_example.py`)

Achieve better load distribution across Kafka partitions.

**Examples:**
- ✅ Simple Key Partitioning (baseline)
- ✅ Region-Based Compound Keys
- ✅ Segment-Based Compound Keys
- ✅ Hash-Based Keys
- ✅ Strategy Comparison

**When to use:**
- Partition hotspots (uneven load)
- Geographic distribution matters
- Different user segments with varying activity
- Need to prevent skew

**Run:**
```bash
python examples/compound_keys_example.py
```

**Key Concepts:**
- Partition hotspots problem
- Compound key strategies
- Load distribution analysis
- When to use which strategy

**Related Documentation:**
- `docs/PARTITIONING.md` - Complete guide

## 🎯 Example Selection Guide

### By Use Case

| Use Case | Example | Priority |
|----------|---------|----------|
| **Building production consumer** | `offset_management.py` #1 | ⭐⭐⭐ Must know |
| **Preventing duplicates** | `idempotent_processing.py` #1 | ⭐⭐⭐ Must know |
| **Multiple consumers** | `race_condition_handling.py` #3 | ⭐⭐ Important |
| **High-volume producer** | `backpressure_example.py` | ⭐⭐ Important |
| **Uneven partition load** | `compound_keys_example.py` | ⭐ Good to know |

### By Experience Level

**Beginner** (Start here):
1. `offset_management.py` #1 - Manual commit
2. `idempotent_processing.py` #1 - Unique constraint
3. Basic producer/consumer (in root directory)

**Intermediate** (After basics):
1. `offset_management.py` #3 - Batch commit
2. `idempotent_processing.py` #2 - In-memory dedup
3. `race_condition_handling.py` #2 - Lock-based
4. `backpressure_example.py`

**Advanced** (Complex scenarios):
1. `race_condition_handling.py` #4 - Optimistic locking
2. `idempotent_processing.py` #4 - State tracking
3. `compound_keys_example.py` - All strategies

## 🧪 Testing the Examples

### 1. Generate Test Data

```bash
# Start Kafka
docker compose up -d

# Produce test messages
python order_producer.py

# Verify messages
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning \
  --max-messages 5
```

### 2. Run Examples

```bash
# Offset management
python examples/offset_management.py 1

# Idempotent processing
python examples/idempotent_processing.py 1

# Race conditions
python examples/race_condition_handling.py all
```

### 3. Monitor Results

```bash
# Check consumer groups
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

# Check specific group
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group manual-commit-example
```

## 💡 Best Practices Demonstrated

### ✅ DO (Examples show you how)

1. **Use manual commit** in production (`offset_management.py` #1)
2. **Make processing idempotent** (`idempotent_processing.py` #1)
3. **Handle race conditions** (`race_condition_handling.py` #3)
4. **Apply back pressure** when needed (`backpressure_example.py`)
5. **Use compound keys** to prevent hotspots (`compound_keys_example.py`)

### ❌ DON'T (Examples show why)

1. **Don't use auto-commit** in production (see `offset_management.py` #2)
2. **Don't ignore duplicates** (see `idempotent_processing.py`)
3. **Don't skip race condition handling** (see `race_condition_handling.py` #1)
4. **Don't ignore BufferError** (see `backpressure_example.py`)
5. **Don't use simple keys** with uneven load (see `compound_keys_example.py`)

## 📖 Learning Path

### Path 1: Building a Reliable Consumer (Most Common)

```
1. offset_management.py #1      → Manual commit
2. idempotent_processing.py #1  → Prevent duplicates
3. race_condition_handling.py #3 → Handle concurrency
4. Done! You have a production-ready consumer
```

### Path 2: Building a High-Performance Producer

```
1. backpressure_example.py      → Handle high volume
2. compound_keys_example.py     → Optimize distribution
3. Done! You have an optimized producer
```

### Path 3: Understanding Kafka Internals

```
1. offset_management.py (all)   → Understand offset tracking
2. compound_keys_example.py     → Understand partitioning
3. race_condition_handling.py #1 → Understand concurrency issues
4. Done! You understand how Kafka works internally
```

## 🔧 Common Issues & Solutions

### Issue 1: "No messages received"

**Solution:**
```bash
# Check if topic has messages
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning \
  --max-messages 1

# If empty, produce some messages
python order_producer.py
```

### Issue 2: "Consumer group has no offset"

**Solution:**
- This is normal for new consumer groups
- Set `auto.offset.reset` to `earliest` or `latest`
- See `offset_management.py` for examples

### Issue 3: "Processing duplicates"

**Solution:**
- Use idempotent processing patterns
- See `idempotent_processing.py` #1 for recommended approach

### Issue 4: "BufferError"

**Solution:**
- Apply back pressure strategies
- See `backpressure_example.py` for solutions

## 📚 Related Documentation

- **README.md** - Main project documentation
- **docs/BACKPRESSURE.md** - Back pressure deep dive
- **docs/PARTITIONING.md** - Partitioning strategies guide
- **Apache Kafka Docs** - https://kafka.apache.org/documentation/

## 🎓 Additional Resources

### Kafka Concepts

- [Understanding Kafka Partitioning](../README.md#understanding-kafka-partitioning)
- [Understanding Kafka Offsets](../README.md#understanding-kafka-offsets)
- [Idempotent Processing](../README.md#idempotent-processing)

### Example Code

All examples follow these principles:
- ✅ Production-ready patterns
- ✅ Comprehensive error handling
- ✅ Clear logging and output
- ✅ Interactive and educational
- ✅ Well-documented code

## 🤝 Contributing

To add a new example:

1. Create `examples/your_example.py`
2. Follow the existing structure:
   ```python
   def example_feature_name():
       """Example N: Description"""
       print("\n" + "=" * 70)
       print("EXAMPLE N: Title")
       print("=" * 70)
       # ... implementation
   ```
3. Add to `__main__` menu
4. Document in this README
5. Add tests if applicable

## 📝 License

MIT License - See main README.md

---

**Happy Learning! 🎉**

For questions or issues, please check the main README.md or create an issue on GitHub.

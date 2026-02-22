# Understanding Kafka Offsets

Offsets are fundamental to how Kafka tracks message consumption and enables reliable, scalable message processing. Understanding offsets is crucial for building robust Kafka applications.

## What is an Offset?

An **offset** is a unique sequential ID number assigned to each message within a partition. Think of it as a "bookmark" or "position marker" that identifies a specific message's location.

```
Partition 0 (orders topic):
┌────────────────────────────────────────────────────────┐
│ Offset: 0      1      2      3      4      5      6     │
│ Msg:   [msg1] [msg2] [msg3] [msg4] [msg5] [msg6] [msg7]│
│         ↑                    ↑                     ↑     │
│      oldest              current                newest  │
└────────────────────────────────────────────────────────┘
```

**Key Characteristics:**
- Assigned by Kafka broker when a message is written
- Sequential within a partition (0, 1, 2, 3...)
- Never changes once assigned
- Unique per partition (not globally unique across topic)

## Two Types of Offsets

### 1. Message Offset (Position in Partition)
The immutable position where a message is stored:

```python
# When you produce a message, Kafka assigns it an offset
producer.produce(topic="orders", value=b"order data")
# → Stored at offset 42 in partition 0
```

### 2. Consumer Offset (Last Read Position)
Tracks which messages a consumer group has already processed:

```
Topic: orders (partition 0)
Messages:
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Off:0│ Off:1│ Off:2│ Off:3│ Off:4│ Off:5│ Off:6│
│ "A"  │ "B"  │ "C"  │ "D"  │ "E"  │ "F"  │ "G"  │
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘

Consumer Group "order-processors":
Last committed offset: 3
                       ↓
Messages consumed: 0, 1, 2, 3
Next to consume:   4
```

## Consumer Offset Configuration

### Starting Position: auto.offset.reset

When a consumer starts without a committed offset, `auto.offset.reset` determines where to begin:

```python
consumer_config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "order-consumer",
    "auto.offset.reset": "earliest",  # Important configuration!
}
```

**Configuration Options:**

| Value | Behavior | Use Case |
|-------|----------|----------|
| **`earliest`** | Start from beginning (offset 0) | Reprocess all historical data |
| **`latest`** | Start from end (only new messages) | Ignore history, consume new only |
| **`none`** | Throw error if no offset found | Fail-fast for safety |

**Visual Example:**
```
Existing partition:
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Off:0│ Off:1│ Off:2│ Off:3│ Off:4│ Off:5│ Off:6│
└──────┴──────┴──────┴──────┴──────┴──────┴──────┘
   ↑                                            ↑
   └─ "earliest" starts here                    └─ "latest" starts here
      (reads ALL messages)                         (reads ONLY new messages)
```

## Committing Offsets

**Committing** = Saving your current read position so you can resume later.

### Auto-Commit (Default)

Kafka automatically commits offsets at regular intervals:

```python
consumer_config = {
    "group.id": "order-consumer",
    "enable.auto.commit": True,       # Default
    "auto.commit.interval.ms": 5000,  # Commit every 5 seconds
}
```

**Pros:**
- Simple - no code required
- Works well for most use cases

**Cons:**
- Risk of message loss if consumer crashes before commit
- Risk of duplicate processing after crash

### Manual Commit (Recommended for Production)

You control exactly when offsets are committed:

```python
consumer_config = {
    "group.id": "order-consumer",
    "enable.auto.commit": False,  # Manual control
}

consumer = Consumer(consumer_config)
consumer.subscribe(["orders"])

while True:
    message = consumer.poll(1.0)
    
    if message is None:
        continue
    
    if message.error():
        continue
    
    try:
        # 1. Process the message
        order = Order.model_validate_json(message.value().decode())
        save_to_database(order)
        
        # 2. Commit ONLY after successful processing
        consumer.commit(message=message)
        print(f"✅ Committed offset {message.offset()}")
        
    except Exception as e:
        print(f"❌ Processing failed, will retry: {e}")
        # Don't commit - will reprocess this message
```

## Message Delivery Semantics

How you commit offsets determines your delivery guarantee:

### 1. At-Most-Once (Commit Before Processing) ❌

```python
message = consumer.poll(1.0)
consumer.commit()  # ← Commit FIRST
process(message)   # If this fails, message is LOST!
```

**Result:** Messages may be lost
**Use case:** Logging, metrics (where loss is acceptable)

### 2. At-Least-Once (Commit After Processing) ✅ **Recommended**

```python
message = consumer.poll(1.0)
process(message)       # Process FIRST
consumer.commit()      # ← Commit AFTER success
```

**Result:** Messages may be processed twice if consumer crashes
**Use case:** Most production systems (make processing idempotent)

### 3. Exactly-Once (Transactional)

```python
# Requires Kafka transactions + idempotent processing
# More complex - typically for financial systems
```

**Result:** Each message processed exactly once
**Use case:** Financial transactions, critical operations

## Monitoring Offsets

### Check Consumer Group Status

```bash
# View current offset positions and lag
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group order-consumer
```

**Sample Output:**
```
GROUP           TOPIC    PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
order-consumer  orders   0          150             200             50
order-consumer  orders   1          175             200             25
order-consumer  orders   2          200             200             0
```

**Key Metrics:**
- **CURRENT-OFFSET**: Last committed offset (consumer's position)
- **LOG-END-OFFSET**: Latest message offset (end of partition)
- **LAG**: How far behind consumer is (LOG-END - CURRENT)

⚠️ **High lag** indicates consumer is falling behind!

## Resetting Offsets

Sometimes you need to reprocess messages or skip ahead:

### Reset to Earliest (Reprocess All)
```bash
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group order-consumer \
  --topic orders \
  --reset-offsets \
  --to-earliest \
  --execute
```

### Reset to Specific Offset
```bash
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group order-consumer \
  --topic orders:0 \
  --reset-offsets \
  --to-offset 100 \
  --execute
```

### Reset to Timestamp
```bash
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group order-consumer \
  --topic orders \
  --reset-offsets \
  --to-datetime 2024-12-26T10:00:00.000 \
  --execute
```

⚠️ **Important:** Consumer must be stopped before resetting offsets!

## Idempotent Processing

Since at-least-once delivery may cause duplicates, make your processing idempotent.

**See:** [Idempotent Processing Examples](../examples/idempotent_processing.py) and [README Idempotent Processing Section](../README.md#idempotent-processing)

## Common Offset Pitfalls

### ❌ Pitfall 1: Auto-Commit + Crash = Lost Messages

```python
# BAD: Auto-commit enabled
config = {"enable.auto.commit": True}

message = consumer.poll(1.0)
process(message)  # ← Crash here = message lost (already committed)!
```

**✅ Solution:**
```python
config = {"enable.auto.commit": False}
message = consumer.poll(1.0)
process(message)
consumer.commit()  # Only commit after successful processing
```

### ❌ Pitfall 2: Forgetting to Commit

```python
# BAD: Never committing
config = {"enable.auto.commit": False}

while True:
    message = consumer.poll(1.0)
    process(message)
    # Forgot consumer.commit()!
    # Will reprocess same messages forever!
```

**✅ Solution:**
```python
while True:
    message = consumer.poll(1.0)
    process(message)
    consumer.commit()  # Always commit after processing
```

### ❌ Pitfall 3: Committing Too Frequently

```python
# BAD: Committing every single message
for message in messages:
    process(message)
    consumer.commit()  # Too many commits = performance overhead
```

**✅ Solution:**
```python
# Commit in batches
for i, message in enumerate(messages):
    process(message)
    if i % 100 == 0:  # Commit every 100 messages
        consumer.commit()
```

## Offset Storage

Offsets are stored in a special internal Kafka topic:

```
__consumer_offsets (internal topic)
  ↓
Stores for each consumer group:
  - Topic name
  - Partition number
  - Committed offset
  - Metadata
```

This is why consumer groups can resume from where they left off even after a restart!

## Best Practices

1. ✅ **Use manual commit** in production for reliability
2. ✅ **Commit after processing** (at-least-once semantics)
3. ✅ **Make processing idempotent** to handle duplicates
4. ✅ **Monitor consumer lag** regularly
5. ✅ **Set appropriate `auto.offset.reset`** for your use case
6. ✅ **Handle rebalances gracefully** (commit before rebalance)
7. ✅ **Test offset reset scenarios** before production

## Offset Summary

| Concept | Description | Key Point |
|---------|-------------|-----------|
| **Message Offset** | Position in partition | Immutable, sequential (0, 1, 2...) |
| **Consumer Offset** | Last read position | Tracks progress per consumer group |
| **earliest** | Start from beginning | Reprocess all historical data |
| **latest** | Start from newest | Ignore history |
| **Auto-commit** | Automatic offset commits | Simple but risky |
| **Manual commit** | Explicit offset commits | Safer for production |
| **Lag** | How far behind | LOG-END - CURRENT |
| **At-least-once** | Commit after processing | May have duplicates ✅ |
| **At-most-once** | Commit before processing | May lose messages ❌ |
| **Idempotent** | Safe to process twice | Essential for at-least-once |

## Quick Decision Guide

**Choose auto.offset.reset:**
- `earliest` → Need to process all historical messages
- `latest` → Only care about new messages going forward
- `none` → Want to fail if no offset exists (safety first)

**Choose commit strategy:**
- Manual commit → Production systems (recommended)
- Auto-commit → Simple applications, acceptable message loss

**Choose delivery semantics:**
- At-least-once → Most use cases (with idempotent processing)
- At-most-once → Metrics/logging (loss acceptable)
- Exactly-once → Financial/critical systems only

## Related Resources

- **Examples:** [Offset Management Examples](../examples/offset_management.py) - 5 interactive examples
- **Main Guide:** [README.md](../README.md)
- **Idempotent Processing:** See README and examples for duplicate handling strategies

---

**For hands-on examples, run:**
```bash
python examples/offset_management.py
```

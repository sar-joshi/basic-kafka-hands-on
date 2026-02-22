# Kafka Producer Back Pressure Guide

## What is Back Pressure?

**Back pressure** is a flow control mechanism that prevents a producer from overwhelming the system when messages can't be sent as fast as they're being produced.

### The Problem

```
Producer generating messages:     1000 msg/sec  📤📤📤📤📤
Kafka accepting messages:         100 msg/sec   📥
                                          ↓
Internal buffer fills up  →  BufferError! ❌
```

### The Solution

```
Producer → Check buffer → [FULL?] → Yes → Poll & Wait → Retry
                              ↓
                             No
                              ↓
                         Send message ✅
```

## Why is Back Pressure Important?

### Without Back Pressure ❌
- **Message Loss**: Buffer overflows, messages dropped
- **Crashes**: `BufferError` exceptions crash the application
- **Resource Exhaustion**: Memory issues from unbounded queuing
- **Unpredictable Behavior**: System becomes unstable under load

### With Back Pressure ✅
- **Graceful Degradation**: System slows down instead of crashing
- **No Message Loss**: Messages are queued or retried safely
- **Predictable Behavior**: System handles load spikes gracefully
- **Better Resource Usage**: Controlled memory consumption

## Implementation Strategies

### Strategy 1: Basic Polling (Simple)

Use `poll()` to trigger callbacks and free buffer space:

```python
from kafka.producer import KafkaProducer

producer = KafkaProducer()

# Produce many messages
for i in range(1000):
    producer.produce(
        topic="orders",
        value=f"message-{i}".encode(),
    )
    
    # Poll every 10 messages to prevent buffer buildup
    if i % 10 == 0:
        producer.poll(0)  # Non-blocking call

# Final flush
producer.flush()
```

**Pros:**
- Simple to implement
- Minimal code changes
- Works for moderate load

**Cons:**
- Doesn't handle BufferError
- No retry logic
- May still fail under extreme load

### Strategy 2: Try-Catch with Retry (Recommended)

Handle `BufferError` and retry with backoff:

```python
import time
from kafka.producer_with_backpressure import KafkaProducerWithBackpressure

producer = KafkaProducerWithBackpressure(
    queue_buffering_max_messages=10000,
    linger_ms=10,
)

# This handles BufferError internally
producer.produce_with_backpressure(
    topic="orders",
    key=order.customer_id.encode(),
    value=order.model_dump_json().encode(),
)
```

**Pros:**
- Handles BufferError gracefully
- Exponential backoff prevents hammering
- Suitable for high-load production systems

**Cons:**
- More complex implementation
- Adds latency during back pressure

### Strategy 3: Async with Rate Limiting (Advanced)

Control the message rate proactively:

```python
import asyncio
from asyncio import Semaphore

async def produce_with_rate_limit(producer, messages, rate_limit=100):
    """
    Produce messages with rate limiting.
    
    Args:
        producer: KafkaProducer instance
        messages: List of messages to produce
        rate_limit: Maximum messages per second
    """
    semaphore = Semaphore(rate_limit)
    
    async def send_one(msg):
        async with semaphore:
            producer.produce(
                topic="orders",
                value=msg.encode(),
            )
            producer.poll(0)
            await asyncio.sleep(1 / rate_limit)
    
    await asyncio.gather(*[send_one(msg) for msg in messages])
```

**Pros:**
- Prevents buffer overflow proactively
- Smooth, predictable load
- Good for rate-sensitive applications

**Cons:**
- More complex (async programming)
- May underutilize Kafka capacity

## Configuration Parameters

Key producer configurations for back pressure:

```python
producer_config = {
    # Maximum messages in buffer (default: 100,000)
    "queue.buffering.max.messages": 10000,
    
    # Maximum buffer size in KB (default: 32 MB)
    "queue.buffering.max.kbytes": 32768,
    
    # How long to wait if buffer is full (default: 0 = throw error immediately)
    "queue.buffering.max.ms": 1000,  # Wait up to 1 second
    
    # Batch messages for this long (default: 0 = send immediately)
    "linger.ms": 10,  # Wait 10ms to batch messages
    
    # Max batch size (default: 1 MB)
    "batch.size": 16384,  # 16 KB
}
```

### Tuning Recommendations

| Use Case | Configuration | Reason |
|----------|--------------|--------|
| **High Throughput** | `linger.ms=10-50`, `batch.size=64KB` | Better batching |
| **Low Latency** | `linger.ms=0`, small buffer | Send immediately |
| **Bursty Traffic** | Large buffer, `queue.buffering.max.ms=1000` | Absorb spikes |
| **Limited Memory** | Small buffer, aggressive polling | Control memory |

## Monitoring Back Pressure

### Check Queue Length

```python
queue_length = len(producer.producer)
print(f"Messages in queue: {queue_length}")

# Alert if queue is growing
if queue_length > 1000:
    print("⚠️  Queue length high - applying back pressure!")
```

### Track Delivery Success/Failure

```python
success_count = 0
failure_count = 0

def delivery_report(err, msg):
    global success_count, failure_count
    if err:
        failure_count += 1
    else:
        success_count += 1

# Monitor ratio
if failure_count / (success_count + failure_count) > 0.01:
    print("⚠️  High failure rate - check Kafka health!")
```

### Production Metrics

In production, track:
- **Producer Queue Length**: `kafka.producer.queue.length`
- **Buffer Full Rate**: How often `BufferError` occurs
- **Message Send Rate**: Messages per second
- **Delivery Callback Latency**: Time from produce to callback
- **Flush Duration**: How long `flush()` takes

## Best Practices

### ✅ DO

1. **Always poll periodically**
   ```python
   for i, message in enumerate(messages):
       producer.produce(topic="orders", value=message)
       if i % 10 == 0:
           producer.poll(0)
   ```

2. **Handle BufferError gracefully**
   ```python
   try:
       producer.produce(topic="orders", value=message)
   except BufferError:
       producer.poll(1.0)  # Block and wait
       # Retry logic here
   ```

3. **Configure appropriate buffer sizes**
   ```python
   # For high-volume producers
   config = {
       "queue.buffering.max.messages": 100000,
       "queue.buffering.max.kbytes": 1048576,  # 1 GB
   }
   ```

4. **Use batching for throughput**
   ```python
   config = {"linger.ms": 10}  # Batch for 10ms
   ```

5. **Monitor queue length**
   ```python
   if len(producer.producer) > threshold:
       # Apply back pressure
   ```

### ❌ DON'T

1. **Don't ignore BufferError**
   ```python
   # Bad - will crash
   producer.produce(topic="orders", value=message)
   ```

2. **Don't forget to flush on shutdown**
   ```python
   # Bad - messages lost
   # Good
   producer.flush(timeout=30)
   ```

3. **Don't set infinite retry**
   ```python
   # Bad - can hang forever
   while True:
       try:
           producer.produce(...)
           break
       except BufferError:
           time.sleep(1)
   ```

4. **Don't use tiny buffers with high load**
   ```python
   # Bad for high volume
   config = {"queue.buffering.max.messages": 100}
   ```

## Testing Back Pressure

### Test Script

```python
def test_back_pressure():
    """Test producer behavior under load."""
    producer = KafkaProducerWithBackpressure(
        queue_buffering_max_messages=100,  # Small buffer for testing
    )
    
    print("Sending 1000 messages rapidly...")
    start = time.time()
    
    for i in range(1000):
        producer.produce_with_backpressure(
            topic="test",
            value=f"message-{i}".encode(),
        )
    
    duration = time.time() - start
    print(f"Took {duration:.2f}s (back pressure applied: {duration > 1})")
    
    producer.flush()
```

### Load Test

```bash
# Terminal 1: Start consumer
python order_consumer.py

# Terminal 2: Run high-volume producer
python order_producer_with_backpressure.py

# Terminal 3: Monitor queue
watch -n 1 'docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group order-consumer'
```

## Comparison: With vs Without Back Pressure

### Without Back Pressure

```python
# Simple producer - will fail under load
for i in range(10000):
    producer.produce(topic="orders", value=f"msg-{i}".encode())
    # ❌ No polling - buffer fills up
    # ❌ No error handling - crashes on BufferError

producer.flush()  # May timeout or fail
```

**Result:** Crashes after ~5000 messages with `BufferError`

### With Back Pressure

```python
# Producer with back pressure
for i in range(10000):
    producer.produce_with_backpressure(
        topic="orders",
        value=f"msg-{i}".encode()
    )
    # ✅ Handles BufferError internally
    # ✅ Polls and retries automatically

producer.flush()  # Completes successfully
```

**Result:** All 10,000 messages sent successfully (may take longer)

## Summary

**Key Takeaways:**

1. 📊 **Back pressure prevents system overload** by controlling message flow
2. 🔄 **Use `poll()`** regularly to free up buffer space
3. 🛡️ **Handle `BufferError`** with retry and exponential backoff
4. ⚙️ **Tune configurations** based on your workload
5. 📈 **Monitor queue length** and delivery metrics
6. 🧪 **Test under load** before production deployment

**Quick Decision Guide:**

- **Low volume (<100 msg/sec)**: Basic polling is fine
- **Medium volume (100-1000 msg/sec)**: Add BufferError handling
- **High volume (>1000 msg/sec)**: Use full back pressure implementation
- **Extreme volume (>10k msg/sec)**: Consider rate limiting + multiple producers

---

**Related Files:**
- `kafka/producer_with_backpressure.py` - Full implementation
- `order_producer_with_backpressure.py` - Usage example
- `kafka/producer.py` - Basic producer with poll() support


# Basic Kafka Hands-On

A hands-on project demonstrating Apache Kafka fundamentals with Python, featuring a producer-consumer architecture for processing order events.

## About The Project

This project provides a practical introduction to Apache Kafka by implementing a complete event-driven system for order processing. It showcases:

- **Event Production**: Publishing order events to Kafka topics with message batching
- **Event Consumption**: Subscribing to topics and processing messages in real-time
- **Data Validation**: Using Pydantic models for type-safe message serialization/deserialization
- **Modern Kafka**: Running Kafka in KRaft mode (without ZooKeeper)
- **Clean Architecture**: Modular design with separate models, Kafka utilities, and application logic
- **Comprehensive Testing**: Unit tests for producers, consumers, and data models

### Project Structure

```
basic-kafka-hands-on/
├── kafka/              # Kafka producer and consumer wrappers
│   ├── producer.py
│   └── consumer.py
├── models/             # Pydantic data models
│   └── order.py
├── tests/              # Unit tests
│   ├── conftest.py
│   ├── test_kafka_producer.py
│   ├── test_kafka_consumer.py
│   └── test_order.py
├── order_producer.py   # Order producer application
├── order_consumer.py   # Order consumer application
├── docker-compose.yml  # Kafka infrastructure
└── requirements.txt    # Python dependencies
```

### Built With

* [![Python][Python-badge]][Python-url]
* [![Kafka][Kafka-badge]][Kafka-url]
* [![Pydantic][Pydantic-badge]][Pydantic-url]
* [![Docker][Docker-badge]][Docker-url]
* [![Pytest][Pytest-badge]][Pytest-url]

**Key Technologies:**
- **Python 3.11+** - Core programming language
- **Apache Kafka 7.8.6** - Distributed event streaming platform (KRaft mode)
- **Pydantic 2.10.5** - Data validation and settings management
- **confluent-kafka 2.12.2** - High-performance Kafka client library
- **pytest 7.4.3** - Testing framework
- **Docker** - Containerized Kafka deployment

## Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

* **Python 3.11 or higher**
  ```bash
  python --version
  ```

* **Docker and Docker Compose**
  ```bash
  docker --version
  docker compose version
  ```

* **pip** (Python package installer)
  ```bash
  pip --version
  ```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sar-joshi/basic-kafka-hands-on.git
   cd basic-kafka-hands-on
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Kafka with Docker Compose**
   ```bash
   docker compose up -d
   ```

5. **Verify Kafka is running**
   ```bash
   docker ps
   ```
   You should see the `kafka` container running on port 9092.

6. **Create the `orders` topic** (optional - auto-created on first message)
   ```bash
   docker exec -it kafka kafka-topics --create \
     --bootstrap-server localhost:9092 \
     --topic orders \
     --partitions 3 \
     --replication-factor 1
   ```

## Usage

### Running the Producer

The producer creates and sends order events to the `orders` topic:

```bash
python order_producer.py
```

**Example Output:**
```
✅ Delivered: {"order_id":"abc-123","customer_name":"John Doe","item":"MacBook Pro",...}
✅ Topic: orders, Partition: 0, Offset: 42
```

### Running the Consumer

The consumer subscribes to the `orders` topic and processes incoming messages:

```bash
python order_consumer.py
```

**Example Output:**
```
🔵 Consumer started. Waiting for messages...
Press Ctrl+C to stop.

✅ Order received: abc-123
   Customer: John Doe, Item: MacBook Pro, Qty: 1
```

Press `Ctrl+C` to stop the consumer gracefully.

### Running Tests

Execute the test suite to verify functionality:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_kafka_producer.py -v

# Run with coverage
pytest tests/ --cov=kafka --cov=models -v
```

### Useful Kafka Commands

**List all topics:**
```bash
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

**Describe a topic:**
```bash
docker exec -it kafka kafka-topics --describe --topic orders --bootstrap-server localhost:9092
```

**Consume messages from CLI:**
```bash
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning
```

**Check consumer group status:**
```bash
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group order-consumer
```

### Stopping the Project

1. **Stop the consumer/producer** - Press `Ctrl+C`

2. **Stop Kafka**
   ```bash
   docker compose down
   ```

3. **Remove volumes (clean slate)**
   ```bash
   docker compose down -v
   ```

## Key Concepts Demonstrated

### Producer Concepts
- ✅ Message batching and buffering
- ✅ Delivery callbacks and error handling
- ✅ Topic partitioning
- ✅ JSON serialization with Pydantic

### Consumer Concepts
- ✅ Consumer groups
- ✅ Offset management (earliest/latest)
- ✅ Polling and message processing
- ✅ Graceful shutdown
- ✅ Error handling for malformed messages

### Kafka Architecture
- ✅ KRaft mode (no ZooKeeper required)
- ✅ Topics and partitions
- ✅ Producers and consumers
- ✅ Message ordering within partitions

## Understanding Kafka Partitioning

Partitioning is a fundamental concept in Kafka that enables scalability and ordering guarantees. Let's dive deep into how it works.

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

### Message Ordering Guarantees

**Critical Rule:** Kafka guarantees message order **within a partition**, but **NOT across partitions**.

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

### Implementing Key-Based Partitioning

Update your producer to support message keys:

**1. Update the producer wrapper:**
```python
# kafka/producer.py
def produce(self, topic: str, key: bytes = None, value: bytes, callback=None):
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

### Monitoring Partition Distribution

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

## Acknowledgments

* [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
* [Confluent Kafka Python](https://docs.confluent.io/kafka-clients/python/current/overview.html)
* [Pydantic Documentation](https://docs.pydantic.dev/)
* [Kafka: The Definitive Guide](https://www.confluent.io/resources/kafka-the-definitive-guide/)
* [Kafka Crash Course by TechWorld with Nana](https://youtu.be/B7CwU_tNYIE?si=dhcSRShtdqgAIQci)

---

<!-- Badge URLs -->
[Python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Kafka-badge]: https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white
[Kafka-url]: https://kafka.apache.org/
[Pydantic-badge]: https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white
[Pydantic-url]: https://docs.pydantic.dev/
[Docker-badge]: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
[Pytest-badge]: https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white
[Pytest-url]: https://pytest.org/

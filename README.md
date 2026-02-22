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
├── kafka/                     # Kafka producer and consumer wrappers
│   ├── producer.py
│   ├── producer_with_backpressure.py
│   └── consumer.py
├── models/                    # Pydantic data models
│   └── order.py
├── utils/                     # Utility functions
│   └── partitioning.py       # Compound partition key strategies
├── examples/                  # 🎓 Comprehensive examples
│   ├── README.md             # Examples guide and index
│   ├── offset_management.py
│   ├── idempotent_processing.py
│   ├── race_condition_handling.py
│   ├── backpressure_example.py
│   └── compound_keys_example.py
├── tests/                     # Unit tests (62 tests)
│   ├── conftest.py
│   ├── test_kafka_producer.py
│   ├── test_kafka_consumer.py
│   ├── test_backpressure.py
│   ├── test_partitioning.py
│   └── test_order.py
├── docs/                      # Documentation
│   ├── PROJECT_STRUCTURE.md  # Project organization guide
│   ├── OFFSETS.md            # Offset management deep dive
│   ├── BACKPRESSURE.md       # Back pressure guide
│   └── PARTITIONING.md       # Partitioning strategies guide
├── order_producer.py          # Simple producer (getting started)
├── order_consumer.py          # Simple consumer (getting started)
├── docker-compose.yml         # Kafka infrastructure
└── requirements.txt           # Python dependencies
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
   git clone https://github.com/yourusername/basic-kafka-hands-on.git
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

### 🎓 Exploring Advanced Examples

The `examples/` directory contains comprehensive, production-ready examples demonstrating advanced Kafka patterns:

```bash
# Browse available examples
ls examples/

# Read the examples guide
cat examples/README.md

# Run specific examples
python examples/offset_management.py 1      # Manual offset commit
python examples/idempotent_processing.py 1   # Handle duplicates
python examples/race_condition_handling.py 2 # Prevent race conditions
python examples/backpressure_example.py      # Flow control
python examples/compound_keys_example.py     # Partition optimization
```

**Available Examples:**
- 📍 **Offset Management** (5 examples) - Manual commit, auto-commit, batch commit, seeking, lag monitoring
- 🔄 **Idempotent Processing** (4 examples) - Unique constraints, deduplication, state tracking
- 🔐 **Race Condition Handling** (5 examples) - Locks, transactions, optimistic locking
- ⚡ **Back Pressure** (4 demos) - High-volume production, buffer management
- 🎯 **Compound Keys** (5 strategies) - Region-based, segment-based, hash-based partitioning

👉 **See `examples/README.md` for complete guide and learning paths!**

### Running Tests

Execute the test suite to verify functionality:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_kafka_producer.py -v

# Run with coverage
pytest tests/ --cov=kafka --cov=models --cov=utils -v
```

**Test Coverage:**
- 78 tests total (all passing ✅)
- Producer tests: 9
- Consumer tests: 11
- Back pressure tests: 19
- Partitioning tests: 22
- **Examples tests: 16** ⭐ NEW
- Model tests: 1

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
- ✅ Topic partitioning with compound keys
- ✅ Back pressure management
- ✅ JSON serialization with Pydantic

### Consumer Concepts
- ✅ Consumer groups
- ✅ Offset management (earliest/latest)
- ✅ Manual vs auto-commit
- ✅ Polling and message processing
- ✅ Graceful shutdown
- ✅ Idempotent processing
- ✅ Error handling for malformed messages

### Kafka Architecture
- ✅ KRaft mode (no ZooKeeper required)
- ✅ Topics and partitions
- ✅ Producers and consumers
- ✅ Message ordering within partitions
- ✅ Consumer group coordination

## 📚 Documentation

Complete guides and examples are organized in `docs/` and `examples/` directories.

### 📖 Core Concepts Guides (`docs/`)

| Guide | Topics | Read Time |
|-------|--------|-----------|
| **[Kafka Concepts](docs/KAFKA_CONCEPTS.md)** | Partitioning basics, message ordering | 10-15 min |
| **[Understanding Offsets](docs/OFFSETS.md)** | Offset management, commit strategies, delivery semantics | 15-20 min |
| **[Back Pressure](docs/BACKPRESSURE.md)** | Flow control, buffer management, high-volume production | 20-25 min |
| **[Advanced Partitioning](docs/PARTITIONING.md)** | Compound keys, hotspot prevention, load distribution | 20-25 min |
| **[Project Structure](docs/PROJECT_STRUCTURE.md)** | Project organization, navigation, learning paths | 10 min |
| **[Docs Index](docs/README.md)** | Complete documentation index and reading guide | 5 min |

### 🎓 Interactive Examples (`examples/`)

| Example | What You'll Learn | Demos |
|---------|-------------------|-------|
| **[Offset Management](examples/offset_management.py)** | Manual commit, auto-commit, batch commit, seeking, lag monitoring | 5 |
| **[Idempotent Processing](examples/idempotent_processing.py)** | Unique constraints, deduplication, state tracking | 4 |
| **[Race Conditions](examples/race_condition_handling.py)** | Locks, transactions, optimistic locking, coordination | 5 |
| **[Back Pressure](examples/backpressure_example.py)** | High-volume production, buffer management | 4 |
| **[Compound Keys](examples/compound_keys_example.py)** | Region-based, segment-based, hash-based partitioning | 5 |
| **[Examples Guide](examples/README.md)** | Complete index with learning paths | - |

**Total: 23+ interactive examples** 🎯

### Quick Start Paths

**🎯 Path 1: Get Started (30 minutes)**
```
1. Run order_producer.py
2. Run order_consumer.py
3. Explore docker-compose.yml
```

**📚 Path 2: Production Consumer (2-3 hours)**
```
1. Read docs/OFFSETS.md
2. Run examples/offset_management.py
3. Run examples/idempotent_processing.py
4. Review tests/test_kafka_consumer.py
```

**⚡ Path 3: High-Performance Producer (2-3 hours)**
```
1. Read docs/BACKPRESSURE.md
2. Read docs/PARTITIONING.md
3. Run examples/backpressure_example.py
4. Run examples/compound_keys_example.py
```

**🎓 Path 4: Master All Concepts (6-8 hours)**
```
1. Read all docs in docs/
2. Run all examples in examples/
3. Review all tests in tests/
4. Study implementation in kafka/, models/, utils/
```

## Troubleshooting

### Kafka won't start

```bash
# Check Docker logs
docker logs kafka

# Restart with clean state
docker compose down -v
docker compose up -d
```

### No messages received

```bash
# Verify topic has messages
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning \
  --max-messages 5

# If empty, produce some messages
python order_producer.py
```

### Import errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Tests failing

```bash
# Run tests with verbose output
pytest tests/ -v --tb=short

# Check specific test file
pytest tests/test_kafka_producer.py -v
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Update documentation
5. Submit a pull request

## Acknowledgments

* [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
* [Confluent Kafka Python](https://docs.confluent.io/kafka-clients/python/current/overview.html)
* [Pydantic Documentation](https://docs.pydantic.dev/)
* [Kafka: The Definitive Guide](https://www.confluent.io/resources/kafka-the-definitive-guide/)
* [Best Practices for Developing Apache Kafka Applications](https://www.confluent.io/blog/apache-kafka-best-practices/)

---

**License:** MIT
**Last Updated:** February 2026

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

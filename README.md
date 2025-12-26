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

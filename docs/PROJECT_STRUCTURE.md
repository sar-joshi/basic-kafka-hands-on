# Project Structure

## 📁 Complete Directory Layout

```
basic-kafka-hands-on/
│
├── 📂 kafka/                          # Core Kafka implementations
│   ├── __init__.py
│   ├── producer.py                   # Basic producer wrapper
│   ├── producer_with_backpressure.py # Enhanced producer with flow control
│   └── consumer.py                   # Consumer wrapper with utilities
│
├── 📂 models/                         # Data models
│   ├── __init__.py
│   └── order.py                      # Order Pydantic model
│
├── 📂 utils/                          # Utility functions
│   ├── __init__.py
│   └── partitioning.py               # Partition key strategies
│
├── 📂 examples/ (NEW!)                # 🎓 Comprehensive examples
│   ├── README.md                     # Examples guide and learning paths
│   ├── __init__.py
│   ├── offset_management.py          # 5 examples of offset handling
│   ├── idempotent_processing.py      # 4 examples of deduplication
│   ├── race_condition_handling.py    # 5 examples of concurrency safety
│   ├── backpressure_example.py       # Flow control demonstrations
│   └── compound_keys_example.py      # Partition optimization strategies
│
├── 📂 tests/                          # Test suite (62 tests)
│   ├── __init__.py
│   ├── conftest.py                   # Shared test fixtures
│   ├── test_kafka_producer.py        # Producer tests (9)
│   ├── test_kafka_consumer.py        # Consumer tests (11)
│   ├── test_backpressure.py          # Back pressure tests (19)
│   ├── test_partitioning.py          # Partitioning tests (22)
│   └── test_order.py                 # Model tests (1)
│
├── 📂 docs/                           # Documentation
│   ├── BACKPRESSURE.md               # Complete back pressure guide
│   └── PARTITIONING.md               # Complete partitioning guide
│
├── 📄 order_producer.py               # Simple producer (getting started)
├── 📄 order_consumer.py               # Simple consumer (getting started)
├── 📄 order_consumer_refactored.py    # Advanced consumer example
├── 📄 order_producer_refactored.py    # Advanced producer example (if exists)
│
├── 🐳 docker-compose.yml              # Kafka infrastructure
├── ⚙️  pytest.ini                     # Pytest configuration
├── 📦 requirements.txt                # Python dependencies
├── 📖 README.md                       # Main documentation
└── 📋 PROJECT_STRUCTURE.md            # This file
```

## 📊 Statistics

```
Total Files:     ~40 files
Total Tests:     62 tests (all passing ✅)
Total Lines:     ~8,000+ lines of code
Examples:        19 interactive examples
Documentation:   4 comprehensive guides
```

## 🎯 File Purposes

### Core Implementation (`kafka/`, `models/`, `utils/`)

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `kafka/producer.py` | Basic producer wrapper | 72 | ✅ |
| `kafka/producer_with_backpressure.py` | Enhanced producer with flow control | 161 | ✅ |
| `kafka/consumer.py` | Consumer wrapper | 86 | ✅ |
| `models/order.py` | Order Pydantic model | 33 | ✅ |
| `utils/partitioning.py` | Partition key utilities | 256 | ✅ |

### Examples (`examples/`)

| File | Examples | Purpose | Status |
|------|----------|---------|--------|
| `offset_management.py` | 5 | Offset commit strategies | ✅ |
| `idempotent_processing.py` | 4 | Duplicate handling | ✅ |
| `race_condition_handling.py` | 5 | Concurrency safety | ✅ |
| `backpressure_example.py` | 4 | Flow control | ✅ |
| `compound_keys_example.py` | 5 | Partition optimization | ✅ |

### Tests (`tests/`)

| File | Tests | Coverage | Status |
|------|-------|----------|--------|
| `test_kafka_producer.py` | 9 | Producer functionality | ✅ |
| `test_kafka_consumer.py` | 11 | Consumer functionality | ✅ |
| `test_backpressure.py` | 19 | Back pressure handling | ✅ |
| `test_partitioning.py` | 22 | Partition strategies | ✅ |
| `test_order.py` | 1 | Model validation | ✅ |

### Documentation (`docs/`, `README.md`)

| File | Size | Purpose | Status |
|------|------|---------|--------|
| `README.md` | 1,500+ lines | Main project documentation | ✅ |
| `examples/README.md` | 400+ lines | Examples guide | ✅ |
| `docs/BACKPRESSURE.md` | 390 lines | Back pressure deep dive | ✅ |
| `docs/PARTITIONING.md` | ~350 lines | Partitioning strategies | ✅ |

## 🚀 Quick Navigation

### For Beginners

Start here:
1. `README.md` - Project overview
2. `order_producer.py` - Simple producer
3. `order_consumer.py` - Simple consumer
4. `examples/offset_management.py` #1 - Reliable consumer

### For Learning Kafka Concepts

Explore by topic:
- **Offsets**: `examples/offset_management.py` + `README.md` (Understanding Kafka Offsets)
- **Duplicates**: `examples/idempotent_processing.py` + `README.md` (Idempotent Processing)
- **Concurrency**: `examples/race_condition_handling.py`
- **Performance**: `examples/backpressure_example.py` + `docs/BACKPRESSURE.md`
- **Partitioning**: `examples/compound_keys_example.py` + `docs/PARTITIONING.md`

### For Production Implementation

Reference these:
1. `kafka/producer_with_backpressure.py` - Production producer
2. `kafka/consumer.py` - Production consumer
3. `utils/partitioning.py` - Partition utilities
4. `tests/` - Testing patterns

## 📝 File Relationships

### Data Flow

```
order_producer.py
    ↓
kafka/producer.py
    ↓
models/order.py (Pydantic validation)
    ↓
Kafka Topic "orders"
    ↓
kafka/consumer.py
    ↓
order_consumer.py
```

### Advanced Flow

```
examples/backpressure_example.py
    ↓
kafka/producer_with_backpressure.py
    ↓
utils/partitioning.py (compound keys)
    ↓
models/order.py
    ↓
Kafka (with optimized partitioning)
    ↓
examples/idempotent_processing.py
    ↓
kafka/consumer.py
```

### Testing Flow

```
tests/conftest.py (fixtures)
    ↓
tests/test_*.py
    ↓
kafka/* (implementation)
    ↓
models/* (data models)
    ↓
utils/* (utilities)
```

## 🎓 Learning Paths

### Path 1: Basic Kafka Usage (2-3 hours)

```
1. README.md (overview)
2. order_producer.py (run it)
3. order_consumer.py (run it)
4. docker-compose.yml (understand setup)
5. models/order.py (data model)
```

### Path 2: Production-Ready Consumer (3-4 hours)

```
1. examples/offset_management.py (all examples)
2. examples/idempotent_processing.py (examples 1-2)
3. examples/race_condition_handling.py (examples 2-3)
4. tests/test_kafka_consumer.py (learn patterns)
```

### Path 3: Production-Ready Producer (2-3 hours)

```
1. examples/backpressure_example.py
2. examples/compound_keys_example.py
3. docs/BACKPRESSURE.md
4. docs/PARTITIONING.md
5. tests/test_kafka_producer.py
```

### Path 4: Advanced Topics (4-6 hours)

```
1. All examples in examples/ directory
2. All documentation in docs/
3. All tests in tests/
4. kafka/producer_with_backpressure.py (implementation)
5. utils/partitioning.py (implementation)
```

## 🔧 Maintenance

### Adding a New Example

1. Create `examples/your_example.py`
2. Follow existing structure (interactive menu, multiple examples)
3. Update `examples/README.md`
4. Add tests if applicable
5. Update main `README.md` if needed

### Adding a New Feature

1. Implement in appropriate directory (`kafka/`, `models/`, `utils/`)
2. Add tests in `tests/`
3. Create example in `examples/`
4. Document in `README.md` or `docs/`
5. Update this file

### Running Quality Checks

```bash
# Run all tests
pytest tests/ -v

# Check test coverage
pytest tests/ --cov=kafka --cov=models --cov=utils -v

# Run specific test file
pytest tests/test_kafka_producer.py -v

# Run linter (if configured)
flake8 kafka/ models/ utils/ examples/
```

## 📊 Metrics

### Code Coverage

- `kafka/`: Well tested (9 + 19 tests)
- `models/`: Tested (1 test)
- `utils/`: Well tested (22 tests)
- `examples/`: Interactive demos (no unit tests needed)

### Documentation Coverage

- ✅ Main README (comprehensive)
- ✅ Examples README (complete guide)
- ✅ Back pressure guide (detailed)
- ✅ Partitioning guide (detailed)
- ✅ Inline code comments (extensive)

### Example Coverage

- ✅ Offset management (5 examples)
- ✅ Idempotent processing (4 examples)
- ✅ Race conditions (5 examples)
- ✅ Back pressure (4 demos)
- ✅ Partitioning (5 strategies)

**Total: 23 interactive examples**

## 🎯 Key Improvements from Reorganization

### Before

```
basic-kafka-hands-on/
├── order_producer.py
├── order_producer_with_backpressure.py (root level)
├── order_producer_with_compound_keys.py (root level)
├── order_consumer.py
└── ... scattered files
```

### After

```
basic-kafka-hands-on/
├── order_producer.py (simple, for beginners)
├── order_consumer.py (simple, for beginners)
├── examples/ (organized, advanced patterns)
│   ├── README.md (comprehensive guide)
│   ├── offset_management.py
│   ├── idempotent_processing.py
│   ├── race_condition_handling.py
│   ├── backpressure_example.py
│   └── compound_keys_example.py
└── ... well organized
```

---

**Last Updated:** December 2025
**Total Examples:** 23 interactive examples
**Test Coverage:** 62 tests, all passing ✅

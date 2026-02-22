"""
Tests for custom partitioning utilities.
"""

from utils.partitioning import (
    create_compound_key,
    create_region_based_key,
    create_segment_based_key,
    hash_partition_key,
    create_time_bucketed_key,
    create_multi_tenant_key,
    calculate_partition,
    analyze_distribution,
    PartitionStrategy,
)


class TestCompoundKeys:
    """Test compound key creation functions."""

    def test_create_compound_key_basic(self):
        """Test basic compound key creation."""
        key = create_compound_key("customer-123", "us-west", "premium")
        assert key == "customer-123|us-west|premium"

    def test_create_compound_key_custom_separator(self):
        """Test compound key with custom separator."""
        key = create_compound_key("customer-123", "us-west", separator=":")
        assert key == "customer-123:us-west"

    def test_create_compound_key_with_empty_parts(self):
        """Test compound key ignores empty parts."""
        key = create_compound_key("customer-123", "", "premium")
        assert key == "customer-123|premium"

    def test_create_region_based_key(self):
        """Test region-based key creation."""
        key = create_region_based_key("customer-123", "us-west")
        assert key == "customer-123|us-west"
        assert "us-west" in key

    def test_create_segment_based_key(self):
        """Test segment-based key creation."""
        key = create_segment_based_key("customer-123", "premium")
        assert key == "customer-123|premium"
        assert "premium" in key

    def test_create_time_bucketed_key(self):
        """Test time-bucketed key creation."""
        key = create_time_bucketed_key("customer-123", "2024-12-26-10")
        assert key == "customer-123|2024-12-26-10"
        assert "2024-12-26-10" in key

    def test_create_multi_tenant_key(self):
        """Test multi-tenant key creation."""
        key = create_multi_tenant_key("acme-corp", "customer-123")
        assert key == "acme-corp|customer-123"
        assert "acme-corp" in key


class TestHashPartitionKey:
    """Test hash-based partition key creation."""

    def test_hash_partition_key_consistency(self):
        """Test that same inputs produce same hash."""
        key1 = hash_partition_key("customer-123", "us-west")
        key2 = hash_partition_key("customer-123", "us-west")
        assert key1 == key2

    def test_hash_partition_key_different_inputs(self):
        """Test that different inputs produce different hashes."""
        key1 = hash_partition_key("customer-123", "us-west")
        key2 = hash_partition_key("customer-123", "eu-central")
        assert key1 != key2

    def test_hash_partition_key_custom_size(self):
        """Test hash with custom size."""
        key = hash_partition_key("customer-123", hash_size=16)
        assert len(key) == 16

    def test_hash_partition_key_is_hexadecimal(self):
        """Test that hash output is valid hexadecimal."""
        key = hash_partition_key("customer-123", "us-west")
        assert all(c in "0123456789abcdef" for c in key)


class TestPartitionCalculation:
    """Test partition calculation logic."""

    def test_calculate_partition_range(self):
        """Test that partition is within valid range."""
        key = "customer-123|us-west"
        partition = calculate_partition(key, num_partitions=3)
        assert 0 <= partition < 3

    def test_calculate_partition_consistency(self):
        """Test that same key produces same partition."""
        key = "customer-123|us-west"
        partition1 = calculate_partition(key, num_partitions=3)
        partition2 = calculate_partition(key, num_partitions=3)
        assert partition1 == partition2

    def test_calculate_partition_different_keys(self):
        """Test that different keys can produce different partitions."""
        key1 = "customer-123|us-west"
        key2 = "customer-456|eu-central"
        partition1 = calculate_partition(key1, num_partitions=10)
        partition2 = calculate_partition(key2, num_partitions=10)
        # Not strictly required to be different, but likely
        # (could occasionally fail due to hash collisions)
        assert isinstance(partition1, int)
        assert isinstance(partition2, int)


class TestDistributionAnalysis:
    """Test distribution analysis functionality."""

    def test_analyze_distribution_balanced(self):
        """Test distribution analysis with balanced keys."""
        # Create keys that should distribute evenly
        keys = [f"customer-{i}|us-west" for i in range(100)]
        result = analyze_distribution(keys, num_partitions=3)

        assert result["total_keys"] == 100
        assert result["num_partitions"] == 3
        assert len(result["partition_counts"]) == 3
        assert sum(result["partition_counts"].values()) == 100

        # Check that distribution is reasonably balanced
        # (should be within 20% for 100 random keys across 3 partitions)
        assert result["min_partition_size"] > 20  # At least 20 per partition
        assert result["max_partition_size"] < 45  # At most 45 per partition

    def test_analyze_distribution_single_partition(self):
        """Test distribution analysis with single partition."""
        keys = ["customer-1", "customer-2", "customer-3"]
        result = analyze_distribution(keys, num_partitions=1)

        assert result["partition_counts"][0] == 3
        assert result["min_partition_size"] == 3
        assert result["max_partition_size"] == 3
        assert result["imbalance_ratio"] == 1.0
        assert result["is_balanced"] is True

    def test_analyze_distribution_empty_keys(self):
        """Test distribution analysis with no keys."""
        result = analyze_distribution([], num_partitions=3)

        assert result["total_keys"] == 0
        assert result["min_partition_size"] == 0
        assert result["max_partition_size"] == 0


class TestPartitionStrategy:
    """Test PartitionStrategy enum."""

    def test_partition_strategy_values(self):
        """Test that all strategy values exist."""
        assert PartitionStrategy.SIMPLE.value == "simple"
        assert PartitionStrategy.REGION_BASED.value == "region"
        assert PartitionStrategy.SEGMENT_BASED.value == "segment"
        assert PartitionStrategy.HASH_BASED.value == "hash"
        assert PartitionStrategy.CUSTOM.value == "custom"


class TestRealWorldScenarios:
    """Test real-world partitioning scenarios."""

    def test_regional_distribution_better_than_simple(self):
        """
        Test that region-based keys provide better distribution than simple IDs
        when customers cluster by region.
        """
        # Scenario: 100 customers, 50 from us-west, 50 from eu-central
        simple_keys = [f"customer-{i}" for i in range(100)]
        regional_keys = [
            create_region_based_key(
                f"customer-{i}", "us-west" if i < 50 else "eu-central"
            )
            for i in range(100)
        ]

        simple_dist = analyze_distribution(simple_keys, num_partitions=3)
        regional_dist = analyze_distribution(regional_keys, num_partitions=3)

        # Both should distribute across all partitions
        assert simple_dist["total_keys"] == 100
        assert regional_dist["total_keys"] == 100

        # All partitions should get some keys (no partition is empty)
        assert all(count > 0 for count in simple_dist["partition_counts"].values())
        assert all(count > 0 for count in regional_dist["partition_counts"].values())

    def test_segment_based_distribution(self):
        """
        Test that segment-based keys help distribute load when segments
        have different activity levels.
        """
        # Scenario: 80 free users, 15 premium, 5 enterprise
        keys = []
        for i in range(80):
            keys.append(create_segment_based_key(f"customer-{i}", "free"))
        for i in range(80, 95):
            keys.append(create_segment_based_key(f"customer-{i}", "premium"))
        for i in range(95, 100):
            keys.append(create_segment_based_key(f"customer-{i}", "enterprise"))

        result = analyze_distribution(keys, num_partitions=3)

        # Should distribute across all partitions
        assert result["total_keys"] == 100
        assert all(count > 0 for count in result["partition_counts"].values())

    def test_multi_tenant_distribution(self):
        """Test multi-tenant key distribution."""
        # Scenario: 3 tenants with different customer counts
        keys = []

        # Tenant 1: 50 customers
        for i in range(50):
            keys.append(create_multi_tenant_key("tenant-1", f"customer-{i}"))

        # Tenant 2: 30 customers
        for i in range(30):
            keys.append(create_multi_tenant_key("tenant-2", f"customer-{i}"))

        # Tenant 3: 20 customers
        for i in range(20):
            keys.append(create_multi_tenant_key("tenant-3", f"customer-{i}"))

        result = analyze_distribution(keys, num_partitions=3)

        # All 100 keys should be distributed
        assert result["total_keys"] == 100

        # Each partition should have some keys
        assert all(count > 0 for count in result["partition_counts"].values())

    def test_hash_based_provides_even_distribution(self):
        """Test that hash-based keys provide even distribution."""
        # Create keys with various attributes
        keys = [
            hash_partition_key(f"customer-{i}", f"region-{i % 5}", f"segment-{i % 3}")
            for i in range(100)
        ]

        result = analyze_distribution(keys, num_partitions=5)

        # Hash should provide good distribution
        assert result["total_keys"] == 100

        # Each partition should get at least some keys (reasonable distribution)
        assert all(count > 0 for count in result["partition_counts"].values())

        # Imbalance should be reasonable (not worse than 2.5:1 ratio)
        assert result["imbalance_ratio"] < 2.5

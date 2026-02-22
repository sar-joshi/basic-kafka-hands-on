"""
Custom Partitioning Utilities for Kafka

This module provides utilities for creating compound partition keys to achieve
better load distribution across Kafka partitions.

Why Compound Keys?
- Simple customer_id keys can create hotspots (some customers more active)
- Compound keys (customer_id + region/segment) distribute load more evenly
- Helps prevent partition skew and improves throughput
"""

import hashlib
from enum import Enum


class PartitionStrategy(Enum):
    """Enumeration of partitioning strategies."""

    SIMPLE = "simple"  # Just use the ID
    REGION_BASED = "region"  # ID + geographical region
    SEGMENT_BASED = "segment"  # ID + user segment
    HASH_BASED = "hash"  # Hash of multiple attributes
    CUSTOM = "custom"  # Custom logic


def create_compound_key(*parts: str, separator: str = "|") -> str:
    """
    Create a compound partition key from multiple parts.

    Args:
        *parts: Variable number of string parts to combine.
        separator: Separator character (default: "|").

    Returns:
        Compound key string.

    Example:
        >>> create_compound_key("customer-123", "us-west", "premium")
        'customer-123|us-west|premium'
    """
    return separator.join(str(part) for part in parts if part)


def create_region_based_key(customer_id: str, region: str, separator: str = "|") -> str:
    """
    Create a region-based compound key for geographical distribution.

    This ensures customers from the same region with similar IDs are distributed
    across different partitions, preventing regional hotspots.

    Args:
        customer_id: Customer identifier.
        region: Geographical region (e.g., "us-west", "eu-central").
        separator: Separator character (default: "|").

    Returns:
        Compound key combining customer_id and region.

    Example:
        >>> create_region_based_key("customer-123", "us-west")
        'customer-123|us-west'

    Use Case:
        When you have customers distributed across regions and want to ensure
        even load distribution regardless of regional activity spikes.
    """
    return create_compound_key(customer_id, region, separator=separator)


def create_segment_based_key(
    customer_id: str, segment: str, separator: str = "|"
) -> str:
    """
    Create a segment-based compound key for user segment distribution.

    Useful when different customer segments (free/premium/enterprise) have
    different activity patterns.

    Args:
        customer_id: Customer identifier.
        segment: Customer segment (e.g., "free", "premium", "enterprise").
        separator: Separator character (default: "|").

    Returns:
        Compound key combining customer_id and segment.

    Example:
        >>> create_segment_based_key("customer-123", "premium")
        'customer-123|premium'

    Use Case:
        When premium users generate more events than free users, this prevents
        all premium user events from clustering in the same partitions.
    """
    return create_compound_key(customer_id, segment, separator=separator)


def hash_partition_key(*parts: str, hash_size: int = 8) -> str:
    """
    Create a hash-based partition key from multiple attributes.

    This creates a deterministic hash from multiple attributes, ensuring:
    - Consistent partitioning for the same inputs
    - Even distribution across partitions
    - Reduced key size compared to concatenation

    Args:
        *parts: Variable number of string parts to hash.
        hash_size: Length of the hash output (default: 8 characters).

    Returns:
        Hexadecimal hash string.

    Example:
        >>> hash_partition_key("customer-123", "us-west", "premium")
        'a7f2c3d1'

    Use Case:
        When you have many attributes and want compact, evenly-distributed keys.
    """
    combined = "|".join(str(part) for part in parts if part)
    hash_object = hashlib.sha256(combined.encode("utf-8"))
    return hash_object.hexdigest()[:hash_size]


def create_time_bucketed_key(
    customer_id: str, time_bucket: str, separator: str = "|"
) -> str:
    """
    Create a time-bucketed compound key for temporal distribution.

    Useful for time-series data where you want to distribute events from
    the same customer across different partitions based on time.

    Args:
        customer_id: Customer identifier.
        time_bucket: Time bucket (e.g., "2024-12-26-10" for hour buckets).
        separator: Separator character (default: "|").

    Returns:
        Compound key combining customer_id and time bucket.

    Example:
        >>> create_time_bucketed_key("customer-123", "2024-12-26-10")
        'customer-123|2024-12-26-10'

    Use Case:
        Time-series analytics where you want to process different time periods
        in parallel while maintaining order within each time bucket.
    """
    return create_compound_key(customer_id, time_bucket, separator=separator)


def create_multi_tenant_key(
    tenant_id: str, customer_id: str, separator: str = "|"
) -> str:
    """
    Create a multi-tenant compound key.

    Ensures that customers from the same tenant are distributed across
    partitions while maintaining order per customer within a tenant.

    Args:
        tenant_id: Tenant/organization identifier.
        customer_id: Customer identifier within the tenant.
        separator: Separator character (default: "|").

    Returns:
        Compound key combining tenant_id and customer_id.

    Example:
        >>> create_multi_tenant_key("acme-corp", "customer-123")
        'acme-corp|customer-123'

    Use Case:
        SaaS applications with multiple tenants where you want to prevent
        one large tenant from dominating specific partitions.
    """
    return create_compound_key(tenant_id, customer_id, separator=separator)


def calculate_partition(key: str, num_partitions: int) -> int:
    """
    Calculate the partition number for a given key.

    This mimics Kafka's default partitioning logic using murmur2 hash,
    but uses Python's hash for simplicity.

    Args:
        key: The partition key.
        num_partitions: Total number of partitions.

    Returns:
        Partition number (0 to num_partitions-1).

    Example:
        >>> calculate_partition("customer-123|us-west", 3)
        2
    """
    # Python's hash is platform-dependent but sufficient for testing
    key_hash = abs(hash(key))
    return key_hash % num_partitions


def analyze_distribution(keys: list[str], num_partitions: int) -> dict:
    """
    Analyze how keys would be distributed across partitions.

    Useful for testing and validating your partitioning strategy.

    Args:
        keys: List of partition keys.
        num_partitions: Total number of partitions.

    Returns:
        Dictionary with distribution statistics.

    Example:
        >>> keys = ["customer-1|us-west", "customer-2|eu", ...]
        >>> analyze_distribution(keys, 3)
        {
            'total_keys': 100,
            'num_partitions': 3,
            'partition_counts': {0: 33, 1: 34, 2: 33},
            'min_partition_size': 33,
            'max_partition_size': 34,
            'imbalance_ratio': 1.03
        }
    """
    partition_counts = {}

    for key in keys:
        partition = calculate_partition(key, num_partitions)
        partition_counts[partition] = partition_counts.get(partition, 0) + 1

    # Fill in missing partitions with 0
    for i in range(num_partitions):
        if i not in partition_counts:
            partition_counts[i] = 0

    counts = list(partition_counts.values())
    min_count = min(counts) if counts else 0
    max_count = max(counts) if counts else 0
    imbalance_ratio = max_count / min_count if min_count > 0 else float("inf")

    return {
        "total_keys": len(keys),
        "num_partitions": num_partitions,
        "partition_counts": partition_counts,
        "min_partition_size": min_count,
        "max_partition_size": max_count,
        "imbalance_ratio": imbalance_ratio,
        "is_balanced": imbalance_ratio <= 1.2,  # Within 20% is considered balanced
    }

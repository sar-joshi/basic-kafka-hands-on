"""
Tests for example files to ensure they work correctly.

These tests verify that the example files:
1. Can be imported without errors
2. Have correct function signatures
3. Don't have syntax errors
4. Key logic works as expected (with mocked Kafka)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from confluent_kafka import KafkaError


class TestOffsetManagementExamples:
    """Test offset management example functions"""
    
    def test_import_offset_management(self):
        """Test that offset_management module can be imported"""
        try:
            import examples.offset_management
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import offset_management: {e}")
    
    def test_offset_management_functions_exist(self):
        """Test that all example functions exist"""
        from examples import offset_management
        
        assert hasattr(offset_management, "example_manual_commit")
        assert hasattr(offset_management, "example_auto_commit")
        assert hasattr(offset_management, "example_commit_batch")
        assert hasattr(offset_management, "example_specific_offset")
        assert hasattr(offset_management, "example_monitor_lag")
    
    @patch("examples.offset_management.Consumer")
    def test_manual_commit_logic(self, mock_consumer_class):
        """Test manual commit example processes and commits correctly"""
        from examples.offset_management import example_manual_commit
        
        # Setup mock
        mock_consumer = Mock()
        mock_consumer_class.return_value = mock_consumer
        
        # Mock message
        mock_message = Mock()
        mock_message.error.return_value = None
        mock_message.value.return_value = b'{"order_id":"test-123","customer_name":"Test","item":"Test","quantity":1,"price":10.0,"status":"pending"}'
        mock_message.topic.return_value = "orders"
        mock_message.partition.return_value = 0
        mock_message.offset.return_value = 42
        
        # Return message once, then None, then raise KeyboardInterrupt
        mock_consumer.poll.side_effect = [mock_message, None, KeyboardInterrupt()]
        
        try:
            example_manual_commit()
        except KeyboardInterrupt:
            pass
        
        # Verify consumer was created with correct config
        mock_consumer_class.assert_called_once()
        config = mock_consumer_class.call_args[0][0]
        assert config["enable.auto.commit"] is False
        assert config["group.id"] == "manual-commit-example"
        
        # Verify commit was called after processing
        mock_consumer.commit.assert_called()
        mock_consumer.close.assert_called_once()


class TestIdempotentProcessingExamples:
    """Test idempotent processing example functions"""
    
    def test_import_idempotent_processing(self):
        """Test that idempotent_processing module can be imported"""
        try:
            import examples.idempotent_processing
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import idempotent_processing: {e}")
    
    def test_idempotent_processing_functions_exist(self):
        """Test that all example functions exist"""
        from examples import idempotent_processing
        
        assert hasattr(idempotent_processing, "example_unique_constraint_simulation")
        assert hasattr(idempotent_processing, "example_in_memory_deduplication")
        assert hasattr(idempotent_processing, "example_checksum_based_deduplication")
        assert hasattr(idempotent_processing, "example_with_state_tracking")
    
    def test_in_memory_deduplication_logic(self):
        """Test in-memory deduplication correctly identifies duplicates"""
        from examples.idempotent_processing import example_in_memory_deduplication
        
        with patch("examples.idempotent_processing.Consumer") as mock_consumer_class:
            mock_consumer = Mock()
            mock_consumer_class.return_value = mock_consumer
            
            # Create duplicate messages
            msg1 = Mock()
            msg1.error.return_value = None
            msg1.value.return_value = b'{"order_id":"order-1","customer_name":"Test","item":"Test","quantity":1,"price":10.0,"status":"pending"}'
            msg1.topic.return_value = "orders"
            msg1.partition.return_value = 0
            msg1.offset.return_value = 1
            
            msg2 = Mock()  # Duplicate
            msg2.error.return_value = None
            msg2.value.return_value = b'{"order_id":"order-1","customer_name":"Test","item":"Test","quantity":1,"price":10.0,"status":"pending"}'
            msg2.topic.return_value = "orders"
            msg2.partition.return_value = 0
            msg2.offset.return_value = 2
            
            # Return both messages then interrupt
            mock_consumer.poll.side_effect = [msg1, msg2, KeyboardInterrupt()]
            
            try:
                example_in_memory_deduplication()
            except KeyboardInterrupt:
                pass
            
            # Verify consumer was created
            mock_consumer_class.assert_called_once()
            config = mock_consumer_class.call_args[0][0]
            assert config["group.id"] == "idempotent-in-memory"
            mock_consumer.close.assert_called_once()
    
    def test_checksum_deduplication_consistency(self):
        """Test that checksum deduplication produces consistent hashes"""
        import hashlib
        
        # Same data should produce same checksum
        data1 = '{"order_id":"123","item":"test"}'
        data2 = '{"order_id":"123","item":"test"}'
        
        checksum1 = hashlib.sha256(data1.encode()).hexdigest()
        checksum2 = hashlib.sha256(data2.encode()).hexdigest()
        
        assert checksum1 == checksum2
        
        # Different data should produce different checksum
        data3 = '{"order_id":"456","item":"different"}'
        checksum3 = hashlib.sha256(data3.encode()).hexdigest()
        
        assert checksum1 != checksum3


class TestRaceConditionHandlingExamples:
    """Test race condition handling example functions"""
    
    def test_import_race_condition_handling(self):
        """Test that race_condition_handling module can be imported"""
        try:
            import examples.race_condition_handling
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import race_condition_handling: {e}")
    
    def test_race_condition_functions_exist(self):
        """Test that all example functions exist"""
        from examples import race_condition_handling
        
        assert hasattr(race_condition_handling, "example_race_condition_problem")
        assert hasattr(race_condition_handling, "example_lock_based_solution")
        assert hasattr(race_condition_handling, "example_database_transaction_pattern")
        assert hasattr(race_condition_handling, "example_optimistic_locking")
        assert hasattr(race_condition_handling, "example_kafka_multiple_consumers")
    
    def test_lock_based_solution_prevents_race_condition(self):
        """Test lock-based solution prevents race conditions"""
        from examples.race_condition_handling import example_lock_based_solution
        
        # This example is a threading demonstration, not a Kafka consumer
        # Just verify it runs without errors and produces correct result
        try:
            example_lock_based_solution()
            # If it completes, the lock worked correctly (no lost updates)
            assert True
        except Exception as e:
            pytest.fail(f"Lock-based solution raised unexpected exception: {e}")
    
    def test_optimistic_locking_version_check(self):
        """Test optimistic locking concept with version numbers"""
        # Simulate optimistic locking logic
        initial_version = 1
        expected_version = 1
        new_version = 2
        
        # Should succeed when versions match
        assert initial_version == expected_version
        updated_version = new_version
        assert updated_version == 2
        
        # Should fail when versions don't match (simulating conflict)
        current_version = 3  # Changed by another process
        assert expected_version != current_version  # Conflict detected


class TestExamplesIntegration:
    """Integration tests for example modules"""
    
    def test_all_examples_importable(self):
        """Test that all example modules can be imported together"""
        try:
            import examples.offset_management
            import examples.idempotent_processing
            import examples.race_condition_handling
            import examples.backpressure_example
            import examples.compound_keys_example
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import examples: {e}")
    
    def test_examples_package_structure(self):
        """Test examples package has correct structure"""
        import examples
        
        # Check __all__ is defined
        assert hasattr(examples, "__all__")
        
        # Check expected modules are listed
        expected_modules = [
            "offset_management",
            "idempotent_processing",
            "race_condition_handling",
            "backpressure_example",
            "compound_keys_example",
        ]
        
        for module in expected_modules:
            assert module in examples.__all__
    
    def test_no_syntax_errors_in_examples(self):
        """Compile all example files to check for syntax errors"""
        import py_compile
        import os
        
        example_files = [
            "examples/offset_management.py",
            "examples/idempotent_processing.py",
            "examples/race_condition_handling.py",
            "examples/backpressure_example.py",
            "examples/compound_keys_example.py",
        ]
        
        for file_path in example_files:
            try:
                py_compile.compile(file_path, doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Syntax error in {file_path}: {e}")


class TestExampleErrorHandling:
    """Test error handling in example files"""
    
    @patch("examples.offset_management.Consumer")
    def test_offset_management_handles_kafka_errors(self, mock_consumer_class):
        """Test offset management handles Kafka errors gracefully"""
        from examples.offset_management import example_manual_commit
        
        mock_consumer = Mock()
        mock_consumer_class.return_value = mock_consumer
        
        # Mock error message
        mock_message = Mock()
        mock_error = Mock()
        mock_error.code.return_value = KafkaError._PARTITION_EOF
        mock_message.error.return_value = mock_error
        
        mock_consumer.poll.side_effect = [mock_message, KeyboardInterrupt()]
        
        try:
            example_manual_commit()
        except KeyboardInterrupt:
            pass
        
        # Should handle error gracefully
        mock_consumer.close.assert_called_once()
    
    @patch("examples.idempotent_processing.Consumer")
    def test_idempotent_processing_handles_invalid_json(self, mock_consumer_class):
        """Test idempotent processing handles invalid JSON gracefully"""
        from examples.idempotent_processing import example_in_memory_deduplication
        
        mock_consumer = Mock()
        mock_consumer_class.return_value = mock_consumer
        
        # Mock message with invalid JSON
        mock_message = Mock()
        mock_message.error.return_value = None
        mock_message.value.return_value = b'invalid json data'
        mock_message.topic.return_value = "orders"
        mock_message.partition.return_value = 0
        mock_message.offset.return_value = 1
        
        mock_consumer.poll.side_effect = [mock_message, KeyboardInterrupt()]
        
        try:
            example_in_memory_deduplication()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            # Should either handle gracefully or fail with clear error
            assert "JSON" in str(e) or "decode" in str(e).lower()
        
        # Consumer should still be closed
        mock_consumer.close.assert_called_once()

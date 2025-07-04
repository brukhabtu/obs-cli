"""Unit tests for caching functionality."""

import pytest
import time
from unittest.mock import Mock, patch, ANY
from obs_cli.core.cache import CacheManager
from obs_cli.core.dataview import DataviewClient


class TestCacheManager:
    """Test CacheManager class."""
    
    def test_cache_hit(self):
        """Test cache hit scenario."""
        cache = CacheManager(ttl_seconds=60, max_size=10)
        
        # Store a value
        cache.set("test_key", {"result": "test_value"})
        
        # Retrieve should hit cache
        result = cache.get("test_key")
        assert result == {"result": "test_value"}
        assert cache._hits == 1
        assert cache._misses == 0
    
    def test_cache_miss(self):
        """Test cache miss scenario."""
        cache = CacheManager(ttl_seconds=60, max_size=10)
        
        # Try to get non-existent key
        result = cache.get("non_existent_key")
        assert result is None
        assert cache._hits == 0
        assert cache._misses == 1
    
    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = CacheManager(ttl_seconds=0.1, max_size=10)  # 100ms TTL
        
        # Store a value
        cache.set("test_key", {"result": "test_value"})
        
        # Immediate retrieval should hit
        result = cache.get("test_key")
        assert result == {"result": "test_value"}
        assert cache._hits == 1
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired now
        result = cache.get("test_key")
        assert result is None
        assert cache._misses == 1
    
    def test_cache_size_limit(self):
        """Test cache size limit enforcement."""
        cache = CacheManager(ttl_seconds=60, max_size=3)
        
        # Add 4 items (exceeding max_size)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1
        
        # Check that oldest was evicted
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
        assert len(cache._cache) == 3
    
    def test_cache_lru_order(self):
        """Test LRU (Least Recently Used) ordering."""
        cache = CacheManager(ttl_seconds=60, max_size=3)
        
        # Add 3 items
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it most recently used
        cache.get("key1")
        
        # Add a 4th item - should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # Still there
        assert cache.get("key4") == "value4"  # New item
    
    def test_cache_clear(self):
        """Test cache clearing."""
        cache = CacheManager(ttl_seconds=60, max_size=10)
        
        # Add some items
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")  # Generate some hits
        cache.get("non_existent")  # Generate a miss
        
        # Clear cache
        cache.clear()
        
        # Check everything is cleared
        assert len(cache._cache) == 0
        assert cache._hits == 0
        assert cache._misses == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = CacheManager(ttl_seconds=300, max_size=100)
        
        # Generate some activity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")  # Hit
        cache.get("key2")  # Hit
        cache.get("key3")  # Miss
        
        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 100
        assert stats["ttl_seconds"] == 300
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 2/3
    
    def test_make_key(self):
        """Test cache key generation."""
        cache = CacheManager()
        
        # Same query and vault should produce same key
        key1 = cache._make_key("LIST FROM \"folder\"", "/path/to/vault")
        key2 = cache._make_key("LIST FROM \"folder\"", "/path/to/vault")
        assert key1 == key2
        
        # Different query should produce different key
        key3 = cache._make_key("TABLE file.name", "/path/to/vault")
        assert key1 != key3
        
        # Different vault should produce different key
        key4 = cache._make_key("LIST FROM \"folder\"", "/different/vault")
        assert key1 != key4


class TestDataviewClientCaching:
    """Test DataviewClient caching integration."""
    
    @patch('obs_cli.core.dataview.DataviewClient._read_database')
    @patch('obs_cli.core.dataview.DataviewClient._write_database')
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_dataview_cache_integration(self, mock_sleep, mock_write, mock_read):
        """Test caching integration in DataviewClient."""
        # Create client with caching enabled
        client = DataviewClient(vault_path="/test/vault", enable_cache=True, cache_ttl=60)
        
        # First query - should hit database
        query = "LIST FROM \"folder\""
        query_id = None
        
        # Mock successful query execution
        def read_side_effect():
            nonlocal query_id
            if mock_read.call_count == 1:
                # Initial read - dataview is available
                return {'dataviewAvailable': True, 'dataviewQueries': {}}
            elif mock_read.call_count == 2:
                # After write - capture the query_id from the write call
                if mock_write.call_count > 0:
                    write_data = mock_write.call_args[0][0]
                    query_id = list(write_data['dataviewQueries'].keys())[0]
                return {'dataviewAvailable': True, 'dataviewQueries': {}}
            else:
                # Return success result
                return {
                    'dataviewAvailable': True,
                    'dataviewQueries': {
                        query_id: {
                            'query': query,
                            'status': 'success',
                            'result': {'values': ['file1', 'file2']}
                        }
                    }
                }
        
        mock_read.side_effect = read_side_effect
        
        # Execute query
        result1 = client.execute_dataview_query(query)
        assert result1['status'] == 'success'
        
        # Reset mocks to track new calls
        mock_read.reset_mock()
        mock_write.reset_mock()
        mock_read.side_effect = None  # Remove side effect
        
        # Second identical query - should hit cache
        result2 = client.execute_dataview_query(query)
        assert result2['status'] == 'success'
        assert result2['result'] == result1['result']
        
        # Should not have called database methods
        mock_read.assert_not_called()
        mock_write.assert_not_called()
        
        # Check cache stats in get_stats
        mock_read.return_value = {'stats': {}}  # Mock for get_stats
        stats = client.get_stats()
        assert 'cache' in stats
        assert stats['cache']['hits'] == 1
        assert stats['cache']['misses'] == 1  # First query was a miss
    
    def test_dataview_cache_disabled(self):
        """Test DataviewClient with cache disabled."""
        with patch('obs_cli.core.dataview.DataviewClient._read_database'):
            client = DataviewClient(vault_path="/test/vault", enable_cache=False)
            assert client.cache is None
            assert client.cache_enabled is False
            
            stats = client.get_stats()
            assert 'cache' not in stats
    
    @patch('obs_cli.core.dataview.DataviewClient._read_database')
    @patch('obs_cli.core.dataview.DataviewClient._write_database')
    def test_clear_dataview_cache_clears_memory_cache(self, mock_write, mock_read):
        """Test that clear_dataview_cache also clears the in-memory cache."""
        mock_read.return_value = {
            'dataviewQueries': {
                'query1': {'status': 'success'},
                'query2': {'status': 'success'},
                '_internal': {'status': 'success'}  # Should not be cleared
            }
        }
        
        client = DataviewClient(vault_path="/test/vault", enable_cache=True)
        
        # Add something to the cache
        client.cache.set("test_key", "test_value")
        assert len(client.cache._cache) == 1
        
        # Clear dataview cache
        count = client.clear_dataview_cache()
        assert count == 2  # Only non-internal queries
        
        # Check that in-memory cache was also cleared
        assert len(client.cache._cache) == 0
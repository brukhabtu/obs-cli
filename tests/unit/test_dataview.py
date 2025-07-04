"""Unit tests for DataviewClient."""
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open, MagicMock
import time

from obs_cli.core.dataview import DataviewClient
from obs_cli.core.cache import CacheManager
from obs_cli.core.exceptions import (
    VaultNotFoundError,
    DataviewNotAvailableError,
    QueryTimeoutError,
    DatabaseCorruptedError
)


class TestDataviewClient:
    """Test suite for DataviewClient."""

    def test_vault_path_auto_detection_success(self):
        """Test successful auto-detection of vault path."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            client = DataviewClient()
            
            assert client.vault_path == Path.home() / "storage/shared/Obsidian/Claude"
            assert client.db_path == client.vault_path / ".obsidian/plugins/obsidian-dataview-bridge/metadata.json"

    def test_vault_path_auto_detection_failure(self):
        """Test auto-detection failure when default vault doesn't exist."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            with pytest.raises(ValueError, match="Could not auto-detect vault path"):
                DataviewClient()

    def test_vault_path_explicit(self):
        """Test explicit vault path specification."""
        test_path = "/custom/vault/path"
        client = DataviewClient(vault_path=test_path)
        
        assert client.vault_path == Path(test_path)
        assert client.db_path == Path(test_path) / ".obsidian/plugins/obsidian-dataview-bridge/metadata.json"

    def test_database_file_not_found(self):
        """Test handling of missing database file."""
        with patch('pathlib.Path.exists') as mock_exists:
            # First call for vault path check, second for db file check
            mock_exists.side_effect = [True, False]
            
            client = DataviewClient()
            
            with pytest.raises(FileNotFoundError, match="Database file not found"):
                client._read_database()

    def test_database_file_loading_success(self):
        """Test successful database file loading."""
        test_data = {
            "version": "1.0.0",
            "lastUpdated": "2024-01-01T00:00:00Z",
            "dataviewAvailable": True,
            "notes": {}
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                client = DataviewClient()
                data = client._read_database()
                
                assert data == test_data

    def test_corrupted_database_handling(self):
        """Test handling of corrupted JSON database."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="invalid json")):
                client = DataviewClient()
                
                with pytest.raises(json.JSONDecodeError):
                    client._read_database()

    def test_write_database(self):
        """Test writing data to database file."""
        test_data = {"test": "data"}
        
        mock_file = mock_open()
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_file):
                client = DataviewClient()
                client._write_database(test_data)
                
                # Verify file was opened for writing
                mock_file.assert_called_with(client.db_path, 'w', encoding='utf-8')
                
                # Verify JSON was written
                handle = mock_file()
                written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
                assert json.loads(written_content) == test_data

    def test_get_stats(self):
        """Test getting database statistics."""
        test_data = {
            "stats": {
                "noteCount": 100,
                "tagCount": 50,
                "lastUpdated": "2024-01-01T12:00:00+00:00"
            }
        }
        
        with patch.object(DataviewClient, '_read_database', return_value=test_data):
            client = DataviewClient("/test/vault")
            stats = client.get_stats()
            
            assert stats["noteCount"] == 100
            assert stats["tagCount"] == 50
            assert "lastUpdatedHuman" in stats
            assert stats["lastUpdatedHuman"] == "2024-01-01 12:00:00"

    def test_get_stats_empty(self):
        """Test getting stats when no stats exist."""
        test_data = {}
        
        with patch.object(DataviewClient, '_read_database', return_value=test_data):
            client = DataviewClient("/test/vault")
            stats = client.get_stats()
            
            # When cache is enabled, stats will include cache stats
            assert 'cache' in stats
            assert stats['cache']['size'] == 0
            assert stats['cache']['hits'] == 0
            assert stats['cache']['misses'] == 0

    def test_execute_dataview_query_success(self):
        """Test successful Dataview query execution."""
        initial_data = {"dataviewAvailable": True}
        result_data = {
            "dataviewAvailable": True,
            "dataviewQueries": {
                "test_query_idxxx": {
                    "query": "LIST",
                    "status": "success",
                    "result": [{"file": "Note1.md"}, {"file": "Note2.md"}],
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }
        
        with patch.object(DataviewClient, '_read_database') as mock_read:
            # First call returns initial data, subsequent calls return result
            call_count = {'count': 0}
            def side_effect():
                call_count['count'] += 1
                if call_count['count'] == 1:
                    return initial_data
                return result_data
            mock_read.side_effect = side_effect
            
            with patch.object(DataviewClient, '_write_database') as mock_write:
                with patch('time.sleep'):  # Speed up test
                    with patch('hashlib.sha256') as mock_hash:
                        mock_hash.return_value.hexdigest.return_value = "test_query_id" + "x" * 50
                        
                        client = DataviewClient("/test/vault", enable_cache=False)
                        result = client.execute_dataview_query("LIST")
                        
                        assert result["status"] == "success"
                        assert result["result"] == [{"file": "Note1.md"}, {"file": "Note2.md"}]
                        
                        # Verify query was submitted
                        mock_write.assert_called_once()

    def test_execute_dataview_query_not_available(self):
        """Test query execution when Dataview is not available."""
        data = {"dataviewAvailable": False}
        
        with patch.object(DataviewClient, '_read_database', return_value=data):
            with patch.object(DataviewClient, '_write_database'):
                with patch('time.sleep'):
                    client = DataviewClient("/test/vault")
                    result = client.execute_dataview_query("LIST")
                    
                    assert result is None

    def test_execute_dataview_query_timeout(self):
        """Test query execution timeout."""
        data = {
            "dataviewAvailable": True,
            "dataviewQueries": {}
        }
        
        with patch.object(DataviewClient, '_read_database', return_value=data):
            with patch.object(DataviewClient, '_write_database'):
                with patch('time.sleep') as mock_sleep:
                    # Simulate timeout by not changing the data
                    client = DataviewClient("/test/vault")
                    result = client.execute_dataview_query("LIST")
                    
                    assert result["status"] == "timeout"
                    assert "Query execution timed out" in result["error"]
                    
                    # Verify we waited the expected time
                    assert mock_sleep.call_count >= 50  # 5 seconds / 0.1 interval

    def test_execute_dataview_query_error(self):
        """Test query execution with error result."""
        initial_data = {"dataviewAvailable": True}
        error_data = {
            "dataviewAvailable": True,
            "dataviewQueries": {
                "test_query_idxxx": {
                    "query": "INVALID QUERY",
                    "status": "error",
                    "error": "Invalid query syntax",
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }
        
        with patch.object(DataviewClient, '_read_database') as mock_read:
            # First call returns initial data, subsequent calls return error result
            call_count = {'count': 0}
            def side_effect():
                call_count['count'] += 1
                if call_count['count'] == 1:
                    return initial_data
                return error_data
            mock_read.side_effect = side_effect
            
            with patch.object(DataviewClient, '_write_database'):
                with patch('time.sleep'):
                    with patch('hashlib.sha256') as mock_hash:
                        mock_hash.return_value.hexdigest.return_value = "test_query_id" + "x" * 50
                        
                        client = DataviewClient("/test/vault", enable_cache=False)
                        result = client.execute_dataview_query("INVALID QUERY")
                        
                        assert result["status"] == "error"
                        assert result["error"] == "Invalid query syntax"

    def test_get_cached_dataview_results(self):
        """Test retrieving cached Dataview results."""
        test_data = {
            "dataviewQueries": {
                "query1": {"query": "LIST", "status": "success"},
                "query2": {"query": "TABLE", "status": "success"},
                "_check": {"query": "CHECK_DATAVIEW", "status": "success"}  # Internal query
            }
        }
        
        with patch.object(DataviewClient, '_read_database', return_value=test_data):
            client = DataviewClient("/test/vault")
            results = client.get_cached_dataview_results()
            
            assert len(results) == 2
            assert "query1" in results
            assert "query2" in results
            assert "_check" not in results  # Internal queries excluded

    def test_get_cached_dataview_results_empty(self):
        """Test getting cached results when none exist."""
        test_data = {}
        
        with patch.object(DataviewClient, '_read_database', return_value=test_data):
            client = DataviewClient("/test/vault")
            results = client.get_cached_dataview_results()
            
            assert results == {}

    def test_clear_dataview_cache(self):
        """Test clearing Dataview cache."""
        initial_data = {
            "dataviewQueries": {
                "query1": {"query": "LIST", "status": "success"},
                "query2": {"query": "TABLE", "status": "success"},
                "_check": {"query": "CHECK_DATAVIEW", "status": "success"}
            }
        }
        
        with patch.object(DataviewClient, '_read_database', return_value=initial_data):
            with patch.object(DataviewClient, '_write_database') as mock_write:
                client = DataviewClient("/test/vault")
                count = client.clear_dataview_cache()
                
                assert count == 2  # Only non-internal queries counted
                
                # Verify internal queries were preserved
                written_data = mock_write.call_args[0][0]
                assert "_check" in written_data["dataviewQueries"]
                assert "query1" not in written_data["dataviewQueries"]
                assert "query2" not in written_data["dataviewQueries"]

    def test_clear_dataview_cache_empty(self):
        """Test clearing cache when no queries exist."""
        test_data = {}
        
        with patch.object(DataviewClient, '_read_database', return_value=test_data):
            client = DataviewClient("/test/vault")
            count = client.clear_dataview_cache()
            
            assert count == 0

    def test_mobile_vault_detection(self):
        """Test mobile vault path detection."""
        mobile_path = Path.home() / "storage/shared/Obsidian/Claude"
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            client = DataviewClient()
            
            assert client.vault_path == mobile_path

    def test_query_result_formats(self):
        """Test different query result formats."""
        test_results = [
            {
                "dataviewQueries": {
                    "q1xxxxxxxxxxxxxx": {
                        "status": "success",
                        "result": [{"file": "Note.md"}],
                        "format": "table"
                    }
                }
            },
            {
                "dataviewQueries": {
                    "q1xxxxxxxxxxxxxx": {
                        "status": "success",
                        "result": {"key": "value"},
                        "format": "json"
                    }
                }
            },
            {
                "dataviewQueries": {
                    "q1xxxxxxxxxxxxxx": {
                        "status": "success",
                        "result": "csv,data\nrow1,val1",
                        "format": "csv"
                    }
                }
            }
        ]
        
        for result_data in test_results:
            with patch.object(DataviewClient, '_read_database') as mock_read:
                # First call returns initial data, subsequent calls return result
                call_count = {'count': 0}
                def side_effect():
                    call_count['count'] += 1
                    if call_count['count'] == 1:
                        return {"dataviewAvailable": True}
                    return result_data
                mock_read.side_effect = side_effect
                
                with patch.object(DataviewClient, '_write_database'):
                    with patch('time.sleep'):
                        with patch('hashlib.sha256') as mock_hash:
                            mock_hash.return_value.hexdigest.return_value = "q1" + "x" * 62 + "x" * 62
                            
                            client = DataviewClient("/test/vault")
                            result = client.execute_dataview_query("TEST")
                            
                            assert result["status"] == "success"
                            assert "result" in result

    def test_concurrent_access(self):
        """Test handling of concurrent database access."""
        # Simulate file being modified between read and write
        initial_data = {"dataviewAvailable": True}
        modified_data = {
            "dataviewAvailable": True,
            "dataviewQueries": {"other_query": {"status": "pending"}}
        }
        
        with patch.object(DataviewClient, '_read_database') as mock_read:
            # First call returns initial data, subsequent calls return modified data
            call_count = {'count': 0}
            def side_effect():
                call_count['count'] += 1
                if call_count['count'] == 1:
                    return initial_data
                return modified_data
            mock_read.side_effect = side_effect
            
            with patch.object(DataviewClient, '_write_database') as mock_write:
                with patch('time.sleep'):
                    client = DataviewClient("/test/vault", enable_cache=False)
                    result = client.execute_dataview_query("LIST")
                    
                    # Should still work despite concurrent modification
                    written_data = mock_write.call_args[0][0]
                    assert "dataviewQueries" in written_data

    def test_special_characters_in_query(self):
        """Test handling of special characters in queries."""
        special_queries = [
            'LIST WHERE contains(file.name, "test\'s file")',
            'TABLE file.name WHERE path = "folder/with spaces"',
            'LIST FROM #tag/with-dash',
            'TASK WHERE contains(text, "emoji 😀")'
        ]
        
        for query in special_queries:
            with patch.object(DataviewClient, '_read_database', return_value={"dataviewAvailable": True}):
                with patch.object(DataviewClient, '_write_database') as mock_write:
                    with patch('time.sleep'):
                        client = DataviewClient("/test/vault")
                        client.execute_dataview_query(query)
                        
                        # Verify query was written correctly
                        written_data = mock_write.call_args[0][0]
                        query_data = list(written_data["dataviewQueries"].values())[0]
                        assert query_data["query"] == query

    def test_very_large_results(self):
        """Test handling of very large query results."""
        large_result = [{"file": f"Note{i}.md"} for i in range(10000)]
        result_data = {
            "dataviewAvailable": True,
            "dataviewQueries": {
                "q1xxxxxxxxxxxxxx": {
                    "status": "success",
                    "result": large_result,
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }
        
        with patch.object(DataviewClient, '_read_database') as mock_read:
            # First call returns initial data, subsequent calls return result
            call_count = {'count': 0}
            def side_effect():
                call_count['count'] += 1
                if call_count['count'] == 1:
                    return {"dataviewAvailable": True}
                return result_data
            mock_read.side_effect = side_effect
            
            with patch.object(DataviewClient, '_write_database'):
                with patch('time.sleep'):
                    with patch('hashlib.sha256') as mock_hash:
                        mock_hash.return_value.hexdigest.return_value = "q1" + "x" * 62
                        
                        client = DataviewClient("/test/vault", enable_cache=False)
                        result = client.execute_dataview_query("LIST")
                        
                        assert result["status"] == "success"
                        assert len(result["result"]) == 10000

    def test_empty_database(self):
        """Test handling of empty database file."""
        with patch.object(DataviewClient, '_read_database', return_value={}):
            client = DataviewClient("/test/vault")
            
            # Should handle gracefully
            stats = client.get_stats()
            # Will have cache stats
            assert 'cache' in stats
            
            results = client.get_cached_dataview_results()
            assert results == {}
            
            count = client.clear_dataview_cache()
            assert count == 0

    def test_cache_enabled_by_default(self):
        """Test that cache is enabled by default."""
        with patch('pathlib.Path.exists', return_value=True):
            client = DataviewClient()
            assert client.cache_enabled is True
            assert client.cache is not None
            assert isinstance(client.cache, CacheManager)

    def test_cache_disabled(self):
        """Test disabling cache."""
        client = DataviewClient("/test/vault", enable_cache=False)
        assert client.cache_enabled is False
        assert client.cache is None

    def test_query_caching(self):
        """Test that query results are cached."""
        initial_data = {"dataviewAvailable": True}
        result_data = {
            "dataviewAvailable": True,
            "dataviewQueries": {
                "q1xxxxxxxxxxxxxx": {
                    "query": "LIST",
                    "status": "success",
                    "result": [{"file": "Note1.md"}],
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }
        
        with patch.object(DataviewClient, '_read_database') as mock_read:
            # First call returns initial data, subsequent calls return result
            call_count = {'count': 0}
            def side_effect():
                call_count['count'] += 1
                if call_count['count'] <= 2:
                    return initial_data
                return result_data
            mock_read.side_effect = side_effect
            
            with patch.object(DataviewClient, '_write_database'):
                with patch('time.sleep'):
                    with patch('hashlib.sha256') as mock_hash:
                        mock_hash.return_value.hexdigest.return_value = "q1" + "x" * 62
                        
                        client = DataviewClient("/test/vault")
                        
                        # First query should hit the database
                        result1 = client.execute_dataview_query("LIST")
                        assert result1["status"] == "success"
                        
                        # Second query should come from cache
                        result2 = client.execute_dataview_query("LIST")
                        assert result2 == result1
                        
                        # Verify cache stats
                        stats = client.cache.get_stats()
                        assert stats["hits"] == 1
                        assert stats["misses"] == 1

    def test_cache_ttl(self):
        """Test cache TTL expiration."""
        client = DataviewClient("/test/vault", cache_ttl=1)  # 1 second TTL
        
        # Mock the cache to test TTL behavior
        with patch.object(client.cache, 'get') as mock_get:
            mock_get.return_value = None  # Simulate cache miss
            
            with patch.object(DataviewClient, '_read_database', return_value={"dataviewAvailable": False}):
                with patch.object(DataviewClient, '_write_database'):
                    with patch('time.sleep'):
                        result = client.execute_dataview_query("LIST")
                        assert result is None

    def test_cache_disabled_no_caching(self):
        """Test that caching doesn't occur when disabled."""
        initial_data = {"dataviewAvailable": True}
        result_data = {
            "dataviewAvailable": True,
            "dataviewQueries": {
                "q1xxxxxxxxxxxxxx": {
                    "query": "LIST",
                    "status": "success",
                    "result": [{"file": "Note1.md"}],
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
        }
        
        with patch.object(DataviewClient, '_read_database') as mock_read:
            # Provide enough responses for two queries
            # Each query needs: initial check + multiple poll reads
            mock_read.side_effect = [
                initial_data,  # First query - initial check
                result_data,   # First query - poll result
                initial_data,  # Second query - initial check 
                result_data,   # Second query - poll result
                result_data,   # Extra for any additional polls
                result_data,   # Extra for any additional polls
            ]
            
            with patch.object(DataviewClient, '_write_database'):
                with patch('time.sleep'):
                    with patch('hashlib.sha256') as mock_hash:
                        mock_hash.return_value.hexdigest.return_value = "q1" + "x" * 62
                        
                        client = DataviewClient("/test/vault", enable_cache=False)
                        
                        # Both queries should hit the database
                        result1 = client.execute_dataview_query("LIST")
                        result2 = client.execute_dataview_query("LIST")
                        
                        assert result1["status"] == "success"
                        assert result2["status"] == "success"
                        
                        # Should have called read_database 4 times total
                        assert mock_read.call_count == 4
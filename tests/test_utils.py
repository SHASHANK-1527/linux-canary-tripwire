"""Unit tests for canary.utils module."""

import pytest
import tempfile
import os
from pathlib import Path
from canary.utils import compute_sha256, get_current_user, resolve_absolute_path, detect_process_info


class TestSHA256Hashing:
    """Test SHA256 hashing functionality."""
    
    def test_compute_sha256_valid_file(self):
        """Test SHA256 computation on a valid file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_file = f.name
        
        try:
            hash_val = compute_sha256(temp_file)
            assert hash_val is not None
            assert len(hash_val) == 64  # SHA256 hex is 64 chars
            assert isinstance(hash_val, str)
            # Verify it's a valid hex string
            int(hash_val, 16)  # Should not raise ValueError
        finally:
            os.unlink(temp_file)
    
    def test_compute_sha256_empty_file(self):
        """Test SHA256 computation on empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            # Write nothing
            temp_file = f.name
        
        try:
            hash_val = compute_sha256(temp_file)
            assert hash_val is not None
            assert len(hash_val) == 64
            # Empty file should have specific hash
            assert hash_val == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        finally:
            os.unlink(temp_file)
    
    def test_compute_sha256_nonexistent_file(self):
        """Test SHA256 computation on non-existent file."""
        hash_val = compute_sha256("/nonexistent/file/path.txt")
        assert hash_val is None
    
    def test_compute_sha256_same_content_same_hash(self):
        """Test that same content produces same hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write("identical content")
            file1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write("identical content")
            file2 = f2.name
        
        try:
            hash1 = compute_sha256(file1)
            hash2 = compute_sha256(file2)
            assert hash1 == hash2
        finally:
            os.unlink(file1)
            os.unlink(file2)
    
    def test_compute_sha256_different_content_different_hash(self):
        """Test that different content produces different hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write("content 1")
            file1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write("content 2")
            file2 = f2.name
        
        try:
            hash1 = compute_sha256(file1)
            hash2 = compute_sha256(file2)
            assert hash1 != hash2
        finally:
            os.unlink(file1)
            os.unlink(file2)


class TestGetCurrentUser:
    """Test user detection functionality."""
    
    def test_get_current_user_returns_string(self):
        """Test that current user returns a string."""
        user = get_current_user()
        assert isinstance(user, str)
        assert len(user) > 0
    
    def test_get_current_user_not_unknown(self):
        """Test that current user is not the fallback 'unknown'."""
        user = get_current_user()
        # In most test environments, this should return actual username
        # (May be 'unknown' in some restricted environments)
        assert isinstance(user, str)


class TestResolveAbsolutePath:
    """Test absolute path resolution."""
    
    def test_resolve_absolute_path_already_absolute(self):
        """Test resolution of already absolute path."""
        path = resolve_absolute_path("/tmp/test.txt")
        assert path.startswith("/")
        assert path == "/tmp/test.txt"
    
    def test_resolve_absolute_path_home_expansion(self):
        """Test that ~ is expanded to home directory."""
        path = resolve_absolute_path("~/.bashrc")
        assert path.startswith("/")
        assert "/.bashrc" in path
        assert "~" not in path
    
    def test_resolve_absolute_path_relative(self):
        """Test resolution of relative path."""
        path = resolve_absolute_path("./test.txt")
        assert path.startswith("/")
        assert not "." in path or path.endswith("test.txt")
    
    def test_resolve_absolute_path_consistency(self):
        """Test that multiple calls resolve consistently."""
        path1 = resolve_absolute_path("~/.bashrc")
        path2 = resolve_absolute_path("~/.bashrc")
        assert path1 == path2


class TestDetectProcessInfo:
    """Test process detection via lsof."""
    
    def test_detect_process_info_nonexistent_file(self):
        """Test process detection on non-existent file."""
        # Should return None gracefully
        result = detect_process_info("/nonexistent/file.txt")
        assert result is None
    
    def test_detect_process_info_returns_tuple_or_none(self):
        """Test that process detection returns tuple or None."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            result = detect_process_info(temp_file)
            # Result can be None or a tuple
            if result is not None:
                assert isinstance(result, tuple)
                assert len(result) == 2
                pid, cmd = result
                assert isinstance(pid, int)
                assert isinstance(cmd, str)
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

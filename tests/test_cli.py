"""Unit tests for canary.cli module."""

import pytest
import sys
import tempfile
import os
import json
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock
from canary.cli import main, cmd_init, cmd_add, cmd_remove, cmd_list, cmd_set_webhook
from canary.config import CanaryConfig


class TestCLICommands:
    """Test CLI command functionality."""
    
    def test_cmd_init(self):
        """Test canary init command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock config directory
            with patch('canary.cli.get_config_dir', return_value=tmpdir):
                # Capture output
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    result = cmd_init(MagicMock())
                    assert result == 0
                    output = fake_out.getvalue()
                    assert "Initialized" in output or "initialized" in output
            
            # Verify files created
            assert Path(tmpdir).exists()
            assert (Path(tmpdir) / "config.json").exists()
            assert (Path(tmpdir) / "logs").exists()
    
    def test_cmd_add(self):
        """Test canary add command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('canary.cli.get_config_dir', return_value=tmpdir):
                # Create config first
                config = CanaryConfig(tmpdir)
                
                # Add file
                args = MagicMock()
                args.file = "/test/file.txt"
                
                with patch('sys.stdout', new=StringIO()):
                    result = cmd_add(args)
                    assert result == 0
                
                # Verify file was added
                config = CanaryConfig(tmpdir)
                assert "/test/file.txt" in config.get_monitored_files()
    
    def test_cmd_add_resolves_path(self):
        """Test that add resolves path to absolute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('canary.cli.get_config_dir', return_value=tmpdir):
                config = CanaryConfig(tmpdir)
                
                args = MagicMock()
                args.file = "~/.bashrc"
                
                with patch('sys.stdout', new=StringIO()):
                    result = cmd_add(args)
                    assert result == 0
                
                config = CanaryConfig(tmpdir)
                files = config.get_monitored_files()
                assert len(files) > 0
                # Should be absolute path
                assert files[0].startswith("/")
                assert "bashrc" in files[0]
    
    def test_cmd_remove(self):
        """Test canary remove command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('canary.cli.get_config_dir', return_value=tmpdir):
                # Add file first
                config = CanaryConfig(tmpdir)
                config.add_file("/test/file.txt")
                
                # Remove it
                args = MagicMock()
                args.file = "/test/file.txt"
                
                with patch('sys.stdout', new=StringIO()):
                    result = cmd_remove(args)
                    assert result == 0
                
                # Verify removal
                config = CanaryConfig(tmpdir)
                assert "/test/file.txt" not in config.get_monitored_files()
    
    def test_cmd_list(self):
        """Test canary list command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('canary.cli.get_config_dir', return_value=tmpdir):
                config = CanaryConfig(tmpdir)
                config.add_file("/test/file1.txt")
                config.add_file("/test/file2.txt")
                
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    result = cmd_list(MagicMock())
                    assert result == 0
                    output = fake_out.getvalue()
                    assert "/test/file1.txt" in output
                    assert "/test/file2.txt" in output
    
    def test_cmd_list_empty(self):
        """Test canary list with no monitored files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('canary.cli.get_config_dir', return_value=tmpdir):
                config = CanaryConfig(tmpdir)
                
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    result = cmd_list(MagicMock())
                    assert result == 0
                    output = fake_out.getvalue()
                    assert "No monitored files" in output or "no" in output.lower()
    
    def test_cmd_set_webhook(self):
        """Test canary set-webhook command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('canary.cli.get_config_dir', return_value=tmpdir):
                config = CanaryConfig(tmpdir)
                
                args = MagicMock()
                args.url = "https://example.com/webhook"
                
                with patch('sys.stdout', new=StringIO()):
                    result = cmd_set_webhook(args)
                    assert result == 0
                
                # Verify webhook was set
                config = CanaryConfig(tmpdir)
                assert config.get_webhook_url() == "https://example.com/webhook"
    
    def test_cmd_set_webhook_none(self):
        """Test clearing webhook with 'none'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('canary.cli.get_config_dir', return_value=tmpdir):
                config = CanaryConfig(tmpdir)
                config.set_webhook_url("https://example.com/webhook")
                
                args = MagicMock()
                args.url = "none"
                
                with patch('sys.stdout', new=StringIO()):
                    result = cmd_set_webhook(args)
                    assert result == 0
                
                # Verify webhook was cleared
                config = CanaryConfig(tmpdir)
                assert config.get_webhook_url() is None


class TestCLIMain:
    """Test main CLI entry point."""
    
    def test_main_help(self):
        """Test main with --help."""
        with patch('sys.argv', ['canary', '--help']):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with pytest.raises(SystemExit):
                    main()
                output = fake_out.getvalue()
                assert "usage" in output.lower() or "canary" in output.lower()
    
    def test_main_no_args(self):
        """Test main with no arguments."""
        with patch('sys.argv', ['canary']):
            with patch('sys.stdout', new=StringIO()):
                result = main()
                assert result == 0
    
    def test_main_init_command(self):
        """Test main with init command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('sys.argv', ['canary', 'init']):
                with patch('canary.cli.get_config_dir', return_value=tmpdir):
                    with patch('sys.stdout', new=StringIO()):
                        result = main()
                        assert result == 0
    
    def test_main_list_command(self):
        """Test main with list command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('sys.argv', ['canary', 'list']):
                with patch('canary.cli.get_config_dir', return_value=tmpdir):
                    config = CanaryConfig(tmpdir)
                    config.add_file("/test/file.txt")
                    
                    with patch('sys.stdout', new=StringIO()) as fake_out:
                        result = main()
                        assert result == 0
                        output = fake_out.getvalue()
                        assert "/test/file.txt" in output
    
    def test_main_add_command(self):
        """Test main with add command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('sys.argv', ['canary', 'add', '/test/file.txt']):
                with patch('canary.cli.get_config_dir', return_value=tmpdir):
                    with patch('sys.stdout', new=StringIO()):
                        result = main()
                        assert result == 0
    
    def test_main_unknown_command(self):
        """Test main with unknown command."""
        with patch('sys.argv', ['canary', 'unknown_command']):
            with patch('sys.stdout', new=StringIO()):
                # Unknown command goes to argparse subcommand
                # May raise or return error
                try:
                    result = main()
                except SystemExit:
                    pass  # argparse exits on unknown command


class TestCLIIntegration:
    """Integration tests for CLI."""
    
    def test_full_workflow_init_add_list(self):
        """Test complete workflow: init -> add -> list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('canary.cli.get_config_dir', return_value=tmpdir):
                # Init
                with patch('sys.stdout', new=StringIO()):
                    result = cmd_init(MagicMock())
                    assert result == 0
                
                # Add multiple files
                for i in range(3):
                    args = MagicMock()
                    args.file = f"/test/file{i}.txt"
                    with patch('sys.stdout', new=StringIO()):
                        result = cmd_add(args)
                        assert result == 0
                
                # List
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    result = cmd_list(MagicMock())
                    assert result == 0
                    output = fake_out.getvalue()
                    assert "file0.txt" in output
                    assert "file1.txt" in output
                    assert "file2.txt" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

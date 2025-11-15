"""Integration and unit tests for the demo functionality."""

import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestDemoConfiguration:
    """Test demo configuration and CLI arguments."""

    def test_demo_accepts_headless_argument(self) -> None:
        """Test that demo accepts --headless argument."""
        # This will be implemented to test CLI argument parsing
        from demo.demo import parse_arguments

        args = parse_arguments(["--headless"])
        assert args.headless is True

    def test_demo_accepts_speed_argument(self) -> None:
        """Test that demo accepts --speed argument."""
        from demo.demo import parse_arguments

        args = parse_arguments(["--speed", "fast"])
        assert args.speed == "fast"

    def test_demo_accepts_screenshots_argument(self) -> None:
        """Test that demo accepts --screenshots argument."""
        from demo.demo import parse_arguments

        args = parse_arguments(["--screenshots"])
        assert args.screenshots is True

    def test_demo_accepts_keep_db_argument(self) -> None:
        """Test that demo accepts --keep-db argument."""
        from demo.demo import parse_arguments

        args = parse_arguments(["--keep-db"])
        assert args.keep_db is True

    def test_demo_default_configuration(self) -> None:
        """Test demo default configuration values."""
        from demo.demo import parse_arguments

        args = parse_arguments([])
        assert args.headless is False
        assert args.speed == "normal"
        assert args.screenshots is False
        assert args.keep_db is False


class TestDemoScreenshots:
    """Test screenshot capture functionality."""

    def test_screenshot_directory_created(self) -> None:
        """Test that screenshot directory is created."""
        from demo.demo import ensure_screenshot_dir

        screenshot_dir = ensure_screenshot_dir()
        assert screenshot_dir.exists()
        assert screenshot_dir.is_dir()
        assert screenshot_dir.name == "demo_screenshots"

    def test_screenshot_capture(self) -> None:
        """Test screenshot capture with timestamp."""
        from demo.demo import capture_screenshot

        mock_page = Mock()
        screenshot_path = capture_screenshot(mock_page, "test_action")

        assert screenshot_path.suffix == ".png"
        assert "test_action" in screenshot_path.stem
        mock_page.screenshot.assert_called_once()

    def test_screenshot_naming_convention(self) -> None:
        """Test screenshot file naming includes timestamp and action."""
        from demo.demo import generate_screenshot_name

        name = generate_screenshot_name("search_items")
        assert "search_items" in name
        assert name.endswith(".png")


class TestDemoSummaryReport:
    """Test demo summary report generation."""

    def test_summary_report_creation(self) -> None:
        """Test that summary report is created with all sections."""
        from demo.demo import DemoReport

        report = DemoReport()
        report.add_action("Search", "success", "Searched for items")
        report.add_action("Add Item", "success", "Added demo item")

        summary = report.generate_summary()
        assert "Search" in summary
        assert "Add Item" in summary
        assert "Successful:" in summary

    def test_summary_report_tracks_failures(self) -> None:
        """Test that summary report tracks failed actions."""
        from demo.demo import DemoReport

        report = DemoReport()
        report.add_action("CSV Upload", "failed", "File not found")

        summary = report.generate_summary()
        assert "Failed:" in summary
        assert "CSV Upload" in summary

    def test_summary_report_calculates_statistics(self) -> None:
        """Test that summary report calculates success/failure stats."""
        from demo.demo import DemoReport

        report = DemoReport()
        report.add_action("Action 1", "success", "OK")
        report.add_action("Action 2", "success", "OK")
        report.add_action("Action 3", "failed", "Error")

        stats = report.get_statistics()
        assert stats["total"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
        assert stats["success_rate"] == pytest.approx(66.67, rel=0.1)


class TestDemoFlaskIntegration:
    """Test Flask app integration with demo."""

    def test_flask_startup_verification(self) -> None:
        """Test that Flask app startup is verified before demo."""
        from demo.demo import verify_flask_running

        # Mock successful connection
        with patch("demo.demo.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            assert verify_flask_running("http://127.0.0.1:5000") is True

    def test_flask_startup_failure_handling(self) -> None:
        """Test handling of Flask startup failure."""
        from demo.demo import verify_flask_running

        # Mock connection failure
        with patch("demo.demo.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            assert verify_flask_running("http://127.0.0.1:5000") is False

    def test_flask_startup_retry_logic(self) -> None:
        """Test Flask startup verification retries."""
        from demo.demo import wait_for_flask

        with patch("demo.demo.verify_flask_running") as mock_verify:
            # Fail first 2 times, succeed on 3rd
            mock_verify.side_effect = [False, False, True]
            result = wait_for_flask(max_retries=3, delay=0.1)
            assert result is True
            assert mock_verify.call_count == 3


class TestDemoDatabaseManagement:
    """Test database management for demo."""

    def test_demo_database_cleanup(self) -> None:
        """Test that demo database is cleaned up when requested."""
        from demo.demo import cleanup_demo_database

        demo_db = Path("demo.db")
        demo_db.touch()  # Create dummy file

        cleanup_demo_database()
        assert not demo_db.exists()

    def test_demo_database_persistence(self) -> None:
        """Test that demo database persists when keep_db is True."""
        from demo.demo import DemoRunner

        demo_db = Path("demo.db")
        demo_db.touch()

        runner = DemoRunner(keep_db=True)
        runner.cleanup()
        assert demo_db.exists()

        # Cleanup for next test
        demo_db.unlink()


class TestDemoSpeedModes:
    """Test different speed modes for demo."""

    def test_speed_mode_delay_calculation(self) -> None:
        """Test that speed modes calculate correct delays."""
        from demo.demo import get_speed_delay

        assert get_speed_delay("fast") < get_speed_delay("normal")
        assert get_speed_delay("normal") < get_speed_delay("slow")

    def test_slow_mode_delay(self) -> None:
        """Test slow mode delay value."""
        from demo.demo import get_speed_delay

        delay = get_speed_delay("slow")
        assert delay == 2.0

    def test_fast_mode_delay(self) -> None:
        """Test fast mode delay value."""
        from demo.demo import get_speed_delay

        delay = get_speed_delay("fast")
        assert delay == 0.3

    def test_normal_mode_delay(self) -> None:
        """Test normal mode delay value."""
        from demo.demo import get_speed_delay

        delay = get_speed_delay("normal")
        assert delay == 1.0


class TestDemoPlaywrightIntegration:
    """Test Playwright integration in demo."""

    def test_browser_launch_configuration_headless(self) -> None:
        """Test browser launches in headless mode when configured."""
        from demo.demo import get_browser_config

        config = get_browser_config(headless=True, speed="fast")
        assert config["headless"] is True

    def test_browser_launch_configuration_headed(self) -> None:
        """Test browser launches in headed mode by default."""
        from demo.demo import get_browser_config

        config = get_browser_config(headless=False, speed="normal")
        assert config["headless"] is False
        assert "slow_mo" in config

    def test_browser_slow_mo_configuration(self) -> None:
        """Test browser slow_mo is set based on speed."""
        from demo.demo import get_browser_config

        config_fast = get_browser_config(headless=False, speed="fast")
        config_slow = get_browser_config(headless=False, speed="slow")

        assert config_fast["slow_mo"] < config_slow["slow_mo"]


class TestDemoErrorHandling:
    """Test error handling in demo."""

    def test_demo_handles_flask_startup_failure(self) -> None:
        """Test demo handles Flask startup failure gracefully."""
        from demo.demo import DemoRunner

        with patch("demo.demo.wait_for_flask") as mock_wait:
            mock_wait.return_value = False

            runner = DemoRunner()
            with pytest.raises(RuntimeError, match="Flask failed to start"):
                runner.start_flask()

    def test_demo_handles_browser_launch_failure(self) -> None:
        """Test demo handles browser launch failure."""
        from demo.demo import DemoRunner

        with patch("demo.demo.sync_playwright") as mock_pw:
            # Mock the context manager and chromium launch
            mock_context = MagicMock()
            mock_chromium = MagicMock()
            mock_error = RuntimeError("Browser not found")
            mock_chromium.launch.side_effect = mock_error
            mock_context.__enter__.return_value.chromium = mock_chromium
            mock_pw.return_value = mock_context

            runner = DemoRunner()
            with pytest.raises(RuntimeError):
                runner.run()

    def test_demo_cleanup_on_error(self) -> None:
        """Test that demo cleans up resources on error."""
        from demo.demo import DemoRunner

        runner = DemoRunner(keep_db=False)
        demo_db = Path("demo.db")
        demo_db.touch()

        # Test cleanup removes database
        runner.cleanup()

        assert not demo_db.exists()

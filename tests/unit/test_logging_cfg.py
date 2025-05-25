"""Unit tests for logging configuration."""

import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from classifier_router.config.logging_cfg import (
    setup_logging,
    get_logger,
    ClassifierLoggerMixin,
    _get_logging_config,
)


class TestLoggingConfiguration:
    """Test cases for logging configuration functions."""

    def test_setup_logging_default_config(self):
        """Test setup_logging with default configuration."""
        setup_logging()

        # Verify logger is configured
        logger = logging.getLogger("classifier_router")
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logging_debug_level(self):
        """Test setup_logging with DEBUG level."""
        setup_logging(level="DEBUG")

        logger = logging.getLogger("classifier_router")
        assert logger.level == logging.DEBUG

    def test_setup_logging_with_file(self):
        """Test setup_logging with file logging."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file = tmp_file.name

        try:
            setup_logging(level="INFO", log_file=log_file)

            # Verify file handler is added
            logger = logging.getLogger("classifier_router")
            file_handlers = [
                h
                for h in logger.handlers
                if isinstance(h, logging.handlers.RotatingFileHandler)
            ]
            assert len(file_handlers) > 0

            # Test logging to file
            logger.info("Test message")

            # Verify file was created and contains log
            assert os.path.exists(log_file)
            with open(log_file, "r") as f:
                content = f.read()
                assert "Test message" in content

        finally:
            # Cleanup
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_setup_logging_no_console(self):
        """Test setup_logging with console disabled."""
        setup_logging(enable_console=False, log_file=None)

        logger = logging.getLogger("classifier_router")
        console_handlers = [
            h for h in logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        # Should have no console handlers when disabled and no file specified
        assert len(console_handlers) == 0

    def test_get_logging_config_structured_format(self):
        """Test _get_logging_config with structured format."""
        config = _get_logging_config("INFO", "structured", True, None)

        assert config["version"] == 1
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config

        # Check structured format
        formatter = config["formatters"]["default"]
        assert "%(asctime)s" in formatter["format"]
        assert "%(levelname)" in formatter["format"]
        assert "%(funcName)s:%(lineno)d" in formatter["format"]

    def test_get_logging_config_simple_format(self):
        """Test _get_logging_config with simple format."""
        config = _get_logging_config("DEBUG", "simple", True, None)

        formatter = config["formatters"]["default"]
        assert formatter["format"] == "%(levelname)s - %(name)s - %(message)s"

    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"


class TestClassifierLoggerMixin:
    """Test cases for ClassifierLoggerMixin."""

    class TestComponent(ClassifierLoggerMixin):
        """Test component using the mixin."""

        pass

    def test_logger_property(self):
        """Test logger property creates logger correctly."""
        component = self.TestComponent()
        logger = component.logger

        assert isinstance(logger, logging.Logger)
        # Logger name should be based on module
        assert "test_logging_cfg" in logger.name

    def test_logger_property_caching(self):
        """Test logger property caches the logger instance."""
        component = self.TestComponent()
        logger1 = component.logger
        logger2 = component.logger

        # Should return the same instance
        assert logger1 is logger2

    def test_log_detection_start(self, caplog):
        """Test log_detection_start method."""
        component = self.TestComponent()

        with caplog.at_level(logging.DEBUG):
            component.log_detection_start(1500, "test_detector")

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "DEBUG"
        assert "Starting detection" in record.message
        assert record.detector == "test_detector"
        assert record.text_length == 1500
        assert record.operation == "detect"

    def test_log_detection_result(self, caplog):
        """Test log_detection_result method."""
        component = self.TestComponent()

        with caplog.at_level(logging.DEBUG):
            component.log_detection_result("test_detector", True, "LEASE", 25.5)

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "DEBUG"
        assert "Detection completed" in record.message
        assert record.detector == "test_detector"
        assert record.detected is True
        assert record.value == "LEASE"
        assert record.processing_time_ms == 25.5

    def test_log_detection_result_without_timing(self, caplog):
        """Test log_detection_result method without timing info."""
        component = self.TestComponent()

        with caplog.at_level(logging.DEBUG):
            component.log_detection_result("test_detector", False, "")

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert not hasattr(record, "processing_time_ms")

    def test_log_error(self, caplog):
        """Test log_error method."""
        component = self.TestComponent()
        error = ValueError("Test error message")
        context = {"detector": "test_detector", "text_length": 1000}

        with caplog.at_level(logging.ERROR):
            component.log_error(error, context)

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "ERROR"
        assert "Error occurred: Test error message" in record.message
        assert record.error_type == "ValueError"
        assert record.error_message == "Test error message"
        assert record.context == context


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def test_logging_setup_and_usage(self):
        """Test complete logging setup and usage flow."""
        # Setup logging
        setup_logging(level="DEBUG", format_type="simple")

        # Get logger and test logging
        logger = get_logger("test.integration")

        # Verify logger is configured correctly
        assert (
            logger.level == logging.DEBUG or logger.getEffectiveLevel() == logging.DEBUG
        )

        # Test that logger has handlers
        root_logger = logging.getLogger("classifier_router")
        assert len(root_logger.handlers) > 0

    def test_mixin_with_configured_logging(self):
        """Test ClassifierLoggerMixin with configured logging."""
        setup_logging(level="DEBUG", format_type="structured")

        class TestDetector(ClassifierLoggerMixin):
            def __init__(self):
                self.detection_calls = []

            def detect(self, text: str) -> bool:
                self.log_detection_start(len(text), "test_detector")
                # Simulate detection logic
                result = "LEASE" in text.upper()
                self.log_detection_result(
                    "test_detector", result, "LEASE" if result else ""
                )
                self.detection_calls.append((len(text), result))
                return result

        detector = TestDetector()
        result = detector.detect("This is a LEASE agreement")

        # Verify the detection worked
        assert result is True
        assert len(detector.detection_calls) == 1
        assert detector.detection_calls[0] == (25, True)

        # Verify logger is properly configured
        assert hasattr(detector, "_logger")
        assert isinstance(detector.logger, logging.Logger)

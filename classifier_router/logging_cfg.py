"""Logging configuration for the classifier router microservice."""

import logging
import logging.config
import sys
from typing import Dict, Any, Optional


def setup_logging(
    level: str = "INFO",
    format_type: str = "structured",
    enable_console: bool = True,
    log_file: Optional[str] = None,
) -> None:
    """Configure logging for the classifier router microservice.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format type ('structured' or 'simple')
        enable_console: Whether to enable console logging
        log_file: Optional file path for file logging

    Examples:
        # Development setup
        setup_logging(level="DEBUG", format_type="simple")

        # Production setup
        setup_logging(level="INFO", format_type="structured", log_file="/var/log/classifier.log")
    """
    config = _get_logging_config(level, format_type, enable_console, log_file)
    logging.config.dictConfig(config)

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "level": level,
            "format_type": format_type,
            "console_enabled": enable_console,
            "file_logging": log_file is not None,
        },
    )


def _get_logging_config(
    level: str, format_type: str, enable_console: bool, log_file: Optional[str]
) -> Dict[str, Any]:
    """Generate logging configuration dictionary.

    Args:
        level: Logging level
        format_type: Format type ('structured' or 'simple')
        enable_console: Enable console handler
        log_file: Optional log file path

    Returns:
        Logging configuration dictionary
    """
    # Format configurations
    formats = {
        "structured": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s - %(name)s - %(message)s"},
    }

    # Base configuration
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": formats.get(format_type, formats["structured"])},
        "handlers": {},
        "loggers": {
            "classifier_router": {"level": level, "handlers": [], "propagate": False},
            "root": {"level": level, "handlers": []},
        },
    }

    # Console handler
    if enable_console:
        config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": "default",
            "stream": sys.stdout,
        }
        config["loggers"]["classifier_router"]["handlers"].append("console")
        config["loggers"]["root"]["handlers"].append("console")

    # File handler
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "default",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        }
        config["loggers"]["classifier_router"]["handlers"].append("file")
        config["loggers"]["root"]["handlers"].append("file")

    return config


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing document", extra={"doc_id": "123", "text_length": 1500})
    """
    return logging.getLogger(name)


class ClassifierLoggerMixin:
    """Mixin class to add logging capabilities to classifier components.

    Provides consistent logging methods with structured data for
    detector and router components.
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this component."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__module__)
        return self._logger

    def log_detection_start(self, text_length: int, detector_name: str) -> None:
        """Log the start of a detection operation.

        Args:
            text_length: Length of text being processed
            detector_name: Name of the detector
        """
        self.logger.debug(
            "Starting detection",
            extra={
                "detector": detector_name,
                "text_length": text_length,
                "operation": "detect",
            },
        )

    def log_detection_result(
        self,
        detector_name: str,
        detected: bool,
        value: str,
        processing_time_ms: Optional[float] = None,
    ) -> None:
        """Log the result of a detection operation.

        Args:
            detector_name: Name of the detector
            detected: Whether detection was successful
            value: Detected value (if any)
            processing_time_ms: Optional processing time in milliseconds
        """
        extra_data = {
            "detector": detector_name,
            "detected": detected,
            "value": value,
            "operation": "detect_complete",
        }

        if processing_time_ms is not None:
            extra_data["processing_time_ms"] = processing_time_ms

        self.logger.debug("Detection completed", extra=extra_data)

    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log an error with context information.

        Args:
            error: The exception that occurred
            context: Additional context information
        """
        self.logger.error(
            f"Error occurred: {str(error)}",
            extra={
                "error_type": error.__class__.__name__,
                "error_message": str(error),
                "context": context,
            },
            exc_info=True,
        )

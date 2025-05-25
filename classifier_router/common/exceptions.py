"""Custom exceptions for the classifier router."""


class ClassifierError(Exception):
    """Base exception for classifier router errors."""

    pass


class ConfigError(ClassifierError):
    """Exception raised for configuration-related errors.

    This includes issues with:
    - Invalid configuration file format
    - Missing detector classes
    - Invalid detector class paths
    - Configuration validation failures
    """

    pass

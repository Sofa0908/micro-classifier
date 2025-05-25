"""Document Classifier and Router microservice package."""

__version__ = "0.1.0"

# Core classification components
from classifier_router.core.router import ClassifierRouter
from classifier_router.core.models import ClassificationResult
from classifier_router.core.factory import DetectorFactory

# Kafka integration components
from classifier_router.kafka.service import KafkaService
from classifier_router.kafka.processor import MessageProcessor
from classifier_router.kafka.schemas import (
    TextExtractionMessage,
    LLMRequestMessage,
    ClassificationMetadata,
)

# Configuration and settings
from classifier_router.config.settings import (
    settings,
    Settings,
    KafkaSettings,
    ApplicationSettings,
)

# Main application entry point
from classifier_router.main import main, run

__all__ = [
    # Core components
    "ClassifierRouter",
    "ClassificationResult",
    "DetectorFactory",
    # Kafka components
    "KafkaService",
    "MessageProcessor",
    "TextExtractionMessage",
    "LLMRequestMessage",
    "ClassificationMetadata",
    # Configuration
    "settings",
    "Settings",
    "KafkaSettings",
    "ApplicationSettings",
    # Application entry points
    "main",
    "run",
]

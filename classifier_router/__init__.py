"""Document Classifier and Router microservice package."""

__version__ = "0.1.0"

# Core classification components
from .router import ClassifierRouter
from .models import ClassificationResult
from .factory import DetectorFactory

# Kafka integration components
from .kafka_service import KafkaService
from .message_processor import MessageProcessor
from .schemas import TextExtractionMessage, LLMRequestMessage, ClassificationMetadata

# Configuration and settings
from .settings import settings, Settings, KafkaSettings, ApplicationSettings

# Main application entry point
from .main import main, run

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

"""Kafka integration components."""

from classifier_router.kafka.service import KafkaService
from classifier_router.kafka.processor import MessageProcessor
from classifier_router.kafka.schemas import (
    TextExtractionMessage,
    LLMRequestMessage,
    ClassificationMetadata,
)

__all__ = [
    "KafkaService",
    "MessageProcessor",
    "TextExtractionMessage",
    "LLMRequestMessage",
    "ClassificationMetadata",
]

"""Core classification components."""

from classifier_router.core.router import ClassifierRouter
from classifier_router.core.models import ClassificationResult
from classifier_router.core.factory import DetectorFactory

__all__ = [
    "ClassifierRouter",
    "ClassificationResult",
    "DetectorFactory",
]

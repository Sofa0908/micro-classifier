"""Data models for the classifier router."""

from dataclasses import dataclass
from typing import Dict, Set

from .detector.base import DetectionResult


@dataclass
class ClassificationResult:
    """Result from running multiple detectors on input text.

    Attributes:
        text_length: Length of the input text that was classified
        detector_results: Dictionary mapping detector names to their results
        successful_detectors: Set of detector names that ran successfully
        failed_detectors: Dict mapping detector names to their error messages
    """

    text_length: int
    detector_results: Dict[str, DetectionResult]
    successful_detectors: Set[str]
    failed_detectors: Dict[str, str]

    @property
    def has_detections(self) -> bool:
        """Check if any detector found a positive detection."""
        return any(result.detected for result in self.detector_results.values())

    @property
    def detected_values(self) -> Dict[str, str]:
        """Get all detected values from successful detectors."""
        return {
            name: result.value
            for name, result in self.detector_results.items()
            if name in self.successful_detectors and result.detected and result.value
        }

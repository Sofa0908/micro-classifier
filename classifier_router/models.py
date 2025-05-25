"""Data models for the classifier router."""

from dataclasses import dataclass
from typing import Dict, Set, Optional

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

    def get_output_by_type(
        self, detector_configs: Dict[str, str]
    ) -> Dict[str, Optional[str]]:
        """Map detector results by their output types.

        Args:
            detector_configs: Dict mapping detector names to their output_type

        Returns:
            Dict mapping output types to detected values (None if not detected)

        Example:
            detector_configs = {
                "lease_header_detector": "docType",
                "jurisdiction_detector": "jurisdiction"
            }

            Returns: {
                "docType": "lease",
                "jurisdiction": "CA"
            }
        """
        output_mapping = {}

        for detector_name, output_type in detector_configs.items():
            if detector_name in self.successful_detectors:
                result = self.detector_results.get(detector_name)
                if result and result.detected and result.value:
                    output_mapping[output_type] = result.value
                else:
                    output_mapping[output_type] = None
            else:
                output_mapping[output_type] = None

        return output_mapping

"""Core classification router that orchestrates multiple detectors."""

from dataclasses import dataclass
from typing import Dict, List, Set
import logging

from .factory import DetectorFactory
from .detector.base import DetectionResult
from .exceptions import ClassifierError


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


class ClassifierRouter:
    """Main classification router that orchestrates multiple detectors.

    The router loads detectors via the DetectorFactory and provides methods
    to run classification against input text. It handles detector failures
    gracefully and aggregates results from multiple detectors.
    """

    def __init__(self, config_path: str = "config/detector_config.json"):
        """Initialize the classifier router.

        Args:
            config_path: Path to the detector configuration file

        Raises:
            ClassifierError: If factory initialization fails
        """
        try:
            self.factory = DetectorFactory(config_path)
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            raise ClassifierError(f"Failed to initialize ClassifierRouter: {e}")

    def classify(self, text: str) -> ClassificationResult:
        """Run all available detectors against the input text.

        Args:
            text: Input text to classify

        Returns:
            Classification result with outcomes from all detectors

        Raises:
            ClassifierError: If text is empty or None
        """
        if not text or not text.strip():
            raise ClassifierError("Input text cannot be empty or None")

        # Get all available detector names
        available_detectors = [
            config.name for config in self.factory.list_available_detectors()
        ]

        return self.classify_with_detectors(text, available_detectors)

    def classify_with_detectors(
        self, text: str, detector_names: List[str]
    ) -> ClassificationResult:
        """Run specific detectors against the input text.

        Args:
            text: Input text to classify
            detector_names: List of detector names to run

        Returns:
            Classification result with outcomes from specified detectors

        Raises:
            ClassifierError: If text is empty, None, or detector_names is empty
        """
        if not text or not text.strip():
            raise ClassifierError("Input text cannot be empty or None")

        if not detector_names:
            raise ClassifierError("At least one detector name must be specified")

        detector_results: Dict[str, DetectionResult] = {}
        successful_detectors: Set[str] = set()
        failed_detectors: Dict[str, str] = {}

        for detector_name in detector_names:
            try:
                # Create detector instance
                detector = self.factory.create_detector(detector_name)

                # Run detection
                result = detector.detect(text)

                # Store results
                detector_results[detector_name] = result
                successful_detectors.add(detector_name)

                self.logger.debug(
                    f"Detector '{detector_name}' completed: detected={result.detected}, value='{result.value}'"
                )

            except Exception as e:
                error_msg = str(e)
                failed_detectors[detector_name] = error_msg

                self.logger.warning(f"Detector '{detector_name}' failed: {error_msg}")

        return ClassificationResult(
            text_length=len(text),
            detector_results=detector_results,
            successful_detectors=successful_detectors,
            failed_detectors=failed_detectors,
        )

    def get_available_detectors(self) -> List[str]:
        """Get list of available detector names.

        Returns:
            List of detector names that can be used for classification
        """
        return [config.name for config in self.factory.list_available_detectors()]

    def get_detector_info(self, detector_name: str) -> Dict[str, str]:
        """Get information about a specific detector.

        Args:
            detector_name: Name of the detector

        Returns:
            Dictionary with detector information (name, class_path, description)

        Raises:
            ClassifierError: If detector name is not found
        """
        try:
            config = self.factory.get_detector_config(detector_name)
            return {
                "name": config.name,
                "class_path": config.class_path,
                "description": config.description,
            }
        except Exception as e:
            raise ClassifierError(f"Failed to get detector info: {e}")

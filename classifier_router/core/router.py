"""Core classification router that orchestrates multiple detectors."""

from typing import Dict, List, Set
import logging
import time

from classifier_router.core.factory import DetectorFactory
from classifier_router.core.detector.base import DetectionResult
from classifier_router.common.exceptions import ClassifierError
from classifier_router.core.models import ClassificationResult
from classifier_router.config.logging_cfg import get_logger, ClassifierLoggerMixin


class ClassifierRouter(ClassifierLoggerMixin):
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

            # Log successful initialization
            available_detectors = self.get_available_detectors()
            self.logger.info(
                "ClassifierRouter initialized successfully",
                extra={
                    "config_path": config_path,
                    "detector_count": len(available_detectors),
                    "available_detectors": available_detectors,
                },
            )

        except Exception as e:
            # Log initialization failure before re-raising
            logger = get_logger(__name__)
            logger.error(
                "Failed to initialize ClassifierRouter",
                extra={
                    "config_path": config_path,
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
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
            self.logger.warning(
                "Classification attempted with empty text",
                extra={
                    "text_provided": text is not None,
                    "text_length": len(text) if text else 0,
                },
            )
            raise ClassifierError("Input text cannot be empty or None")

        # Get all available detector names
        available_detectors = [
            config.name for config in self.factory.list_available_detectors()
        ]

        self.logger.info(
            "Starting classification with all detectors",
            extra={
                "text_length": len(text),
                "detector_count": len(available_detectors),
                "detectors": available_detectors,
            },
        )

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
        start_time = time.time()

        # Input validation with logging
        if not text or not text.strip():
            self.logger.warning(
                "Classification attempted with empty text",
                extra={
                    "text_provided": text is not None,
                    "text_length": len(text) if text else 0,
                },
            )
            raise ClassifierError("Input text cannot be empty or None")

        if not detector_names:
            self.logger.warning("Classification attempted with empty detector list")
            raise ClassifierError("At least one detector name must be specified")

        # Use mixin method for high-level detection start
        self.log_detection_start(len(text), "classification_batch")

        detector_results: Dict[str, DetectionResult] = {}
        successful_detectors: Set[str] = set()
        failed_detectors: Dict[str, str] = {}

        for detector_name in detector_names:
            detector_start_time = time.time()

            try:
                # Use mixin method for individual detector start
                self.log_detection_start(len(text), detector_name)

                # Create detector instance
                detector = self.factory.create_detector(detector_name)

                # Run detection
                result = detector.detect(text)

                detector_time_ms = (time.time() - detector_start_time) * 1000

                # Store results
                detector_results[detector_name] = result
                successful_detectors.add(detector_name)

                # Use mixin method for detection result
                self.log_detection_result(
                    detector_name,
                    result.detected,
                    result.value or "",
                    round(detector_time_ms, 2),
                )

            except Exception as e:
                detector_time_ms = (time.time() - detector_start_time) * 1000
                error_msg = str(e)
                failed_detectors[detector_name] = error_msg

                # Use mixin method for error logging
                self.log_error(
                    e,
                    {
                        "detector": detector_name,
                        "processing_time_ms": round(detector_time_ms, 2),
                        "operation": "detect",
                    },
                )

        total_time_ms = (time.time() - start_time) * 1000

        result = ClassificationResult(
            text_length=len(text),
            detector_results=detector_results,
            successful_detectors=successful_detectors,
            failed_detectors=failed_detectors,
        )

        # Use mixin method for final classification result
        self.log_detection_result(
            "classification_batch",
            result.has_detections,
            f"completed: {len(result.detected_values)} detections",
            round(total_time_ms, 2),
        )

        return result

    def get_available_detectors(self) -> List[str]:
        """Get list of available detector names.

        Returns:
            List of detector names that can be used for classification
        """
        detectors = [config.name for config in self.factory.list_available_detectors()]
        self.logger.debug(
            "Retrieved available detectors",
            extra={"detector_count": len(detectors), "detectors": detectors},
        )
        return detectors

    def get_detector_info(self, detector_name: str) -> Dict[str, str]:
        """Get information about a specific detector.

        Args:
            detector_name: Name of the detector

        Returns:
            Dictionary with detector information (name, class_path, description, output_type)

        Raises:
            ClassifierError: If detector name is not found
        """
        try:
            config = self.factory.get_detector_config(detector_name)
            info = {
                "name": config.name,
                "class_path": config.class_path,
                "description": config.description,
                "output_type": config.output_type,
            }

            self.logger.debug(
                "Retrieved detector info",
                extra={
                    "detector": detector_name,
                    "class_path": config.class_path,
                    "output_type": config.output_type,
                },
            )

            return info

        except Exception as e:
            self.logger.error(
                "Failed to get detector info",
                extra={
                    "detector": detector_name,
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                },
            )
            raise ClassifierError(f"Failed to get detector info: {e}")

    def get_output_type_mapping(self) -> Dict[str, str]:
        """Get mapping of detector names to their output types.

        Returns:
            Dictionary mapping detector names to their output_type values

        Example:
            {
                "lease_header_detector": "docType",
                "jurisdiction_detector": "jurisdiction"
            }
        """
        mapping = {}
        for config in self.factory.list_available_detectors():
            mapping[config.name] = config.output_type

        self.logger.debug(
            "Retrieved output type mapping",
            extra={"mapping": mapping, "detector_count": len(mapping)},
        )

        return mapping

"""Unit tests for data models."""

from classifier_router.models import ClassificationResult
from classifier_router.detector.base import DetectionResult


class TestClassificationResult:
    """Test cases for ClassificationResult dataclass."""

    def test_classification_result_creation(self):
        """Test creating a ClassificationResult with basic data."""
        detector_results = {
            "lease_header_detector": DetectionResult(detected=True, value="LEASE"),
            "jurisdiction_detector": DetectionResult(detected=False, value=""),
        }
        successful_detectors = {"lease_header_detector", "jurisdiction_detector"}
        failed_detectors = {}

        result = ClassificationResult(
            text_length=1000,
            detector_results=detector_results,
            successful_detectors=successful_detectors,
            failed_detectors=failed_detectors,
        )

        assert result.text_length == 1000
        assert len(result.detector_results) == 2
        assert result.successful_detectors == {
            "lease_header_detector",
            "jurisdiction_detector",
        }
        assert result.failed_detectors == {}

    def test_has_detections_true(self):
        """Test has_detections property when detections are found."""
        detector_results = {
            "lease_header_detector": DetectionResult(detected=True, value="LEASE"),
            "jurisdiction_detector": DetectionResult(detected=False, value=""),
        }

        result = ClassificationResult(
            text_length=1000,
            detector_results=detector_results,
            successful_detectors={"lease_header_detector", "jurisdiction_detector"},
            failed_detectors={},
        )

        assert result.has_detections is True

    def test_has_detections_false(self):
        """Test has_detections property when no detections are found."""
        detector_results = {
            "lease_header_detector": DetectionResult(detected=False, value=""),
            "jurisdiction_detector": DetectionResult(detected=False, value=""),
        }

        result = ClassificationResult(
            text_length=1000,
            detector_results=detector_results,
            successful_detectors={"lease_header_detector", "jurisdiction_detector"},
            failed_detectors={},
        )

        assert result.has_detections is False

    def test_detected_values_with_detections(self):
        """Test detected_values property with positive detections."""
        detector_results = {
            "lease_header_detector": DetectionResult(
                detected=True, value="LEASE AGREEMENT"
            ),
            "jurisdiction_detector": DetectionResult(detected=True, value="CA"),
            "other": DetectionResult(detected=False, value=""),
        }

        result = ClassificationResult(
            text_length=1000,
            detector_results=detector_results,
            successful_detectors={
                "lease_header_detector",
                "jurisdiction_detector",
                "other",
            },
            failed_detectors={},
        )

        expected_values = {
            "lease_header_detector": "LEASE AGREEMENT",
            "jurisdiction_detector": "CA",
        }
        assert result.detected_values == expected_values

    def test_detected_values_empty(self):
        """Test detected_values property with no detections."""
        detector_results = {
            "lease_header_detector": DetectionResult(detected=False, value=""),
            "jurisdiction_detector": DetectionResult(detected=False, value=""),
        }

        result = ClassificationResult(
            text_length=1000,
            detector_results=detector_results,
            successful_detectors={"lease_header_detector", "jurisdiction_detector"},
            failed_detectors={},
        )

        assert result.detected_values == {}

    def test_detected_values_excludes_failed_detectors(self):
        """Test that detected_values excludes results from failed detectors."""
        # Simulate edge case: detector produced result but then failed
        detector_results = {
            "lease_header_detector": DetectionResult(detected=True, value="LEASE"),
            "failed_detector": DetectionResult(
                detected=True, value="SHOULD_NOT_APPEAR"
            ),
        }

        result = ClassificationResult(
            text_length=1000,
            detector_results=detector_results,
            successful_detectors={"lease_header_detector"},  # Only this one succeeded
            failed_detectors={"failed_detector": "Some error occurred"},
        )

        # Should only include results from successful detectors
        expected_values = {"lease_header_detector": "LEASE"}
        assert result.detected_values == expected_values
        assert "failed_detector" not in result.detected_values

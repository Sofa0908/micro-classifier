"""Unit tests for data models."""

import pytest
from classifier_router.models import ClassificationResult
from classifier_router.detector.base import DetectionResult


class TestClassificationResult:
    """Test cases for ClassificationResult dataclass."""

    @pytest.fixture
    def sample_results(self):
        """Sample detection results for testing."""
        return {
            "lease_header_detector": DetectionResult(detected=True, value="lease"),
            "jurisdiction_detector": DetectionResult(detected=True, value="CA"),
            "failed_detector": DetectionResult(detected=False, value=None),
        }

    @pytest.fixture
    def sample_classification_result(self, sample_results):
        """Sample ClassificationResult for testing."""
        return ClassificationResult(
            text_length=150,
            detector_results=sample_results,
            successful_detectors={"lease_header_detector", "jurisdiction_detector"},
            failed_detectors={"failed_detector": "Some error message"},
        )

    def test_classification_result_creation(self, sample_classification_result):
        """Test ClassificationResult creation with all fields."""
        result = sample_classification_result

        assert result.text_length == 150
        assert len(result.detector_results) == 3
        assert len(result.successful_detectors) == 2
        assert len(result.failed_detectors) == 1

    def test_has_detections_true(self, sample_classification_result):
        """Test has_detections property when detections exist."""
        result = sample_classification_result
        assert result.has_detections is True

    def test_has_detections_false(self):
        """Test has_detections property when no detections exist."""
        no_detection_results = {
            "detector1": DetectionResult(detected=False, value=None),
            "detector2": DetectionResult(detected=False, value=None),
        }

        result = ClassificationResult(
            text_length=100,
            detector_results=no_detection_results,
            successful_detectors={"detector1", "detector2"},
            failed_detectors={},
        )

        assert result.has_detections is False

    def test_detected_values_with_detections(self, sample_classification_result):
        """Test detected_values property with successful detections."""
        result = sample_classification_result
        detected = result.detected_values

        assert len(detected) == 2
        assert detected["lease_header_detector"] == "lease"
        assert detected["jurisdiction_detector"] == "CA"

    def test_detected_values_empty(self):
        """Test detected_values property with no detections."""
        no_detection_results = {
            "detector1": DetectionResult(detected=False, value=None),
        }

        result = ClassificationResult(
            text_length=100,
            detector_results=no_detection_results,
            successful_detectors={"detector1"},
            failed_detectors={},
        )

        assert result.detected_values == {}

    def test_detected_values_excludes_failed_detectors(self):
        """Test that detected_values excludes results from failed detectors."""
        mixed_results = {
            "successful_detector": DetectionResult(detected=True, value="success"),
            "failed_detector": DetectionResult(detected=True, value="failed"),
        }

        result = ClassificationResult(
            text_length=100,
            detector_results=mixed_results,
            successful_detectors={"successful_detector"},
            failed_detectors={"failed_detector": "Error message"},
        )

        detected = result.detected_values
        assert len(detected) == 1
        assert detected["successful_detector"] == "success"
        assert "failed_detector" not in detected

    def test_get_output_by_type_with_detections(self, sample_classification_result):
        """Test get_output_by_type method with successful detections."""
        result = sample_classification_result
        detector_configs = {
            "lease_header_detector": "docType",
            "jurisdiction_detector": "jurisdiction",
        }

        output_mapping = result.get_output_by_type(detector_configs)

        assert output_mapping == {
            "docType": "lease",
            "jurisdiction": "CA",
        }

    def test_get_output_by_type_with_failed_detectors(
        self, sample_classification_result
    ):
        """Test get_output_by_type method including failed detectors."""
        result = sample_classification_result
        detector_configs = {
            "lease_header_detector": "docType",
            "jurisdiction_detector": "jurisdiction",
            "failed_detector": "someType",
        }

        output_mapping = result.get_output_by_type(detector_configs)

        assert output_mapping == {
            "docType": "lease",
            "jurisdiction": "CA",
            "someType": None,
        }

    def test_get_output_by_type_no_detections(self):
        """Test get_output_by_type method with no detections."""
        no_detection_results = {
            "detector1": DetectionResult(detected=False, value=None),
            "detector2": DetectionResult(detected=False, value=None),
        }

        result = ClassificationResult(
            text_length=100,
            detector_results=no_detection_results,
            successful_detectors={"detector1", "detector2"},
            failed_detectors={},
        )

        detector_configs = {
            "detector1": "type1",
            "detector2": "type2",
        }

        output_mapping = result.get_output_by_type(detector_configs)

        assert output_mapping == {
            "type1": None,
            "type2": None,
        }

    def test_get_output_by_type_empty_configs(self, sample_classification_result):
        """Test get_output_by_type method with empty detector configs."""
        result = sample_classification_result
        output_mapping = result.get_output_by_type({})
        assert output_mapping == {}

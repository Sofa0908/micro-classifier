"""Tests for the ClassifierRouter and ClassificationResult classes."""

import pytest
from unittest.mock import patch

from classifier_router.router import ClassifierRouter, ClassificationResult
from classifier_router.detector.base import DetectionResult
from classifier_router.exceptions import ClassifierError


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


class TestClassifierRouter:
    """Test cases for ClassifierRouter class."""

    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return """
        LEASE AGREEMENT
        
        This lease agreement is made in the State of California
        between the landlord and tenant for residential property.
        """

    @pytest.fixture
    def router(self):
        """Create a ClassifierRouter instance for testing."""
        return ClassifierRouter()

    @pytest.fixture
    def expected_detectors(self, router):
        """Get expected detector names from actual configuration."""
        return router.get_available_detectors()

    def test_router_initialization_success(self):
        """Test successful router initialization."""
        router = ClassifierRouter()
        assert router.factory is not None
        assert router.logger is not None

    def test_router_initialization_with_custom_config(self):
        """Test router initialization with custom config path."""
        router = ClassifierRouter("config/detector_config.json")
        assert router.factory is not None

    @patch("classifier_router.router.DetectorFactory")
    def test_router_initialization_failure(self, mock_factory):
        """Test router initialization failure."""
        mock_factory.side_effect = Exception("Config error")

        with pytest.raises(
            ClassifierError, match="Failed to initialize ClassifierRouter"
        ):
            ClassifierRouter()

    def test_classify_with_real_detectors(
        self, router, sample_text, expected_detectors
    ):
        """Test classify method with real detector instances."""
        result = router.classify(sample_text)

        # Verify result structure
        assert isinstance(result, ClassificationResult)
        assert result.text_length == len(sample_text)
        assert len(result.detector_results) == len(
            expected_detectors
        )  # Should match config

        # Check that we got results from all expected detectors
        detector_names = set(result.detector_results.keys())
        expected_detector_set = set(expected_detectors)
        assert detector_names == expected_detector_set

        # Verify successful detection (using sample text that should trigger both detectors)
        assert result.has_detections is True
        detected_values = result.detected_values

        # Verify we have at least some detections (sample text contains "LEASE AGREEMENT" and "California")
        assert len(detected_values) > 0

        # Verify specific detections if they exist in config
        if "lease_header_detector" in expected_detectors:
            assert "lease_header_detector" in detected_values
        if "jurisdiction_detector" in expected_detectors:
            assert "jurisdiction_detector" in detected_values
            assert detected_values["jurisdiction_detector"] == "CA"

    def test_classify_empty_text(self, router):
        """Test classify with empty text."""
        with pytest.raises(ClassifierError, match="Input text cannot be empty or None"):
            router.classify("")

        with pytest.raises(ClassifierError, match="Input text cannot be empty or None"):
            router.classify("   ")

        with pytest.raises(ClassifierError, match="Input text cannot be empty or None"):
            router.classify(None)

    def test_classify_with_detectors_specific_list(self, router, sample_text):
        """Test classify_with_detectors with specific detector list."""
        detector_names = ["lease_header_detector"]
        result = router.classify_with_detectors(sample_text, detector_names)

        assert len(result.detector_results) == 1
        assert "lease_header_detector" in result.detector_results
        assert "lease_header_detector" in result.successful_detectors
        assert len(result.failed_detectors) == 0

    def test_classify_with_detectors_empty_list(self, router, sample_text):
        """Test classify_with_detectors with empty detector list."""
        with pytest.raises(
            ClassifierError, match="At least one detector name must be specified"
        ):
            router.classify_with_detectors(sample_text, [])

    def test_classify_with_detectors_empty_text(self, router):
        """Test classify_with_detectors with empty text."""
        with pytest.raises(ClassifierError, match="Input text cannot be empty or None"):
            router.classify_with_detectors("", ["lease_header_detector"])

        with pytest.raises(ClassifierError, match="Input text cannot be empty or None"):
            router.classify_with_detectors("   ", ["lease_header_detector"])

        with pytest.raises(ClassifierError, match="Input text cannot be empty or None"):
            router.classify_with_detectors(None, ["lease_header_detector"])

    def test_classify_with_detectors_invalid_detector(self, router, sample_text):
        """Test classify_with_detectors with invalid detector name."""
        detector_names = ["nonexistent_detector"]
        result = router.classify_with_detectors(sample_text, detector_names)

        # Should handle the error gracefully
        assert len(result.detector_results) == 0
        assert len(result.successful_detectors) == 0
        assert len(result.failed_detectors) == 1
        assert "nonexistent_detector" in result.failed_detectors

    def test_classify_with_detectors_mixed_valid_invalid(self, router, sample_text):
        """Test classify_with_detectors with mix of valid and invalid detectors."""
        detector_names = ["lease_header_detector", "nonexistent_detector"]
        result = router.classify_with_detectors(sample_text, detector_names)

        # Should succeed with valid detector and fail with invalid one
        assert len(result.detector_results) == 1
        assert "lease_header_detector" in result.detector_results
        assert "lease_header_detector" in result.successful_detectors
        assert len(result.failed_detectors) == 1
        assert "nonexistent_detector" in result.failed_detectors

    def test_get_available_detectors(self, router, expected_detectors):
        """Test get_available_detectors method."""
        detectors = router.get_available_detectors()

        assert isinstance(detectors, list)
        assert len(detectors) == len(expected_detectors)
        assert set(detectors) == set(expected_detectors)

        # Verify all detector names are non-empty strings
        for detector_name in detectors:
            assert isinstance(detector_name, str)
            assert len(detector_name) > 0

    def test_get_detector_info_valid(self, router, expected_detectors):
        """Test get_detector_info with valid detector name."""
        # Use the first available detector from config
        detector_name = expected_detectors[0]
        info = router.get_detector_info(detector_name)

        assert isinstance(info, dict)
        assert "name" in info
        assert "class_path" in info
        assert "description" in info
        assert info["name"] == detector_name

    def test_get_detector_info_invalid(self, router):
        """Test get_detector_info with invalid detector name."""
        with pytest.raises(ClassifierError, match="Failed to get detector info"):
            router.get_detector_info("nonexistent_detector")

    def test_classify_no_detections(self, router, expected_detectors):
        """Test classify with text that should not trigger any detections."""
        text = "This is just some random text with no legal document patterns."
        result = router.classify(text)

        assert isinstance(result, ClassificationResult)
        assert result.has_detections is False
        assert result.detected_values == {}
        assert len(result.successful_detectors) == len(
            expected_detectors
        )  # All detectors ran successfully

    def test_classify_with_logging(self, router, sample_text, caplog):
        """Test that classification produces appropriate log messages."""
        with caplog.at_level("DEBUG"):
            router.classify_with_detectors(sample_text, ["lease_header_detector"])

        # Should have debug log for successful detection
        assert any(
            "lease_header_detector" in record.message and "completed" in record.message
            for record in caplog.records
        )

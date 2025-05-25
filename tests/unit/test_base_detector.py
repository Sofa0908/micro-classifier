"""Unit tests for base detector strategy interface."""

import pytest
from abc import ABC

from classifier_router.detector.base import DetectorStrategy, DetectionResult


class TestDetectionResult:
    """Test cases for DetectionResult dataclass."""

    def test_detection_result_creation(self):
        """Test creating a DetectionResult with all fields."""
        result = DetectionResult(detected=True, value="lease")

        assert result.detected is True
        assert result.value == "lease"

    def test_detection_result_defaults(self):
        """Test DetectionResult with default values."""
        result = DetectionResult(detected=False)

        assert result.detected is False
        assert result.value is None

    def test_detection_result_no_value(self):
        """Test DetectionResult when detection fails."""
        result = DetectionResult(detected=False, value=None)

        assert result.detected is False
        assert result.value is None


class TestDetectorStrategy:
    """Test cases for DetectorStrategy abstract base class."""

    def test_detector_strategy_is_abstract(self):
        """Test that DetectorStrategy cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DetectorStrategy()

    def test_detector_strategy_inheritance(self):
        """Test that DetectorStrategy is properly abstract."""
        assert issubclass(DetectorStrategy, ABC)

        # Verify required abstract methods
        abstract_methods = DetectorStrategy.__abstractmethods__
        assert "detect" in abstract_methods
        assert "name" in abstract_methods

    def test_concrete_implementation_required(self):
        """Test that concrete implementations must implement all abstract methods."""

        # Missing both abstract methods
        class IncompleteDetector(DetectorStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteDetector()

        # Missing name property
        class PartialDetector(DetectorStrategy):
            def detect(self, text: str) -> DetectionResult:
                return DetectionResult(detected=False)

        with pytest.raises(TypeError):
            PartialDetector()

        # Complete implementation should work
        class CompleteDetector(DetectorStrategy):
            def detect(self, text: str) -> DetectionResult:
                return DetectionResult(detected=False)

            @property
            def name(self) -> str:
                return "test_detector"

        # This should not raise an exception
        detector = CompleteDetector()
        assert detector.name == "test_detector"
        assert isinstance(detector.detect("test"), DetectionResult)

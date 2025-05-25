"""Unit tests for JurisdictionDetector."""

from pathlib import Path

from classifier_router.core.detector.jurisdiction import JurisdictionDetector
from classifier_router.core.detector.base import DetectionResult


class TestJurisdictionDetector:
    """Test cases for JurisdictionDetector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = JurisdictionDetector()

    def test_detector_name(self):
        """Test that detector returns correct name."""
        assert self.detector.name == "jurisdiction_detector"

    # California (CA) Tests
    def test_detect_california_state_of(self):
        """Test detection of 'State of California' pattern."""
        text = "This agreement is governed by the laws of the State of California."
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "CA"

    def test_detect_california_name(self):
        """Test detection of 'California' pattern."""
        text = "Property located in Los Angeles, California."
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "CA"

    def test_detect_california_abbreviation(self):
        """Test detection of 'CA' abbreviation."""
        text = "Mailing address: 123 Main St, Los Angeles, CA 90210"
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "CA"

    def test_detect_california_fixture(self):
        """Test detection using the California lease fixture."""
        fixture_path = Path("tests/fixtures/classifier/lease_state_ca.txt")
        with open(fixture_path, "r") as f:
            text = f.read()

        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "CA"

    # Massachusetts (MA) Tests
    def test_detect_massachusetts_state_of(self):
        """Test detection of 'State of Massachusetts' pattern."""
        text = "Governed by the laws of the State of Massachusetts."
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "MA"

    def test_detect_massachusetts_commonwealth(self):
        """Test detection of 'Commonwealth of Massachusetts' pattern."""
        text = (
            "Corporation organized under the laws of the Commonwealth of Massachusetts."
        )
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "MA"

    def test_detect_massachusetts_name(self):
        """Test detection of 'Massachusetts' pattern."""
        text = "Individual residing in Boston, Massachusetts."
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "MA"

    def test_detect_massachusetts_abbreviation(self):
        """Test detection of 'MA' abbreviation."""
        text = "Address: 456 Oak St, Boston, MA 02101"
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "MA"

    def test_detect_massachusetts_fixture(self):
        """Test detection using the Massachusetts NDA fixture."""
        fixture_path = Path("tests/fixtures/classifier/nda_ma.txt")
        with open(fixture_path, "r") as f:
            text = f.read()

        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "MA"

    # New York (NY) Tests
    def test_detect_new_york_state_of(self):
        """Test detection of 'State of New York' pattern."""
        text = "This Power of Attorney shall be governed by the laws of the State of New York."
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "NY"

    def test_detect_new_york_name(self):
        """Test detection of 'New York' pattern."""
        text = "County of New York, State of New York."
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "NY"

    def test_detect_new_york_abbreviation(self):
        """Test detection of 'NY' abbreviation."""
        text = "Notary Public, State of NY"
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "NY"

    def test_detect_new_york_fixture(self):
        """Test detection using the New York POA fixture."""
        fixture_path = Path("tests/fixtures/classifier/poa_ny.txt")
        with open(fixture_path, "r") as f:
            text = f.read()

        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "NY"

    # Edge Cases and Error Handling
    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive for state names."""
        text = "governed by the laws of the state of california"
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "CA"

    def test_word_boundary_enforcement(self):
        """Test that word boundaries are enforced."""
        text = (
            "The document discusses Californian law."  # "Californian" not "California"
        )
        result = self.detector.detect(text)

        assert result.detected is False
        assert result.value is None

    def test_abbreviation_case_sensitive(self):
        """Test that state abbreviations are case-sensitive."""
        text = "Address includes ca as part of the street name"  # lowercase "ca"
        result = self.detector.detect(text)

        assert result.detected is False
        assert result.value is None

    def test_empty_text(self):
        """Test handling of empty text."""
        result = self.detector.detect("")

        assert result.detected is False
        assert result.value is None

    def test_none_text(self):
        """Test handling of None text."""
        result = self.detector.detect(None)

        assert result.detected is False
        assert result.value is None

    def test_no_jurisdiction_found(self):
        """Test that documents without jurisdiction patterns are not detected."""
        text = "This is a generic document with no state references."
        result = self.detector.detect(text)

        assert result.detected is False
        assert result.value is None

    def test_first_match_wins(self):
        """Test that the first matching jurisdiction is returned."""
        text = "This document references both California and Massachusetts."
        result = self.detector.detect(text)

        # Should return CA since it appears first in the iteration order
        assert result.detected is True
        assert result.value == "CA"

    def test_multiple_patterns_same_jurisdiction(self):
        """Test that multiple patterns for the same jurisdiction work."""
        text = "State of Massachusetts and Commonwealth of Massachusetts"
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "MA"

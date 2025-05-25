"""Unit tests for LeaseHeaderDetector."""

import pytest
from pathlib import Path

from classifier_router.detector.lease_header import LeaseHeaderDetector
from classifier_router.detector.base import DetectionResult


class TestLeaseHeaderDetector:
    """Test cases for LeaseHeaderDetector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = LeaseHeaderDetector()

    def test_detector_name(self):
        """Test that detector returns correct name."""
        assert self.detector.name == "lease_header_detector"

    def test_detect_lease_agreement_fixture(self):
        """Test detection using the lease fixture file."""
        # Load the fixture file
        fixture_path = Path("tests/fixtures/classifier/lease_state_ca.txt")
        with open(fixture_path, "r") as f:
            text = f.read()

        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "lease"

    def test_detect_lease_keyword(self):
        """Test detection of simple LEASE keyword."""
        text = "LEASE AGREEMENT between parties..."
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "lease"

    def test_detect_rental_agreement(self):
        """Test detection of RENTAL AGREEMENT pattern."""
        text = "RENTAL AGREEMENT for property at 123 Main St"
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "lease"

    def test_detect_tenancy_agreement(self):
        """Test detection of TENANCY AGREEMENT pattern."""
        text = "TENANCY AGREEMENT between landlord and tenant"
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "lease"

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        text = "lease agreement for residential property"
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "lease"

    def test_word_boundary_enforcement(self):
        """Test that word boundaries are enforced (no partial matches)."""
        text = (
            "Please review this document carefully"  # Contains "lease" but not as word
        )
        result = self.detector.detect(text)

        assert result.detected is False
        assert result.value is None

    def test_header_area_only(self):
        """Test that detection only looks in header area (first 500 chars)."""
        # Create text with lease keyword after 500 characters
        filler = "x" * 500
        text = filler + " LEASE AGREEMENT"
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

    def test_non_lease_document(self):
        """Test that non-lease documents are not detected."""
        text = "EMPLOYMENT AGREEMENT between company and employee"
        result = self.detector.detect(text)

        assert result.detected is False
        assert result.value is None

    def test_multiple_patterns_in_text(self):
        """Test that detection works when multiple patterns are present."""
        text = "RESIDENTIAL LEASE AGREEMENT and RENTAL AGREEMENT terms"
        result = self.detector.detect(text)

        assert result.detected is True
        assert result.value == "lease"

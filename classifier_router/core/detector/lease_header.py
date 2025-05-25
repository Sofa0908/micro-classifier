"""Lease header detection strategy implementation."""

import re
from typing import Pattern

from classifier_router.core.detector.base import DetectorStrategy, DetectionResult


class LeaseHeaderDetector(DetectorStrategy):
    """Detector for lease documents based on header patterns.

    This detector identifies lease documents by looking for lease-related
    keywords and phrases typically found at the beginning of lease agreements.

    Patterns detected:
    - "LEASE" (case-insensitive, word boundary)
    - "RENTAL AGREEMENT"
    - "TENANCY AGREEMENT"
    - "LEASE AGREEMENT"
    """

    def __init__(self):
        """Initialize the lease header detector with compiled regex patterns."""
        # Compile patterns for better performance
        self._patterns: list[Pattern[str]] = [
            re.compile(r"\bLEASE\b", re.IGNORECASE),
            re.compile(r"\bRENTAL\s+AGREEMENT\b", re.IGNORECASE),
            re.compile(r"\bTENANCY\s+AGREEMENT\b", re.IGNORECASE),
            re.compile(r"\bLEASE\s+AGREEMENT\b", re.IGNORECASE),
        ]

    def detect(self, text: str) -> DetectionResult:
        """Detect lease patterns in the document text.

        Args:
            text: The document text to analyze

        Returns:
            DetectionResult with detected=True and value="lease" if patterns found,
            otherwise detected=False
        """
        if not text:
            return DetectionResult(detected=False)

        # Search in the first 500 characters (header area)
        header_text = text[:500]

        for pattern in self._patterns:
            match = pattern.search(header_text)
            if match:
                return DetectionResult(detected=True, value="lease")

        return DetectionResult(detected=False)

    @property
    def name(self) -> str:
        """Return the name of this detector strategy.

        Returns:
            Human-readable name for logging and debugging
        """
        return "lease_header_detector"

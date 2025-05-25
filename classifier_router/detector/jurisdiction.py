"""Jurisdiction detection strategy implementation."""

import re
from typing import Pattern, Dict

from .base import DetectorStrategy, DetectionResult


class JurisdictionDetector(DetectorStrategy):
    """Detector for jurisdiction codes based on state references in document text.

    This detector identifies jurisdiction by looking for state-specific patterns
    throughout the document text, including formal legal references and
    common state name variations.

    Supported jurisdictions:
    - California (CA): "State of California", "California", "CA"
    - Massachusetts (MA): "State of Massachusetts", "Commonwealth of Massachusetts", "Massachusetts", "MA"
    - New York (NY): "State of New York", "New York", "NY"
    """

    def __init__(self):
        """Initialize the jurisdiction detector with compiled regex patterns."""
        # Define patterns for each jurisdiction
        self._jurisdiction_patterns: Dict[str, list[Pattern[str]]] = {
            "CA": [
                re.compile(r"\bState\s+of\s+California\b", re.IGNORECASE),
                re.compile(r"\bCalifornia\b", re.IGNORECASE),
                re.compile(r"\bCA\b"),  # Exact case for state abbreviation
            ],
            "MA": [
                re.compile(r"\bState\s+of\s+Massachusetts\b", re.IGNORECASE),
                re.compile(r"\bCommonwealth\s+of\s+Massachusetts\b", re.IGNORECASE),
                re.compile(r"\bMassachusetts\b", re.IGNORECASE),
                re.compile(r"\bMA\b"),  # Exact case for state abbreviation
            ],
            "NY": [
                re.compile(r"\bState\s+of\s+New\s+York\b", re.IGNORECASE),
                re.compile(r"\bNew\s+York\b", re.IGNORECASE),
                re.compile(r"\bNY\b"),  # Exact case for state abbreviation
            ],
        }

    def detect(self, text: str) -> DetectionResult:
        """Detect jurisdiction patterns in the document text.

        Args:
            text: The document text to analyze

        Returns:
            DetectionResult with detected=True and value=jurisdiction_code if patterns found,
            otherwise detected=False
        """
        if not text:
            return DetectionResult(detected=False)

        # Search for jurisdiction patterns in order of specificity
        # (more specific patterns first to avoid false positives)
        for jurisdiction_code, patterns in self._jurisdiction_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    return DetectionResult(detected=True, value=jurisdiction_code)

        return DetectionResult(detected=False)

    @property
    def name(self) -> str:
        """Return the name of this detector strategy.

        Returns:
            Human-readable name for logging and debugging
        """
        return "jurisdiction_detector"

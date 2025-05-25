"""Base detector strategy interface and result models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class DetectionResult:
    """Result of a detection operation.

    Attributes:
        detected: Whether the pattern was detected in the text
        value: The detected value (e.g., document type, jurisdiction code)
    """

    detected: bool
    value: Optional[str] = None


class DetectorStrategy(ABC):
    """Abstract base class for document detection strategies.

    This interface defines the contract that all detector implementations
    must follow. Detectors use regex patterns or other methods to identify
    document types, jurisdictions, or other classification attributes.
    """

    @abstractmethod
    def detect(self, text: str) -> DetectionResult:
        """Detect patterns in the given text.

        Args:
            text: The document text to analyze

        Returns:
            DetectionResult containing detection outcome
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this detector strategy.

        Returns:
            Human-readable name for logging and debugging
        """
        pass

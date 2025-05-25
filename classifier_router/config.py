"""Configuration models for the classifier router."""

from typing import List
from pydantic import BaseModel, Field


class DetectorConfig(BaseModel):
    """Configuration for a single detector.

    Attributes:
        name: Unique identifier for the detector
        class_path: Full Python import path to the detector class
        description: Human-readable description of what the detector does
        output_type: Type of output this detector produces (e.g., 'docType', 'jurisdiction')
    """

    name: str = Field(..., description="Unique identifier for the detector")
    class_path: str = Field(
        ..., description="Full Python import path to the detector class"
    )
    description: str = Field(
        ..., description="Human-readable description of the detector"
    )
    output_type: str = Field(
        ...,
        description="Type of output this detector produces (e.g., 'docType', 'jurisdiction')",
    )


class DetectorRegistryConfig(BaseModel):
    """Configuration for the detector registry.

    Attributes:
        detectors: List of detector configurations
    """

    detectors: List[DetectorConfig] = Field(
        ..., description="List of detector configurations"
    )

"""Message schemas for Kafka integration."""

from typing import Optional
from pydantic import BaseModel, Field


class TextExtractionMessage(BaseModel):
    """Input message from text-extraction topic.

    This represents the message format consumed from the upstream
    text extraction component.
    """

    docId: str = Field(..., description="Unique document identifier")
    text: str = Field(..., description="Extracted text content from the document")


class LLMRequestMessage(BaseModel):
    """Output message to llm-requests topic.

    This represents the message format produced to the downstream
    LLM processing component.
    """

    docId: str = Field(..., description="Unique document identifier")
    text: str = Field(..., description="Original text content")
    docType: Optional[str] = Field(
        None, description="Detected document type (e.g., 'lease')"
    )
    jurisdictionCode: Optional[str] = Field(
        None, description="Detected jurisdiction code (e.g., 'CA')"
    )


class ClassificationMetadata(BaseModel):
    """Metadata about the classification process.

    Used for internal tracking and monitoring.
    """

    processing_time_ms: float = Field(
        ..., description="Total processing time in milliseconds"
    )
    detectors_run: int = Field(..., description="Number of detectors executed")
    successful_detectors: int = Field(..., description="Number of successful detectors")
    failed_detectors: int = Field(..., description="Number of failed detectors")
    has_detections: bool = Field(..., description="Whether any detections were found")

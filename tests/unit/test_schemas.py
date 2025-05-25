"""Unit tests for message schemas."""

import pytest
from pydantic import ValidationError

from classifier_router.schemas import (
    TextExtractionMessage,
    LLMRequestMessage,
    ClassificationMetadata,
)


class TestTextExtractionMessage:
    """Test cases for TextExtractionMessage schema."""

    def test_valid_message_creation(self):
        """Test creating a valid TextExtractionMessage."""
        message = TextExtractionMessage(
            docId="doc_123", text="This is a sample document text."
        )

        assert message.docId == "doc_123"
        assert message.text == "This is a sample document text."

    def test_missing_doc_id_raises_error(self):
        """Test that missing docId raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TextExtractionMessage(text="Sample text")

        assert "docId" in str(exc_info.value)

    def test_missing_text_raises_error(self):
        """Test that missing text raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TextExtractionMessage(docId="doc_123")

        assert "text" in str(exc_info.value)

    def test_empty_strings_allowed(self):
        """Test that empty strings are allowed for text."""
        message = TextExtractionMessage(docId="doc_123", text="")

        assert message.docId == "doc_123"
        assert message.text == ""

    def test_serialization(self):
        """Test message serialization to dict."""
        message = TextExtractionMessage(docId="doc_123", text="Sample text")

        data = message.model_dump()
        expected = {"docId": "doc_123", "text": "Sample text"}

        assert data == expected


class TestLLMRequestMessage:
    """Test cases for LLMRequestMessage schema."""

    def test_valid_message_creation(self):
        """Test creating a valid LLMRequestMessage."""
        message = LLMRequestMessage(
            docId="doc_123",
            text="Sample lease text",
            docType="lease",
            jurisdictionCode="CA",
        )

        assert message.docId == "doc_123"
        assert message.text == "Sample lease text"
        assert message.docType == "lease"
        assert message.jurisdictionCode == "CA"

    def test_optional_fields_default_to_none(self):
        """Test that optional fields default to None."""
        message = LLMRequestMessage(docId="doc_123", text="Sample text")

        assert message.docId == "doc_123"
        assert message.text == "Sample text"
        assert message.docType is None
        assert message.jurisdictionCode is None

    def test_partial_optional_fields(self):
        """Test message with only some optional fields set."""
        message = LLMRequestMessage(
            docId="doc_123", text="Sample text", docType="lease"
        )

        assert message.docType == "lease"
        assert message.jurisdictionCode is None

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LLMRequestMessage(docId="doc_123")

        assert "text" in str(exc_info.value)

    def test_serialization_with_all_fields(self):
        """Test serialization with all fields set."""
        message = LLMRequestMessage(
            docId="doc_123", text="Sample text", docType="lease", jurisdictionCode="CA"
        )

        data = message.model_dump()
        expected = {
            "docId": "doc_123",
            "text": "Sample text",
            "docType": "lease",
            "jurisdictionCode": "CA",
        }

        assert data == expected

    def test_serialization_with_none_values(self):
        """Test serialization includes None values."""
        message = LLMRequestMessage(docId="doc_123", text="Sample text")

        data = message.model_dump()
        expected = {
            "docId": "doc_123",
            "text": "Sample text",
            "docType": None,
            "jurisdictionCode": None,
        }

        assert data == expected


class TestClassificationMetadata:
    """Test cases for ClassificationMetadata schema."""

    def test_valid_metadata_creation(self):
        """Test creating valid ClassificationMetadata."""
        metadata = ClassificationMetadata(
            processing_time_ms=125.5,
            detectors_run=2,
            successful_detectors=2,
            failed_detectors=0,
            has_detections=True,
        )

        assert metadata.processing_time_ms == 125.5
        assert metadata.detectors_run == 2
        assert metadata.successful_detectors == 2
        assert metadata.failed_detectors == 0
        assert metadata.has_detections is True

    def test_all_fields_required(self):
        """Test that all fields are required."""
        with pytest.raises(ValidationError) as exc_info:
            ClassificationMetadata()

        error_str = str(exc_info.value)
        assert "processing_time_ms" in error_str
        assert "detectors_run" in error_str
        assert "successful_detectors" in error_str
        assert "failed_detectors" in error_str
        assert "has_detections" in error_str

    def test_type_validation(self):
        """Test type validation for fields."""
        # Test invalid processing_time_ms type
        with pytest.raises(ValidationError):
            ClassificationMetadata(
                processing_time_ms="invalid",
                detectors_run=2,
                successful_detectors=2,
                failed_detectors=0,
                has_detections=True,
            )

        # Test invalid boolean type
        with pytest.raises(ValidationError):
            ClassificationMetadata(
                processing_time_ms=125.5,
                detectors_run=2,
                successful_detectors=2,
                failed_detectors=0,
                has_detections="invalid",
            )

    def test_serialization(self):
        """Test metadata serialization."""
        metadata = ClassificationMetadata(
            processing_time_ms=125.5,
            detectors_run=2,
            successful_detectors=1,
            failed_detectors=1,
            has_detections=True,
        )

        data = metadata.model_dump()
        expected = {
            "processing_time_ms": 125.5,
            "detectors_run": 2,
            "successful_detectors": 1,
            "failed_detectors": 1,
            "has_detections": True,
        }

        assert data == expected

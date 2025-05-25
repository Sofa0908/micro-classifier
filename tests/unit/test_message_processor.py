"""Unit tests for MessageProcessor."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from classifier_router.message_processor import MessageProcessor
from classifier_router.schemas import TextExtractionMessage, LLMRequestMessage
from classifier_router.exceptions import ClassifierError
from classifier_router.models import ClassificationResult
from classifier_router.detector.base import DetectionResult


class TestMessageProcessor:
    """Test cases for MessageProcessor."""

    @pytest.fixture
    def processor(self):
        """Create a MessageProcessor instance for testing."""
        return MessageProcessor()

    @pytest.fixture
    def sample_input_message(self):
        """Sample input message for testing."""
        return TextExtractionMessage(
            docId="doc_123",
            text="LEASE AGREEMENT\n\nThis lease is made in the State of California.",
        )

    @pytest.fixture
    def sample_classification_result(self):
        """Sample classification result for testing."""
        return ClassificationResult(
            text_length=50,
            detector_results={
                "lease_header_detector": DetectionResult(detected=True, value="lease"),
                "jurisdiction_detector": DetectionResult(detected=True, value="CA"),
            },
            successful_detectors={"lease_header_detector", "jurisdiction_detector"},
            failed_detectors={},
        )

    @pytest.mark.asyncio
    async def test_initialize_success(self, processor):
        """Test successful processor initialization."""
        with patch(
            "classifier_router.message_processor.ClassifierRouter"
        ) as mock_router_class:
            mock_router = MagicMock()
            mock_router.get_output_type_mapping.return_value = {
                "lease_header_detector": "docType",
                "jurisdiction_detector": "jurisdiction",
            }
            mock_router_class.return_value = mock_router

            await processor.initialize()

            assert processor.router is not None
            assert processor._output_type_mapping is not None
            mock_router_class.assert_called_once()
            mock_router.get_output_type_mapping.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_success(
        self, processor, sample_input_message, sample_classification_result
    ):
        """Test successful message processing."""
        # Setup mocks
        processor.router = MagicMock()
        processor._output_type_mapping = {
            "lease_header_detector": "docType",
            "jurisdiction_detector": "jurisdiction",
        }

        # Mock the async classification
        with patch.object(
            processor, "_run_classification", new_callable=AsyncMock
        ) as mock_classify:
            mock_classify.return_value = sample_classification_result

            # Create input message bytes
            input_bytes = json.dumps(sample_input_message.model_dump()).encode("utf-8")

            # Process message
            result = await processor.process_message(input_bytes)

            # Verify result
            assert isinstance(result, LLMRequestMessage)
            assert result.docId == "doc_123"
            assert result.docType == "lease"
            assert result.jurisdictionCode == "CA"
            mock_classify.assert_called_once()

    def test_parse_input_message_success(self, processor):
        """Test successful input message parsing."""
        message_data = {"docId": "doc_123", "text": "Sample text"}
        message_bytes = json.dumps(message_data).encode("utf-8")

        result = processor._parse_input_message(message_bytes)

        assert isinstance(result, TextExtractionMessage)
        assert result.docId == "doc_123"
        assert result.text == "Sample text"

"""Message processor for Kafka integration."""

import asyncio
import json
import time
from typing import Dict, Optional

from .router import ClassifierRouter
from .schemas import TextExtractionMessage, LLMRequestMessage, ClassificationMetadata
from .settings import settings
from .logging_cfg import ClassifierLoggerMixin
from .exceptions import ClassifierError


class MessageProcessor(ClassifierLoggerMixin):
    """Processes messages from Kafka using the classification router.

    This class bridges the async Kafka world with our synchronous
    classification logic, handling message parsing, processing,
    and result formatting.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the message processor.

        Args:
            config_path: Optional path to detector configuration file
        """
        self.config_path = config_path or settings.app.detector_config_path
        self.router: Optional[ClassifierRouter] = None
        self._output_type_mapping: Optional[Dict[str, str]] = None

    async def initialize(self) -> None:
        """Initialize the classification router and cache output type mapping.

        This is called once during startup to prepare the processor.
        """
        try:
            # Initialize router (synchronous operation)
            self.router = ClassifierRouter(self.config_path)

            # Cache output type mapping for efficient processing
            self._output_type_mapping = self.router.get_output_type_mapping()

            self.logger.info(
                "MessageProcessor initialized successfully",
                extra={
                    "config_path": self.config_path,
                    "available_detectors": len(self._output_type_mapping),
                    "output_mapping": self._output_type_mapping,
                },
            )

        except Exception as e:
            self.logger.error(
                "Failed to initialize MessageProcessor",
                extra={
                    "config_path": self.config_path,
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise ClassifierError(f"Failed to initialize MessageProcessor: {e}")

    async def process_message(self, message_value: bytes) -> LLMRequestMessage:
        """Process a single message from the text-extraction topic.

        Args:
            message_value: Raw message bytes from Kafka

        Returns:
            Processed message ready for llm-requests topic

        Raises:
            ClassifierError: If message processing fails
        """
        start_time = time.time()

        try:
            # Parse input message
            input_message = self._parse_input_message(message_value)

            self.logger.info(
                "Processing message",
                extra={
                    "doc_id": input_message.docId,
                    "text_length": len(input_message.text),
                },
            )

            # Validate text length
            if len(input_message.text) > settings.app.max_text_length:
                raise ClassifierError(
                    f"Text length {len(input_message.text)} exceeds maximum {settings.app.max_text_length}"
                )

            # Run classification
            classification_result = await self._run_classification(input_message.text)

            # Map results to output format
            output_message = self._create_output_message(
                input_message, classification_result
            )

            # Log processing completion
            processing_time_ms = (time.time() - start_time) * 1000
            metadata = ClassificationMetadata(
                processing_time_ms=processing_time_ms,
                detectors_run=len(classification_result.detector_results),
                successful_detectors=len(classification_result.successful_detectors),
                failed_detectors=len(classification_result.failed_detectors),
                has_detections=classification_result.has_detections,
            )

            self.logger.info(
                "Message processed successfully",
                extra={
                    "doc_id": input_message.docId,
                    "doc_type": output_message.docType,
                    "jurisdiction_code": output_message.jurisdictionCode,
                    "processing_time_ms": round(processing_time_ms, 2),
                    "has_detections": metadata.has_detections,
                },
            )

            return output_message

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000

            self.logger.error(
                "Failed to process message",
                extra={
                    "processing_time_ms": round(processing_time_ms, 2),
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise

    def _parse_input_message(self, message_value: bytes) -> TextExtractionMessage:
        """Parse raw Kafka message into TextExtractionMessage.

        Args:
            message_value: Raw message bytes

        Returns:
            Parsed input message

        Raises:
            ClassifierError: If message parsing fails
        """
        try:
            # Decode JSON
            message_data = json.loads(message_value.decode("utf-8"))

            # Validate and parse using Pydantic
            return TextExtractionMessage(**message_data)

        except json.JSONDecodeError as e:
            raise ClassifierError(f"Invalid JSON in message: {e}")
        except Exception as e:
            raise ClassifierError(f"Failed to parse input message: {e}")

    async def _run_classification(self, text: str):
        """Run classification in a thread pool to avoid blocking the event loop.

        Args:
            text: Text to classify

        Returns:
            Classification result
        """
        if not self.router:
            raise ClassifierError("MessageProcessor not initialized")

        # Run synchronous classification in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.router.classify, text)

    def _create_output_message(
        self, input_message: TextExtractionMessage, classification_result
    ) -> LLMRequestMessage:
        """Create output message from classification results.

        Args:
            input_message: Original input message
            classification_result: Results from classification

        Returns:
            Formatted output message
        """
        if not self._output_type_mapping:
            raise ClassifierError("Output type mapping not initialized")

        # Map detector results to semantic output types
        output_by_type = classification_result.get_output_by_type(
            self._output_type_mapping
        )

        # Create output message with mapped values
        return LLMRequestMessage(
            docId=input_message.docId,
            text=input_message.text,
            docType=output_by_type.get("docType"),
            jurisdictionCode=output_by_type.get("jurisdiction"),
        )

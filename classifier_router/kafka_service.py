"""Kafka service for consuming and producing messages."""

import asyncio
import json
import signal
from typing import Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from .message_processor import MessageProcessor
from .settings import settings
from .logging_cfg import ClassifierLoggerMixin
from .exceptions import ClassifierError


class KafkaService(ClassifierLoggerMixin):
    """Kafka service for consuming text-extraction messages and producing llm-requests.

    This service manages the Kafka consumer and producer, handles the main
    message processing loop, and provides graceful shutdown capabilities.
    """

    def __init__(self):
        """Initialize the Kafka service."""
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.producer: Optional[AIOKafkaProducer] = None
        self.processor: Optional[MessageProcessor] = None
        self.running = False
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> None:
        """Initialize Kafka consumer, producer, and message processor."""
        try:
            self.logger.info(
                "Initializing Kafka service",
                extra={
                    "bootstrap_servers": settings.kafka.bootstrap_servers,
                    "input_topic": settings.kafka.input_topic,
                    "output_topic": settings.kafka.output_topic,
                    "consumer_group": settings.kafka.consumer_group_id,
                },
            )

            # Initialize message processor
            self.processor = MessageProcessor()
            await self.processor.initialize()

            # Initialize Kafka consumer
            self.consumer = AIOKafkaConsumer(
                settings.kafka.input_topic,
                bootstrap_servers=settings.kafka.bootstrap_servers,
                group_id=settings.kafka.consumer_group_id,
                auto_offset_reset=settings.kafka.auto_offset_reset,
                max_poll_records=settings.kafka.max_poll_records,
                security_protocol=settings.kafka.security_protocol,
                sasl_mechanism=(
                    settings.kafka.sasl_mechanism
                    if settings.kafka.sasl_username
                    else None
                ),
                sasl_plain_username=(
                    settings.kafka.sasl_username
                    if settings.kafka.sasl_username
                    else None
                ),
                sasl_plain_password=(
                    settings.kafka.sasl_password
                    if settings.kafka.sasl_password
                    else None
                ),
            )

            # Initialize Kafka producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka.bootstrap_servers,
                security_protocol=settings.kafka.security_protocol,
                sasl_mechanism=(
                    settings.kafka.sasl_mechanism
                    if settings.kafka.sasl_username
                    else None
                ),
                sasl_plain_username=(
                    settings.kafka.sasl_username
                    if settings.kafka.sasl_username
                    else None
                ),
                sasl_plain_password=(
                    settings.kafka.sasl_password
                    if settings.kafka.sasl_password
                    else None
                ),
            )

            # Start consumer and producer
            await self.consumer.start()
            await self.producer.start()

            self.logger.info("Kafka service initialized successfully")

        except Exception as e:
            self.logger.error(
                "Failed to initialize Kafka service",
                extra={
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            await self.cleanup()
            raise ClassifierError(f"Failed to initialize Kafka service: {e}")

    async def start(self) -> None:
        """Start the main message processing loop."""
        if not self.consumer or not self.producer or not self.processor:
            raise ClassifierError("Kafka service not initialized")

        self.running = True
        self.logger.info("Starting Kafka message processing loop")

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        try:
            while self.running and not self._shutdown_event.is_set():
                try:
                    # Poll for messages with timeout
                    message_batch = await asyncio.wait_for(
                        self.consumer.getmany(timeout_ms=1000),
                        timeout=settings.app.processing_timeout_seconds,
                    )

                    if not message_batch:
                        continue

                    # Process messages in batch
                    await self._process_message_batch(message_batch)

                except asyncio.TimeoutError:
                    # Normal timeout, continue polling
                    continue

                except KafkaError as e:
                    self.logger.error(
                        "Kafka error during message processing",
                        extra={
                            "error_type": e.__class__.__name__,
                            "error_message": str(e),
                        },
                    )
                    # Wait before retrying
                    await asyncio.sleep(5)

                except Exception as e:
                    self.logger.error(
                        "Unexpected error in message processing loop",
                        extra={
                            "error_type": e.__class__.__name__,
                            "error_message": str(e),
                        },
                        exc_info=True,
                    )
                    # Wait before retrying
                    await asyncio.sleep(5)

        finally:
            self.logger.info("Message processing loop stopped")
            await self.cleanup()

    async def _process_message_batch(self, message_batch) -> None:
        """Process a batch of messages.

        Args:
            message_batch: Batch of messages from Kafka consumer
        """
        total_messages = sum(len(messages) for messages in message_batch.values())

        self.logger.debug(
            "Processing message batch", extra={"batch_size": total_messages}
        )

        for topic_partition, messages in message_batch.items():
            for message in messages:
                try:
                    await self._process_single_message(message)

                except Exception as e:
                    self.logger.error(
                        "Failed to process message",
                        extra={
                            "topic": topic_partition.topic,
                            "partition": topic_partition.partition,
                            "offset": message.offset,
                            "error_type": e.__class__.__name__,
                            "error_message": str(e),
                        },
                        exc_info=True,
                    )
                    # Continue processing other messages
                    continue

    async def _process_single_message(self, message) -> None:
        """Process a single Kafka message.

        Args:
            message: Kafka message to process
        """
        try:
            # Process message using message processor
            output_message = await self.processor.process_message(message.value)

            # Produce result to output topic
            await self._produce_message(output_message)

            self.logger.debug(
                "Message processed and produced successfully",
                extra={
                    "doc_id": output_message.docId,
                    "offset": message.offset,
                },
            )

        except Exception as e:
            # Log error and re-raise for batch-level handling
            self.logger.error(
                "Error processing single message",
                extra={
                    "offset": message.offset,
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                },
            )
            raise

    async def _produce_message(self, output_message) -> None:
        """Produce a message to the output topic.

        Args:
            output_message: LLMRequestMessage to produce
        """
        try:
            # Serialize message to JSON
            message_data = output_message.model_dump()
            message_bytes = json.dumps(message_data).encode("utf-8")

            # Produce to Kafka
            await self.producer.send_and_wait(
                settings.kafka.output_topic,
                value=message_bytes,
                key=output_message.docId.encode(
                    "utf-8"
                ),  # Use docId as key for partitioning
            )

        except Exception as e:
            self.logger.error(
                "Failed to produce message",
                extra={
                    "doc_id": output_message.docId,
                    "topic": settings.kafka.output_topic,
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            raise

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal", extra={"signal": signum})
            self.running = False
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def stop(self) -> None:
        """Stop the Kafka service gracefully."""
        self.logger.info("Stopping Kafka service")
        self.running = False
        self._shutdown_event.set()
        await self.cleanup()

    async def cleanup(self) -> None:
        """Cleanup Kafka resources."""
        try:
            if self.consumer:
                await self.consumer.stop()
                self.consumer = None

            if self.producer:
                await self.producer.stop()
                self.producer = None

            self.logger.info("Kafka service cleanup completed")

        except Exception as e:
            self.logger.error(
                "Error during Kafka service cleanup",
                extra={
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )

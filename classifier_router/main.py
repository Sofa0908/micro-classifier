"""Main application entry point for the Kafka-based classifier router."""

import asyncio
import sys

from classifier_router.kafka.service import KafkaService
from classifier_router.config.logging_cfg import setup_logging
from classifier_router.config.settings import settings


async def main() -> None:
    """Main application entry point."""
    # Setup logging
    log_file = settings.app.log_file if settings.app.log_file else None
    setup_logging(
        level=settings.app.log_level,
        format_type=settings.app.log_format,
        log_file=log_file,
    )

    # Create and initialize Kafka service
    kafka_service = KafkaService()

    try:
        # Initialize the service
        await kafka_service.initialize()

        # Start the message processing loop
        await kafka_service.start()

    except KeyboardInterrupt:
        kafka_service.logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        kafka_service.logger.error(
            "Fatal error in main application",
            extra={
                "error_type": e.__class__.__name__,
                "error_message": str(e),
            },
            exc_info=True,
        )
        sys.exit(1)
    finally:
        # Ensure cleanup happens
        await kafka_service.cleanup()


def run() -> None:
    """Entry point for running the application."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()

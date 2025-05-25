"""Application settings and configuration."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class KafkaSettings(BaseSettings):
    """Kafka connection and topic configuration."""

    bootstrap_servers: List[str] = Field(
        default=["localhost:9092"], description="Kafka bootstrap servers"
    )

    # Consumer settings
    consumer_group_id: str = Field(
        default="classifier-router", description="Kafka consumer group ID"
    )

    input_topic: str = Field(
        default="text-extraction",
        description="Topic to consume text extraction messages from",
    )

    # Producer settings
    output_topic: str = Field(
        default="llm-requests", description="Topic to produce classification results to"
    )

    # Connection settings
    security_protocol: str = Field(
        default="PLAINTEXT", description="Kafka security protocol"
    )

    sasl_mechanism: str = Field(
        default="PLAIN", description="SASL mechanism for authentication"
    )

    sasl_username: str = Field(default="", description="SASL username")

    sasl_password: str = Field(default="", description="SASL password")

    # Processing settings
    max_poll_records: int = Field(
        default=100, description="Maximum number of records to poll at once"
    )

    auto_offset_reset: str = Field(
        default="latest", description="Auto offset reset policy"
    )

    class Config:
        env_prefix = "KAFKA_"


class ApplicationSettings(BaseSettings):
    """Application-wide configuration."""

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    log_format: str = Field(
        default="structured", description="Log format type (structured or simple)"
    )

    log_file: str = Field(
        default="", description="Log file path (empty for console only)"
    )

    # Classification
    detector_config_path: str = Field(
        default="config/detector_config.json",
        description="Path to detector configuration file",
    )

    # Processing
    max_text_length: int = Field(
        default=1000000, description="Maximum text length to process"  # 1MB
    )

    processing_timeout_seconds: int = Field(
        default=30, description="Maximum processing time per message"
    )

    # Idempotency (for future implementation)
    idempotency_store_url: str = Field(
        default="redis://localhost:6379", description="Redis URL for idempotency store"
    )

    idempotency_ttl_hours: int = Field(
        default=24, description="TTL for idempotency keys in hours"
    )

    class Config:
        env_prefix = "APP_"


class Settings(BaseSettings):
    """Combined application settings."""

    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    app: ApplicationSettings = Field(default_factory=ApplicationSettings)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize nested settings
        self.kafka = KafkaSettings()
        self.app = ApplicationSettings()


# Global settings instance
settings = Settings()

"""Unit tests for DetectorFactory."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from classifier_router.factory import DetectorFactory
from classifier_router.config import DetectorConfig, DetectorRegistryConfig
from classifier_router.exceptions import ConfigError
from classifier_router.detector.base import DetectorStrategy
from classifier_router.detector.lease_header import LeaseHeaderDetector
from classifier_router.detector.jurisdiction import JurisdictionDetector


class TestDetectorFactory:
    """Test cases for DetectorFactory."""

    @pytest.fixture
    def expected_detectors(self):
        """Load expected detectors from the actual config file."""
        config_path = Path("config/detector_config.json")
        with open(config_path, "r") as f:
            config_data = json.load(f)
        return config_data["detectors"]

    def test_actual_config_file_is_valid(self):
        """Test that the actual detector_config.json file is valid and all classes are importable."""
        config_path = Path("config/detector_config.json")

        # File should exist
        assert config_path.exists(), "detector_config.json file is missing"

        # Should be valid JSON
        with open(config_path, "r") as f:
            config_data = json.load(f)

        # Should validate against our Pydantic schema
        config = DetectorRegistryConfig(**config_data)
        assert (
            len(config.detectors) > 0
        ), "Configuration should have at least one detector"

        # All detector configurations should be valid
        for detector_config in config.detectors:
            assert detector_config.name, "Detector name should not be empty"
            assert detector_config.class_path, "Class path should not be empty"
            assert detector_config.description, "Description should not be empty"
            assert (
                "." in detector_config.class_path
            ), "Class path should contain module path"

        # Factory should be able to load the configuration without errors
        factory = DetectorFactory()
        assert len(factory._config.detectors) == len(config.detectors)

        # All configured classes should be importable and valid DetectorStrategy subclasses
        for detector_config in config.detectors:
            detector = factory.create_detector(detector_config.name)
            assert isinstance(detector, DetectorStrategy)
            assert detector.name == detector_config.name

    def test_factory_loads_valid_config(self, expected_detectors):
        """Test that factory loads valid configuration successfully."""
        factory = DetectorFactory()

        # Should load without errors
        assert factory._config is not None
        assert len(factory._config.detectors) == len(expected_detectors)

        # Check detector names match expected
        detector_names = [d.name for d in factory._config.detectors]
        expected_names = [d["name"] for d in expected_detectors]

        for expected_name in expected_names:
            assert expected_name in detector_names

    def test_factory_loads_detector_classes(self, expected_detectors):
        """Test that factory loads detector classes correctly."""
        factory = DetectorFactory()

        # Should have loaded all configured detector classes
        assert len(factory._detector_classes) == len(expected_detectors)

        # Check that all expected detectors are loaded
        expected_names = [d["name"] for d in expected_detectors]
        for expected_name in expected_names:
            assert expected_name in factory._detector_classes

        # Verify specific known detectors (these are implementation details we control)
        if "lease_header_detector" in factory._detector_classes:
            assert (
                factory._detector_classes["lease_header_detector"]
                == LeaseHeaderDetector
            )
        if "jurisdiction_detector" in factory._detector_classes:
            assert (
                factory._detector_classes["jurisdiction_detector"]
                == JurisdictionDetector
            )

    def test_create_detector_by_name(self, expected_detectors):
        """Test creating detector instances by name."""
        factory = DetectorFactory()

        # Test creating each configured detector
        for detector_config in expected_detectors:
            detector_name = detector_config["name"]
            detector = factory.create_detector(detector_name)

            # Should be a DetectorStrategy instance
            assert isinstance(detector, DetectorStrategy)
            assert detector.name == detector_name

    def test_create_unknown_detector_raises_error(self):
        """Test that creating unknown detector raises ConfigError."""
        factory = DetectorFactory()

        with pytest.raises(ConfigError) as exc_info:
            factory.create_detector("unknown_detector")

        assert "Unknown detector 'unknown_detector'" in str(exc_info.value)
        assert "Available detectors:" in str(exc_info.value)

    def test_create_all_detectors(self, expected_detectors):
        """Test creating all configured detectors."""
        factory = DetectorFactory()

        detectors = factory.create_all_detectors()

        # Should create all configured detectors
        assert len(detectors) == len(expected_detectors)

        # Check that all expected detectors are created
        expected_names = [d["name"] for d in expected_detectors]
        for expected_name in expected_names:
            assert expected_name in detectors
            assert isinstance(detectors[expected_name], DetectorStrategy)

    def test_list_available_detectors(self, expected_detectors):
        """Test listing available detector configurations."""
        factory = DetectorFactory()

        configs = factory.list_available_detectors()

        assert len(configs) == len(expected_detectors)
        assert all(isinstance(config, DetectorConfig) for config in configs)

        # Check that all expected detectors are listed
        config_names = [config.name for config in configs]
        expected_names = [d["name"] for d in expected_detectors]

        for expected_name in expected_names:
            assert expected_name in config_names

    def test_get_detector_config(self, expected_detectors):
        """Test getting specific detector configuration."""
        factory = DetectorFactory()

        # Test getting config for each configured detector
        for detector_config in expected_detectors:
            detector_name = detector_config["name"]
            config = factory.get_detector_config(detector_name)

            assert isinstance(config, DetectorConfig)
            assert config.name == detector_name
            assert config.class_path == detector_config["class_path"]
            assert config.description == detector_config["description"]

    def test_get_unknown_detector_config_raises_error(self):
        """Test that getting unknown detector config raises ConfigError."""
        factory = DetectorFactory()

        with pytest.raises(ConfigError) as exc_info:
            factory.get_detector_config("unknown_detector")

        assert "Detector 'unknown_detector' not found" in str(exc_info.value)

    def test_missing_config_file_raises_error(self):
        """Test that missing configuration file raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            DetectorFactory("nonexistent_config.json")

        assert "Configuration file not found" in str(exc_info.value)

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises ConfigError."""
        invalid_json = "{ invalid json }"

        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(ConfigError) as exc_info:
                    DetectorFactory("invalid_config.json")

        assert "Invalid JSON in configuration file" in str(exc_info.value)

    def test_invalid_config_schema_raises_error(self):
        """Test that invalid configuration schema raises ConfigError."""
        invalid_config = {"invalid": "schema"}

        with patch("builtins.open", mock_open(read_data=json.dumps(invalid_config))):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(ConfigError) as exc_info:
                    DetectorFactory("invalid_config.json")

        assert "Failed to load configuration" in str(exc_info.value)

    def test_invalid_class_path_raises_error(self):
        """Test that invalid class path raises ConfigError."""
        invalid_config = {
            "detectors": [
                {
                    "name": "invalid_detector",
                    "class_path": "nonexistent.module.Class",
                    "description": "Invalid detector",
                }
            ]
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(invalid_config))):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(ConfigError) as exc_info:
                    DetectorFactory("invalid_config.json")

        assert "Failed to import detector 'invalid_detector'" in str(exc_info.value)

    def test_non_detector_class_raises_error(self):
        """Test that non-DetectorStrategy class raises ConfigError."""
        invalid_config = {
            "detectors": [
                {
                    "name": "invalid_detector",
                    "class_path": "builtins.str",  # str is not a DetectorStrategy
                    "description": "Invalid detector",
                }
            ]
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(invalid_config))):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(ConfigError) as exc_info:
                    DetectorFactory("invalid_config.json")

        assert "is not a subclass of DetectorStrategy" in str(exc_info.value)

    def test_malformed_class_path_raises_error(self):
        """Test that malformed class path raises ConfigError."""
        invalid_config = {
            "detectors": [
                {
                    "name": "invalid_detector",
                    "class_path": "invalid_path_without_dots",
                    "description": "Invalid detector",
                }
            ]
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(invalid_config))):
            with patch("pathlib.Path.exists", return_value=True):
                with pytest.raises(ConfigError) as exc_info:
                    DetectorFactory("invalid_config.json")

        assert "Invalid class path format" in str(exc_info.value)

    def test_factory_with_custom_config_path(self):
        """Test factory with custom configuration path."""
        custom_config = {
            "detectors": [
                {
                    "name": "test_detector",
                    "class_path": "classifier_router.detector.lease_header.LeaseHeaderDetector",
                    "description": "Test detector",
                }
            ]
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(custom_config))):
            with patch("pathlib.Path.exists", return_value=True):
                factory = DetectorFactory("custom_config.json")

        assert len(factory._config.detectors) == 1
        assert factory._config.detectors[0].name == "test_detector"

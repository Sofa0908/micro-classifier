"""Factory for creating detector instances from configuration."""

import json
import importlib
from pathlib import Path
from typing import Dict, Type, List

from .config import DetectorRegistryConfig, DetectorConfig
from .detector.base import DetectorStrategy
from .exceptions import ConfigError


class DetectorFactory:
    """Factory for creating detector instances from configuration.

    This factory loads detector configurations from JSON files and uses
    importlib to dynamically instantiate detector classes. It provides
    config-driven extensibility for adding new detector types.
    """

    def __init__(self, config_path: str = "config/detector_config.json"):
        """Initialize the detector factory.

        Args:
            config_path: Path to the detector configuration JSON file

        Raises:
            ConfigError: If configuration file is invalid or missing
        """
        self.config_path = config_path
        self._config: DetectorRegistryConfig = self._load_config()
        self._detector_classes: Dict[str, Type[DetectorStrategy]] = {}
        self._load_detector_classes()

    def _load_config(self) -> DetectorRegistryConfig:
        """Load and validate the detector configuration.

        Returns:
            Validated detector registry configuration

        Raises:
            ConfigError: If configuration file is invalid or missing
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise ConfigError(f"Configuration file not found: {self.config_path}")

            with open(config_file, "r") as f:
                config_data = json.load(f)

            return DetectorRegistryConfig(**config_data)

        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}")

    def _load_detector_classes(self) -> None:
        """Load detector classes from configuration.

        Iterates through detector configurations and imports each class
        using the _import_detector_class method.

        Raises:
            ConfigError: If any detector class cannot be imported
        """
        for detector_config in self._config.detectors:
            try:
                self._detector_classes[detector_config.name] = (
                    self._import_detector_class(detector_config.class_path)
                )
            except Exception as e:
                raise ConfigError(
                    f"Failed to import detector '{detector_config.name}' "
                    f"from '{detector_config.class_path}': {e}"
                )

    def _import_detector_class(self, class_path: str) -> Type[DetectorStrategy]:
        """Import a detector class from its module path using importlib.

        Args:
            class_path: Full Python import path (e.g., 'module.submodule.ClassName')

        Returns:
            The imported detector class

        Raises:
            ConfigError: If the class cannot be imported or is not a DetectorStrategy
        """
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            detector_class = getattr(module, class_name)

            # Validate that it's a DetectorStrategy subclass
            if not issubclass(detector_class, DetectorStrategy):
                raise ConfigError(
                    f"Class '{class_path}' is not a subclass of DetectorStrategy"
                )

            return detector_class

        except ValueError:
            raise ConfigError(f"Invalid class path format: '{class_path}'")
        except ImportError as e:
            raise ConfigError(f"Cannot import module from '{class_path}': {e}")
        except AttributeError:
            raise ConfigError(
                f"Class '{class_name}' not found in module '{module_path}'"
            )

    def create_detector(self, detector_name: str) -> DetectorStrategy:
        """Create a detector instance by name.

        Args:
            detector_name: Name of the detector to create

        Returns:
            Instantiated detector

        Raises:
            ConfigError: If detector name is not found
        """
        if detector_name not in self._detector_classes:
            available = list(self._detector_classes.keys())
            raise ConfigError(
                f"Unknown detector '{detector_name}'. Available detectors: {available}"
            )

        detector_class = self._detector_classes[detector_name]
        return detector_class()

    def create_all_detectors(self) -> Dict[str, DetectorStrategy]:
        """Create instances of all configured detectors.

        Returns:
            Dictionary mapping detector names to instances
        """
        return {
            name: self.create_detector(name) for name in self._detector_classes.keys()
        }

    def list_available_detectors(self) -> List[DetectorConfig]:
        """List all available detector configurations.

        Returns:
            List of detector configurations
        """
        return self._config.detectors

    def get_detector_config(self, detector_name: str) -> DetectorConfig:
        """Get configuration for a specific detector.

        Args:
            detector_name: Name of the detector

        Returns:
            Detector configuration

        Raises:
            ConfigError: If detector name is not found
        """
        for config in self._config.detectors:
            if config.name == detector_name:
                return config

        raise ConfigError(f"Detector '{detector_name}' not found in configuration")

# API Reference

## 📚 **Core Classes**

### **ClassifierRouter**

Main orchestration class for document classification.

```python
from classifier_router import ClassifierRouter

router = ClassifierRouter(config_path="config/detector_config.json")
```

#### **Constructor**

```python
def __init__(self, config_path: str = "config/detector_config.json") -> None
```

**Parameters:**
- `config_path` (str): Path to detector configuration JSON file

**Raises:**
- `ClassifierError`: If configuration loading or detector initialization fails

#### **Methods**

##### `classify(text: str) -> ClassificationResult`

Run all available detectors against input text.

**Parameters:**
- `text` (str): Input text to classify

**Returns:**
- `ClassificationResult`: Aggregated results from all detectors

**Raises:**
- `ClassifierError`: If text is empty or None

**Example:**
```python
result = router.classify("LEASE AGREEMENT\n\nState of California...")
print(f"Has detections: {result.has_detections}")
print(f"Detected values: {result.detected_values}")
```

##### `classify_with_detectors(text: str, detector_names: List[str]) -> ClassificationResult`

Run specific detectors against input text.

**Parameters:**
- `text` (str): Input text to classify
- `detector_names` (List[str]): List of detector names to run

**Returns:**
- `ClassificationResult`: Results from specified detectors

**Raises:**
- `ClassifierError`: If text is empty, None, or detector_names is empty

**Example:**
```python
result = router.classify_with_detectors(
    text="LEASE AGREEMENT...", 
    detector_names=["lease_header_detector"]
)
```

##### `get_available_detectors() -> List[str]`

Get list of available detector names.

**Returns:**
- `List[str]`: List of detector names that can be used for classification

##### `get_detector_info(detector_name: str) -> Dict[str, str]`

Get information about a specific detector.

**Parameters:**
- `detector_name` (str): Name of the detector

**Returns:**
- `Dict[str, str]`: Dictionary with detector information (name, class_path, description, output_type)

**Raises:**
- `ClassifierError`: If detector name is not found

##### `get_output_type_mapping() -> Dict[str, str]`

Get mapping of detector names to their output types.

**Returns:**
- `Dict[str, str]`: Dictionary mapping detector names to their output_type values

---

### **DetectorStrategy**

Abstract base class for all detection strategies.

```python
from classifier_router.core.detector.base import DetectorStrategy, DetectionResult
```

#### **Abstract Methods**

##### `detect(text: str) -> DetectionResult`

Detect patterns in the given text.

**Parameters:**
- `text` (str): The document text to analyze

**Returns:**
- `DetectionResult`: Detection outcome with detected flag and value

**Must be implemented by subclasses.**

##### `name -> str` (property)

Return the name of this detector strategy.

**Returns:**
- `str`: Human-readable name for logging and debugging

**Must be implemented by subclasses.**

---

### **LeaseHeaderDetector**

Detector for lease documents based on header patterns.

```python
from classifier_router.core.detector.lease_header import LeaseHeaderDetector

detector = LeaseHeaderDetector()
```

#### **Detection Patterns**
- "LEASE" (case-insensitive, word boundary)
- "RENTAL AGREEMENT"
- "TENANCY AGREEMENT"
- "LEASE AGREEMENT"

#### **Methods**

##### `detect(text: str) -> DetectionResult`

Detect lease patterns in document text.

**Parameters:**
- `text` (str): The document text to analyze

**Returns:**
- `DetectionResult`: detected=True and value="lease" if patterns found, otherwise detected=False

**Note:** Only searches in the first 500 characters (header area).

---

### **JurisdictionDetector**

Detector for jurisdiction codes based on state references.

```python
from classifier_router.core.detector.jurisdiction import JurisdictionDetector

detector = JurisdictionDetector()
```

#### **Supported Jurisdictions**
- **California (CA)**: "State of California", "California", "CA"
- **Massachusetts (MA)**: "State of Massachusetts", "Commonwealth of Massachusetts", "Massachusetts", "MA"
- **New York (NY)**: "State of New York", "New York", "NY"

#### **Methods**

##### `detect(text: str) -> DetectionResult`

Detect jurisdiction patterns in document text.

**Parameters:**
- `text` (str): The document text to analyze

**Returns:**
- `DetectionResult`: detected=True and value=jurisdiction_code if patterns found, otherwise detected=False

---

### **DetectorFactory**

Factory for creating detector instances from configuration.

```python
from classifier_router.core.factory import DetectorFactory

factory = DetectorFactory(config_path="config/detector_config.json")
```

#### **Methods**

##### `create_detector(detector_name: str) -> DetectorStrategy`

Create a detector instance by name.

**Parameters:**
- `detector_name` (str): Name of the detector to create

**Returns:**
- `DetectorStrategy`: Instantiated detector

**Raises:**
- `ConfigError`: If detector name is not found

##### `create_all_detectors() -> Dict[str, DetectorStrategy]`

Create instances of all configured detectors.

**Returns:**
- `Dict[str, DetectorStrategy]`: Dictionary mapping detector names to instances

##### `list_available_detectors() -> List[DetectorConfig]`

List all available detector configurations.

**Returns:**
- `List[DetectorConfig]`: List of detector configurations

##### `get_detector_config(detector_name: str) -> DetectorConfig`

Get configuration for a specific detector.

**Parameters:**
- `detector_name` (str): Name of the detector

**Returns:**
- `DetectorConfig`: Detector configuration

**Raises:**
- `ConfigError`: If detector name is not found

---

## 📊 **Data Models**

### **DetectionResult**

Result of a detection operation.

```python
@dataclass
class DetectionResult:
    detected: bool
    value: Optional[str] = None
```

**Attributes:**
- `detected` (bool): Whether the pattern was detected in the text
- `value` (Optional[str]): The detected value (e.g., document type, jurisdiction code)

### **ClassificationResult**

Aggregated results from multiple detectors.

```python
@dataclass
class ClassificationResult:
    text_length: int
    detector_results: Dict[str, DetectionResult]
    successful_detectors: Set[str]
    failed_detectors: Dict[str, str]
```

**Attributes:**
- `text_length` (int): Length of the input text that was classified
- `detector_results` (Dict[str, DetectionResult]): Dictionary mapping detector names to their results
- `successful_detectors` (Set[str]): Set of detector names that ran successfully
- `failed_detectors` (Dict[str, str]): Dict mapping detector names to their error messages

**Properties:**

##### `has_detections -> bool`

Check if any detector found a positive detection.

##### `detected_values -> Dict[str, str]`

Get all detected values from successful detectors.

**Methods:**

##### `get_output_by_type(detector_configs: Dict[str, str]) -> Dict[str, Optional[str]]`

Map detector results by their output types.

**Parameters:**
- `detector_configs` (Dict[str, str]): Dict mapping detector names to their output_type

**Returns:**
- `Dict[str, Optional[str]]`: Dict mapping output types to detected values (None if not detected)

---

## 🔄 **Kafka Integration**

### **KafkaService**

Main Kafka service for consuming and producing messages.

```python
from classifier_router.kafka.service import KafkaService
import asyncio

async def main():
    service = KafkaService()
    await service.initialize()
    await service.start()

asyncio.run(main())
```

#### **Methods**

##### `async initialize() -> None`

Initialize Kafka consumer, producer, and message processor.

**Raises:**
- `ClassifierError`: If initialization fails

##### `async start() -> None`

Start the main message processing loop.

**Note:** Runs until interrupted or shutdown signal received.

##### `async stop() -> None`

Stop the Kafka service gracefully.

##### `async cleanup() -> None`

Cleanup Kafka resources.

---

### **MessageProcessor**

Processes messages from Kafka using the classification router.

```python
from classifier_router.kafka.processor import MessageProcessor

processor = MessageProcessor(config_path="config/detector_config.json")
await processor.initialize()
```

#### **Methods**

##### `async initialize() -> None`

Initialize the classification router and cache output type mapping.

**Raises:**
- `ClassifierError`: If initialization fails

##### `async process_message(message_value: bytes) -> LLMRequestMessage`

Process a single message from the text-extraction topic.

**Parameters:**
- `message_value` (bytes): Raw message bytes from Kafka

**Returns:**
- `LLMRequestMessage`: Processed message ready for llm-requests topic

**Raises:**
- `ClassifierError`: If message processing fails

---

## 📨 **Message Schemas**

### **TextExtractionMessage**

Input message from text-extraction topic.

```python
from classifier_router.kafka.schemas import TextExtractionMessage

message = TextExtractionMessage(
    docId="doc_123",
    text="LEASE AGREEMENT\n\nThis lease..."
)
```

**Fields:**
- `docId` (str): Unique document identifier
- `text` (str): Extracted text content from the document

### **LLMRequestMessage**

Output message to llm-requests topic.

```python
from classifier_router.kafka.schemas import LLMRequestMessage

message = LLMRequestMessage(
    docId="doc_123",
    text="LEASE AGREEMENT\n\nThis lease...",
    docType="lease",
    jurisdictionCode="CA"
)
```

**Fields:**
- `docId` (str): Unique document identifier
- `text` (str): Original text content
- `docType` (Optional[str]): Detected document type (e.g., 'lease')
- `jurisdictionCode` (Optional[str]): Detected jurisdiction code (e.g., 'CA')

### **ClassificationMetadata**

Metadata about the classification process.

```python
from classifier_router.kafka.schemas import ClassificationMetadata

metadata = ClassificationMetadata(
    processing_time_ms=125.5,
    detectors_run=2,
    successful_detectors=2,
    failed_detectors=0,
    has_detections=True
)
```

**Fields:**
- `processing_time_ms` (float): Total processing time in milliseconds
- `detectors_run` (int): Number of detectors executed
- `successful_detectors` (int): Number of successful detectors
- `failed_detectors` (int): Number of failed detectors
- `has_detections` (bool): Whether any detections were found

---

## ⚙️ **Configuration**

### **DetectorConfig**

Configuration for a single detector.

```python
from classifier_router.config.config import DetectorConfig

config = DetectorConfig(
    name="lease_header_detector",
    class_path="classifier_router.core.detector.lease_header.LeaseHeaderDetector",
    description="Detects lease documents by header patterns",
    output_type="docType"
)
```

**Fields:**
- `name` (str): Unique identifier for the detector
- `class_path` (str): Full Python import path to the detector class
- `description` (str): Human-readable description of the detector
- `output_type` (str): Type of output this detector produces

### **DetectorRegistryConfig**

Configuration for the detector registry.

```python
from classifier_router.config.config import DetectorRegistryConfig

config = DetectorRegistryConfig(
    detectors=[detector_config1, detector_config2]
)
```

**Fields:**
- `detectors` (List[DetectorConfig]): List of detector configurations

### **Settings**

Application settings with environment variable support.

```python
from classifier_router.config.settings import settings

# Access Kafka settings
print(settings.kafka.bootstrap_servers)
print(settings.kafka.input_topic)

# Access application settings
print(settings.app.log_level)
print(settings.app.detector_config_path)
```

**Kafka Settings:**
- `bootstrap_servers`: Kafka broker addresses
- `consumer_group_id`: Consumer group ID
- `input_topic`: Input topic name
- `output_topic`: Output topic name
- `security_protocol`: Security protocol
- `sasl_mechanism`: SASL mechanism
- `sasl_username`: SASL username
- `sasl_password`: SASL password
- `max_poll_records`: Maximum records per poll
- `auto_offset_reset`: Offset reset policy

**Application Settings:**
- `log_level`: Logging level
- `log_format`: Log format type
- `log_file`: Log file path
- `detector_config_path`: Detector configuration file path
- `max_text_length`: Maximum text length
- `processing_timeout_seconds`: Processing timeout
- `idempotency_store_url`: Redis URL for idempotency
- `idempotency_ttl_hours`: TTL for idempotency keys

---

## 🚨 **Exceptions**

### **ClassifierError**

Base exception for classification-related errors.

```python
from classifier_router.common.exceptions import ClassifierError

try:
    result = router.classify(text)
except ClassifierError as e:
    print(f"Classification failed: {e}")
```

### **ConfigError**

Exception for configuration-related errors.

```python
from classifier_router.common.exceptions import ConfigError

try:
    factory = DetectorFactory("invalid_config.json")
except ConfigError as e:
    print(f"Configuration error: {e}")
```

---

## 📝 **Usage Examples**

### **Basic Classification**

```python
from classifier_router import ClassifierRouter

# Initialize router
router = ClassifierRouter()

# Classify document
text = "LEASE AGREEMENT\n\nState of California..."
result = router.classify(text)

# Check results
if result.has_detections:
    print(f"Document type: {result.detected_values.get('lease_header_detector')}")
    print(f"Jurisdiction: {result.detected_values.get('jurisdiction_detector')}")
else:
    print("No detections found")
```

### **Custom Detector Selection**

```python
# Run only specific detectors
result = router.classify_with_detectors(
    text="LEASE AGREEMENT...",
    detector_names=["lease_header_detector"]
)

# Get detector information
info = router.get_detector_info("lease_header_detector")
print(f"Detector: {info['description']}")
```

### **Kafka Message Processing**

```python
import asyncio
from classifier_router.kafka.service import KafkaService

async def run_service():
    service = KafkaService()
    try:
        await service.initialize()
        await service.start()  # Runs until interrupted
    except KeyboardInterrupt:
        await service.stop()

asyncio.run(run_service())
```

### **Custom Detector Implementation**

```python
from classifier_router.core.detector.base import DetectorStrategy, DetectionResult

class NDAAgreementDetector(DetectorStrategy):
    def detect(self, text: str) -> DetectionResult:
        if "NON-DISCLOSURE AGREEMENT" in text.upper():
            return DetectionResult(detected=True, value="nda")
        return DetectionResult(detected=False)
    
    @property
    def name(self) -> str:
        return "nda_detector"
```

---
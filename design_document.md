# Document Processing System Design

## Data Flow Overview

The system is a fully async pipeline. Messages pass between components via a message queue (e.g. Kafka, SQS). Each component enforces per-stage idempotency with a key `<docId>::<stageName>` in a fast KV store. User‐level dedup is applied at ingestion.

1. **Ingestion & User-Level Dedup**  
2. **Extractor**  
3. **Classifier & Router**  
4. **LLM Engine (Async Batch)**  
5. **Rules Engine (Validation & Auto-Fix)**  
6. **Formatter & Output Export**  
7. **Storage & Audit Log**  
8. **Monitoring & Quality Assurance**

## Component Roles & Responsibilities

### 1. Ingestion & User-Level Dedup  
- **File Hashing:** compute SHA-256 of raw upload  
- **Dedup Check:** if `fileHash` exists in “file registry,” return existing `docId` & outputs; otherwise generate new `docId` and record it  
- **Normalize:** Deskew/denoise scans, Word docs/Scans→PDF
- **Metadata:** tag `uploadTs`, `source`  
- **Idempotency:** write `docId::INGESTION` key
- **Emit:** `{"docId", "fileRef", "metadata"}` → `raw-docs`

### 2. Extractor  
- **Consumes:** `raw-docs`  
- **Native-Text PDFs:** PDFBox/Tika  
- **Scanned Images:** AWS Textract or Tesseract OCR  
- **Normalize:** encoding, language artifacts  
- **Idempotency:** skip if `docId::EXTRACTOR` exists  
- **Emit:** `{"docId", "text"}` → `text-extraction`

### 3. Classifier & Router  
- **Consumes:** `text-extraction`  
- **Doc-Type Detection:** regex on header (e.g. `^Lease\b`)  
- **Jurisdiction Detection:** regex on body (e.g. `\bState of California\b`)  
- **Idempotency:** skip if `docId::CLASSIFIER_ROUTER` exists  
- **Emit:** `{"docId", "text", "docType", "jurisdictionCode"}` → `llm-requests`


### 4. LLM Engine (Async Batch) 
- **Consumes:** `llm-requests` 
- **Batching Loop:** buffer up to N docs or wait T ms  
- **Prompt Builder:** combine texts + context into one LLM call, guardrails LLM for only essential outputs
- **Inference:** call LLM endpoint asynchronously  
- **Post-Process:** parse results, normalize formats, compute per-field confidences, flag low-confidence fields  
- **Idempotency:** skip publish if `docId::LLM_ENGINE` exists  
- **Emit:** `{"docId", "fields": { "TenantName": "Acme Corp", … }, "confidence": { "TenantName": 0.92, … }, "reviewFlags": [{"field":"TenantName","reason":"below-threshold"}]}` → `llm-responses`

### 5. Rules Engine (Validation & Auto-Fix)  
- **Consumes:** `llm-responses` 
- **Load Schema:** JSON-Schema or decision table for `docType.jurisdictionCode`  
- **Auto-Fix:** declarative transforms (dates → ISO 8601, trim/title-case, strip commas)  
- **Validate:** required fields, regex formats, mandatory blocks  
- **Flag:** unfixable/missing values in `reviewFlags`  
- **Audit:** append `{ruleId, outcome}` entries  
- **Idempotency:** skip if `docId::RULES_ENGINE` exists  
- **Emit:** `{docId, validatedFields, reviewFlags, auditLog}` → `validated-docs`

### 6. Formatter & Output Export  
- **Consumes:** `validated-docs`  
- **Form Filling:** merge `validatedFields` into PDF/Word templates via docxtpl or iText  
- **Structured Export:** serialize to JSON/CSV (with schema version & timestamp)  
- **Notifier:** send webhook or email with links + any flags  
- **Idempotency:** skip if `docId::FORMAT_EXPORT` exists  
- **Persist:** final artifacts to storage

### 7. Storage & Audit Log  
- **Encrypted Blobs:** store originals & outputs under customer-managed KMS keys  
- **Audit Ledger:** append-only store of every `<docId, stage, result>`  
- **Idempotency:** skip if `docId::STORAGE` exists

### 8. Monitoring & Quality Assurance  
- **Metrics:** queue depths, throughput (docs/sec), error rates, `reviewFlags` rate  
- **Alerts:** dedup-store availability, TTL-eviction anomalies, error spikes  
- **Sampling:** human audits to refine regex rules, transforms, and prompts

---

## Risk Identification & Mitigation Strategies

1. **Duplicate Processing & Audit Noise**  
   - *Mitigation:* per-stage idempotency + unique DB constraints  
2. **Dedup Store Availability**  
   - *Mitigation:* HA configuration (clustered Redis/Multi-AZ DynamoDB), fallback alerts  
3. **Stateful TTL Evictions**  
   - *Mitigation:* TTL ≥ max processing time (e.g. 24 hrs), monitor eviction metrics  
4. **Data Leakage & Unauthorized Access**  
   - *Mitigation:* TLS in transit, encryption at rest with KMS, strict RBAC, immutable audit logs  
5. **LLM Hallucinations & Extraction Errors**  
   - *Mitigation:* per-field confidence thresholds, schema checks, human-in-loop for flagged docs  
6. **Queue Backlogs & Throughput Spikes**  
   - *Mitigation:* auto-scale consumers, ingestion rate limits, dead-letter queues  
7. **Rule Drift & Maintenance Overhead**  
   - *Mitigation:* log “unknown” patterns, versioned config repo, quarterly rule coverage reviews  
8. **Vendor Lock-In & Model Outages**  
   - *Mitigation:* abstract LLM calls via LangChain (or similar), support multiple providers, fallback regex extractor, cache recent outputs  
9. **Compliance & Audit Requirements**  
   - *Mitigation:* append-only logs with component/template versions, queryable by `docId`  
10. **Upstream Poisoned Documents**  
    - *Mitigation:* pre-parser validation, sandboxing, quarantine queue for malformed inputs

---

## Monitoring & Quality Assurance

- **Operational Metrics:**  
  - Throughput (documents/sec)  
  - Queue depths & consumer lag  
  - Error rates per component  
  - Distribution of per-field confidence scores

- **Alerts & Dashboards:**  
  - Dedup-store health (availability, eviction anomalies)  
  - Spikes in `reviewFlags` or dead-letter queue size  
  - Model latency regressions

- **Human-in-Loop Sampling:**  
  - Periodically review a random subset of “passed” docs  
  - Feed corrections back into regex patterns, auto-fix specs, or prompt templates

- **Continuous Improvement:**  
  - Track error patterns over time  
  - Retrain or reconfigure components based on observed drift  
  - Conduct quarterly reviews of both rules and model performance

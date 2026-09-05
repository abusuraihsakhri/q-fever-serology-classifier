# Q Fever Serology Classifier

> **Domain:** Infectious Disease Surveillance & Microbiology
> **Reference Guidelines & Standards:** `CLSI M100, EUCAST & CDC NHSN Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Q Fever Phase I/II Serology & Chronic Phase Classifier
Interprets Coxiella burnetii Phase I and II IgG/IgM titers for acute vs chronic Q fever endocarditis.

Zero-dependency Python core with single and batch evaluation, plus an enterprise FastAPI REST API with multi-worker agent architecture.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- pip

### Quick Install
```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/q-fever-serology-classifier.git
cd q-fever-serology-classifier

# Install with web dependencies (for FastAPI server)
pip install -e ".[web]"

# Or install with development dependencies (includes pytest)
pip install -e ".[dev]"
```

### Security Configuration

**IMPORTANT:** You must set the `AUDIT_SECRET_KEY` environment variable before running the service. This key is used for HMAC-SHA256 audit trail signing.

```bash
# Generate a secure random key
python -c "import secrets; print(secrets.token_hex(32))"

# Set the environment variable
export AUDIT_SECRET_KEY="your-generated-key-here"
```

The key must be at least 32 characters long for cryptographic security.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Analytical Functions

- **`calculate_metrics()`** — Core domain algorithm that computes weighted scores from numeric inputs and classifies into Low/Standard, Moderate/Intermediate, or High/Severe tiers.
- **`process_single()`** — Evaluates a single case from CLI parameters.
- **`process_batch()`** — Processes batch CSV files with validation and error handling.

### 🤖 Enterprise Agent Architecture

- **InvariantQCWorker** — Primary mathematical & protocol boundary auditor
- **SafetyEscalationWorker** — Safety boundary & emergency interlock detection
- **ProtocolConformanceWorker** — Spec conformance & discordance checking
- **SystemSupervisor** — Multi-worker orchestrator with consensus building

---

## 📐 Classification Logic

The classifier computes a weighted score from input parameters:

```text
score = v1 + v2 * (1/2) + v3 * (1/3) + ...
```

Classification tiers:
- **Low / Standard** (score < 10.0): Standard monitoring or negative cutoff
- **Moderate / Intermediate** (10.0 ≤ score < 25.0): Close observation or secondary evaluation
- **High / Severe** (score ≥ 25.0): Urgent clinical intervention or primary positive finding

---

## 💻 CLI Usage

### 1. Single Case Evaluation
```bash
python -m q_fever_serology single --v1 14.5 --v2 4.2 --v3 1.8
```

### 2. Batch CSV Processing
```bash
python -m q_fever_serology batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI (requires web dependencies)
```bash
# Run audit task
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail
python cli.py verify-audit

# Start REST API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema (Batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Unique patient identifier | Required |
| `v1` | Primary measurement value | Required |
| `v2` | Secondary measurement value | Required |
| `v3` | Tertiary measurement value | Optional |

---

## 🌐 REST API

The FastAPI server provides these endpoints:

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | Health check and service metadata |
| `/metrics` | GET | Prometheus operational metrics |
| `/api/audit` | POST | Submit task for multi-worker evaluation |
| `/api/chat` | POST | Supervisory conversational assistant |
| `/api/audit/logs` | GET | Retrieve and verify HMAC audit trail |

### Example API Request
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-001",
    "target_identifier": "SPECIMEN-01",
    "primary_metric": 28.5,
    "secondary_metric": 14.2,
    "status_descriptor": "DISCORDANT_ANOMALY",
    "is_critical_flag": true
  }'
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker Compose
AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") docker-compose up -d

# Or build and run manually
docker build -t q-fever-serology-classifier .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" q-fever-serology-classifier
```

---

## 📁 Project Structure

```
q-fever-serology-classifier/
├── agents/                  # Enterprise agent architecture
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Multi-worker orchestrator
│   ├── workers.py          # Specialized domain workers
│   ├── llm_factory.py      # LLM provider factory
│   ├── learning.py         # Bayesian calibration engine
│   ├── metrics.py          # Prometheus metrics collector
│   └── streamer.py         # WebSocket telemetry broadcaster
├── tests/                  # Test suite
│   ├── test_api.py         # API endpoint tests
│   ├── test_enrichment.py  # Enrichment engine tests
│   └── test_q_fever_serology_classifier.py  # Core classifier tests
├── web/                    # Operations console (HTML)
├── q_fever_serology.py     # Core algorithm (zero-dependency)
├── cli.py                  # Enterprise CLI entry point
├── enrichment.py           # Enrichment feature engines
├── simulator.py            # High-throughput stress tester
├── pyproject.toml          # Project configuration
├── Dockerfile              # Container build
└── docker-compose.yml      # Container orchestration
```

# Document Classifier

An AI-powered document classification system that ingests scanned documents via SFTP, classifies them using a deep learning model, and exposes results through a secured REST API.

---

## Overview

The system accepts TIFF documents uploaded by external scanner vendors over SFTP. Each document is automatically classified into one of 16 document categories using a fine-tuned ConvNeXt neural network. Classification results are stored in a PostgreSQL database alongside annotated overlay images, and are accessible through an authenticated, role-based REST API.

---

## Document Classes

The model classifies documents into 16 categories derived from the RVL-CDIP dataset:

`letter`, `form`, `email`, `handwritten`, `advertisement`, `scientific_report`, `scientific_publication`, `specification`, `file_folder`, `news_article`, `budget`, `invoice`, `presentation`, `questionnaire`, `resume`, `memo`

---

## System Architecture

```
SFTP Upload
    │
    ▼
SFTP Server (port 2222)
    │
    ▼  polls every 5 seconds
SFTP Ingest Worker
    ├── validates TIFF files
    ├── groups arrivals into 30-second batch windows
    ├── uploads originals to MinIO (/documents bucket)
    ├── creates Batch record in PostgreSQL (state: PENDING)
    └── enqueues inference job in Redis Queue
                │
                ▼
        Redis Queue (RQ)
                │
                ▼
        Inference Worker
            ├── updates Batch state → PROCESSING
            ├── downloads TIFF from MinIO
            ├── preprocesses image (grayscale → 224×224 → normalize)
            ├── runs ConvNeXt model (softmax → top class + confidence)
            ├── generates annotated PNG overlay
            ├── uploads overlay to MinIO (/overlays bucket)
            ├── writes Prediction record to PostgreSQL
            ├── invalidates Redis cache
            └── updates Batch state → COMPLETE (or FAILED)
                        │
                        ▼
                 PostgreSQL (source of truth)
                        │
                        ▼
                 FastAPI REST API (port 8000)
                    ├── JWT authentication
                    ├── Casbin RBAC enforcement
                    └── Redis HTTP caching
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.104, Uvicorn |
| ML Model | PyTorch 2.4+, torchvision ConvNeXt Tiny |
| Database | PostgreSQL 16, SQLAlchemy 2.0, Alembic |
| Async DB Driver | asyncpg |
| Sync DB Driver (workers) | psycopg2-binary |
| Job Queue | Redis 7, RQ (Redis Queue) |
| Object Storage | MinIO (S3-compatible) |
| Authentication | fastapi-users 13, JWT (HS256, 1h lifetime) |
| Authorization | Casbin + casbin-sqlalchemy-adapter |
| Caching | fastapi-cache2, redis.asyncio |
| Secrets Management | HashiCorp Vault 1.15 |
| SFTP Client | Paramiko |
| Image Processing | Pillow |
| Logging | python-json-logger (structured JSON) |
| Configuration | Pydantic Settings, python-dotenv |
| Containerization | Docker Compose |
| CI/CD | GitHub Actions |
| Testing | pytest, pytest-asyncio, httpx |

---

## Project Structure

```
Document-Classifier/
├── app/
│   ├── main.py                     # FastAPI entry point, router mounting
│   ├── api/
│   │   ├── routers/                # HTTP route handlers
│   │   │   ├── auth.py             # Login, registration
│   │   │   ├── users.py            # Profile, role management
│   │   │   ├── batches.py          # Batch listing and detail
│   │   │   ├── predictions.py      # Recent predictions, relabeling
│   │   │   └── audit.py            # Audit log access
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── deps/                   # FastAPI dependencies (auth, permissions, cache)
│   │   └── middleware/
│   │       └── request_id.py       # X-Request-ID propagation
│   ├── auth/
│   │   ├── jwt.py                  # JWT strategy and bearer transport
│   │   ├── users.py                # fastapi-users UserManager
│   │   └── casbin.py               # Casbin RBAC engine, policy seeding
│   ├── classifier/
│   │   ├── models/
│   │   │   ├── classifier.pt       # Trained ConvNeXt model weights
│   │   │   ├── model_card.json     # SHA256, accuracy metrics, class breakdown
│   │   │   └── labels.json         # 16 document class names
│   │   ├── inference/
│   │   │   ├── predictor.py        # load_model(), predict(), SHA256 validation
│   │   │   ├── preprocessing.py    # Image preprocessing pipeline
│   │   │   ├── postprocessing.py   # InferenceResult dataclass
│   │   │   └── overlays.py         # Annotated PNG overlay generation
│   │   ├── training/
│   │   │   └── train_colab.ipynb   # Training notebook (offline, not in production)
│   │   └── eval/
│   │       ├── golden.py           # Golden set regression test runner
│   │       ├── golden_expected.json
│   │       └── golden_images/      # 50 TIFF files for CI validation
│   ├── services/                   # Business logic layer
│   ├── repositories/               # Database access layer
│   ├── domain/                     # Domain model definitions
│   ├── db/                         # ORM models, sessions, migrations
│   ├── core/
│   │   ├── config.py               # Pydantic settings (all env vars)
│   │   ├── security.py             # JWT secret resolution via Vault
│   │   ├── constants.py            # Enums: BatchStatus, Role, AuditAction
│   │   └── startup.py              # Application startup hooks
│   ├── infra/
│   │   ├── blob/minio_client.py    # TIFF download, PNG upload
│   │   ├── queue/rq_queue.py       # Job enqueueing
│   │   ├── cache/redis_cache.py    # fastapi-cache2 initialization
│   │   ├── vault/vault_client.py   # Vault secret loading
│   │   ├── sftp/watcher.py         # SFTPWatcher (5s poll loop)
│   │   └── logging/logger.py       # Structured JSON logger
│   └── workers/
│       ├── inference_worker.py     # Consumes RQ jobs, runs model, saves predictions
│       └── sftp_ingest_worker.py   # Polls SFTP, validates, batches, enqueues
├── docker/
│   ├── api.Dockerfile
│   ├── worker.Dockerfile
│   ├── ingest.Dockerfile
│   ├── startup.sh
│   └── vault/
│       ├── init-vault.sh           # Bootstrap Vault secrets
│       └── bootstrap.py
├── docker-compose.yml
├── .env.example
├── alembic.ini
├── requirements.txt
├── requirements-ml.txt             # Inference-only subset for worker container
├── pyproject.toml                  # Ruff config, pytest settings
├── scripts/                        # Dev utilities (seed, reset, benchmark)
└── tests/
    ├── api/
    ├── classifier/
    ├── infra/
    ├── services/
    └── smoke/                      # Docker Compose integration tests
```

---

## ML Model

**Architecture:** ConvNeXt Tiny (torchvision), fine-tuned on RVL-CDIP

**Performance:**
- Top-1 accuracy: 90.01%
- Top-5 accuracy: 98.61%

**Inference pipeline:**
1. Load TIFF with Pillow
2. Convert to grayscale, then 3-channel RGB
3. Resize to 224×224
4. Normalize with ImageNet statistics (mean `[0.485, 0.456, 0.406]`, std `[0.229, 0.224, 0.225]`)
5. Forward pass → softmax over 16 classes → take argmax
6. Annotate original image with predicted label and confidence score

**Safety:** At worker startup, the SHA256 hash of `classifier.pt` is verified against `model_card.json`. A mismatch causes the worker to refuse to start.

---

## API Endpoints

All endpoints (except `/auth/*`) require a `Bearer` JWT token in the `Authorization` header.

### Authentication
| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/jwt/login` | Get a JWT access token |

### Users
| Method | Path | Roles | Description |
|---|---|---|---|
| `GET` | `/users/me` | all | Get current user profile |
| `PATCH` | `/users/{uid}/role` | admin | Change a user's role |

### Batches
| Method | Path | Roles | Description |
|---|---|---|---|
| `GET` | `/batches` | all | List all batches (cached 60s) |
| `GET` | `/batches/{bid}` | all | Get batch detail (cached 60s) |

### Predictions
| Method | Path | Roles | Description |
|---|---|---|---|
| `GET` | `/predictions/recent` | all | List recent predictions (cached 30s) |
| `PATCH` | `/predictions/{pid}/label` | reviewer | Correct label on low-confidence predictions (confidence < 0.7 only) |

### Audit
| Method | Path | Roles | Description |
|---|---|---|---|
| `GET` | `/audit-log` | admin, auditor | View audit log with optional filters |

---

## Roles and Permissions

| Action | admin | reviewer | auditor |
|---|:---:|:---:|:---:|
| View batches | ✓ | ✓ | ✓ |
| View predictions | ✓ | ✓ | ✓ |
| Relabel predictions (confidence < 0.7) | | ✓ | |
| View audit log | ✓ | | ✓ |
| Change user roles | ✓ | | |

Permissions are enforced by Casbin policies stored in PostgreSQL. Role changes take effect on the next request. The system prevents the last remaining admin from demoting themselves.

---

## Audit Logging

Every state-changing action is recorded in the `audit_logs` table:

| Action | Trigger |
|---|---|
| `CHANGE_ROLE` | Admin changes a user's role |
| `RELABEL_PRED` | Reviewer corrects a prediction label |
| `CHANGE_STATE` | Batch state transitions |

Each entry captures: actor, action, target type, target ID, previous value (JSON), new value (JSON), and timestamp.

---

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Running Locally

```bash
# 1. Copy the environment template
cp .env.example .env

# 2. Start all services
docker compose up -d --build

# 3. Register a user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'

# 4. Log in to get a JWT token
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=user@example.com&password=yourpassword'

# 5. Use the token to call the API
curl -H "Authorization: Bearer <token>" http://localhost:8000/batches
```

### Uploading a Document

```bash
sftp -P 2222 docuser@localhost
# Password: docpass
put /path/to/document.tiff /uploads/
```

The ingest worker picks up the file within 5 seconds, batches it into a 30-second window, and enqueues it for inference. The result is available via the API once the inference worker completes the job.

### Interactive API Docs

Swagger UI is available at: `http://localhost:8000/docs`

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"
```

Migrations run automatically at container startup via the `migrate` service in Docker Compose.

---

## Testing

```bash
# Full test suite
pytest tests/ -v

# Smoke tests (requires running Docker Compose stack)
pytest tests/smoke/ -v --timeout=360

# Golden set regression (CI check — fails if model output drifts)
PYTHONPATH=. python app/classifier/eval/golden.py

# Lint
ruff check .
```

---

## CI/CD

GitHub Actions runs on every push to `main` and `feat/*` branches:

1. **Lint** — `ruff check .`
2. **Golden set** — runs the 50-image regression suite; any confidence drift greater than `1e-6` fails the build
3. **Smoke tests** — spins up the full Docker Compose stack and runs integration tests

---

## Configuration

All configuration is loaded from environment variables (see `.env.example`). Secrets (database password, JWT secret, MinIO credentials) are injected at runtime from HashiCorp Vault. The API and workers refuse to start if Vault is unreachable.

Key settings managed by Vault:

| Secret Path | Variable |
|---|---|
| `kv/postgres/password` | `POSTGRES_PASSWORD` |
| `kv/auth/jwt_secret` | `JWT_SECRET` |
| `kv/minio/root_user` | `MINIO_ROOT_USER` |
| `kv/minio/root_password` | `MINIO_ROOT_PASSWORD` |

---

## Services Summary

| Service | Port | Description |
|---|---|---|
| FastAPI | 8000 | REST API |
| PostgreSQL | 5432 | Relational database |
| Redis | 6379 | Job queue and HTTP cache |
| MinIO S3 API | 9000 | Object storage |
| MinIO Console | 9001 | MinIO web UI |
| HashiCorp Vault | 8200 | Secrets management |
| SFTP Server | 2222 | Document upload entry point |

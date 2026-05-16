<!-- Owner: ALL -->
# ARCHITECTURE OVERVIEW

## Project Summary

This project is an internal AI-powered document classification system that processes scanned TIFF documents uploaded through SFTP, classifies them using a ConvNeXt model, stores predictions and artifacts, and exposes results through an authenticated FastAPI API with role-based access control.

The system is fully containerized using Docker Compose and follows a strict layered architecture.

---

# High-Level System Flow

```text
Scanner Vendor
      ↓
SFTP Server
      ↓
SFTP-Ingest Worker
      ↓
MinIO Blob Storage
      ↓
Redis Queue (RQ)
      ↓
Inference Worker
      ↓
ConvNeXt Classifier
      ↓
PostgreSQL Database
      ↓
FastAPI API
      ↓
Authenticated Users
```

---

# Main Components

## 1. SFTP Server

Technology:
- atmoz/sftp

Purpose:
- receives incoming TIFF document uploads from external systems

Behavior:
- stores uploaded files in a shared folder
- does not perform validation or inference

---

## 2. SFTP-Ingest Worker

Purpose:
- polls the SFTP folder every few seconds
- validates uploaded files
- uploads valid TIFFs to MinIO
- creates processing jobs in Redis queue

Responsibilities:
- reject malformed files
- quarantine invalid uploads
- create batch records


---

## 3. MinIO Blob Storage

Purpose:
- stores:
  - original TIFF files
  - overlay PNGs

Behavior:
- acts as S3-compatible blob storage


---

## 4. Redis Queue (RQ)

Purpose:
- stores asynchronous inference jobs

Behavior:
- decouples ingestion from inference
- prevents blocking uploads

Example Job Payload:

```json
{
  "batch_id": 12,
  "blob_path": "raw/file1.tiff"
}
```

---

## 5. Inference Worker

Purpose:
- consumes jobs from Redis queue
- downloads TIFFs from MinIO
- runs ConvNeXt inference
- generates predictions and overlays
- stores results in PostgreSQL

Responsibilities:
- validate model SHA256
- refuse startup if model invalid
- generate overlay PNGs

---

## 6. ConvNeXt Classifier

Model:
- ConvNeXt Tiny (torchvision)

Dataset:
- RVL-CDIP

Outputs:
- predicted document class
- confidence score

Artifacts:
- classifier.pt
- model_card.json
- golden set

---

## 7. PostgreSQL Database

Purpose:
- source of truth for system state

Stores:
- users
- batches
- predictions
- audit logs
- relabel actions

---

## 8. Repository Layer

Purpose:
- handles raw SQLAlchemy queries only

Rules:
- no business logic
- no cache invalidation
- no HTTP exceptions

---

## 9. Service Layer

Purpose:
- handles:
  - business logic
  - transaction boundaries
  - cache invalidation
  - audit logging

Rules:
- routers never touch repositories directly

---

## 10. Authentication System

Technology:
- fastapi-users
- JWT

Purpose:
- registration
- login
- identity validation

---

## 11. Authorization System

Technology:
- Casbin

Roles:
- admin
- reviewer
- auditor

Purpose:
- enforce role-based permissions

Behavior:
- permissions update dynamically
- role changes apply immediately

---

## 12. API Layer

Technology:
- FastAPI

Purpose:
- expose authenticated endpoints

Rules:
- API never runs inference
- routers only call services

---

## 13. Cache System

Technology:
- Redis
- fastapi-cache2

Cached Endpoints:
- GET /me
- GET /batches
- GET /batches/{id}
- GET /predictions/recent

Rules:
- invalidation occurs only in service layer

---

## 14. Vault Secrets System

Technology:
- HashiCorp Vault

Purpose:
- store secrets securely

Stores:
- JWT signing keys
- DB credentials
- MinIO credentials

Behavior:
- API and workers refuse startup if Vault unavailable

---

## 15. CI/CD

Technology:
- GitHub Actions

Checks:
- lint
- type-check
- Docker build
- golden-set replay
- compose smoke test

---

# Layered Architecture Rules

## API Layer
- HTTP only
- no SQLAlchemy access
- no cache invalidation

## Service Layer
- business logic only
- transaction boundaries
- cache invalidation

## Repository Layer
- database queries only
- no HTTP logic
- no business rules

## Domain Layer
- pydantic domain models only

## Infra Layer
- external systems adapters only

---

# Runtime Flows

## Document Processing Flow

```text
TIFF uploaded via SFTP
        ↓
Ingest worker validates file
        ↓
TIFF uploaded to MinIO
        ↓
Job pushed into Redis queue
        ↓
Inference worker consumes job
        ↓
Model predicts class
        ↓
Prediction stored in PostgreSQL
        ↓
Overlay PNG uploaded to MinIO
        ↓
Cache invalidated
        ↓
Prediction exposed through API
```

---

## Authentication Flow

```text
User login
    ↓
JWT generated
    ↓
JWT attached to future requests
```

---

## Authorization Flow

```text
Request received
    ↓
JWT validated
    ↓
Casbin checks permissions
    ↓
Request allowed or denied
```

---

# Failure Handling

## Vault Unavailable
- API refuses startup

## Missing Model
- worker refuses startup

## Invalid SHA256
- worker refuses startup

## Empty Casbin Policies
- API refuses startup

## MinIO Failure
- inference job retried
- batch marked failed after retry limit

## Invalid TIFF Upload
- file quarantined
- structured log emitted

---

# Logging

Structured JSON logs include:
- request_id
- batch_id
- timestamps
- worker status
- errors

Request IDs propagate across:
- API
- queue
- worker

---

# Golden Set Validation

A fixed 50-image golden set ensures:
- deterministic predictions
- reproducible outputs

CI fails if:
- labels differ
- confidence scores differ beyond tolerance
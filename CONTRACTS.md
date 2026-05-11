<!--Used By all-->

# SYSTEM CONTRACTS

This document defines shared contracts between system components.

All team members must follow these schemas exactly.

---

# Shared Enums

## BatchStatus

```python
class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
```

---

# Roles

```text
admin
reviewer
auditor
```

---

# Queue Contracts

## Inference Job Payload

Produced By:
- SFTP-Ingest Worker

Consumed By:
- Inference Worker

Schema:

```json
{
  "batch_id": 12,
  "blob_path": "raw/file1.tiff",
  "request_id": "uuid-string"
}
```

Fields:

| Field | Type | Description |
|---|---|---|
| batch_id | int | batch identifier |
| blob_path | str | MinIO TIFF path |
| request_id | str | tracing identifier |

---

# Prediction Contract

Produced By:
- Inference Worker

Consumed By:
- Services / Database Layer

Schema:

```json
{
  "batch_id": 12,
  "filename": "invoice1.tiff",
  "predicted_label": "invoice",
  "confidence": 0.9321,
  "overlay_path": "overlays/invoice1.png"
}
```

---

# API Contracts

## GET /batches/{id}

Response:

```json
{
  "id": 12,
  "status": "complete",
  "created_at": "2026-05-11T10:00:00Z",
  "documents": [
    {
      "filename": "invoice1.tiff",
      "predicted_label": "invoice",
      "confidence": 0.9321,
      "overlay_url": "/overlays/invoice1.png"
    }
  ]
}
```

---

## GET /predictions/recent

Response:

```json
[
  {
    "batch_id": 12,
    "predicted_label": "invoice",
    "confidence": 0.9321
  }
]
```

---

## PATCH /users/{id}/role

Request:

```json
{
  "role": "reviewer"
}
```

Response:

```json
{
  "message": "role updated successfully"
}
```

---

# Database Contracts

## predictions Table

| Column | Type |
|---|---|
| id | integer |
| batch_id | integer |
| filename | string |
| predicted_label | string |
| confidence | float |
| corrected_label | string nullable |
| overlay_path | string |
| created_at | datetime |

---

## batches Table

| Column | Type |
|---|---|
| id | integer |
| status | string |
| source_path | string |
| created_at | datetime |

---

## audit_logs Table

| Column | Type |
|---|---|
| id | integer |
| actor_id | integer |
| action | string |
| target | string |
| timestamp | datetime |

---

# Cache Contracts

Cached Endpoints:

```text
GET /me
GET /batches
GET /batches/{id}
GET /predictions/recent
```

Invalidation Rules:

| Action | Cache Invalidated |
|---|---|
| role change | /me |
| new prediction | /batches |
| relabel prediction | /predictions/recent |

---

# Model Contracts

## Model Validation

Startup checks:

```text
classifier.pt exists
SHA256 matches model_card.json
top-1 accuracy >= README threshold
```

Failure:
- worker refuses startup

---

# Golden Set Contract

Golden set replay requires:

```text
identical labels
confidence tolerance <= 1e-6
```

Failure:
- CI fails

---

# Overlay Contract

Overlay PNG requirements:
- PNG format
- includes:
  - predicted label
  - confidence score

Example Path:

```text
overlays/invoice1.png
```

---

# Security Contracts

## Secrets

All secrets must come from Vault.

Forbidden:
- hardcoded passwords
- committed credentials

---

# Logging Contracts

All logs must contain:

```json
{
  "request_id": "...",
  "timestamp": "...",
  "service": "...",
  "level": "..."
}
```
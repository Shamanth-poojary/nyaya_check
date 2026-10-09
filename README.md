# NyayaCheck — Legal Metrology AI Verification Platform

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-3.7.0-red.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Next.js](https://img.shields.io/badge/Next.js-16.3.5-black.svg)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg)](https://react.dev/)
[![Express](https://img.shields.io/badge/Express-4.21-lightgrey.svg)](https://expressjs.com/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-v4-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-Proprietary-orange.svg)]()

**NyayaCheck** is an integrated AI-powered enforcement and verification platform built for statutory compliance auditing under the **Legal Metrology (Packaged Commodities) Rules, 2011** and the **Legal Metrology Act, 2009**.

Designed for Legal Metrology officers, state enforcement controllers, and enterprise packaging compliance teams, NyayaCheck accelerates on-site packaging inspections from minutes to seconds — capturing package labels, extracting statutory declarations, validating them against the law, and generating court-admissible, tamper-evident **Spot Panchnama Memos** complete with Section 65B Indian Evidence Act certificates.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Statutory Compliance Rules Engine](#statutory-compliance-rules-engine)
- [Platform Features](#platform-features)
- [Quick Start Guide](#quick-start-guide)
  - [Prerequisites](#prerequisites)
  - [1. OCR & Rules Microservice (`ocr-service`)](#1-ocr--rules-microservice-port-8000)
  - [2. Authentication Backend (`backend`)](#2-authentication-backend-port-5000)
  - [3. Frontend Application (`frontend`)](#3-frontend-application-port-3000)
  - [4. Docker Deployment](#4-docker-deployment)
- [Environment Configuration](#environment-configuration)
- [API Reference](#api-reference)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Evidence & Panchnama Dossier Generation](#evidence--panchnama-dossier-generation)
- [Directory Layout](#directory-layout)
- [Legal & Compliance Notice](#legal--compliance-notice)

---

## System Architecture

NyayaCheck follows a decoupled, three-tier microservice architecture:

```
                                    ┌─────────────────────────────────────────────────┐
                                    │        Frontend Application                     │
                                    │        Next.js 16 (App Router) + React 19       │
                                    │        Tailwind CSS v4 + jsPDF                  │
                                    │        Port 3000                                │
                                    └───────────────┬─────────────────┬───────────────┘
                                                    │                 │
                                Direct Multipart    │                 │ Authentication &
                                OCR Scans & Audits  │                 │ User Sessions
                                                    ▼                 ▼
              ┌───────────────────────────────────────────┐   ┌───────────────────────────────────────────┐
              │      OCR & Rules Microservice             │   │       Authentication Backend API          │
              │      FastAPI + PaddleOCR 3.7 + OpenCV     │   │       Node.js Express (ESM)               │
              │      Pydantic v2 + Statutory Engine       │   │       PostgreSQL Connection Pool          │
              │      Port 8000                            │   │       Port 5000                           │
              └───────────────────────────────────────────┘   └───────────────────────────────────────────┘
```

1. **Frontend (`frontend/`)**: Client portal providing dual role-based workflows (Field Inspector & Central Administrator), industrial camera viewfinder with flashlight & rear-facing camera support, multi-angle upload, real-time extraction HUD, and client-side cryptographic Panchnama PDF export.
2. **OCR Microservice (`ocr-service/`)**: Independent Python microservice running PaddleOCR recognition, row-clustering split-line normalization, visual contrast/clearance analysis, multi-image evidence merging, and the Legal Metrology statutory rules engine.
3. **Backend API (`backend/`)**: Node.js Express service backed by PostgreSQL for secure inspector credential management, role-based access control (RBAC), and session cookie management.

---

## Statutory Compliance Rules Engine

The rules engine evaluates packaging declarations against the **Legal Metrology (Packaged Commodities) Rules, 2011 (PCR 2011)**:

| PCR 2011 Rule | Statutory Mandate | Automated Check | Severity |
| :--- | :--- | :--- | :--- |
| **Rule 6(1)(a)** | Generic / Common Commodity Identity | Verifies commodity identity presence on label and Principal Display Panel (PDP). | `blocking` |
| **Rule 6(1)(b)** | Name & Complete Address of Manufacturer / Packer / Importer | Extracts party block; flags missing entity or missing imported declarations. | `blocking` |
| **Rule 6(1)(c)** | Net Quantity Declaration | Validates declared quantity against standardized unit symbols per Rules 11–13. | `blocking` |
| **Rule 6(1)(d)** | Month & Year of Manufacture / Packing / Import | Validates date formatting (`MM/YYYY` or `Month YYYY`); checks forward-dating. | `blocking` |
| **Rule 6(1)(e)** | Maximum Retail Price (MRP) & Unit Sale Price (USP) | Checks mandatory "incl. of all taxes" wording and USP calculation for qualifying quantities. | `blocking` |
| **Rule 6(1)(n)** | Consumer Grievance Care Cell | Mandates presence of contact person, telephone number, and email address. | `warning` |
| **Rule 7 & 8** | Principal Display Panel (PDP) Dimensions | Calculates PDP area and validates placement proportion. | `warning` |
| **Rule 9 & 10** | Legibility, Contrast & Prominence | Computes grayscale standard-deviation contrast across field crops. | `warning` |
| **Rule 14 (Table-I)** | Minimum Numeral & Letter Height | Audits minimum character height as a percentage of PDP area. | `warning` |
| **Rule 15** | Clearance & Spatial Separation | Evaluates boundary whitespace surrounding declared net quantity. | `info` |
| **Second Schedule** | Standard Package Quantities | Verifies commodity sizes against prescribed statutory pack sizes. | `warning` |

---

## Platform Features

### 1. Field Inspector Workflow (`/inspector`)
- **Industrial Camera Viewfinder**: Built with HTML5 `getUserMedia`, prioritized for mobile/tablet rear lenses (`facingMode: environment`) with grid guidelines, torch/flashlight toggles, and instant snapshot preview.
- **Multi-Angle Evidence Capture**: Simultaneously attach and inspect front PDP, back label, nutritional panels, barcode/batch panels, and MRP stamp.
- **CLAHE Adaptive Contrast**: Optional Contrast Limited Adaptive Histogram Equalization for glossy, reflective, or low-contrast packages.
- **Live Statutory HUD**: Real-time extraction cards for MRP, Net Quantity, Unit Sale Price, Dates, Batch Number, and Manufacturer details with confidence ratings and bounding-box coordinates.
- **Statutory Audit Matrix**: Interactive findings breakdown detailing passed checks, actionable deficits, statutory legal citations, and corrective recommendations.

### 2. Spot Panchnama & Evidence Generation
- **Court-Admissible PDF Export**: One-click generation of statutory Panchnama inspection memos formatted according to standard enforcement department templates.
- **Section 65B Indian Evidence Act Certification**: Automated tamper-evident electronic certificate embedded with officer badge, timestamp, and SHA-256 digital signature hashes.
- **Bulk Ledger Export**: Export multi-record Panchnama packages in landscape PDF or CSV format for regional tribunal submission.

### 3. Central Administrator Portal (`/admin`)
- **Operational Dashboard**: System-wide compliance KPIs, deficit breakdown charts, and inspection throughput tracking.
- **Statutory Audit Trail (`/admin/audit-log`)**: Immutable event log tracking every scan, report attestation, login event, and parameter modification.
- **User Governance (`/admin/manage-users`)**: Administrative user onboarding, inspector badge assignment, and role configuration.

---

## Quick Start Guide

### Prerequisites
- **Python**: Version 3.12 or 3.13 (64-bit)
- **Node.js**: Version 18.x or 20.x+
- **PostgreSQL**: Local instance or remote connection URI (optional for OCR-only mode)

---

### 1. OCR & Rules Microservice (Port 8000)

```powershell
# Navigate to OCR service directory
cd ocr-service

# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\activate          # On Linux/macOS: source venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt

# Start FastAPI microservice
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Probe**: `http://localhost:8000/v1/health`
- **Readiness Probe**: `http://localhost:8000/v1/ready`
- **Interactive Swagger Documentation**: `http://localhost:8000/docs`

> [!NOTE]
> On the very first launch, PaddleOCR downloads its lightweight detection and recognition models (~15MB). The application caches these models locally for subsequent sub-second inferences.

---

### 2. Authentication Backend (Port 5000)

```powershell
# Navigate to backend directory
cd backend

# Install Node dependencies
npm install

# Run database migrations (seeds default admin user)
npm run migrate

# Start Express server
npm start
```

- **API Root**: `http://localhost:5000/api`
- **Default Admin Account**: `admin@example.com` / `admin123`

---

### 3. Frontend Application (Port 3000)

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

- **Application Portal**: [http://localhost:3000](http://localhost:3000)
- **Inspector Scanner**: [http://localhost:3000/inspector/new-scan](http://localhost:3000/inspector/new-scan)
- **Inspection Ledger**: [http://localhost:3000/inspector/reports](http://localhost:3000/inspector/reports)
- **Admin Dashboard**: [http://localhost:3000/admin/dashboard](http://localhost:3000/admin/dashboard)

---

### 4. Docker Deployment

Deploy the containerized OCR Microservice with pre-baked model weights (eliminating cold-start latencies):

```powershell
cd ocr-service

# Build and run with Docker Compose
docker compose up -d --build
```

The service will be accessible at `http://localhost:8000` with pre-warmed OCR engines and production Gunicorn concurrency (`WEB_CONCURRENCY=2`).

---

## Environment Configuration

### `ocr-service/.env`
| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `MAX_IMAGES_PER_REQUEST` | `10` | Maximum photos permitted in a single multi-angle package audit. |
| `MAX_FILE_SIZE_MB` | `15` | Maximum upload size per individual image. |
| `ALLOWED_CONTENT_TYPES` | `["image/jpeg", "image/png", "image/webp"]` | Whitelisted MIME types. |
| `PREPROCESS_ENABLED_DEFAULT`| `false` | Default status of OpenCV CLAHE / Denoise preprocessing. |
| `API_KEY` | *(empty)* | Optional API key string; if specified, enforces `X-API-Key` header on all extraction routes. |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:3000", ...]` | Allowed client origins for browser fetch calls. |
| `LOG_LEVEL` | `INFO` | Application log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `WEB_CONCURRENCY` | `2` | Gunicorn worker process count inside Docker. |

### `backend/.env`
| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `PORT` | `5000` | HTTP port for the Express authentication server. |
| `DATABASE_URL` | *(Postgres connection string)* | External or local PostgreSQL connection URI. |
| `FRONTEND_URL` | `http://localhost:3000` | Allowed origin for credentialed CORS cookies. |
| `JWT_SECRET` | `SIH2024SecretKey` | HMAC secret key used to sign session tokens. |
| `JWT_EXPIRES_IN` | `24h` | Validity duration for inspector session tokens. |
| `ADMIN_EMAIL` | `admin@example.com` | Seed administrator account email. |
| `ADMIN_PASSWORD` | `admin123` | Seed administrator password. |

### `frontend/.env.local` (Optional overrides)
| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_OCR_URL` | `http://localhost:8000` | Target URL for the Python OCR & Rules Microservice. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:5000` | Target URL for the Express authentication backend. |

---

## API Reference

### OCR & Compliance Endpoints (`ocr-service`)

#### 1. Full Statutory Compliance Audit
`POST /v1/check` (aliases: `/check`)

Processes one or more packaging photos end-to-end, executing OCR, classification, visual analysis, and Legal Metrology rule checks.

- **Request Type**: `multipart/form-data`
- **Parameters**:
  - `images`: One or more image binary files (JPEG, PNG, WebP).
  - `preprocess` *(boolean, optional)*: Enable CLAHE contrast and denoising.
  - `format` *(query param, optional)*: `json` (default) or `markdown`.
- **Response**: `ComplianceReport` JSON object (or formatted Markdown when requested).

```bash
curl -X POST "http://localhost:8000/v1/check?format=json" \
  -F "images=@ocr-service/test_images/clean/sample.png"
```

```json
{
  "schemaVersion": "4.0",
  "summary": {
    "status": "compliant",
    "totalRules": 9,
    "passedCount": 9,
    "deficitCount": 0,
    "reviewCount": 0,
    "verdict": "Product satisfies statutory declarations under Legal Metrology Rules, 2011."
  },
  "product": {
    "commodityName": "Turmeric Powder",
    "netQuantity": "100 g",
    "mrp": "Rs 42.00",
    "dates": "08/2026",
    "manufacturerName": "Everest Food Products Pvt Ltd"
  },
  "rules": [
    {
      "ruleId": "rule_6_1_e_mrp",
      "ruleReference": "Rule 6(1)(e)",
      "passed": true,
      "severity": "blocking",
      "message": "Declared MRP Rs 42.00 with mandatory 'incl. of all taxes' verified."
    }
  ]
}
```

#### 2. Raw Text & Field Extraction
- `POST /v1/extract`: Single-image OCR and field classification.
- `POST /v1/extract/multi`: Multi-image extraction with cross-photo entity resolution.
- `GET /v1/health`: Liveness probe (`{"status": "healthy", "service": "ocr-service"}`).
- `GET /v1/ready`: Readiness probe verifying PaddleOCR model initialization.

---

## Testing & Quality Assurance

NyayaCheck includes comprehensive test suites across the full stack:

### 1. OCR & Rules Service Regression Tests (254+ Tests)
Covers OCR text parsing, split-line normalization, regex field extraction, Rule 6–15 legal validation, and real-package regression tests:

```powershell
.\ocr-service\venv\Scripts\pytest -v ocr-service/tests
```

### 2. End-to-End Full-Stack Integration Suite
Executes end-to-end HTTP tests simulating browser multipart uploads directly against the running microservice:

```powershell
node frontend/test-ocr-integration.mjs
```

### 3. Frontend Production Build & Typecheck
Validates Next.js App Router compilation, TypeScript contracts, and Tailwind CSS v4 styling:

```powershell
cd frontend
npm run build
```

---

## Evidence & Panchnama Dossier Generation

Every registered inspection in NyayaCheck produces a court-admissible record containing:

1. **Unique Report Code**: High-entropy hexadecimal inspection identifier (e.g., `#LM-2026-9F83A`).
2. **Statutory Findings Matrix**: Tabulated audit breakdown with passed checks, statutory violations, and exact rule references.
3. **Declared Product Values**: Bounding-box extracted values for declared MRP, net weight/volume, batch number, consumer grievance contact, and manufacturer details.
4. **Digital Signature Hash**: SHA-256 cryptographic digest binding the extracted parameters, officer badge number, and inspection timestamp.
5. **Section 65B Certificate**: Explicit certification text satisfying the statutory requirements of the Indian Evidence Act for electronic records.

---

## Directory Layout

```
nyayacheck/
├── frontend/                       # Next.js 16 + React 19 Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── admin/              # Admin dashboard, audit logs, user management
│   │   │   ├── inspector/          # Inspector scanner, live HUD, reports ledger
│   │   │   ├── login/              # Authentication portal
│   │   │   └── page.tsx            # Main landing page
│   │   ├── components/             # Reusable UI components & Viewfinder
│   │   ├── lib/
│   │   │   ├── exportUtils.ts      # Panchnama PDF & CSV export engine
│   │   │   ├── ocrApi.ts           # Client for FastAPI /v1/check & /v1/extract
│   │   │   └── api.ts              # Client for Express authentication API
│   │   └── types/                  # Shared TypeScript interfaces
│   └── test-ocr-integration.mjs    # Full-stack E2E verification test suite
│
├── ocr-service/                    # Python 3.12+ FastAPI Microservice
│   ├── app/
│   │   ├── main.py                 # FastAPI application & CORS/logging setup
│   │   ├── config.py               # Centralized pydantic-settings configuration
│   │   ├── pipeline.py             # Image processing & analysis coordinator
│   │   ├── ocr/                    # PaddleOCR integration & split-line repair
│   │   ├── classification/         # Regex & heuristic statutory field extraction
│   │   ├── visual/                 # Relative font height, contrast, PDP heuristic
│   │   ├── rules/                  # Legal Metrology 2011 statutory rules engine
│   │   ├── reporting/              # Markdown & JSON report assembly
│   │   ├── routes/                 # Versioned /v1 API routes
│   │   └── schemas/                # Pydantic v2 data models
│   ├── tests/                      # 254+ pytest test cases & real product fixtures
│   ├── test_images/                # Sample test images (clean, glossy, angled)
│   ├── Dockerfile                  # Production container with pre-warmed weights
│   └── docker-compose.yml          # Containerized orchestration
│
├── backend/                        # Node.js Express Authentication Backend
│   ├── src/
│   │   ├── controllers/            # Auth controller (login, register, session)
│   │   ├── middleware/             # JWT cookie verification middleware
│   │   ├── migrations/             # PostgreSQL database migration scripts
│   │   ├── routes/                 # Express API routes
│   │   └── server.js               # Express application entrypoint
│   └── package.json
│
└── README.md                       # Project documentation
```

---

## Legal & Compliance Notice

This software is designed as an automated regulatory assistance tool under the **Legal Metrology Act, 2009** and the **Legal Metrology (Packaged Commodities) Rules, 2011**. 

Automated optical character recognition and heuristic compliance audits are intended to aid authorized officers and statutory auditors in identifying potential deficits. Formal statutory notices, seizures, and compounding of offences remain subject to manual verification and official panchnama attestation by appointed Legal Metrology Inspectors.

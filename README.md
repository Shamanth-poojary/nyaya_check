# NyayaCheck — Legal Metrology AI Verification Platform

NyayaCheck is an integrated AI-powered enforcement and verification platform built for statutory compliance auditing under the **Legal Metrology (Packaged Commodities) Rules, 2011**.

---

## System Architecture

```
                                      ┌─────────────────────────────────────────┐
                                      │        Frontend (Next.js 16 + React 19) │
                                      │        Port 3000                        │
                                      └───────┬─────────────────────────┬───────┘
                                              │                         │
                          Direct OCR Scans    │                         │ Auth & Sessions
                          & Live Inferences   │                         │ (JWT Cookies)
                                              ▼                         ▼
            ┌─────────────────────────────────────────┐     ┌─────────────────────────────────────────┐
            │        OCR & Rules Microservice         │     │         Backend (Express ESM)           │
            │        FastAPI + PaddleOCR + OpenCV     │     │         Port 5000                       │
            │        Port 8000                        │     │         PostgreSQL Database             │
            └─────────────────────────────────────────┘     └─────────────────────────────────────────┘
```

- **`frontend/`**: Next.js 16.3.5 (App Router, Turbopack), React 19, Tailwind CSS v4. Features live industrial camera viewfinder (`getUserMedia`), multi-angle packaging photo upload, real-time OCR progress HUD, dynamic statutory findings cards, and inspection report filing.
- **`ocr-service/`**: Python 3.12 FastAPI microservice. Runs PaddleOCR detection & recognition, visual contrast analysis, principal display panel (PDP) identification, and statutory rules engine evaluation (`POST /v1/check`).
- **`backend/`**: Node.js Express server with PostgreSQL connection pool. Manages user authentication, role-based access control (Admin & Inspector), and secure session cookies.

---

## Quick Start (Running Locally)

### 1. Start the OCR Microservice (Port 8000)
```powershell
cd ocr-service
.\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- Health Check: `http://localhost:8000/v1/health`
- Interactive Swagger Docs: `http://localhost:8000/docs`

### 2. Start the Backend Authentication API (Port 5000)
```powershell
cd backend
npm start
```
- Health Check: `http://localhost:5000/api`

### 3. Start the Next.js Frontend (Port 3000)
```powershell
cd frontend
npm run dev
```
- Open [http://localhost:3000](http://localhost:3000) in your web browser.
- Scanner URL: [http://localhost:3000/inspector/new-scan](http://localhost:3000/inspector/new-scan)
- Reports Register: [http://localhost:3000/inspector/reports](http://localhost:3000/inspector/reports)

---

## Full-Stack Feature Walkthrough

1. **Package Verification Scan (`/inspector/new-scan`)**:
   - Switch between **Upload** and **Live Camera** modes.
   - Attach or snap multiple photos (Front PDP, Back, Sides, MRP panel).
   - Toggle **CLAHE Preprocess** for faint or glossy packages.
   - Click **Scan Package**: Real-time progress indicators track image upload, PaddleOCR bounding box extraction, and rule evaluation.
2. **Statutory Findings & Rule Breakdown**:
   - **Key Declarations**: Real declared MRP, Net Quantity, Unit Sale Price, Dates, and Manufacturer/Packer.
   - **Rule Audits Tab**: Inspect Rule 6, Rule 14 (letter/numeral height), unit validity, and schedule specifications with exact statutory references.
3. **Report Generation & Filing**:
   - Click **Confirm & Register Report**: Saves the attested report to the inspector's statutory ledger.
   - Automatically navigates to `/inspector/reports` and opens the inspection dossier drawer with cryptographic hash and complete evidence.

---

## Verification & Automated Tests

### Run Full E2E Integration Suite
```powershell
node frontend/test-ocr-integration.mjs
```

### Run OCR Service Unit & Regression Tests (254 tests)
```powershell
.\ocr-service\venv\Scripts\pytest -v ocr-service/tests
```

### Verify Frontend Production Build
```powershell
cd frontend
npm run build
```

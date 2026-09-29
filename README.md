# AI Email Classification Agent with NeonDB & Human-in-the-Loop (HITL)

A production-ready **AI Email Classification Agent** built with **FastAPI**, **LangGraph**, and **Neon PostgreSQL (Lakebase)**. It reads employee email records, classifies each email into one of three strict categories (**Payroll**, **Benefits**, **Tax**), initiates a Human-in-the-Loop interrupt, asks a human reviewer to verify or correct the prediction, and persists the verified result back into NeonDB.

---

## 1. Project Overview

In enterprise HR and Finance operations, emails must be routed accurately without risk of hallucination or silent misclassification. This project implements an **Agentic Workflow** where:
* The AI Agent accesses database tools to retrieve emails and historical context (precedent verified examples).
* Structured output restricts predictions strictly to `Payroll`, `Benefits`, and `Tax` with confidence scores and reasoning.
* Execution **pauses** using LangGraph's native `interrupt()` mechanism for mandatory human verification.
* If approved (`YES`), the AI classification is accepted. If rejected (`NO`), the human selects the correct category with optional feedback.
* Neon PostgreSQL stores both the original AI prediction (for evaluation tracking) and the verified ground truth.

---

## 2. Architecture Diagram

```mermaid
flowchart TD
    subgraph UI ["Modern Web Frontend (SPA)"]
        Dashboard["Real-time Dashboard (Total, Payroll, Benefits, Tax, Pending, Verified)"]
        EmailList["Interactive Email Table (Filter, Search, Status Badges)"]
        ModalHITL["Human-in-the-Loop Verification Modal"]
        EvalModal["Model Evaluation View (Accuracy, Precision, Recall, F1)"]
    end

    subgraph API ["FastAPI Backend Layer"]
        RouterEmails["GET /emails & GET /emails/{id}"]
        RouterClassify["POST /emails/{id}/classify"]
        RouterVerify["POST /emails/{id}/verify"]
        RouterStats["GET /statistics & GET /evaluation"]
    end

    subgraph LangGraph ["LangGraph Agent & HITL Engine"]
        NodeFetch["1. fetch_email_node (NeonDB)"]
        NodeSimilar["2. find_similar_emails (Few-shot context)"]
        NodeClassify["3. classify_email_node (Ollama gemma4 / Gemini)"]
        NodeInterrupt{"4. human_verification_node (LangGraph interrupt())"}
        BranchDecision{"Decision Branch"}
        NodeApprove["5a. Accept AI Category"]
        NodeCorrect["5b. human_correction_node (Manual Override)"]
        NodeFinalize["6. determine_final_category"]
        NodeUpdate["7. update_database_node (NeonDB)"]
    end

    subgraph Database ["Neon PostgreSQL Database"]
        TableEmail[("Email_data Table")]
        ViewEmail[("emails View")]
    end

    EmailList -->|Click Classify| RouterClassify
    RouterClassify --> NodeFetch
    NodeFetch --> TableEmail
    NodeFetch --> NodeSimilar
    NodeSimilar --> NodeClassify
    NodeClassify --> NodeInterrupt
    NodeInterrupt -.->|Yields Interrupt State| ModalHITL

    ModalHITL -->|Click YES or NO| RouterVerify
    RouterVerify -->|Command(resume=payload)| BranchDecision
    BranchDecision -->|YES| NodeApprove
    BranchDecision -->|NO| NodeCorrect
    NodeApprove --> NodeFinalize
    NodeCorrect --> NodeFinalize
    NodeFinalize --> NodeUpdate
    NodeUpdate --> TableEmail

    Dashboard --> RouterStats
    EvalModal --> RouterStats
    RouterStats --> TableEmail
```

---

## 3. Technology Stack

* **Backend**: Python 3.13, FastAPI, Pydantic v2, Pydantic-Settings, SQLAlchemy 2.0, Psycopg 3, python-dotenv
* **Database**: Neon PostgreSQL (Serverless Lakebase Postgres with connection pooling)
* **Agent Framework**: LangGraph, LangChain Core, LangChain Ollama, LangChain Google GenAI
* **LLM Engine**: Local Ollama (`gemma4:latest`) or Google Gemini (`gemini-2.5-flash`), fully configurable via environment variables
* **Frontend**: Vanilla HTML5, Modern CSS3 (Glassmorphism, CSS Custom Properties, Inter & Outfit typography), Vanilla JavaScript SPA
* **Testing**: Pytest, Pytest-Asyncio, HTTPX

---

## 4. Email Categories & Classification Rules

The system restricts classifications to exactly three categories:

| Category | Typical Topics | Example Subjects |
|---|---|---|
| **Payroll** | Salary, payslips, wages, overtime, direct deposits, bonus payouts, deductions | *"Monthly Salary Update - September"*, *"September Payslip Available"* |
| **Benefits** | Health, dental, vision insurance, 401(k), parental leave, wellness, HSA | *"Health Insurance Open Enrollment"*, *"401(k) Retirement Contribution"* |
| **Tax** | Form W-2, 1099, TDS, tax withholding, W-4 allowances, state tax nexus | *"Important: Your Form W-2 is Ready"*, *"TDS Deduction Update"* |

---

## 5. Database Schema & Inspection

The application inspects the live NeonDB database dynamically upon boot and applies non-destructive migrations.

### Table: `public."Email_data"` (with `public.emails` view)

| Column Name | Data Type | Description |
|---|---|---|
| `id` | `INTEGER` (PK) | Auto-increment primary key |
| `To` / `recipient` | `VARCHAR(255)` | Recipient email address |
| `From` / `sender` | `VARCHAR(255)` | Sender email address |
| `Subject` / `subject` | `VARCHAR(300)` | Email subject line |
| `Body` / `body` | `TEXT` | Email content |
| `ai_category` | `VARCHAR(50)` | Original prediction (`Payroll`, `Benefits`, `Tax`) |
| `ai_confidence` | `DOUBLE PRECISION` | Prediction confidence (0.0 to 1.0) |
| `classification_reason`| `TEXT` | Detailed explanation from the LLM |
| `verified_category` | `VARCHAR(50)` | Ground truth verified by human |
| `verification_status` | `VARCHAR(50)` | `pending`, `approved`, or `corrected` |
| `human_feedback` | `TEXT` | Reviewer notes or reason for correction |
| `verified_by` | `VARCHAR(100)` | Reviewer identifier |
| `verified_at` | `TIMESTAMPTZ` | Timestamp when review was submitted |
| `received_at` | `TIMESTAMPTZ` | Timestamp when email arrived |

> **Critical Rule**: `ai_category`, `ai_confidence`, and `classification_reason` are **never overwritten** when a human submits a correction. This preserves AI evaluation integrity.

---

## 6. Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration (NeonDB)
DATABASE_URL=postgresql://neondb_owner:npg_bdWvh97uAEmD@ep-summer-heart-b70gjut1-pooler.c-13.us-east-1.aws.neon.tech/OrangeData?sslmode=require
DATABASE_URL_DIRECT=postgresql://neondb_owner:npg_bdWvh97uAEmD@ep-summer-heart-b70gjut1.c-13.us-east-1.aws.neon.tech/OrangeData?sslmode=require

# LLM Configuration
# Options: ollama, google, openai, anthropic
LLM_PROVIDER=ollama
MODEL_NAME=gemma4:latest
OLLAMA_BASE_URL=http://localhost:11434

# If switching to Google Gemini:
# LLM_PROVIDER=google
# GOOGLE_API_KEY=your_key_here
# MODEL_NAME=gemini-2.5-flash

# Application Settings
FRONTEND_URL=http://localhost:5173
PORT=8000
HOST=0.0.0.0
```

---

## 7. Installation & Setup

1. **Clone & Enter Directory**:
   ```bash
   cd /Users/athrvabhawsar07/Documents/Email_Synthesizer
   ```

2. **Sync Dependencies with `uv`**:
   ```bash
   uv sync
   ```

3. **Verify Database Connection & Run Inspection/Migration**:
   ```bash
   uv run python -m backend.app.database.inspect_db
   ```

4. **(Optional) Seed/Reset Realistic Sample Emails**:
   ```bash
   uv run python -m backend.app.database.seed
   ```

---

## 8. Running the Application

### Option A: Modern Streamlit UI (Dark Theme with Interactive Tabs)
```bash
uv run streamlit run streamlit_app.py
```
Open your browser to: **http://localhost:8501**
* **Tab 1: 🎯 Human-in-the-Loop Verification**: Review emails, click to classify with Ollama gemma4, accept with YES or override with NO + category selection and feedback.
* **Tab 2: 📋 Email Explorer**: Search and filter email records with live NeonDB updates.
* **Tab 3: 📊 Analytics & Distribution**: Category breakdown and verification status charts.
* **Tab 4: 📈 Model Evaluation**: Live Accuracy, Precision, Recall, and F1-Scores against verified ground truth.
* **Tab 5: ⚙️ Database & System**: Inspect live Neon schema and seed test data.

### Option B: FastAPI Backend & Integrated SPA Web App
```bash
uv run python backend/app/main.py
# or
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser to:
* **Integrated Web App**: [http://localhost:8000](http://localhost:8000)
* **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 9. Agent Tools Implemented

The agent leverages 6 dedicated tools:

1. `get_email(email_id)`: Fetches full email record from NeonDB.
2. `search_emails(query, limit)`: Full-text search across subject, body, and sender.
3. `get_email_statistics()`: Aggregates real-time metrics from NeonDB.
4. `update_email_classification(email_id, category, confidence, ...)`: Updates classification in NeonDB.
5. `find_similar_emails(email_id, limit)`: Contextual similarity search over verified precedents.
6. `get_classification_history(email_id)`: Returns full audit trail of AI and human decisions.

---

## 10. Human-in-the-Loop Architecture (LangGraph)

Instead of CLI `input()` prompts, LangGraph native `interrupt()` suspends execution across stateless HTTP calls:

1. **Client calls `POST /emails/{id}/classify`**:
   * The graph executes `fetch_email` &rarr; `classify_email` &rarr; `prepare_verification`.
   * `human_verification_node` invokes `interrupt(payload)`.
   * Execution freezes; current state is saved in the LangGraph Checkpointer.
   * API responds with the prediction and confidence.
2. **Reviewer interacts with the UI Modal**:
   * Reviewer clicks **YES**: API calls `POST /emails/{id}/verify` with `{"decision": "YES"}`.
   * Reviewer clicks **NO**: Reviewer picks alternate category and submits `{"decision": "NO", "correct_category": "Tax", "feedback": "..."}`.
3. **API Resumes Execution**:
   * Graph resumes with `Command(resume=payload)`.
   * Conditionally branches to `human_correction_node` if `NO`.
   * Executes `determine_final_category` &rarr; `update_database` &rarr; `END`.
   * Persists changes to NeonDB and broadcasts updated statistics.

---

## 11. API Documentation & Examples

### Classify Email
```http
POST /emails/1/classify HTTP/1.1
Host: localhost:8000
```
**Response:**
```json
{
  "email_id": 1,
  "category": "Payroll",
  "confidence": 1.0,
  "reasoning": "The email discusses salary compensation and monthly payroll disbursement.",
  "requires_verification": true
}
```

### Verify Email (Approve AI Label)
```http
POST /emails/1/verify HTTP/1.1
Content-Type: application/json

{
  "decision": "YES",
  "verified_by": "human_reviewer"
}
```

### Verify Email (Correct AI Label)
```http
POST /emails/2/verify HTTP/1.1
Content-Type: application/json

{
  "decision": "NO",
  "correct_category": "Tax",
  "feedback": "Discusses state income tax withholding, not benefits.",
  "verified_by": "senior_auditor"
}
```

### Get Real-Time Statistics
```http
GET /statistics HTTP/1.1
```
**Response:**
```json
{
  "total_emails": 30,
  "payroll_emails": 10,
  "benefits_emails": 9,
  "tax_emails": 11,
  "pending_verification": 26,
  "approved": 2,
  "corrected": 2
}
```

### Get Evaluation Metrics
```http
GET /evaluation HTTP/1.1
```
**Response:**
```json
{
  "verified_count": 4,
  "accuracy": 0.75,
  "payroll": {
    "precision": 1.0,
    "recall": 1.0,
    "f1": 1.0,
    "support": 2
  },
  "benefits": {
    "precision": 0.0,
    "recall": 0.0,
    "f1": 0.0,
    "support": 0
  },
  "tax": {
    "precision": 0.5,
    "recall": 1.0,
    "f1": 0.6667,
    "support": 2
  }
}
```

---

## 12. Running Tests

Run the full automated test suite:
```bash
uv run pytest -v
```

Tests cover:
* Database connection to NeonDB
* Email retrieval and pagination
* LLM structured output and category constraints
* LangGraph `interrupt()` and `resume` execution branches
* Human approval and correction flows
* End-to-end FastAPI endpoint integration

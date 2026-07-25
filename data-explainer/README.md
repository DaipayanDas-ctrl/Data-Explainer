<div align="center">

# 📊 Data Explainer

**Privacy-First, Local-First Deterministic Data Intelligence & LLM Narration Engine**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Security: Zero Raw Data Leakage](https://img.shields.io/badge/Security-Zero%20Raw%20Data%20Leakage-success.svg)](#-security--privacy-architecture)
[![AWS Ready](https://img.shields.io/badge/AWS-App%20Runner%20%7C%20ECS%20%7C%20Lambda-ff9900.svg?logo=amazon-aws&logoColor=white)](#-production-deployment-aws)

---

[Key Features](#-key-features) •
[Architecture](#-architecture) •
[Quick Start](#-quick-start) •
[API Specification](#-api-specification) •
[Deployment](#-production-deployment-aws) •
[Security](#-security--privacy-architecture)

</div>

<br />

## 🌟 Overview

**Data Explainer** is a modern hybrid data analysis application designed with a strict **Local-First & Privacy-First Architecture**. 

All data parsing, schema profiling, statistical calculations, anomaly detection, Pearson correlation matrix computation, and exponential-smoothing forecasting execute **100% client-side in plain JavaScript**. 

The lightweight Python FastAPI backend serves a single dedicated function: securely proxying computed summary statistics to LLMs (**Anthropic Claude** or **Groq Llama 3**) so that **raw dataset rows never leave your local machine or browser environment**.

---

## 🏗️ Architecture

```
                               ┌─────────────────────────────────────────┐
                               │           BROWSER ENVIRONMENT           │
                               │                                         │
 ┌──────────────┐              │  ┌───────────────┐   ┌───────────────┐  │
 │  User CSV    │ ───────────► │  │ CSV Parser    │   │ PII Redaction │  │
 └──────────────┘              │  │ (PapaParse)   │ ─►│ (Regex/Rules) │  │
                               │  └───────────────┘   └───────┬───────┘  │
                               │                              │          │
                               │  ┌───────────────┐   ┌───────▼───────┐  │
                               │  │ Visualization │   │ Stats Engine  │  │
                               │  │ (Chart.js)    │◄──│ Math & Models │  │
                               │  └───────────────┘   └───────┬───────┘  │
                               └──────────────────────────────┼──────────┘
                                                              │
                                            ONLY COMPUTED STATS (JSON)
                                            NO RAW ROWS OR PII
                                                              │
                                                              ▼
                               ┌─────────────────────────────────────────┐
                               │             FASTAPI BACKEND             │
                               │                                         │
                               │   ┌──────────────┐   ┌──────────────┐   │
                               │   │ Rate Limiter │   │ Auth Guard   │   │
                               │   │ (SlowAPI)    │   │ (API Key/JWT)│   │
                               │   └──────┬───────┘   └──────┬───────┘   │
                               │          └──────────┬───────┘           │
                               │                     ▼                   │
                               │          ┌─────────────────────┐        │
                               │          │  LLM Provider Proxy │        │
                               │          └──────────┬──────────┘        │
                               └─────────────────────┼───────────────────┘
                                                     │
                                                     ▼
                               ┌─────────────────────────────────────────┐
                               │           LLM PROVIDER APIS             │
                               │  Anthropic Claude / Groq Llama 3        │
                               └─────────────────────────────────────────┘
```

---

## ✨ Key Features

- 🔒 **Zero Raw-Data Leakage**: 100% of data profiling runs locally in JavaScript. Raw rows never leave your device.
- 🛡️ **PII Auto-Scrubbing**: Automatic regex pattern matching (email, SSN, phone numbers, credit cards) and header heuristic scrubbing before LLM proxying.
- 📐 **Deterministic Math Engine**:
  - **Schema Profiling**: Mean, median, std dev, min/max, null %, unique counts.
  - **Quality Checks**: Exact-match duplicate row detection, high-null warnings, mixed date format checks.
  - **Outlier Detection**: Dual $z$-score ($|z| > 3$) and $1.5 \times \text{IQR}$ fence identification.
  - **Pearson Correlation Matrix**: Rigorous $[-1.0, 1.0]$ Pearson $r$ calculations between numeric columns.
  - **Trend Forecasting**: Multi-period exponential smoothing ($\alpha = 0.3$) and linear slope trend forecasting over chronological time series.
- 💬 **Grounded LLM Insights**: Every insight generated by Claude or Groq Llama 3 is strictly validated against local `statsRegistry` metrics. Ungrounded claims are automatically rejected.
- 📄 **Export Reports**: Generate downloadable PDF reports (via `jsPDF` + `html2canvas`) and standalone HTML documents.
- 🏷️ **Data Authenticity Verification**: Topbar indicator (`✓ Verified Original Data`) guaranteeing 0% synthetic/fabricated numbers.

---

## 🛠️ Tech Stack

| Domain | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | Vanilla JS, HTML5, CSS3 | Single-page application, zero external bundler required |
| **Parsing & Math** | PapaParse, Chart.js | Local CSV parsing and responsive data visualization |
| **Backend Compute** | Python 3.11+, FastAPI, Uvicorn | High-performance asynchronous API service |
| **Security & Auth** | SlowAPI, PyJWT | IP-based rate limiting, JWT authentication & CORS enforcement |
| **LLM Integrations** | Anthropic SDK, Groq SDK | Provider-flexible structured insight generation |
| **Cloud Deployment** | AWS App Runner, ECS Fargate, Lambda | Containerized serverless cloud target support |

---

## 🚀 Quick Start

### Prerequisites

- **Python**: `3.11` or higher
- **Node.js / HTTP Server**: Optional (Python `http.server` can be used)
- **API Key**: Anthropic API Key or Groq API Key

---

### 1. Backend Setup

```bash
# Clone repository
git clone https://github.com/your-org/data-explainer.git
cd data-explainer/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

#### Environment Configuration (`.env`)

```env
# Provider Selection: "anthropic" | "groq"
LLM_PROVIDER=anthropic

# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
GROQ_API_KEY=gsk_your_groq_key_here

# Models
CLAUDE_MODEL=claude-sonnet-5
GROQ_MODEL=llama-3.3-70b-versatile

# CORS & Security
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080
RATE_LIMIT_PER_MINUTE=15/minute
REQUIRE_CLIENT_AUTH=false
```

#### Run Backend Server

```bash
uvicorn main:app --reload --port 8000
```

Verify backend health:
```bash
curl http://127.0.0.1:8000/api/health
# Output: {"status":"ok"}
```

---

### 2. Frontend Setup

Since the frontend is a zero-build static single-page app, simply serve the `frontend` folder using any HTTP server:

```bash
cd ../frontend

# Using Python HTTP Server
python3 -m http.server 8080
```

Open **http://127.0.0.1:8080** in your browser and upload any `.csv` file.

---

## 📡 API Specification

| Endpoint | Method | Auth | Rate Limit | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | None | None | Health check & infrastructure status |
| `/api/claude` | `POST` | Optional | 15/min | Proxy computed stats to Anthropic Claude |
| `/api/groq` | `POST` | Optional | 15/min | Proxy computed stats to Groq Llama 3 |
| `/api/pii/detect` | `POST` | None | None | Backend column header PII guardrail check |
| `/api/audit-log` | `GET` | None | None | Retrieve structured audit logs |

---

## 🔒 Security & Privacy Architecture

- **CORS Strict Matching**: Wildcard origins (`*`) are automatically blocked in production to prevent unauthorized cross-origin requests.
- **Payload Capping**: Input prompts are capped at 50KB to protect against buffer overflow and billing exhaustion attack vectors.
- **Secrets Management Order**: Secrets resolve dynamically across production providers:
  1. AWS Secrets Manager (`AWS_SECRET_NAME`)
  2. AWS SSM Parameter Store (`AWS_SSM_PARAMETER_NAME`)
  3. Environment Variable Injection
  4. Local `.env` fallback

---

## ☁️ Production Deployment (AWS)

### 1. AWS App Runner (Recommended)
Deployment is configured out-of-the-box via [`apprunner.yaml`](apprunner.yaml):
```bash
# Push code to GitHub and connect repository in AWS App Runner Console
```

### 2. AWS ECS Fargate Container Deployment
```bash
# Build Docker image
docker build -t data-explainer-backend ./backend

# Push to Amazon ECR & deploy behind Application Load Balancer (ALB)
```

### 3. AWS Lambda (Serverless via Mangum)
The application exposes a serverless handler in `backend/main.py`:
```python
handler = Mangum(app)
```

### 4. Frontend Static Hosting (S3 + CloudFront)
Upload `frontend/index.html` to an **S3 Bucket** behind **AWS CloudFront** for edge-cached HTTPS delivery. Override the backend URL if hosted on a separate custom domain:
```html
<script>
  window.DATA_EXPLAINER_BACKEND_URL = 'https://api.yourdomain.com';
</script>
```

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

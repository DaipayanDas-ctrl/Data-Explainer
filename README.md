# 🚀 Data Explainer
### AI-Powered Intelligent Data Analysis Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi">
  <img src="https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react">
  <img src="https://img.shields.io/badge/DuckDB-Analytics-yellow?style=for-the-badge">
  <img src="https://img.shields.io/badge/AI-Powered-success?style=for-the-badge">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge">
</p>

---

## 📖 Overview

Data Explainer is an AI-powered analytics platform that transforms raw datasets into meaningful business insights within seconds.

Unlike traditional AI tools, **Data Explainer never sends raw datasets to the LLM**. All statistical calculations are performed locally using deterministic analytics (DuckDB & Pandas), while the AI focuses solely on interpreting results and generating human-readable insights.

This architecture ensures:

- 🔒 Privacy First
- 📊 Accurate Statistics
- ⚡ High Performance
- 🤖 AI-Powered Narratives
- ✅ Trustworthy Results

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


# ✨ Features

## 📂 Smart Data Upload

- CSV Support
- Excel Support
- JSON Support
- Large Dataset Handling

---

## 📈 Automatic Data Profiling

Generate detailed reports including:

- Column Statistics
- Data Types
- Missing Values
- Duplicate Detection
- Distribution Analysis
- Correlation Matrix

---

## 🤖 AI Insight Generation

Automatically discovers:

- Business Trends
- Hidden Patterns
- Revenue Insights
- Performance Bottlenecks
- Growth Opportunities
- Statistical Observations

---

## 📊 Interactive Visualizations

- Line Charts
- Bar Charts
- Pie Charts
- Scatter Plots
- Histograms
- Correlation Heatmaps

---

## 🧹 Data Quality Analysis

Detects

- Missing Data
- Duplicate Rows
- Incorrect Types
- Invalid Dates
- Outliers
- Data Inconsistencies

---

## 🔒 Privacy & Security

Your data stays protected.

✔ Raw datasets never leave the system

✔ PII Detection

✔ Sensitive Column Redaction

✔ Secure Backend Proxy

✔ Local Statistical Processing

---

## 💬 Chat With Your Data

Ask questions in natural language.

Examples:

```
What caused the revenue drop?

Which region performed best?

Predict next month's sales.

Show top 10 customers.

Compare Q1 and Q2.
```

---

## 📤 Export Reports

Export analysis as

- PDF
- PowerPoint
- Charts
- CSV

---

# 🛠 Tech Stack

## Frontend

- React
- Tailwind CSS
- Vite
- Recharts
- Framer Motion

## Backend

- FastAPI
- Python
- DuckDB
- Pandas
- NumPy

## AI

- OpenAI API
- Prompt Engineering
- Structured JSON Output

---

# 📂 Project Structure

```
Data-Explainer/

├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── assets/
│
├── backend/
│   ├── api/
│   ├── services/
│   ├── utils/
│   ├── models/
│   └── main.py
│
├── docs/
├── screenshots/
├── README.md
└── requirements.txt
```

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/data-explainer.git
```

```bash
cd data-explainer
```

---

## Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# 🎯 How It Works

1. Upload a dataset
2. Automatic data validation
3. Profile generation
4. Statistical computation
5. AI insight generation
6. Interactive dashboard
7. Ask follow-up questions
8. Export reports

---


---

# 🔮 Future Roadmap

- Multi-file Analysis
- Team Collaboration
- Dataset Versioning
- Scheduled Reports
- AI Dashboard Builder
- Root Cause Analysis
- Forecasting
- Google Sheets Integration
- Snowflake Connector
- Slack Notifications

---

# 🌟 Why Data Explainer?

Unlike traditional AI analytics tools,

✅ Deterministic Computation

✅ AI only explains—not calculates

✅ Privacy by Design

✅ Explainable Insights

✅ Interactive Visualizations

✅ Enterprise-Ready Architecture

---

# 🤝 Contributing

Contributions are welcome!

Fork the repository

Create a feature branch

Commit your changes

Open a Pull Request

---

# 📄 License

Licensed under the MIT License.

---

# 👨‍💻 Developer

**Daipayan Das**

B.Tech Student | AI & Data Engineering Enthusiast

Passionate about building AI products that solve real-world business problems.

---

⭐ If you found this project useful, consider giving it a star!

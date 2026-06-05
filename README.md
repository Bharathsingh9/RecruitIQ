<div align="center">
  <h1>RecruitQ  AI</h1>
  <p><b>Enterprise Resume Screening & AI Interview Copilot</b></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version" />
    <img src="https://img.shields.io/badge/React-19-61DAFB.svg" alt="React" />
    <img src="https://img.shields.io/badge/Gen_AI-LLMs_&_RAG-orange.svg" alt="Gen AI & RAG" />
    <img src="https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-yellow.svg" alt="Scikit-Learn" />
  </p>
</div>

---

## 📖 Overview
**RecruitIQ** is an advanced, AI-powered Applicant Tracking System (ATS) and interview assistant designed for modern recruiting teams. It leverages Generative AI (Gen AI), Large Language Models (LLMs), Machine Learning (Random Forest), and Retrieval-Augmented Generation (RAG) to automate resume screening, rank candidates objectively, and assist recruiters during live interviews.

## ✨ Core Features

* 🔍 **Smart Candidate Screening**: Single-resume parsing that automatically calculates match scores against a Job Description. Includes **Explainable AI (SHAP)** to show exactly *why* a candidate was recommended.
* 📂 **Multi-Resume Batch Processing**: Upload an entire folder of resumes to generate a ranked leaderboard of candidates in seconds.
* 🎙️ **AI Interview Copilot**: A real-time assistant that evaluates candidate responses for technical depth, communication, and completeness. Includes a built-in **RAG Knowledge Base** to retrieve technical interview questions on the fly.
* 📊 **Recruiter Analytics**: Comprehensive dashboards featuring Plotly-powered hiring funnels, skill gap heatmaps, and distribution charts.
* 📥 **Exportable Dossiers**: Generate comprehensive PDF dossiers or Excel/CSV campaign reports with a single click.

---

## 🛠️ Tech Stack

* **Frontend / UI:** React 19, Vite, Tailwind CSS, Recharts
* **Backend:** FastAPI (Python)
* **Machine Learning:** Scikit-Learn (Random Forest), SHAP (Explainability)
* **Gen AI & LLM Integration:** Advanced Large Language Models utilizing Retrieval-Augmented Generation (RAG)
* **Vector Database:** ChromaDB / FAISS (for RAG context)
* **Database:** PostgreSQL (Production) / SQLite (Local)
* **Deployment:** Docker & Docker Compose

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+
* Node.js & npm (for the frontend)
* Required API Keys (configured via `.env`)
* Docker (Optional, for containerized deployment)

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/Bharathsingh9/RecruitIQ.git
cd RecruitIQ

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the template `.env` file to configure your credentials:
```bash
cp .env.example .env
```
Open `.env` and configure your API keys. **At minimum, you must provide:**
* `GROQ_API_KEY`: Your provider API key for Gen AI / LLM text generation.
* `DATABASE_URL`: (Optional) Defaults to local SQLite if left blank.

> **Note:** The application includes strict startup validation and will intentionally crash if the required API keys are missing from the `.env` file.

### 4. Running the Application

**Option A: Run via Docker Compose (Recommended)**
```bash
docker-compose up --build
```
* **Frontend:** Available at `http://localhost:3000`
* **Backend API Docs:** Available at `http://localhost:8000/api/v1/openapi.json`

**Option B: Run Locally (Manual)**

*Terminal 1 - Backend:*
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

*Terminal 2 - Frontend:*
```bash
cd frontend
npm install
npm run dev
```

---

## 🔒 Security & Privacy
* **Zero Hardcoded Secrets**: All API keys, database URLs, and JWT secrets are strictly managed via environment variables.
* **Ignored Environment Files**: `.env` configurations are explicitly blocked by `.gitignore` to prevent accidental credential leaks.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Bharathsingh9/RecruitIQ/issues).

## 📝 License
This project is proprietary and for educational / internal use.

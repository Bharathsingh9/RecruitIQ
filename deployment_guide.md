# HireGen AI - Production Deployment & Testing Guide

This guide describes the production architecture, setup instructions for Neon PostgreSQL, deployment guides for Render and Railway platforms, and testing guidelines for the **HireGen AI** platform.

---

## 🏗️ Production Architecture Diagram

```mermaid
graph TD
    subgraph Client Layer
        Browser[Client Browser]
    end

    subgraph Application Layer
        Streamlit[Streamlit App Container]
        GroqClient[Groq LLM Client]
    end

    subgraph Data & Storage Layer
        DB[(PostgreSQL Database / Neon)]
        FAISS[(FAISS Index Files)]
        Chroma[(ChromaDB Store)]
    end

    subgraph External APIs
        GroqAPI[Groq API Endpoint]
    end

    Browser -->|HTTPS / WSS| Streamlit
    Streamlit -->|SQL / psycopg2| DB
    Streamlit -->|Local Disk Read| FAISS
    Streamlit -->|SQLite Client| Chroma
    Streamlit -->|requests / HTTPS| GroqClient
    GroqClient -->|REST API| GroqAPI
```

---

## 🐘 1. Neon PostgreSQL Database Setup

[Neon](https://neon.tech) provides a fully managed serverless PostgreSQL database.

1. **Sign Up / Log In**: Navigate to [neon.tech](https://neon.tech) and create an account.
2. **Create Project**: Click **Create a Project**. Choose a project name, select a PostgreSQL version (recommended: v15 or v16), and select your region.
3. **Database Connection String**: Once created, Neon will present you with your connection details. Copy the **Connection string** (select the **Primary** database role). It looks like this:
   `postgresql://neondb_owner:PASSWORD@ep-noisy-thunder-a58kzv3u.us-east-2.aws.neon.tech/neondb?sslmode=require`
4. **Set Connection Variable**: Paste this string into your environment variables as `DATABASE_URL` (in Render/Railway settings or your local `.env` file). The platform will automatically connect to it and initialize the schema.

---

## 🚀 2. Render Deployment Guide

[Render](https://render.com) is a unified cloud platform to build and run all your apps.

1. **Sign In**: Log in to your Render Dashboard.
2. **New Web Service**: Click **New +** and select **Web Service**.
3. **Connect Repository**: Connect your GitHub/GitLab repository hosting the HireGen AI code.
4. **Configure Settings**:
   - **Name**: `hiregen-ai`
   - **Region**: Choose the region closest to your users.
   - **Branch**: `main`
   - **Runtime**: `Docker` (Render will automatically detect the `Dockerfile` in the root).
   - **Instance Type**: Select **Free** (or a paid instance if you need sustained resources).
5. **Environment Variables**: Click **Advanced** and add:
   - `GROQ_API_KEY`: Your active Groq API Key (`gsk_...`)
   - `DATABASE_URL`: Your Neon PostgreSQL connection string.
   - `LLM_MODEL`: `llama-3.1-8b-instant`
6. **Deploy**: Click **Create Web Service**. Render will build the Docker container, download packages, download the SpaCy model, and spin up the service.
7. **Custom Port (Streamlit)**: Render automatically binds to Streamlit. If needed, configure the container command to listen on Render's `$PORT` environment variable.

---

## 🚄 3. Railway Deployment Guide

[Railway](https://railway.app) is an infrastructure platform where you can provision code and databases.

1. **Login**: Connect your GitHub account to [railway.app](https://railway.app).
2. **New Project**: Click **New Project** and select **Deploy from GitHub repo**.
3. **Select Repo**: Choose the HireGen AI repository.
4. **Add Variables**: Click **Add variables** and insert:
   - `GROQ_API_KEY`: Your active Groq API Key.
   - `DATABASE_URL`: Your Neon PostgreSQL connection string.
   - `LLM_MODEL`: `llama-3.1-8b-instant`
   - `PORT`: `8501`
5. **Deploy**: Railway will automatically detect the `Dockerfile`, build it, and provision a public URL.
6. **Verify Logs**: View the deploy logs to ensure the Streamlit server boots up on port `8501`.

---

## 🧪 4. Standalone & Local Testing Instructions

### Prerequisites
Ensure you have Python 3.10+ installed and the required libraries:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Run Standalone Diagnostics
Verify database migrations, scorer equations, and model prediction classes:
```bash
# 1. Verify Scorer math maps 4 years to 88% and 5 projects to 85%
python -m scoring.resume_scorer

# 2. Verify SHAP Explainer loads model features
$env:PYTHONIOENCODING="utf-8"
python -m explainability.shap_explainer

# 3. Test interview answer evaluator against Groq endpoints
python -m genai.interview_evaluator
```

### Run Local Web Interface
Start the Streamlit client server:
```bash
python -m streamlit run app.py
```
Open [http://127.0.0.1:8501](http://127.0.0.1:8501) in your browser.
- **Candidate Screening**: Upload [sample_resume.pdf](file:///d:/HireGen-AI/data/resumes/sample_resume.pdf), paste a job description, adjust sliders, and view the SHAP graph.
- **Multi-Resume Screening**: Upload files in batch, generate the leaderboard, and click **Download PDF Report**.
- **AI Interview Copilot**: Test responses and evaluate technical answers.
- **Recruiter Analytics**: Inspect hiring funnel charts and download the Excel Campaign matrix.
- **Settings**: Verify your credentials and themes.

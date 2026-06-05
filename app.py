"""
Enterprise UI for HireGen AI - Resume Screening & Interview Copilot.
Conforms to strict SaaS design principles: minimal typography, cards, HSL-harmonized metrics, 
and hidden advanced variables.

Navigation Pages:
1. Candidate Screening (Single resume matching, scoring, RandomForest classification, SHAP XAI, questions).
2. Multi-Resume Screening (Concurrent folder/batch parsing, ranking, sortable leaderboard).
3. AI Interview Copilot (LLM-based candidate answer evaluator + RAG Knowledge Base).
4. Recruiter Analytics (Campaign metrics, Plotly funnel, skill charts, CSV/Excel report exports).
5. Settings (Groq API configuration, DB dialect, model selectors).
"""

import os
import tempfile
import logging
from typing import Optional, List
import streamlit as st
import pandas as pd

# Core config import
import app_config as config

# Configure logger
logger = logging.getLogger(__name__)

# Import core modules
try:
    from resume_parser.parser import extract_text_from_pdf
    from resume_parser.extractor import extract_name, extract_email, extract_phone
    from resume_parser.skills import extract_skills
    
    from matching.jd_matcher import calculate_match_score
    from matching.skill_gap_analyzer import generate_learning_path
    from database.db import (
        create_database, insert_candidate, get_all_candidates, 
        delete_candidate, get_candidate_by_id
    )
    from ml_models.predict import predict_candidate
    from genai.interview_question_generator import generate_interview_questions
    
    # Ingest/RAG modules
    from rag.rag_pipeline import answer_query
    
    # Analytics modules
    from dashboard.analytics import (
        get_total_candidates, get_shortlisted_candidates, get_rejected_candidates,
        get_review_candidates, get_average_match_score, get_candidates_df
    )
    from dashboard.charts import (
        plot_candidate_distribution, plot_skill_frequency, plot_missing_skills,
        plot_hiring_funnel, plot_candidate_scores, plot_skill_heatmap
    )
    from dashboard.reports import generate_csv_report, generate_excel_report
    
    # XAI, Resume Scoring, and Answer Evaluator modules
    from explainability.shap_explainer import explain_prediction, plot_shap_explanation
    from scoring.resume_scorer import calculate_overall_resume_score
    from genai.interview_evaluator import evaluate_answer
    
    # Batch screening and ranking leaderboard
    from screening.batch_processor import process_multiple_resumes
    from screening.leaderboard import generate_leaderboard, search_and_filter_leaderboard
    
    # PDF & Excel export orchestrators
    from reports.report_generator import (
        generate_candidate_pdf_report, generate_campaign_pdf_report, generate_campaign_excel_report
    )
    
except ImportError as err:
    st.error(f"Failed to import core modules: {err}")
    logger.critical(f"Startup Import Error: {err}")

# Initialize Database Schema
create_database()

# Premium Custom CSS Injection for Modern Corporate Look (Preferred Color Palette)
st.markdown("""
<style>
    /* Global Base Reset */
    .stApp {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* Clean Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
        padding-top: 20px;
    }
    section[data-testid="stSidebar"] .stRadio > label {
        display: none !important; /* Hide default radio label */
    }
    
    /* Card Layouts */
    .saas-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    
    .saas-header {
        font-size: 1.1em;
        font-weight: 600;
        color: #111827;
        margin-bottom: 12px;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 6px;
    }
    
    /* Rounded tag badges */
    .tag-matched {
        display: inline-block;
        background-color: #EFF6FF;
        color: #2563EB;
        border: 1px solid #BFDBFE;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.82em;
        font-weight: 500;
        margin: 3px 5px 3px 0;
    }
    
    .tag-missing {
        display: inline-block;
        background-color: #FEF2F2;
        color: #EF4444;
        border: 1px solid #FCA5A5;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.82em;
        font-weight: 500;
        margin: 3px 5px 3px 0;
    }
    
    /* Metric Card overrides */
    div[data-testid="stMetricValue"] {
        font-size: 1.8em !important;
        font-weight: 700 !important;
        color: #2563EB !important;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.85em !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #4A5568 !important;
    }
    
    div[data-testid="stMetricDelta"] {
        font-size: 0.82em !important;
    }
    
    /* Classification badge blocks */
    .badge-shortlist {
        background-color: #10B981;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.9em;
    }
    .badge-review {
        background-color: #F59E0B;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.9em;
    }
    .badge-reject {
        background-color: #EF4444;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    /* Question card styles */
    .question-card {
        background-color: #FFFFFF;
        border-left: 4px solid #2563EB;
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.01);
    }
</style>
""", unsafe_allow_html=True)


def handle_screening_pipeline(
    uploaded_file,
    jd_text: str,
    experience_years: float,
    education_score: float,
    certifications: int,
    projects: List[str],
    api_key: Optional[str] = None
) -> Optional[dict]:
    """
    Core single resume evaluation orchestrator.
    """
    temp_path = None
    try:
        # Save file to temp path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name

        # Parse text from resume PDF
        resume_text = extract_text_from_pdf(temp_path)
        if not resume_text:
            st.error("⚠️ Failed to parse resume PDF. The file may be corrupted.")
            return None

        # Extract name, contact, skills
        name = extract_name(resume_text)
        email = extract_email(resume_text)
        phone = extract_phone(resume_text)
        resume_skills = extract_skills(resume_text)
        
        # JD skills
        jd_skills = extract_skills(jd_text)

        # Match results
        match_results = calculate_match_score(resume_skills, jd_skills)
        match_score = match_results["match_score"]
        matched_skills = match_results["matched_skills"]
        missing_skills = match_results["missing_skills"]

        # Run independent scorer
        scorer_res = calculate_overall_resume_score(
            skills_match=match_score,
            experience_years=experience_years,
            projects_count=len(projects),
            education_score=education_score
        )

        # Run skill gap analyzer recommendations
        gap_results = generate_learning_path(missing_skills)
        learning_path = gap_results["learning_path"]

        # Run candidate prediction
        pred_res = predict_candidate(
            skills_match=match_score,
            experience_years=experience_years,
            education_score=education_score,
            certifications=certifications
        )
        prediction = pred_res["prediction"]
        confidence = pred_res["confidence"]

        # Generate XAI SHAP values
        xai_res = explain_prediction(
            skills_match=match_score,
            experience_years=experience_years,
            education_score=education_score,
            certifications=certifications,
            predicted_class=prediction
        )

        # Generate interview questions using Groq API
        questions = generate_interview_questions(
            candidate_skills=matched_skills if matched_skills else resume_skills,
            projects=projects,
            job_description=jd_text,
            api_key=api_key
        )

        # Save to database
        candidate_id = insert_candidate(
            name=name if name != "Not Found" else "Unknown Candidate",
            resume_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            experience_years=experience_years,
            education_score=education_score,
            certifications=certifications,
            prediction=prediction,
            projects_count=len(projects)
        )

        return {
            "resume_text": resume_text,
            "name": name,
            "email": email,
            "phone": phone,
            "resume_skills": resume_skills,
            "jd_skills": jd_skills,
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "learning_path": learning_path,
            "prediction": prediction,
            "confidence": confidence,
            "scorer": scorer_res,
            "xai": xai_res,
            "questions": questions,
            "candidate_id": candidate_id
        }

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        st.error(f"An unexpected error occurred during candidate screening: {e}")
        return None
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_err:
                logger.warning(f"Error removing temp file: {cleanup_err}")


# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("### 🧭 HireGen AI")
    # Clean page navigation with icons, conforming to exact 5 pages requirement
    page = st.radio(
        "Navigation",
        [
            "🔍 Candidate Screening", 
            "📂 Multi-Resume Screening",
            "🎙️ AI Interview Copilot",
            "📊 Recruiter Analytics",
            "⚙️ Settings"
        ]
    )


# =====================================================================
# PAGE 1: Candidate Screening
# =====================================================================
if page == "🔍 Candidate Screening":
    # Hero section
    st.title("HireGen AI")
    st.markdown("### **AI-Powered Resume Screening & Interview Copilot**")
    st.markdown(
        "Upload a resume and job description to evaluate candidate suitability, "
        "generate interview questions, and receive AI-powered recommendations."
    )
    st.markdown("---")

    # Inputs side-by-side
    col_in_l, col_in_r = st.columns([1, 1])
    
    with col_in_l:
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF)",
            type=["pdf"],
            help="Upload the candidate resume PDF."
        )
        
    with col_in_r:
        jd_text = st.text_area(
            "Job Description",
            height=120,
            value="We are looking for a Software Engineer with Python, Java, SQL, AWS, Docker, Kubernetes, and machine learning.",
            placeholder="Paste the target job description requirements here..."
        )

    # Advanced Settings Expander (hiding controls by default)
    with st.expander("🛠️ Advanced Settings (Baseline Parameters)", expanded=False):
        col_adv_l, col_adv_r = st.columns(2)
        with col_adv_l:
            experience_years = st.slider("Years of Experience Baseline", 0.0, 20.0, 4.0, step=0.5)
            certifications = st.number_input("Certifications count Baseline", min_value=0, max_value=15, value=3)
        with col_adv_r:
            education_score = st.slider("Education Score Baseline", 0.0, 100.0, 85.0, step=5.0)
            projects_text = st.text_area(
                "Candidate Projects Baseline (one per line)",
                height=80,
                value="Fraud Detection System\nResume Screening AI\nDeep Learning Classifier\nKubernetes Microservice\nCloud Query Engine"
            )
            
    # Trigger button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Analyze Candidate Profile", type="primary", use_container_width=True):
        if not uploaded_file:
            st.warning("⚠️ Please upload a candidate resume PDF first.")
        elif jd_text.strip() == "":
            st.warning("⚠️ Please provide a job description.")
        else:
            projects_list = [p.strip() for p in projects_text.split('\n') if p.strip()]
            
            with st.spinner("Analyzing candidate profile against requirements..."):
                results = handle_screening_pipeline(
                    uploaded_file=uploaded_file,
                    jd_text=jd_text,
                    experience_years=experience_years,
                    education_score=education_score,
                    certifications=certifications,
                    projects=projects_list,
                    api_key=config.GROQ_API_KEY
                )
                
            if results:
                st.session_state["screening_results"] = results
                st.success(f"🎉 Evaluation completed! Saved with Database ID: {results['candidate_id']}")

    # Render results if available
    if "screening_results" in st.session_state:
        res = st.session_state["screening_results"]
        
        st.markdown("### 📊 Screening Evaluation Results")
        
        # 1. Row of 4 metric cards
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Match Score", f"{res['match_score']}%")
        m_col2.metric("Prediction", res["prediction"])
        m_col3.metric("Resume Grade", res["scorer"]["grade"])
        m_col4.metric("Confidence", f"{int(res['confidence'] * 100)}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Profile & Skills Card
        col_res_l, col_res_r = st.columns([1, 1])
        
        with col_res_l:
            # Candidate Profile Card
            st.markdown(f"""
            <div class="saas-card">
                <div class="saas-header">👤 Candidate Profile Summary</div>
                <p><b>Name:</b> {res['name'] if res['name'] != "Not Found" else "Not Extracted"}</p>
                <p><b>Email:</b> {res['email'] if res['email'] != "Not Found" else "Not Extracted"}</p>
                <p><b>Phone:</b> {res['phone'] if res['phone'] != "Not Found" else "Not Extracted"}</p>
                <p><b>Experience Baseline:</b> {experience_years} Years</p>
                <p><b>Education Baseline Score:</b> {education_score}%</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_res_r:
            # Skills Badges Card
            st.markdown('<div class="saas-card">', unsafe_allow_html=True)
            st.markdown('<div class="saas-header">🛠️ Skills Match Profile</div>', unsafe_allow_html=True)
            
            st.markdown("<b>Matched Skills:</b>")
            if res["matched_skills"]:
                badges = "".join([f'<span class="tag-matched">{s}</span>' for s in res["matched_skills"]])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.write("None")
                
            st.markdown("<br><b>Missing Required Skills:</b>", unsafe_allow_html=True)
            if res["missing_skills"]:
                badges = "".join([f'<span class="tag-missing">{s}</span>' for s in res["missing_skills"]])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.success("Perfect skill matches!")
                
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        
        # Explainable AI section
        st.markdown("### Why This Candidate Was Recommended")
        xai_col1, xai_col2 = st.columns([2, 3])
        
        with xai_col1:
            st.markdown("##### Top SHAP Decision Factors")
            for factor in res["xai"]["top_factors"]:
                st.markdown(factor)
                
        with xai_col2:
            fig_shap = plot_shap_explanation(res["xai"]["shap_values"])
            st.plotly_chart(fig_shap, use_container_width=True)

        st.markdown("---")
        
        # Interview Questions Section
        st.markdown("### Generated Screening Questions")
        q_col1, q_col2 = st.columns(2)
        
        with q_col1:
            st.markdown("##### 💻 Technical Questions")
            for idx, q in enumerate(res["questions"]["technical_questions"], 1):
                st.markdown(f"""
                <div class="question-card">
                    <b>Question {idx}:</b> {q}
                </div>
                """, unsafe_allow_html=True)
                
        with q_col2:
            st.markdown("##### 🤝 Behavioral Questions")
            for idx, q in enumerate(res["questions"]["behavioral_questions"], 1):
                st.markdown(f"""
                <div class="question-card">
                    <b>Question {idx}:</b> {q}
                </div>
                """, unsafe_allow_html=True)


# =====================================================================
# PAGE 2: Multi-Resume Screening
# =====================================================================
elif page == "📂 Multi-Resume Screening":
    st.title("Multi-Resume Screening")
    st.subheader("Process multiple resume profiles and inspect rankings leaderboard.")
    st.markdown("---")

    col_b_l, col_b_r = st.columns([1, 1])
    
    with col_b_l:
        batch_jd = st.text_area(
            "Campaign Job Description",
            height=120,
            value="We are looking for a Software Engineer with Python, Java, SQL, AWS, Docker, Kubernetes, and machine learning.",
            placeholder="Paste JD requirements..."
        )
        
        batch_files = st.file_uploader(
            "Upload Multiple Resumes",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload all resume PDF profiles to evaluate simultaneously."
        )
        
    with col_b_r:
        st.markdown("##### Campaign Setup Defaults")
        col_bs1, col_bs2 = st.columns(2)
        with col_bs1:
            b_exp = st.slider("Experience Years Baseline", 0.0, 20.0, 4.0, step=0.5, key="b_exp")
            b_certs = st.number_input("Certifications count Baseline", min_value=0, max_value=15, value=2, key="b_certs")
        with col_bs2:
            b_edu = st.slider("Education Score Baseline", 0.0, 100.0, 80.0, step=5.0, key="b_edu")
            b_projs = st.number_input("Projects Baseline Count", min_value=0, max_value=15, value=3, key="b_projs")

    if st.button("🚀 Process Batch Profiles", type="primary", use_container_width=True):
        if not batch_files:
            st.warning("⚠️ Please upload one or more resume PDFs first.")
        elif batch_jd.strip() == "":
            st.warning("⚠️ Please provide a job description.")
        else:
            temp_dir = tempfile.mkdtemp()
            temp_paths = []
            
            for file in batch_files:
                path = os.path.join(temp_dir, file.name)
                with open(path, "wb") as f:
                    f.write(file.getvalue())
                temp_paths.append(path)
                
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            def batch_progress(completed, total):
                progress_bar.progress(float(completed) / total)
                status_text.text(f"Processed {completed} of {total} candidates...")
                
            with st.spinner("Processing concurrent resume screening..."):
                results = process_multiple_resumes(
                    pdf_paths=temp_paths,
                    jd_text=batch_jd,
                    experience_years_list=[b_exp] * len(temp_paths),
                    education_score_list=[b_edu] * len(temp_paths),
                    certifications_list=[b_certs] * len(temp_paths),
                    projects_count_list=[b_projs] * len(temp_paths),
                    progress_callback=batch_progress
                )
                
            # Cleanup
            for p in temp_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass
                
            successes = sum(1 for r in results if r["status"] == "success")
            st.success(f"🎉 Processed {successes} profiles successfully!")

    st.markdown("---")
    st.markdown("### 🏆 Top 10 Candidates Leaderboard")
    
    leaderboard = generate_leaderboard()
    
    if not leaderboard:
        st.info("No candidates screened yet. Upload profiles to generate the leaderboard.")
    else:
        # Display top 10 candidates
        top_10 = leaderboard[:10]
        
        table_rows = []
        for idx, c in enumerate(top_10, 1):
            table_rows.append({
                "Rank": idx,
                "Candidate Name": c["name"],
                "Score": f"{c['rank_score']:.1f}%",
                "Prediction": c["prediction"],
                "Confidence": f"{int(c['confidence'] * 100)}%"
            })
            
        df_top = pd.DataFrame(table_rows)
        st.dataframe(df_top, use_container_width=True)
        
        # Candidate Details selection
        st.markdown("<br>", unsafe_allow_html=True)
        selected_cand_label = st.selectbox(
            "Select Candidate to view dossier & download individual report:",
            [f"ID {c['id']}: {c['name']} (Score: {c['rank_score']:.1f}%)" for c in top_10]
        )
        
        if selected_cand_label:
            selected_id = int(selected_cand_label.split(":")[0].replace("ID ", ""))
            cand = next(c for c in top_10 if c["id"] == selected_id)
            
            det_col1, det_col2 = st.columns(2)
            with det_col1:
                st.markdown(f"""
                <div class="saas-card">
                    <div class="saas-header">Dossier: {cand['name']}</div>
                    <p><b>Email:</b> {cand.get('email', 'Not Extracted')}</p>
                    <p><b>Phone:</b> {cand.get('phone', 'Not Extracted')}</p>
                    <p><b>Experience years:</b> {cand['experience_years']} Years</p>
                </div>
                """, unsafe_allow_html=True)
                
            with det_col2:
                # Generate PDF report for selected candidate
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_cand_pdf:
                    c_pdf_path = tmp_cand_pdf.name
                    
                with st.spinner("Compiling individual PDF Dossier..."):
                    success = generate_candidate_pdf_report(cand["id"], c_pdf_path, groq_key=config.GROQ_API_KEY)
                    
                if success:
                    with open(c_pdf_path, "rb") as f:
                        pdf_data = f.read()
                    try:
                        os.remove(c_pdf_path)
                    except Exception:
                        pass
                        
                    st.download_button(
                        label=f"📥 Download {cand['name']} PDF Report",
                        data=pdf_data,
                        file_name=f"HireGen_{cand['name'].replace(' ', '_')}_Dossier.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )


# =====================================================================
# PAGE 3: AI Interview Copilot
# =====================================================================
elif page == "🎙️ AI Interview Copilot":
    st.title("AI Interview Copilot")
    st.subheader("Evaluate candidate answers using LLM scoring metrics and retrieve guide materials.")
    st.markdown("---")

    # Group evaluation tools and RAG assistant using Streamlit Tabs
    tab_eval, tab_rag = st.tabs(["🎙️ Answer Evaluator", "📖 RAG Prep Guide Assistant"])
    
    with tab_eval:
        st.markdown("### Interview Answer Evaluator")
        
        predefined_questions = [
            "Explain the difference between Random Forest and XGBoost.",
            "What is overfitting and how do you prevent it?",
            "Explain the architecture of a custom K-Means clustering algorithm.",
            "How does TF-IDF differ from word embeddings?",
            "Explain standard gradient descent vs Stochastic Gradient Descent (SGD)."
        ]
        
        sel_q = st.selectbox(
            "Technical Question:",
            ["-- Enter Custom Question --"] + predefined_questions
        )
        
        if sel_q == "-- Enter Custom Question --":
            question_text = st.text_input("Enter custom question text:")
        else:
            question_text = sel_q
            
        candidate_answer = st.text_area(
            "Candidate Response:",
            height=140,
            placeholder="Type or paste candidate response here..."
        )
        
        if st.button("🚀 Evaluate Response", type="primary", use_container_width=True):
            if question_text.strip() == "" or candidate_answer.strip() == "":
                st.warning("⚠️ Both question and answer are required.")
            else:
                with st.spinner("Assessing answer depth, accuracy, and completeness..."):
                    eval_res = evaluate_answer(
                        question=question_text,
                        answer=candidate_answer,
                        api_key=config.GROQ_API_KEY
                    )
                    
                st.success("🎉 Answer successfully evaluated!")
                
                # Output details as modern card grids
                score = eval_res["score"]
                depth = eval_res["technical_depth"]
                comm = eval_res["communication"]
                comp = eval_res["completeness"]
                
                st.markdown("#### Evaluation Summary")
                m_c1, m_c2, m_c3, m_c4 = st.columns(4)
                m_c1.metric("Overall Score", f"{score}/10")
                m_c2.metric("Technical Depth", f"{depth}/10")
                m_c3.metric("Communication", f"{comm}/10")
                m_c4.metric("Completeness", f"{comp}/10")
                
                col_ev_l, col_ev_r = st.columns(2)
                with col_ev_l:
                    st.markdown(f"""
                    <div class="saas-card" style="border-left: 4px solid #10B981;">
                        <div class="saas-header" style="color: #10B981;">🌟 Candidate Strengths</div>
                        {"".join([f"<p>• <b>{s}</b></p>" for s in eval_res['strengths']]) if eval_res['strengths'] else "<p>None</p>"}
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col_ev_r:
                    st.markdown(f"""
                    <div class="saas-card" style="border-left: 4px solid #EF4444;">
                        <div class="saas-header" style="color: #EF4444;">📈 Areas for Improvement</div>
                        {"".join([f"<p>• <b>{imp}</b></p>" for imp in eval_res['improvements']]) if eval_res['improvements'] else "<p>None</p>"}
                    </div>
                    """, unsafe_allow_html=True)
                    
    with tab_rag:
        st.markdown("### Interview Preparation Context Search")
        
        col_rag1, col_rag2 = st.columns([3, 1])
        with col_rag1:
            st.markdown("💡 *Ask prep questions (e.g. 'What questions does Google ask for ML Engineer roles?').*")
        with col_rag2:
            if st.button("🔄 Rebuild Vector Store"):
                with st.spinner("Rebuilding indexes..."):
                    try:
                        from rag.ingest import ingest_pipeline
                        ingest_pipeline(rag_db_type.lower())
                        st.success("Vector index successfully rebuilt!")
                    except Exception as err:
                        st.error(f"Rebuild failed: {err}")
                        
        rag_query = st.text_input(
            "Query prep knowledge base:",
            placeholder="Type your interview prep questions..."
        )
        
        if rag_query.strip() != "":
            with st.spinner("Searching and generating response..."):
                rag_res = answer_query(
                    query=rag_query,
                    db_type=rag_db_type.lower(),
                    api_key=config.GROQ_API_KEY
                )
                
            st.markdown("#### AI Response")
            st.write(rag_res["answer"])
            
            st.markdown("---")
            st.markdown("#### Retrieved Context segments:")
            
            from rag.retriever import retrieve_documents
            docs = retrieve_documents(rag_query, k=2, db_type=rag_db_type.lower())
            
            for i, d in enumerate(docs, 1):
                src = d["metadata"].get("source", "Unknown Source")
                st.markdown(f"""
                <div class="saas-card">
                    <b>[{i}] Source:</b> {src} | <b>Similarity distance (L2):</b> {d['score']:.4f}
                    <br><br>
                    <i>"{d['text']}"</i>
                </div>
                """, unsafe_allow_html=True)


# =====================================================================
# PAGE 4: Recruiter Analytics
# =====================================================================
elif page == "📊 Recruiter Analytics":
    st.title("Recruiter Analytics")
    st.subheader("Hiring campaign metrics, matching trends, and file exports.")
    st.markdown("---")

    df_cand = get_candidates_df()
    
    if df_cand.empty:
        st.info("No candidates evaluated yet. Complete candidate screenings to populate charts.")
    else:
        # KPI Metric Row
        tot = get_total_candidates()
        sh = get_shortlisted_candidates()
        nr = get_review_candidates()
        rj = get_rejected_candidates()
        
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        m_c1.metric("Total Screened", tot)
        m_c2.metric("Shortlisted", sh, delta=f"{int((sh/tot)*100)}%" if tot > 0 else None)
        m_c3.metric("Needs Review", nr)
        m_c4.metric("Rejected", rj)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Plotly charts
        col_ch1, col_ch2 = st.columns(2)
        with col_ch1:
            st.plotly_chart(plot_hiring_funnel(), use_container_width=True)
            st.plotly_chart(plot_candidate_distribution(), use_container_width=True)
            st.plotly_chart(plot_skill_frequency(), use_container_width=True)
        with col_ch2:
            st.plotly_chart(plot_missing_skills(), use_container_width=True)
            st.plotly_chart(plot_candidate_scores(), use_container_width=True)
            st.plotly_chart(plot_skill_heatmap(), use_container_width=True)
            
        st.markdown("---")
        
        # Campaign Report Export Panel
        st.markdown("### Export Campaign Reports")
        
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            # Export Recruiter Summary PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_sum_pdf:
                sum_pdf_path = tmp_sum_pdf.name
                
            if st.button("Generate Campaign PDF Report", key="sum_pdf_btn"):
                with st.spinner("Compiling Campaign PDF..."):
                    success = generate_campaign_pdf_report(sum_pdf_path)
                if success:
                    with open(sum_pdf_path, "rb") as f:
                        pdf_data = f.read()
                    try:
                        os.remove(sum_pdf_path)
                    except Exception:
                        pass
                    st.download_button(
                        label="📥 Download Campaign PDF Report",
                        data=pdf_data,
                        file_name="HireGen_Campaign_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
        with col_ex2:
            # Export Campaign Excel Spreadsheet
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_sum_xlsx:
                sum_xlsx_path = tmp_sum_xlsx.name
                
            if st.button("Generate Campaign Excel Report (XLSX)", key="sum_xlsx_btn"):
                with st.spinner("Compiling Campaign Excel..."):
                    success = generate_campaign_excel_report(sum_xlsx_path)
                if success:
                    with open(sum_xlsx_path, "rb") as f:
                        xlsx_data = f.read()
                    try:
                        os.remove(sum_xlsx_path)
                    except Exception:
                        pass
                    st.download_button(
                        label="📥 Download Excel Campaign Spreadsheet",
                        data=xlsx_data,
                        file_name="HireGen_Campaign_Spreadsheet.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
        # Admin Wipe exp
        with st.expander("⚠️ Campaign Administrative Settings", expanded=False):
            if st.button("Clear Candidates Campaign Data", type="secondary"):
                try:
                    from database.db import get_db_connection
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("DROP TABLE IF EXISTS candidates")
                    conn.commit()
                    cursor.close()
                    conn.close()
                    create_database()
                    st.success("✅ Database candidates campaign wiped and re-initialized successfully!")
                except Exception as wipe_err:
                    st.error(f"Wipe failed: {wipe_err}")


# =====================================================================
# PAGE 5: Settings
# =====================================================================
elif page == "⚙️ Settings":
    st.title("Settings")
    st.subheader("Configure Groq API endpoints, LLM model defaults, and vector databases.")
    st.markdown("---")

    # Labeled form-like parameters inputs
    api_key_input = st.text_input(
        "Groq API Key",
        value=config.GROQ_API_KEY,
        type="password",
        placeholder="gsk_...",
        help="Input your Groq API key to process LLM and evaluators completions."
    )
    
    # Save key
    if api_key_input:
        os.environ["GROQ_API_KEY"] = api_key_input
        config.GROQ_API_KEY = api_key_input
        
    model_sel = st.selectbox(
        "Model Selection",
        ["llama-3.1-8b-instant", "llama3-8b-8192", "mixtral-8x7b-32768"],
        index=0,
        help="Target Groq Cloud LLM model for prompts completion."
    )
    config.LLM_MODEL = model_sel
    
    v_db_sel = st.selectbox(
        "Vector Database Selection",
        ["FAISS", "ChromaDB"],
        index=0 if rag_db_type == "FAISS" else 1,
        help="Target database type for Retrieval-Augmented Generation."
    )
    
    # Theme configuration selection
    theme_sel = st.selectbox(
        "Theme Selection",
        ["Corporate Light (Recommended)", "Corporate Dark", "System Default"],
        index=0,
        help="UI color styling theme configurations."
    )
    
    st.success("✅ Configurations saved successfully!")

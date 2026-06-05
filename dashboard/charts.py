"""
Visualization module for HireGen AI Recruiter Dashboard.
Generates interactive Plotly charts and heatmaps from candidate dataframes.
"""

import logging
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

from dashboard.analytics import get_candidates_df, get_top_skills, get_top_missing_skills, get_candidate_distribution

# Configure logger
logger = logging.getLogger(__name__)


def create_empty_figure(title: str, text: str = "No Candidate Data Available") -> go.Figure:
    """
    Utility function to generate a clean empty figure placeholder when database is empty.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=text,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="grey")
    )
    fig.update_layout(
        title=title,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        template="plotly_dark"
    )
    return fig


def plot_candidate_distribution() -> go.Figure:
    """
    Generates a Pie Chart representing the distribution of candidate ML classifications (Shortlist, Reject, etc.).
    """
    df = get_candidate_distribution()
    if df.empty or df["Count"].sum() == 0:
        return create_empty_figure("Candidate Recommendations Distribution")

    fig = px.pie(
        df,
        values="Count",
        names="Prediction",
        title="Candidate Recommendations Distribution",
        color="Prediction",
        color_discrete_map={
            "Shortlist": "#4CAF50",
            "Needs Review": "#FF9800",
            "Reject": "#F44336"
        },
        hole=0.4
    )
    fig.update_layout(template="plotly_dark", margin=dict(t=50, b=20, l=20, r=20))
    return fig


def plot_skill_frequency() -> go.Figure:
    """
    Generates a horizontal Bar Chart showing the top matched skills among candidates.
    """
    df = get_top_skills(8)
    if df.empty:
        return create_empty_figure("Top Matched Skills Frequency")

    # Sort so that highest is at the top in horizontal layout
    df = df.sort_values(by="Count", ascending=True)

    fig = px.bar(
        df,
        x="Count",
        y="Skill",
        orientation="h",
        title="Top Matched Skills Frequency",
        labels={"Count": "Match Count", "Skill": "Core Skill"},
        color="Count",
        color_continuous_scale=px.colors.sequential.Blues
    )
    fig.update_layout(template="plotly_dark", coloraxis_showscale=False)
    return fig


def plot_missing_skills() -> go.Figure:
    """
    Generates a horizontal Bar Chart showing the most common skill gaps.
    """
    df = get_top_missing_skills(8)
    if df.empty:
        return create_empty_figure("Common Skill Gaps (Missing Skills)")

    df = df.sort_values(by="Count", ascending=True)

    fig = px.bar(
        df,
        x="Count",
        y="Skill",
        orientation="h",
        title="Common Skill Gaps (Missing Skills)",
        labels={"Count": "Candidates Missing Skill", "Skill": "Missing Skill"},
        color="Count",
        color_continuous_scale=px.colors.sequential.OrRd
    )
    fig.update_layout(template="plotly_dark", coloraxis_showscale=False)
    return fig


def plot_hiring_funnel() -> go.Figure:
    """
    Generates a Funnel Chart depicting recruitment progression pipeline stages.
    """
    df = get_candidates_df()
    if df.empty:
        return create_empty_figure("Hiring Pipeline Funnel")

    total = len(df)
    shortlisted = int(df[df["prediction"] == "Shortlist"].shape[0])
    reviewed = int(df[df["prediction"] == "Needs Review"].shape[0])
    
    funnel_stages = ["Total Evaluated", "Needs Review", "Shortlisted"]
    funnel_counts = [total, reviewed + shortlisted, shortlisted]

    fig = go.Figure(go.Funnel(
        y=funnel_stages,
        x=funnel_counts,
        textposition="inside",
        textinfo="value+percent initial",
        marker={"color": ["#2196F3", "#FF9800", "#4CAF50"]}
    ))
    
    fig.update_layout(
        title="Hiring Pipeline Funnel",
        template="plotly_dark",
        margin=dict(t=50, b=20, l=20, r=20)
    )
    return fig


def plot_match_score_histogram() -> go.Figure:
    """
    Generates a Histogram showing candidate Job Match Score ranges.
    """
    df = get_candidates_df()
    if df.empty or "resume_score" not in df.columns:
        return create_empty_figure("Job Match Scores Histogram")

    fig = px.histogram(
        df,
        x="resume_score",
        nbins=10,
        title="Distribution of Job Match Scores",
        labels={"resume_score": "Match Score (%)", "count": "Candidates Count"},
        color_discrete_sequence=["#00bcd4"]
    )
    fig.update_layout(
        template="plotly_dark",
        yaxis_title="Count of Candidates",
        bargap=0.05
    )
    return fig


def plot_candidate_scores() -> go.Figure:
    """
    Generates a Line Chart showing candidate match scores chronologically.
    """
    df = get_candidates_df()
    if df.empty or "resume_score" not in df.columns or "created_at" not in df.columns:
        return create_empty_figure("Job Match Scores Trend")

    # Sort by created timestamp
    df = df.sort_values(by="created_at")

    fig = px.line(
        df,
        x="created_at",
        y="resume_score",
        text="name",
        title="Evaluation Score Timeline",
        labels={"resume_score": "Match Score (%)", "created_at": "Screening Date"},
        markers=True
    )
    fig.update_layout(template="plotly_dark")
    fig.update_traces(textposition="top center", line_color="#00E676")
    return fig


def plot_skill_heatmap() -> go.Figure:
    """
    Generates a Heatmap mapping candidates against skills checkboxes.
    """
    df = get_candidates_df()
    if df.empty:
        return create_empty_figure("Candidate-Skill Heatmap")

    # We extract unique skills from the matched list
    unique_skills_set = set()
    candidate_skills = {}

    for _, row in df.iterrows():
        name = row["name"]
        try:
            skills_raw = row["matched_skills"]
            skills = json.loads(skills_raw) if isinstance(skills_raw, str) else skills_raw
            if not isinstance(skills, list):
                skills = []
        except Exception:
            skills = []
        
        # Clean skills
        skills_clean = [s.strip().title() for s in skills if s]
        candidate_skills[name] = skills_clean
        unique_skills_set.update(skills_clean)

    unique_skills = sorted(list(unique_skills_set))
    candidates = list(candidate_skills.keys())

    if not candidates or not unique_skills:
        return create_empty_figure("Candidate-Skill Heatmap", "No matching skills recorded yet")

    # Build matrix (1 if candidate has skill, else 0)
    matrix = []
    for cand in candidates:
        row_values = []
        cand_matched = candidate_skills[cand]
        for skill in unique_skills:
            row_values.append(1 if skill in cand_matched else 0)
        matrix.append(row_values)

    fig = px.imshow(
        matrix,
        labels=dict(x="Extracted Skills", y="Candidate Profiles", color="Skill Match"),
        x=unique_skills,
        y=candidates,
        color_continuous_scale=[[0, "rgba(255,255,255,0.02)"], [1, "#00E676"]],
        title="Candidate Skills Overlap Grid"
    )
    
    fig.update_layout(
        template="plotly_dark",
        coloraxis_showscale=False
    )
    return fig

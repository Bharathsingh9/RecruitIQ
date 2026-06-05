# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8501

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for compiling certs and database links
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies (including psycopg2-binary and reportlab)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install psycopg2-binary reportlab

# Download SpaCy English model corpus
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application files
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit application on container boot
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

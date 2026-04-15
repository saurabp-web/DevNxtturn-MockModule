# ==========================================
# STAGE 1: The Base (Infrastructure)
# ==========================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Install ONLY Production Requirements
COPY Loopline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# STAGE 2: The Development Stage (Local, Dev Cloud, & Test)
# ==========================================
FROM base AS development

# Install Dev Tools (Pytest, Black, etc.)
COPY Loopline/requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy everything including /tests and simulation bots
COPY Loopline/ .

# Add the Smart Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]

# ==========================================
# STAGE 3: The Production Stage (Clean & Secure)
# ==========================================
FROM base AS production

# Security Standard: Create a non-root user
RUN useradd -m django
USER django

# Copy ONLY the essential app code (Physically isolates tests)
COPY Loopline/community /app/community
COPY Loopline/config /app/config
COPY Loopline/e2e_test_utils /app/e2e_test_utils
COPY Loopline/manage.py /app/manage.py

# Add the Smart Entrypoint
USER root
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
USER django

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
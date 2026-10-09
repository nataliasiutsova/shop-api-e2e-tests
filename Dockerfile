# syntax=docker/dockerfile:1

FROM python:3.12-slim

# ---------- Environment ----------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# ---------- Workdir ----------
WORKDIR /app

# ---------- Python dependencies ----------
# Copy requirements first for better layer caching
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# ---------- Project files ----------
COPY . .

# ---------- Default command ----------
# Run regression tests with Allure results.
# Override at `docker run` if needed:
#   docker run ... pytest -m smoke
CMD ["pytest", "-m", "regression", "--alluredir=allure-results", "-v"]

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build essentials only if a dep needs them; most don't
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY core ./core
COPY models ./models
COPY routers ./routers
COPY migrations ./migrations
COPY main.py ./

RUN pip install --upgrade pip \
    && pip install .

EXPOSE 8000

# Railway / Render / Fly all inject $PORT; default to 8000 locally
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

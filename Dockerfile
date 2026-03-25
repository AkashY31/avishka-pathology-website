FROM python:3.11-slim

# System packages needed by:
#   azure-cognitiveservices-speech → libasound2
#   faiss-cpu                      → libgomp1
#   pydub                          → ffmpeg (optional, for server-side voice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libasound2 \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create persistent data directory for SQLite
# (On Railway: mount a volume at /data)
RUN mkdir -p /data

EXPOSE 8000

# Shell form so $PORT env var is expanded at runtime by Railway
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

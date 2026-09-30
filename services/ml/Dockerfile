FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/ ./services/
COPY data/ ./data/

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "services.ml.serving:app", "--host", "0.0.0.0", "--port", "8001"]

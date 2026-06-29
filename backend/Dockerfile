FROM python:3.11-slim

# Install ffmpeg + system deps
RUN apt-get update && apt-get install -y \
    bzip2 \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app/ ./app/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Create dirs
RUN mkdir -p uploads models data
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

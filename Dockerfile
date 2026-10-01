# Render Cloud Optimized Configuration
FROM python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install python dependencies without cache to minimize memory/image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port (Render sets $PORT dynamically)
ENV PORT=10000
ENV PYTHONPATH=/app
EXPOSE 10000

# Start bot via runner
CMD ["python", "-m", "telegram_clipper.main"]

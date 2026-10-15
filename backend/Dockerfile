# Mera Mentor Backend - Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import os,sys,urllib.request; p=os.environ.get('PORT'); sys.exit('PORT environment variable is required') if not p else urllib.request.urlopen('http://127.0.0.1:'+p+'/api/health', timeout=5)" || exit 1

# Run the application
CMD ["sh", "-c", ": \"${PORT:?PORT environment variable is required}\"; exec uvicorn server:app --host 0.0.0.0 --port \"${PORT}\""]

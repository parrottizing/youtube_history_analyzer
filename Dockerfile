# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies for matplotlib
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for output files
RUN mkdir -p /app/output

# Set default command to run the pipeline and copy only graphs and final CSV to output
CMD ["sh", "-c", "python run_pipeline.py && mkdir -p /app/output && cp *.png /app/output/ 2>/dev/null || true && cp youtube_history_with_categories.csv /app/output/ 2>/dev/null || true"]

FROM python:3.9-slim

# Install system dependencies (wget, gnupg for Chrome)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /app

# Copy requirements if available
COPY requirements.txt .
# Install dependencies (including new ones)
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir youtube-transcript-api groq selenium webdriver-manager pandas matplotlib

# Copy project files
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the pipeline
CMD ["python", "main.py"]
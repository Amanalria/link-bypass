# Official Microsoft Playwright Python base image with all Chromium Linux dependencies pre-installed
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=10000

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium

# Copy application source code
COPY . .

# Expose Render default port
EXPOSE 10000

# Run the healthcheck web server + telegram bot
CMD ["python3", "bot.py"]

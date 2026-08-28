FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=10000

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install python dependencies cleanly
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium with all Linux shared libraries
RUN playwright install --with-deps chromium

COPY . .

EXPOSE 10000

CMD ["python3", "bot.py"]

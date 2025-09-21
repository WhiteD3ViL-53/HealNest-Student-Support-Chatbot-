FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# system deps (ca-certificates helps TLS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# upgrade pip & install
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# copy app code
COPY . .

# make launcher executable
RUN chmod +x ./launcher.sh

EXPOSE 8080

CMD ["./launcher.sh"]

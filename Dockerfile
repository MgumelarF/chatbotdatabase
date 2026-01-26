FROM python:3.10-slim

WORKDIR /app

# Install dependency sistem minimum
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Optimasi pip
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependency Python
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy source code
COPY . .

# Non-root user
RUN useradd -m -u 1000 railway && chown -R railway:railway /app
USER railway

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]

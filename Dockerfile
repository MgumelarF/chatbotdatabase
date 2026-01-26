FROM python:3.10-slim

WORKDIR /app

# Install system dependencies minimal
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip dan setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch CPU (versi ringan)
RUN pip install --no-cache-dir \
    torch==2.1.2+cpu \
    torchvision==0.16.2+cpu \
    torchaudio==2.1.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy aplikasi
COPY . .

# Non-root user untuk security
RUN useradd -m -u 1000 railway && chown -R railway:railway /app
USER railway

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]
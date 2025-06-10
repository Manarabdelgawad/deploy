FROM python:3.9-slim
WORKDIR /app

# Install system dependencies including OpenGL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Ensure pip is up to date
RUN pip install --no-cache-dir --upgrade pip

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 80
CMD ["gunicorn", "--preload", "--timeout", "120", "-w", "4", "-b", "0.0.0.0:80", "app:app"]

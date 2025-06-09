FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y libgomp1 libsm6 libxext6 libxrender-dev && \
    pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 80
CMD ["gunicorn", "--preload", "--timeout", "120", "-w", "4", "-b", "0.0.0.0:80", "app:app"]
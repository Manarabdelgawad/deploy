FROM python:3.9.16-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y libgomp1 && pip install -r requirements.txt
COPY . .
EXPOSE 10000
CMD ["gunicorn", "--preload", "--timeout", "120", "-b", "0.0.0.0:10000", "app:app"]
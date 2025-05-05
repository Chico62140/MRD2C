FROM python:3.11

# ✅ Install netcat using real package name
RUN apt-get update && apt-get install -y netcat-openbsd

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY wait-for-it.sh .

CMD ["./wait-for-it.sh", "db", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

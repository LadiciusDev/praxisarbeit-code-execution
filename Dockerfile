FROM python:3.11-alpine

# Docker CLI direkt und zuverlässig über den Alpine-Paketmanager installieren
RUN apk add --no-cache docker-cli

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8081

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

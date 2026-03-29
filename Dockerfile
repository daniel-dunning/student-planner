# Python Docker Image
FROM python:3.12-slim

WORKDIR /app

# Create a data directory and map it as a persistent volume 
# so the SQLite database is not destroyed when the container stops
RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 8111

COPY requirements.txt .

RUN pip install uv

RUN pip install -r requirements.txt

COPY . .

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8111"]

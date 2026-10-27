# sauce API: one small container, SQLite on a mounted volume at /data
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV SAUCE_DB=/data/sauce.db PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8787
CMD ["python3", "api/server.py", "--host", "0.0.0.0", "--port", "8787"]

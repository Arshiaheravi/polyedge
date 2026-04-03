FROM python:3.12-slim AS builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY backend/ backend/
COPY frontend/ frontend/
ENV PORT=8003
WORKDIR /app/backend
CMD python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT

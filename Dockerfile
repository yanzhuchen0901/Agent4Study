FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
RUN npm run build

FROM python:3.11-slim AS backend

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY src ./src
COPY report ./report
COPY docs ./docs

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM nginx:1.27-alpine AS frontend

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

EXPOSE 80

FROM python:3.11-slim AS modelscope

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data
ENV TEXTBOOK_DIR=/app/data/textbooks
ENV PARSED_DIR=/app/data/parsed
ENV CHUNK_DIR=/app/data/chunks
ENV GRAPH_DIR=/app/data/knowledge_graph

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY report ./report
COPY docs ./docs
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

RUN mkdir -p /app/data/textbooks /app/data/parsed /app/data/chunks /app/data/knowledge_graph /app/data/rag_benchmark

EXPOSE 7860

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-7860}"]

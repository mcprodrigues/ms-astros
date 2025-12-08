FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o conteúdo da pasta app/ diretamente para /app
COPY app .

COPY data ./data

EXPOSE 8000

CMD ["sh", "-c", "\
    echo 'Loading precomputed embeddings...' && \
    python scripts/load_embeddings.py && \
    echo 'Embeddings loaded successfully' && \
    echo 'Starting API server...' && \
    uvicorn main:app --host 0.0.0.0 --port 8000 \
"]

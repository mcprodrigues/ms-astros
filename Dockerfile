# syntax=docker/dockerfile:1

# ---- build: resolve dependencies from the lockfile and bake the model ----
FROM python:3.13-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    HF_HOME=/opt/hf-cache

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Must match EMBEDDING_MODEL / EMBEDDING_MODEL_REVISION in app/settings.py.
# Download only what sentence-transformers needs. Loading the model online would
# make transformers fetch a second, converted copy of the weights from a PR branch
# (+2.3 GB), and the repo also ships ONNX/ColBERT files we never use.
ARG EMBEDDING_MODEL=BAAI/bge-m3
ARG EMBEDDING_MODEL_REVISION=5617a9f61b028005a4858fdac845db406aefb181
ARG EMBEDDING_MODEL_FILES="*.json *.model 1_Pooling/* pytorch_model.bin model.safetensors"
RUN /app/.venv/bin/python -c \
    "from huggingface_hub import snapshot_download; snapshot_download('${EMBEDDING_MODEL}', revision='${EMBEDDING_MODEL_REVISION}', allow_patterns='${EMBEDDING_MODEL_FILES}'.split())" \
 && HF_HUB_OFFLINE=1 /app/.venv/bin/python -c \
    "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}', revision='${EMBEDDING_MODEL_REVISION}')"

# ---- runtime: no build tooling, no network needed for the model ----
FROM python:3.13-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/hf-cache \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

RUN useradd --create-home --uid 1000 astros

WORKDIR /app

COPY --from=build /app/.venv /app/.venv
COPY --from=build --chown=astros:astros /opt/hf-cache /opt/hf-cache
COPY --chown=astros:astros app ./app
COPY --chown=astros:astros data/embeddings ./data/embeddings

USER astros

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

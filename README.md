# 🎬 Astros — Microserviço de Busca Semântica

Busca por significado em um acervo de filmes para estudos de cinema. Uma consulta como
*"trabalhadores rurais e reforma agrária"* encontra *Lavra dor* (1968) mesmo sem
compartilhar palavras com o cadastro do filme.

| Tecnologia | Função |
|-----------|--------|
| **FastAPI** + Pydantic v2 | API HTTP e validação |
| **Haystack 3** | Pipelines de indexação e busca |
| **Weaviate** (≥ 1.27) | Armazenamento e busca vetorial |
| **sentence-transformers** | Embeddings multilíngues (`paraphrase-multilingual-MiniLM-L12-v2`) |
| **uv** · Python 3.13 | Dependências e ambiente |
| **Docker Compose** | API + Weaviate |

---

## 🚀 Como rodar

```bash
cp .env.example .env          # defina API_KEY
docker compose up -d --build  # API em http://localhost:8000, docs em /docs
```

No primeiro startup com o índice vazio, a API carrega os embeddings pré-computados de
`data/embeddings/embeddings.parquet`. Com o índice já populado, nada é recarregado.

Desenvolvimento local (com o Weaviate do compose no ar):

```bash
uv sync
uv run uvicorn app.main:app --reload
```

### Configuração

Toda configuração vem de variáveis de ambiente (ou `.env`), lidas em `app/settings.py`.
Veja `.env.example`. As principais:

| Variável | Padrão | Descrição |
|---|---|---|
| `API_KEY` | — | Exigida no header `X-API-Key` das rotas de escrita. **Sem ela, as escritas ficam desligadas (503).** |
| `EMBEDDING_MODEL` | MiniLM-L12 multilíngue | Precisa ser o mesmo modelo que gerou o parquet. O startup recusa um arquivo de outro modelo. |
| `MIN_SCORE_THRESHOLD` | `0.42` | Similaridade cosseno mínima, calibrada no golden set |
| `CORS_ALLOW_ORIGINS` | `[]` | Lista JSON de origens permitidas. Vazio = CORS desligado. |
| `MAX_UPLOAD_BYTES` | 10 MB | Limite do upload de CSV |

## 📡 Endpoints

| Método | Endpoint | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/search/semantic` | — | Busca semântica (`query`, `top_k`, `min_score`) |
| POST | `/api/v1/index/movie` | 🔑 | Ingerir ou sobrescrever um filme (JSON) |
| POST | `/api/v1/index/movie/form` | 🔑 | Idem, via formulário |
| POST | `/api/v1/index/batch/csv` | 🔑 | Upload do catálogo CSV; relata inseridos, atualizados, duplicatas e linhas inválidas |
| DELETE | `/api/v1/index/movie/{id}` | 🔑 | Remover filme (404 se não existir) |
| GET | `/api/v1/index/count` | — | Total de filmes indexados |
| POST | `/api/v1/index/reset` | 🔑 | Apagar todo o índice |
| GET | `/ping` | — | Liveness |
| GET | `/api/v1/health` | — | Readiness: 503 quando o Weaviate está fora |

```bash
curl -X POST localhost:8000/api/v1/index/batch/csv \
  -H "X-API-Key: $API_KEY" -F "file=@catalogo.csv;type=text/csv"

curl -X POST localhost:8000/api/v1/search/semantic \
  -H 'content-type: application/json' -d '{"query": "memória e identidade negra"}'
```

**Identidade dos filmes:** o ID é derivado de título original + ano (`uuid5`). Reingerir o
mesmo filme o sobrescreve em vez de duplicar, por qualquer caminho de ingestão.

**Scores:** similaridade cosseno entre a consulta e o filme, independente do backend.

## 🧱 Arquitetura

```
app/
├── main.py                 # create_app() + lifespan
├── dependencies.py         # raiz de composição: único lugar onde classes concretas são montadas
├── bootstrap.py            # carga idempotente do parquet no startup
├── domain/                 # Movie, mapeamento CSV → filme, exceções de domínio (sem I/O de rede)
├── routers/                # HTTP fino: valida, chama o service, serializa
├── services/               # regras de negócio; dependem só de interfaces
├── providers/
│   ├── embeddings_file.py  # parquet de embeddings + fingerprint do modelo
│   └── pipelines/          # pipelines Haystack, componentes e contratos (interfaces.py)
├── evaluation/             # métricas de recuperação e golden set
├── scripts/                # jobs offline (geração/carga de embeddings, avaliação)
├── error_handlers.py       # exceções de domínio → 404/422/503; nunca vaza detalhes internos
└── security.py             # API key
```

Classes recebem dependências pelo construtor e implementam os contratos de
`interfaces.py`. Isso permite testar pipelines e services com um store em memória e, no
futuro, trocar o backend sem mexer nas camadas de cima. Veja `AGENTS.md` para as
convenções e princípios do repositório.

## 🛠️ Scripts

```bash
# Gerar embeddings do catálogo (grava o fingerprint do modelo no parquet)
uv run python -m app.scripts.save_embeddings caminho/do/catalogo.csv

# Indexar o parquet manualmente
uv run python -m app.scripts.load_embeddings

# Avaliar a qualidade da busca no golden set (Recall@k, nDCG@k, MRR, varredura de min_score)
uv run python -m app.scripts.evaluate
```

Datasets brutos (`data/*.csv`) não são versionados. O parquet de embeddings é versionado e
só é regenerado pelo script.

## 🧪 Testes e qualidade

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest --cov=app          # unitários: sem Weaviate, sem modelo
uv run pytest -m integration     # integração: Weaviate real (docker compose up -d weaviate)
```

A CI (GitHub Actions) roda lint, testes unitários e integração em todo PR.

**Avaliação:** `tests/eval/golden.jsonl` guarda consultas com julgamentos de relevância
(por título + ano). O baseline da v1 está em `docs/evaluation/v1-baseline.md`. Toda
mudança de modelo, de campos indexados ou de backend deve ser comparada com ele.

## 🤝 Agradecimentos

Este projeto foi baseado no [FastAPI Boilerplate](https://github.com/HiIamZeref/fastapi-boilerplate) desenvolvido por **Felipe Coimbra**.
A estrutura inicial e convenções de diretórios foram adaptadas a partir deste boilerplate.

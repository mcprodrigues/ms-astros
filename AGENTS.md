# AGENTS.md

## Mission

Astros is a search microservice over a catalog of films for cinema studies.
It indexes movie records (title, synopsis, description, keywords, director)
into Weaviate and exposes HTTP endpoints for search and index management.
Catalog content is predominantly Portuguese; retrieval quality on
Portuguese text matters more than raw latency.

## Stack

- Python 3.13, managed with `uv`; `pyproject.toml` is the single source of
  truth for dependencies (pinned versions)
- FastAPI + Pydantic v2 (`pydantic-settings` for configuration)
- Haystack 3.x pipelines; Weaviate (>= 1.27) as document store (`weaviate-haystack`)
- sentence-transformers for embeddings; pandas + pyarrow for batch data
- Docker + docker-compose for the runtime environment (API + Weaviate)

Install: `uv sync`
Run full stack: `docker-compose up --build`
Run API locally (Weaviate must be up): `uv run uvicorn app.main:app --reload`
Interactive API docs: `http://localhost:8000/docs`

## Testing

- pytest + pytest-asyncio; HTTP tests use FastAPI `TestClient`/httpx
- Tests live in `tests/`, mirroring `app/` (e.g. `tests/services/test_search.py`)
- Minimum 80% coverage on `app/services/` and `app/providers/`
- Unit tests mock collaborators through their interfaces
  (`app/**/interfaces.py`); they shall not require Weaviate or download a model
- Tests that need a live Weaviate are marked `@pytest.mark.integration`
  and excluded from the default run
- Every bug fix ships with a regression test
- Run: `uv run pytest --cov=app` (integration: `uv run pytest -m integration`)

## Lint & format

- ruff for linting and formatting; must pass before any PR
- Run: `uv run ruff check . && uv run ruff format --check .`

## Repository layout

- `app/routers/` — HTTP layer: validate input, call a service, map errors to HTTP
- `app/services/` — business logic; depends only on pipeline interfaces
- `app/providers/pipelines/` — Haystack pipelines (indexing, search)
- `app/providers/pipelines/components/` — reusable building blocks
  (embedder, retriever, document store)
- `app/schemas/` — Pydantic request/response models
- `app/scripts/` — offline jobs (e.g. embedding generation), run manually
- `app/settings.py` — the only place configuration is read
- `app/api.py` — mounts all routers under `/api/v1`
- `data/` — local datasets and derived artifacts (see Data)
- `specs/NNN-feature-name/` — one directory per feature spec/plan

Conventions:
- Every service and pipeline has an ABC contract in the sibling
  `interfaces.py`, prefixed `I` (`ISearchService`, `IIndexingPipeline`)
- Dependencies are exposed via cached `get_<name>()` factory functions and
  wired with FastAPI `Depends`
- Code, identifiers, comments, logs and commit messages are in English;
  domain field names mirror the Portuguese catalog vocabulary and are not
  translated
- Public methods first, private (`_`-prefixed) methods below

## Data

- Raw source datasets (CSV exports) are never committed
- The precomputed embeddings parquet under `data/embeddings/` is versioned,
  because the service loads it at startup; it is regenerated only via the
  embedding script in `app/scripts/`, never edited by hand

## Workflow

- Gitflow: branches `<type>/<short-slug>` (`feat/`, `fix/`, `refactor/`,
  `chore/`, `docs/`) off `develop`; PRs target `develop`; only `develop`
  merges into `main`
- Conventional Commits, no emoji: `<type>: <imperative description>`
  (e.g. `refactor: inject pipeline into indexing service`)
- Features with a spec reference their `specs/NNN-feature-name/` directory
  in the PR description
- Before opening a PR: tests and ruff pass locally

## Engineering principles

- Layering: routers shall contain no business logic and shall never access
  pipelines, components or Weaviate directly; services shall depend only on
  interfaces, never on concrete pipeline classes.
- Dependency injection: collaborators shall be passed through constructors;
  a class shall never instantiate its own dependencies. Wiring happens only
  in `get_<name>()` factories.
- Single embedding model: documents and queries shall be embedded with the
  same configured model. Changing the model requires regenerating the
  precomputed embeddings and reindexing in the same change.
- Configuration: URLs, ports, file paths, model names, index names and
  thresholds shall come from `Settings`, never from literals. Every new
  setting is added to `.env.example` in the same change.
- Idempotent startup: application startup shall never duplicate, overwrite
  or delete documents in a populated index. Destructive index operations
  run only on an explicit API call or manual command.
- No secrets in the repository; `.env` is never committed.

## Never do

- Never push directly to `main` or `develop`, and never force-push to them.
- Never commit raw datasets or `.env` files.
- Never hand-edit the embeddings parquet.
- Never reset or bulk-delete a Weaviate index unless the user explicitly asks.
- Never add a dependency without pinning it in `pyproject.toml` and stating
  why in the PR description.
- Never weaken or delete a failing test to make the suite pass.

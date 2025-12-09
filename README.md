# 🎬 Astros — Microserviço de Busca Semântica

Esse é um microserviço de busca semântica para estudos de cinema.

Ele fornece **indexação incremental**, **ingestão em lote**, **busca por similaridade** e **gerenciamento de documentos**, utilizando:

| Tecnologia | Função |
|-----------|--------|
| **FastAPI** | Exposição das rotas HTTP |
| **Haystack 2.x** | Construção dos pipelines de busca |
| **Weaviate Document Store** | Armazenamento e indexação semântica |
| **Pandas** | Ingestão em lote via CSV |
| **Docker** | Orquestração do ambiente |

---

## 🧱 Estrutura do Projeto

```
├── app
│   ├── api.py                      # Configuração das rotas da API
│   ├── main.py                     # Aplicação FastAPI principal
│   ├── providers               
│   │   ├── __init__.py
│   │   ├── pipelines           
│   │   │   ├── components          # Componentes reutilizáveis dos pipelines
│   │   │   │   ├── embedder.py     # Geração de embeddings 
│   │   │   │   ├── retriever.py    # Retriever usado nas buscas
│   │   │   │   └── store.py        # Provedor de WeaviateDocumentStore
│   │   │   ├── indexing.py         # Pipeline responsável pela indexação de documentos
│   │   │   ├── interfaces.py       # Contratos dos pipelines
│   │   │   └── semantic_search.py  # Pipeline de busca semântica
│   ├── routers
│   │   ├── health.py               # Health-check
│   │   ├── index.py                # Endpoints de indexação
│   │   ├── __init__.py
│   │   └── search.py               # Endpoints de busca semântica
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── movie.py                # Dados de filmes
│   │   └── search.py               # Requests/responses de buscas
│   ├── scripts
│   │   ├── load_embeddings.py      # Carregar embeddings existentes
│   │   └── save_embeddings.py      # Exportar/salvar embeddings
│   ├── services
│   │   ├── indexing.py             # Indexar dados + CSV ingest
│   │   ├── __init__.py
│   │   ├── interfaces.py           # Contratos dos serviços
│   │   └── search.py               # Busca semântica
│   └── settings.py                 # Configurações da aplicação
│
├── data
│   ├── embeddings
│   │   └── embeddings.parquet      # Embeddings pré-computados
│   └── movies.csv                  # Dataset de filmes
│
├── docker-compose.yml              # Configuração do Docker Compose
├── Dockerfile                      # Configuração do container Docker
├── pyproject.toml                  # Configuração do projeto e dependências (UV)
├── README.md                       # Esse arquivo
└── requirements.txt                # Dependências (compatibilidade)

```

## 🏗️ Arquitetura
- **Providers:** Fornecem recursos externos (banco, serviços externos, conexões).

- **Pipelines:** Fluxos de processamento organizados em etapas.
- **Components:** Peças menores reutilizáveis usadas dentro dos pipelines.
- **Services:** Implementam a lógica de negócio da aplicação.
- **Routers:** Definem os endpoints da API e conectam requisição → serviço.
- **Schemas:** Modelos de dados para validação e tipagem (via Pydantic).
- **Interfaces:** Contratos abstratos que definem comportamento esperado para injeção de depedências.

## 🚀 Como usar
```bash
# Executar com docker-compose
docker-compose up --build

# Executar em background
docker-compose up -d --build
```

### Endpoints Disponíveis
### Search
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/search/semantic` | Busca semântica |

### Indexing
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/index/movie` | Ingestão de um filme |
| POST | `/api/v1/index/movie/form` | Ingestão via formulário |
| POST | `/api/v1/index/batch/csv` | Ingestão em lote via CSV |
| DELETE | `/api/v1/index/movie/{movie_id}` | Remover filme |
| GET | `/api/v1/index/count` | Contagem de documentos |
| POST | `/api/v1/index/reset` | Resetar índice |

### Root
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Root endpoint |

### Health
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/ping` | Ping |
| GET | `/health` | Health check |

### Documentação da API

Acesse `http://localhost:8000/docs` para ver a documentação interativa da API.

## 🤝 Agradecimentos

Este projeto foi baseado no [FastAPI Boilerplate](https://github.com/HiIamZeref/fastapi-boilerplate) desenvolvido por **Felipe Coimbra**.  
A estrutura inicial e convenções de diretórios foram adaptadas a partir deste boiterplate.
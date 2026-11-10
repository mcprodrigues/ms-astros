# v1 model and content selection

Decision: **`BAAI/bge-m3`**, with curated fields first in the embedded text.
Measured on `tests/eval/golden.jsonl` (28 positive + 5 out-of-domain queries, 84 movies).
The original v1 baseline is in `v1-baseline.md`.

## 1. The truncation problem

`paraphrase-multilingual-MiniLM-L12-v2` reads only the first **128 tokens** of each text
and silently ignores the rest. 32 of the 84 movies, the best-catalogued ones, exceed
that (up to 582 tokens). Fields appended after the long synopsis/description never
reached the model. Appending `Tema` and `Tags` at the end therefore changed nothing for
the queries that needed them.

## 2. Content order (MiniLM, live Weaviate)

| Variant | Recall@5 | nDCG@5 | MRR |
|---|---|---|---|
| v1 baseline: title, synopsis, description, keywords, director | 0.737 | 0.677 | 0.738 |
| + Tema, Tags appended at the end | 0.724 | 0.658 | 0.703 |
| **Curated first, labelled**: title, `Tema:`, `Tags:`, `Palavras-chave:`, `Direção:`, synopsis, description | **0.812** | **0.753** | **0.812** |
| Curated first, no labels | 0.827 | 0.738 | 0.787 |

The labelled order was kept. Without labels, recall rose slightly but ranking (nDCG,
MRR) fell, and an out-of-domain query kept returning results up to `min_score` 0.46.

## 3. Embedding models (in-memory cosine, labelled order)

| Model | Context | Dim | Recall@5 | nDCG@5 | MRR | Best F1 with no out-of-domain results | Top-1 positive vs. max negative score | Query (CPU) |
|---|---|---|---|---|---|---|---|---|
| MiniLM-L12 multilingual | 128 | 384 | 0.812 | 0.753 | 0.812 | 0.571 | 0.61 vs 0.41 | 3 ms |
| multilingual-e5-small | 512 | 384 | 0.793 | 0.779 | 0.859 | 0.604 | **0.87 vs 0.86** | 3 ms |
| multilingual-e5-base | 512 | 768 | 0.817 | 0.787 | 0.875 | 0.569 | **0.84 vs 0.82** | 15 ms |
| **bge-m3** | 8192 | 1024 | **0.873** | **0.860** | **0.901** | **0.655** | 0.55 vs 0.46 | 51 ms |

- **bge-m3** wins on every metric and removes truncation (configured to 1024 tokens).
- **e5** ranks well but compresses all scores into a narrow band: an out-of-domain
  query scores about as high as a real hit, so `min_score` cannot separate results
  from noise. Rejected for that reason.
- The MiniLM row matches the live-Weaviate measurement in §2, which validates the
  in-memory comparison.

**Caveat:** 28 queries is a small set; differences of about 0.02–0.03 are within noise.
bge-m3's lead (+0.07 nDCG over the runner-up) is consistent across all metrics and F1.

## 4. Result on the live index (v1.0)

Same numbers as the in-memory comparison: **Recall@5 0.873, nDCG@5 0.860, MRR 0.901**
(v1 baseline: 0.737 / 0.677 / 0.738).

`MIN_SCORE_THRESHOLD` recalibrated to **0.50**: best F1 (0.655, precision 0.672,
recall 0.639) with no out-of-domain query returning results; 0.48 is the lowest clean
value. Scores are model-specific, so the MiniLM value (0.42) no longer applies.

Still weak, for v2: "religiões de matriz africana" (nDCG 0.00), "povos indígenas e seus
territórios" (0.28), "crianças brincando" (0.23). The indigenous-films query depends on
country/territory and genre, which are not indexed yet.

## 5. Costs accepted

- Model ~2.2 GB on disk; Docker image 6.2 GB. API memory about 1 GB at rest
  (measured), more while embedding large batches.
- Query embedding about 50 ms of CPU in isolation; 0.3–0.9 s end to end measured in
  the container (the first query warms the model).
- Generating embeddings is much slower (84 movies ≈ 1.5 min on CPU). It runs offline;
  very large catalogs would need a GPU or batching over time.

## 6. Changing the model again

The parquet fingerprint and the startup vector-dimension check refuse a model that
does not match the stored vectors. To switch:
`EMBEDDING_MODEL=...` → `uv run python -m app.scripts.save_embeddings <catalog.csv>` →
update the Dockerfile ARGs → reset the index → restart →
`uv run python -m app.scripts.evaluate`, compare, and recalibrate `MIN_SCORE_THRESHOLD`.

# v1 evaluation baseline

Golden set: `tests/eval/golden.jsonl` (28 positive + 5 negative queries).
Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 84 movies.
Regenerate with `uv run python -m app.scripts.evaluate` and compare before changing
model, fields or backend.

## Ranking quality (28 positive queries, k=5)

| Metric | Value |
|---|---|
| Recall@5 | 0.737 |
| nDCG@5 | 0.677 |
| MRR | 0.738 |

| Query | Recall@5 | nDCG@5 | RR |
|---|---|---|---|
| descoberta da sexualidade entre mulheres | 0.00 | 0.00 | 0.00 |
| intervenção artística contra outdoors | 0.00 | 0.00 | 0.00 |
| a morte como espetáculo | 0.00 | 0.00 | 0.09 |
| sertão e caatinga | 0.00 | 0.00 | 0.00 |
| rebeldia e poder feminino | 0.50 | 0.26 | 0.25 |
| crianças brincando | 0.33 | 0.47 | 1.00 |
| caçadores e presas | 0.33 | 0.47 | 1.00 |
| dor e desfiguração da identidade | 1.00 | 0.50 | 0.33 |
| a vida na cidade e o espaço urbano | 0.60 | 0.53 | 0.50 |
| crítica ao imperialismo e à guerra | 1.00 | 0.63 | 0.50 |
| racismo e padrões de beleza | 1.00 | 0.63 | 0.50 |
| o corpo em movimento como forma de expressão | 0.60 | 0.64 | 1.00 |
| fotos e vídeos antigos de família | 1.00 | 0.73 | 0.50 |
| filmar flores e plantas em um campo | 0.67 | 0.77 | 1.00 |
| memória e identidade negra | 0.80 | 0.79 | 1.00 |
| a insignificância humana diante do cosmos | 1.00 | 0.85 | 1.00 |
| povos indígenas e seus territórios | 0.80 | 0.85 | 1.00 |
| conflitos pela terra e trabalhadores do campo | 1.00 | 0.88 | 1.00 |
| cantos de trabalhadores | 1.00 | 0.96 | 1.00 |
| plantio de sementes tradicionais | 1.00 | 1.00 | 1.00 |
| tradições dos povos dos Andes | 1.00 | 1.00 | 1.00 |
| gravidez e maternidade | 1.00 | 1.00 | 1.00 |
| obsolescência tecnológica e ruínas urbanas | 1.00 | 1.00 | 1.00 |
| religiões de matriz africana | 1.00 | 1.00 | 1.00 |
| comida, cozinha e afeto | 1.00 | 1.00 | 1.00 |
| construções de barro e saberes tradicionais | 1.00 | 1.00 | 1.00 |
| música popular e cotidiano em Cuba | 1.00 | 1.00 | 1.00 |
| futebol | 1.00 | 1.00 | 1.00 |

## min_score sweep (top 5, 5 negative queries)

| min_score | Precision | Recall | F1 | Negatives with results |
|---|---|---|---|---|
| 0.30 | 0.312 | 0.738 | 0.439 | 2/5 |
| 0.32 | 0.319 | 0.721 | 0.442 | 2/5 |
| 0.34 | 0.311 | 0.689 | 0.429 | 2/5 |
| 0.36 | 0.323 | 0.689 | 0.440 | 2/5 |
| 0.38 | 0.344 | 0.689 | 0.459 | 1/5 |
| 0.40 ← best F1 | 0.360 | 0.656 | 0.465 | 1/5 |
| 0.42 | 0.356 | 0.590 | 0.444 | 0/5 |
| 0.44 | 0.388 | 0.541 | 0.452 | 0/5 |
| 0.46 | 0.417 | 0.492 | 0.451 | 0/5 |
| 0.48 | 0.426 | 0.426 | 0.426 | 0/5 |
| 0.50 | 0.431 | 0.361 | 0.393 | 0/5 |
| 0.52 | 0.452 | 0.311 | 0.369 | 0/5 |
| 0.54 | 0.528 | 0.311 | 0.392 | 0/5 |
| 0.56 | 0.615 | 0.262 | 0.368 | 0/5 |
| 0.58 | 0.591 | 0.213 | 0.313 | 0/5 |
| 0.60 | 0.706 | 0.197 | 0.308 | 0/5 |

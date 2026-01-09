# Tier-1 Starter Pack (Fact Graph + Jinja2 Template + Golden Queries)

This folder contains:
- `schema.json`: JSON Schema for one Layer-1 day fact graph (Tier-1).
- `market_wrap_l1.md.j2`: Jinja2 template to render a Layer-1 daily market wrap from a fact graph.
- `queries.yaml`: Starter golden query set (retrieval eval) mapping to deterministic `chunk_id` markers in the template.

## How to use

1. Generate or hand-author day JSON objects that validate against `schema.json`.
2. Render with Jinja2:
   - Load the day JSON into a variable named `day` (dict/object).
   - Render `market_wrap_l1.md.j2`.
3. In ingestion, split chunks by the `<!-- chunk_id: ... -->` markers and persist `chunk_id`/`chunk_type` in your chunk registry and Milvus metadata.
4. Use `queries.yaml` to run retrieval eval (Recall@K, MRR, filter correctness).

## Notes

- This template is Layer-1 clean by construction (no causal language, no subjective labels).
- Keep numeric truth in the fact graph. The template only formats those values.

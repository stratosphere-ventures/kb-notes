# Phase 1 — Knowledge Base (Hybrid RAG, Agentic, Grounded)

## 1. Purpose & Scope

### 1.1 Objective

Build an industry-grade, accurate, and auditable knowledge base capable of:

- Answering research and analysis questions
- Generating grounded summaries and SOP-style outputs
- Handling stock-market research with strict separation of narrative vs numeric facts
- Supporting agentic self-correction without hallucination

Phase 1 focuses on retrieval accuracy, grounding, and observability. Knowledge graphs, GNNs, and advanced reasoning are explicitly out of scope for this phase.

## 2. Non-Goals (Explicitly Out of Scope for Phase 1)

- Knowledge graph construction or GNN integration
- Fine-tuning LLMs
- Autonomous long-running agents
- Recommendation engines (buy/sell signals)
- Multi-tenant auth / billing
- Production-scale distributed deployment

## 3. Design Principles (Hard Requirements)

### Retrieval > Generation
The system succeeds or fails on retrieval quality, not prompt cleverness.

### Grounding First
No claim without evidence. Citations are mandatory.

### Determinism Over "Creativity"
The orchestration graph must be replayable and traceable.

### Numeric Facts Are Deterministic
Prices, returns, drawdowns must never come from document RAG.

### Evaluation-Driven Development
Every architectural choice must be testable via offline eval.

## 4. Users & Primary Use Cases

### 4.1 Users
- Internal researcher / analyst
- Portfolio strategist
- Engineering operator debugging retrieval quality

### 4.2 Primary Use Cases
- "Summarize how NVDA's guidance changed in 2024"
- "Generate a risk-management SOP from our internal playbooks"
- "Explain why semiconductors sold off in April 2025"
- "Compare drawdowns of SOXL vs SMH and explain drivers"
- "What changed since last earnings?"

## 5. System Architecture Overview

### 5.1 Core Subsystems
- **RAG Subsystem** (Milvus-backed)
- **Market Data Subsystem** (deterministic facts)
- **Web Research Subsystem** (gated, optional)
- **Agentic Control Plane** (LangGraph/LangChain)
- **Evaluation & Observability Layer**

## 6. Technology Stack (Phase 1)

### 6.1 Core
- **LLM**: GPT-OSS served via SGLang
- **Vector DB**: Milvus
- **Embeddings**: BGE-M3 (dense + sparse)
- **Reranker**: Cross-encoder or NVIDIA NeMo reranker
- **API Layer**: FastAPI
- **Orchestration**: LangChain / LangGraph
- **Web Search**: Tavily (gated)

### 6.2 Supporting Infrastructure (Mandatory)
- Document ingestion & parsing layer
- Chunking + versioning system
- Market data service (TimescaleDB / ClickHouse)
- Evaluation harness
- Tracing & logging
- Caching layer
- Secrets/config management
- UI (Streamlit for debug; Next.js later)

## 7. Data Model & Storage

### 7.1 Milvus Collections

#### kb_chunks (Primary Retrieval)
Stores retrievable content with embeddings and metadata.

**Required fields:**
- chunk_id (PK)
- doc_id
- source_type (internal, filing, transcript, news, web)
- source_name
- source_url
- ticker_symbols
- topic_tags
- doc_version
- effective_start
- effective_end
- is_active
- trust_tier
- ingested_at
- section_path
- chunk_index
- text
- dense_vec
- sparse_vec
- ttl_expire_at (web/news only)

#### kb_docs (Document Registry)
Manages versioning, provenance, and auditability.

## 8. Ingestion Workflow (Offline / Async)

1. Source intake (PDF, HTML, Markdown, notes, web)
2. Parsing & normalization
3. Section-aware chunking
4. Metadata enrichment
5. Dense + sparse embedding (BGE-M3)
6. Upsert into Milvus
7. Mark superseded versions inactive (no hard deletes)

**Non-negotiable**: versioning and tombstones must be supported from day one.

## 9. Query Workflow (Agentic RAG)

### 9.1 High-Level Flow

#### Router Agent
- Classifies intent
- Extracts filters (tickers, dates, source types)

#### Evidence Selection
- Numeric → Market Data Service
- Narrative → Milvus RAG
- Missing/recency → gated web search

#### Hybrid Retrieval
- Dense + sparse search (K=100)
- Reranking
- Reduce to top N (default 12)

#### Evidence Grader
- PASS / WEAK / FAIL
- Emits reason codes

#### Self-Correction Loop
- Rewrite query/filters
- Retry retrieval (max 2 loops)

#### Generation
- GPT-OSS synthesizes grounded answer
- Mandatory citations
- Abstention

## 10. Agent Decision Thresholds

### 10.1 Rerank
Always rerank if >20 candidates retrieved

### 10.2 Rewrite & Retry
**Triggered if:**
- Top rerank score < 0.55
- Mean top-5 score < 0.45
- Missing entity coverage
- Timeframe mismatch
- Grader returns WEAK or FAIL

**Max retries**: 2

### 10.3 Tavily Web Search (Gated)
**Only if:**
- Query is recency-sensitive OR explicitly requests web
- AND
- Local evidence FAILS after ≥1 retry

### 10.4 Abstention
**Triggered when:**
- Rewrite budget exhausted
- Tavily disallowed or insufficient

## 11. Market Data Subsystem (Critical)

### 11.1 Purpose
Provide deterministic numeric facts:
- Prices
- Returns
- Volatility
- Drawdowns
- Earnings calendars
- Macro series

### 11.2 Storage
TimescaleDB / ClickHouse
API-based access (/prices, /returns, /drawdowns)

### 11.3 Rule
No numeric market facts may be generated from RAG documents.

## 12. Output Requirements

### 12.1 Answer Structure
Clear separation:
- Facts (data)
- Interpretation (documents/news)
- Inline citations per paragraph or step
- Source metadata exposed to UI

### 12.2 SOP Output Format
| Step | Description | Responsible role | Inputs | Outputs | Controls | Citations per step |
|------|-------------|-------------------|--------|---------|----------|-------------------|

## 13. Evaluation & Observability

### 13.1 Metrics
- Retrieval recall@K
- Rerank precision@N
- Citation coverage
- Faithfulness score
- Abstention correctness
- Numeric accuracy (market data)

### 13.2 Tooling
- Offline eval runner
- Query trace logs
- Reproducible configs
- UI inspection of retrieval context

## 14. UI Requirements (Phase 1)

### Debug UI (Streamlit)
- Show retrieved chunks
- Show rerank scores
- Show citations
- Show decision path

### Product UI (Later)
- Clean answer display
- Expandable citations
- Confidence indicators

## 15. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Hallucinated numbers | Deterministic market data service |
| Version mixing | Strict doc versioning |
| Over-use of web | Tavily gating + TTL |
| Infinite loops | Hard retry limits |
| Poor retrieval | Hybrid + rerank + eval |

## 16. Phase-1 Exit Criteria (Definition of Done)

Phase 1 is complete when:
- Hybrid RAG consistently outperforms dense-only RAG in eval
- Numeric queries never hallucinate
- Self-correction improves retrieval in ≥60% of weak cases
- Every answer is fully traceable and replayable
- Engineers can explain why an answer was produced

## 17. Phase-2 Preview (Not Implemented)

- Knowledge graph construction
- Entity normalization
- Graph-augmented retrieval
- GNN-based relevance priors

---

# Technical Terms Explained

## Reranking
**Reranking** is the process of reordering retrieved documents to improve relevance. After an initial search returns a set of candidate documents, a reranker model (typically a cross-encoder) scores each document-query pair more accurately than the initial retrieval, allowing the system to prioritize the most relevant results.

## Vector Store
A **vector store** (or vector database) is a specialized database designed to store and query high-dimensional vectors efficiently. It enables similarity search by finding vectors that are closest to a query vector in the embedding space, which is fundamental for RAG systems.

## Retrieval
**Retrieval** is the process of finding and fetching relevant documents or information from a knowledge base in response to a query. In RAG systems, retrieval typically involves vector similarity search to find documents that are semantically similar to the query.

## Routing
**Routing** refers to the process of directing a query to the appropriate subsystem or component based on its characteristics. A router agent analyzes the query intent and determines whether it should be handled by numeric data services, document retrieval, web search, or other specialized components.

## Chunking
**Chunking** is the process of breaking down large documents into smaller, manageable pieces (chunks) that can be effectively embedded and retrieved. Good chunking strategies consider semantic boundaries, context preservation, and optimal chunk sizes for the embedding model.

## Evaluation Harness
An **evaluation harness** is a testing framework that systematically evaluates system performance against predefined datasets and metrics. It provides reproducible, automated testing of retrieval quality, generation accuracy, and other key performance indicators.

## Caching Layer
A **caching layer** stores frequently accessed data or computed results to improve system performance and reduce redundant computations. In RAG systems, caching can store query results, embeddings, or intermediate computations to speed up response times.

## Tracing and Logging
**Tracing and logging** refers to the systematic collection of execution data for debugging, monitoring, and analysis. Tracing captures the flow of requests through the system, while logging records events, errors, and performance metrics for observability.

## Embedding
**Embedding** is the process of converting text, images, or other data into numerical vector representations that capture semantic meaning. These vectors enable mathematical operations like similarity search and are the foundation of modern retrieval systems.

## Hybrid Retrieval
**Hybrid retrieval** combines multiple retrieval approaches, typically dense vector search with sparse keyword search. Dense search captures semantic similarity while sparse search ensures exact keyword matching, providing more comprehensive and accurate results.

## GNN (Graph Neural Network)
A **Graph Neural Network** is a type of neural network designed to work with graph-structured data. GNNs can learn from the relationships and connections between nodes in a graph, making them useful for knowledge graph reasoning and entity relationship analysis. (Note: GNNs are explicitly out of scope for Phase 1)


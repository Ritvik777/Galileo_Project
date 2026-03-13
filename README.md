# Self-Corrective RAG with LangGraph

A portfolio-grade Retrieval-Augmented Generation app that demonstrates **agentic AI patterns** — conditional routing, self-correction, and observability — using LangGraph.

## Architecture

Unlike basic RAG (`retrieve → generate`), this pipeline **self-corrects** by grading documents for relevance and falling back to web search when needed:

```
START → rewrite_query → retrieve → grade_documents ─┬─ relevant     → generate → END
                                                     └─ not relevant → websearch_fallback → generate → END
```

## Project Structure — One File Per Concern

Each file does **one thing**, making the codebase easy to read and explain:

```
RAG/
│
├── config.py        ← All settings and API keys (the only file you configure)
├── embeddings.py    ← Google Gemini embedding model (text → vectors)
├── llm.py           ← OpenAI GPT-4o-mini (generates text)
├── chunker.py       ← Text chunking + PDF extraction
├── database.py      ← Qdrant: connect, store, and search documents
│
├── state.py         ← RAGState definition (data flowing through the graph)
├── nodes.py         ← The 5 LangGraph node functions
├── graph.py         ← Wires nodes into the LangGraph pipeline
│
├── app.py           ← Streamlit UI (chat, PDF upload, pipeline trace)
│
├── requirements.txt
├── .env             ← Your API keys (not committed to git)
├── .env.example     ← Template showing which keys you need
└── .gitignore
```

### How to read the code (recommended order)

1. **`config.py`** — See what settings exist
2. **`embeddings.py`** + **`llm.py`** — The two AI models (one line each)
3. **`chunker.py`** — How text gets split into small pieces
4. **`database.py`** — How documents get stored and searched in Qdrant
5. **`state.py`** — The "form" that flows through the pipeline
6. **`nodes.py`** — The 5 steps of the pipeline (the core logic)
7. **`graph.py`** — How the 5 nodes are wired together
8. **`app.py`** — The user interface

## Pipeline Nodes

| # | Node | What it does |
|---|------|-------------|
| 1 | **rewrite_query** | LLM rewrites the question for better vector search |
| 2 | **retrieve** | Searches Qdrant for the 4 most similar document chunks |
| 3 | **grade_documents** | LLM grades each document as relevant or irrelevant |
| 4 | **websearch_fallback** | If no relevant docs, searches the web via DuckDuckGo |
| 5 | **generate** | LLM generates the final answer from the best available context |

### Why self-corrective?

Vector similarity search often returns documents that are *similar* but not *relevant*. The LLM grading step filters out false positives. If all documents fail grading, the pipeline falls back to web search instead of generating a bad answer.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Vector Database | Qdrant Cloud |
| Embeddings | Google Gemini (`gemini-embedding-001`, 3072-dim) |
| LLM | OpenAI GPT-4o-mini |
| Orchestration | LangGraph (conditional edges, typed state) |
| Web Fallback | DuckDuckGo Search (no API key needed) |
| UI | Streamlit (chat interface, pipeline trace) |

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy env template and add your API keys
cp .env.example .env
# Edit .env with your actual keys

# 3. Run the app
streamlit run app.py
```

## Required API Keys

| Key | Where to get it |
|-----|----------------|
| `GOOGLE_API_KEY` | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `QDRANT_URL` | [Qdrant Cloud](https://cloud.qdrant.io/) |
| `QDRANT_API_KEY` | Qdrant Cloud dashboard → API Keys |

## UI Features

- **Chat interface** with message history
- **PDF upload** with automatic text extraction and chunking
- **Pipeline trace** — expand any answer to see every step the graph took
- **LangGraph visualization** rendered in the sidebar
- **Live document count** from Qdrant

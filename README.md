<div align="center">

# 🧩 RAGarator V1

**AI-Powered RAG Chunking Strategy Benchmarking Platform**

```markdown
> 🚀 **Current Release: RAGarator V1.0**
>
> RAGarator V1.0 is the first deployed version of the platform. It provides document ingestion, four chunking strategies, benchmarking, explainable scoring, confidence estimation, and strategy recommendations.

## 🌐 Live Demo

RAGarator V1.0 is officially deployed and available online.

- **Frontend:** https://ra-garator.vercel.app
- **Backend API:** https://ragarator-api.onrender.com
- **API Documentation (Swagger):** https://ragarator-api.onrender.com/docs

> The frontend is deployed on Vercel, while the FastAPI backend is deployed on Render.

*Version 1.0 — Initial Working Release*

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB.svg)](https://react.dev/)
[![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)]()
[![License](https://img.shields.io/badge/License-Educational%2FResearch-lightgrey.svg)]()

</div>

---

RAGarator is a platform that answers one question for any document you throw at it:

> **Which chunking strategy is most suitable for *this specific document*, and why?**

Retrieval-Augmented Generation (RAG) pipelines live or die by how documents get chunked before embedding. There's no single "best" chunking strategy — a technique that works beautifully on a research paper can fall apart on a legal contract or a plain-text log file. RAGarator removes the guesswork: it runs a document through multiple chunking strategies, benchmarks each one on real retrieval performance, and recommends a winner with a confidence score and a plain-English explanation.

---

## Table of Contents

- [🧩 RAGarator V1](#-ragarator-v1)
  - [Table of Contents](#table-of-contents)
  - [Problem Statement](#problem-statement)
  - [Version 1 Scope](#version-1-scope)
  - [How RAGarator Works](#how-ragarator-works)
  - [Key Features](#key-features)
    - [📄 Document Analysis](#-document-analysis)
    - [🔀 Multiple Chunking Strategies](#-multiple-chunking-strategies)
    - [📊 Chunk Quality Evaluation](#-chunk-quality-evaluation)
    - [🔍 Retrieval Benchmarking](#-retrieval-benchmarking)
    - [💡 Explainable Recommendations](#-explainable-recommendations)
  - [Supported Chunking Strategies](#supported-chunking-strategies)
    - [1. Fixed Chunking](#1-fixed-chunking)
    - [2. Recursive Chunking](#2-recursive-chunking)
    - [3. Sentence-Based Chunking](#3-sentence-based-chunking)
    - [4. Token-Based Chunking](#4-token-based-chunking)
  - [Evaluation Framework](#evaluation-framework)
    - [Benchmarking Pipeline](#benchmarking-pipeline)
  - [Decision Engine](#decision-engine)
  - [Backend Architecture](#backend-architecture)
    - [Frontend](#frontend)
  - [API Endpoints](#api-endpoints)
  - [Tech Stack](#tech-stack)
  - [Running Locally](#running-locally)
    - [Clone the repository](#clone-the-repository)
    - [Backend setup](#backend-setup)
    - [Frontend setup](#frontend-setup)
  - [Testing](#testing)
  - [RAGarator V1 Limitations](#ragarator-v1-limitations)
  - [Future Versions](#future-versions)
    - [🚀 RAGarator V2 — Advanced Intelligence and Optimization](#-ragarator-v2--advanced-intelligence-and-optimization)
    - [🏗️ RAGarator V3 — Production RAG Integration](#️-ragarator-v3--production-rag-integration)
    - [🧠 RAGarator V4 — Intelligent Adaptive Chunking](#-ragarator-v4--intelligent-adaptive-chunking)
  - [Long-Term Vision](#long-term-vision)
  - [Project Status](#project-status)
  - [Author](#author)
  - [License](#license)

---

## Problem Statement

Chunking is one of the most critical — and most underrated — components of a RAG pipeline. Documents must be split into smaller pieces before they can be embedded and retrieved, and the strategy used to split them has a direct impact on:

- Semantic context preservation
- Retrieval accuracy
- Information redundancy
- Embedding efficiency
- Retrieval latency
- Context fragmentation
- Overall RAG response quality

Today, most developers pick a chunking strategy based on intuition or general best practices, then move on. RAGarator makes that decision **systematic and document-aware** — evaluating multiple strategies on the actual document instead of assuming one is universally better.

---

## Version 1 Scope

RAGarator V1 focuses on building and validating the core intelligence and decision engine of the platform.

| Area | Included in V1 |
|---|---|
| Document ingestion & preprocessing | ✅ |
| File support | PDF, DOCX, TXT |
| Chunking strategies | Fixed, Recursive, Sentence-based, Token-based |
| Embedding generation | ✅ |
| Semantic retrieval evaluation | ✅ |
| Chunk quality evaluation | ✅ |
| Benchmark query generation | ✅ |
| Strategy scoring & ranking | ✅ |
| Confidence estimation | ✅ |
| Explainable, document-specific recommendations | ✅ |
| REST API | FastAPI |
| Frontend | React |

---

## How RAGarator Works

```
Document Upload
      │
      ▼
Document Ingestion
      │
      ▼
Text Cleaning & Metadata Extraction
      │
      ▼
Multiple Chunking Strategies
      │
      ├── Fixed Chunking
      ├── Recursive Chunking
      ├── Sentence-Based Chunking
      └── Token-Based Chunking
      │
      ▼
Embedding Generation
      │
      ▼
Retrieval Benchmarking
      │
      ▼
Chunk Quality Evaluation
      │
      ├── Chunk Quality
      ├── Consistency
      ├── Efficiency
      └── Retrieval Quality
      │
      ▼
Decision & Scoring Engine
      │
      ▼
Confidence Estimation
      │
      ▼
Final Recommendation
      │
      ▼
Document-Specific Explanation
```

---

## Key Features

### 📄 Document Analysis
Supports **PDF**, **DOCX**, and **TXT** files. Documents are loaded, cleaned, and normalized before entering the chunking pipeline.

### 🔀 Multiple Chunking Strategies
Every document is run through several chunking strategies in parallel, under identical conditions, enabling direct, apples-to-apples comparison.

### 📊 Chunk Quality Evaluation
Generated chunks are scored on:
- Semantic quality
- Structural consistency
- Chunk size distribution
- Context preservation
- Efficiency

### 🔍 Retrieval Benchmarking
Each strategy's chunks are embedded, indexed, and tested against benchmark queries to measure real-world retrieval effectiveness — not just chunk structure in isolation.

### 💡 Explainable Recommendations
RAGarator doesn't just say *"Use Recursive Chunking."* It explains:
- Why a strategy was selected
- Which document characteristics drove the decision
- How competing strategies performed
- Which metrics contributed to the final score
- How confident the system is in the recommendation

> **Example explanation:**
> *"Recursive chunking was recommended because the document contains long structured sections with varying paragraph lengths. The strategy achieved stronger retrieval performance while preserving more contextual continuity than fixed-size chunking."*

---

## Supported Chunking Strategies

### 1. Fixed Chunking
Splits documents into chunks of a predefined size.

- **Advantages:** simple, predictable chunk sizes, computationally efficient
- **Best for:** uniform documents, structured data, consistently formatted text

### 2. Recursive Chunking
Recursively splits documents using hierarchical separators — paragraphs → sections → sentences → words.

- **Advantages:** better context preservation, adapts to document structure, handles long-form text well
- **Best for:** research papers, technical documentation, long-form content, structured documents

### 3. Sentence-Based Chunking
Groups complete sentences into chunks.

- **Advantages:** preserves sentence boundaries, reduces context fragmentation, maintains natural language flow
- **Best for:** articles, reports, narrative documents, educational content

### 4. Token-Based Chunking
Splits text according to token limits.

- **Advantages:** compatible with LLM context limits, token-aware, production-friendly
- **Best for:** LLM-based applications, context-window optimization, token-sensitive pipelines

---

## Evaluation Framework

RAGarator scores each strategy across four dimensions:

| Dimension | What it measures |
|---|---|
| **Chunk Quality** | Coherence, context preservation, semantic completeness, chunk structure |
| **Consistency** | Chunk size variation, structural uniformity, distribution consistency |
| **Efficiency** | Processing time, number of chunks generated, chunking overhead |
| **Retrieval Quality** | Retrieval relevance, similarity scores, query-to-chunk matching, ranking quality |

### Benchmarking Pipeline

For each chunking strategy:

```
Strategy
   │
   ▼
Generate Chunks
   │
   ▼
Generate Embeddings
   │
   ▼
Create Retrieval Index
   │
   ▼
Run Benchmark Queries
   │
   ▼
Retrieve Relevant Chunks
   │
   ▼
Calculate Retrieval Metrics
```

This lets strategies be compared on **retrieval behavior**, not just chunk structure alone.

---

## Decision Engine

The Decision Engine is the core intelligence layer of RAGarator V1. Rather than optimizing for a single metric, it fuses multiple evaluation signals into one explainable recommendation.

```
Evaluation Metrics
       │
       ▼
Metric Normalization
       │
       ▼
Weighted Scoring
       │
       ▼
Strategy Ranking
       │
       ▼
Confidence Estimation
       │
       ▼
Recommendation Generation
       │
       ▼
Human-Readable Explanation
```

**Output includes:**
- Recommended strategy
- Ranked alternatives
- Overall & per-metric scores
- Confidence level
- Reasoning behind the recommendation
- Document-specific explanation

---

## Backend Architecture

```

backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Application configuration
│   │
│   ├── api/
│   │   ├── health.py           # Health check endpoint
│   │   ├── upload.py           # File upload endpoint
│   │   └── analyze.py          # Document analysis endpoint
│   │
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   │
│   ├── services/
│   │   ├── ingestion/          # Loaders, cleaner, metadata
│   │   ├── chunkers/           # Fixed, recursive, sentence, token, manager
│   │   ├── embeddings/         # Embedder
│   │   ├── retrieval/          # Retriever, evaluator
│   │   ├── evaluation/         # Quality, consistency, efficiency
│   │   ├── decision/           # Scoring, confidence, explanation, recommendation
│   │   ├── benchmark/          # Queries, metrics, evaluator
│   │   ├── jobs/                # Async analyze jobs for the UI
│   │   └── pipeline/            # analyzer.py — complete analysis pipeline
│   │
│   └── utils/
│
└── tests/                       # Backend tests

frontend/
├── package.json
├── vite.config.js
├── index.html
├── public/
│   └── sample.txt
└── src/
    ├── main.jsx
    ├── RAGarator.jsx
    └── index.css

samples/
└── rag_methods.txt

start.sh
```

### Frontend

The frontend lets users:

- Upload a document
- Submit it for analysis
- View the recommended chunking strategy
- Compare strategy scores
- Understand confidence levels
- View explanations and evaluation results

**Frontend stack:** React · Vite · Tailwind CSS

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Checks whether the backend service is running |
| `POST` | `/upload` | Uploads a supported document (`.pdf`, `.docx`, `.txt`) for analysis |
| `POST` | `/analyze` | Runs the complete RAGarator analysis pipeline |

**`POST /analyze` performs:**

1. Document loading
2. Text cleaning
3. Metadata extraction
4. Multiple chunking strategies
5. Embedding generation
6. Chunk quality evaluation
7. Retrieval benchmarking
8. Strategy scoring
9. Confidence estimation
10. Recommendation generation
11. Explainable result generation

---

## ☁️ Deployment Architecture

```text
User
 │
 ▼
Vercel
React + Vite Frontend
https://ra-garator.vercel.app
 │
 │ API Requests
 ▼
Render
FastAPI Backend
https://ragarator-api.onrender.com
 │
 ▼
RAGarator Analysis Pipeline
 │
 ├── Document Ingestion
 ├── Text Cleaning
 ├── Chunking Strategies
 │    ├── Fixed-size
 │    ├── Recursive
 │    ├── Sentence-based
 │    └── Token-based
 │
 ├── Embedding Generation
 ├── Retrieval Evaluation
 ├── Quality Evaluation
 ├── Consistency Evaluation
 ├── Efficiency Evaluation
 │
 ▼
Decision Engine
 │
 ▼
Recommended Chunking Strategy

## Tech Stack

<table>
<tr>
<td valign="top" width="33%">

**Backend**
- Python
- FastAPI
- Pydantic
- Uvicorn

</td>
<td valign="top" width="33%">

**ML & NLP**
- Sentence Transformers
- PyTorch
- NumPy
- Scikit-learn

**Document Processing**
- PyMuPDF
- python-docx

**Chunking**
- LangChain Text Splitters

</td>
<td valign="top" width="33%">

**Frontend**
- React
- Vite
- Tailwind CSS

</td>
</tr>
</table>

---

## Running Locally

### Clone the repository

```bash
git clone https://github.com/geetika-rupani/RAGarator.git
cd RAGarator
```

### Backend setup

```bash
cd backend

# Create a virtual environment
python3.11 -m venv .venv

# Activate it (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload
```

- Backend: `http://localhost:8000`
- Swagger API docs: `http://localhost:8000/docs`

### Frontend setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

- Frontend: `http://localhost:5173`

---

## Testing

Run backend tests from the `backend` directory:

```bash
pytest
```

---

## RAGarator V1 Limitations

RAGarator V1 focuses on building and validating the core chunking decision engine. It is **not** intended to be the final architecture of the platform. Current limitations include:

- Limited number of chunking strategies
- Local embedding generation
- Limited benchmark datasets
- No persistent vector database integration
- Limited asynchronous processing
- Initial metric weighting and scoring logic
- Single-document focused analysis

These limitations set the roadmap for future versions.

---

## Future Versions

### 🚀 RAGarator V2 — Advanced Intelligence and Optimization
- Dynamic chunk size optimization
- Automatic overlap optimization
- Additional chunking strategies
- Advanced semantic evaluation
- Improved benchmark query generation
- More sophisticated confidence estimation
- Multi-document analysis
- Improved visualization and comparison dashboards

### 🏗️ RAGarator V3 — Production RAG Integration
- Vector database integration
- FAISS integration
- Pinecone or Weaviate support
- End-to-end RAG pipeline testing
- LLM-based retrieval evaluation
- Automated RAG performance benchmarking
- Real-world question-answering evaluation

### 🧠 RAGarator V4 — Intelligent Adaptive Chunking
- Hybrid chunking strategies
- Adaptive chunking based on document sections
- Machine learning-based chunking strategy prediction
- Reinforcement learning for chunk optimization
- LLM-guided semantic chunking
- Automatic chunk boundary detection
- Domain-aware chunking strategies

The long-term objective is to move from **"Which existing chunking strategy should I use?"** toward **"How should this specific document be optimally chunked?"**

---

## Long-Term Vision

RAGarator aims to become an intelligent chunking optimization layer for RAG systems — treating chunking not as a static preprocessing step, but as something:

- **Adaptive**
- **Data-driven**
- **Explainable**
- **Document-aware**
- **Performance-oriented**

Eventually, the platform could automatically determine a document's optimal chunking strategy, optimal chunk size, optimal overlap, section-specific chunking behavior, and retrieval configuration — turning chunking into a measurable, optimized component of RAG system design.

---

## Project Status

| | |
|---|---|
| **Current Version** | RAGarator V1 |
| **Status** | Active Development |
| **Core Decision Engine** | Implemented |
| **Backend** | FastAPI |
| **Frontend** | React |
| **Deployment** | In Progress |

RAGarator V1 represents the first working implementation and foundation of the broader RAGarator platform.

---

## Author

**Geetika Rupani**
B.Tech — Information Technology, Vellore Institute of Technology
GitHub: [@geetika-rupani](https://github.com/geetika-rupani)

---

## License

This project is currently developed for educational, research, and portfolio purposes.

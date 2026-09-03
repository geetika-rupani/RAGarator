RAGarator V1
AI-Powered RAG Chunking Strategy Benchmarking Platform

Version 1.0 — Initial Working Release

RAGarator V1 is the first implementation of an AI-powered benchmarking platform designed to determine the most suitable document chunking strategy for Retrieval-Augmented Generation (RAG) systems.

The core idea behind RAGarator is that there is no universally optimal chunking strategy. Different documents have different structures, semantic densities, lengths, and retrieval requirements. A chunking strategy that performs well for one document may perform poorly for another.

RAGarator addresses this problem by analyzing a document using multiple chunking strategies, evaluating them across several dimensions, benchmarking retrieval performance, and recommending the most suitable strategy with a confidence score and document-specific explanation.

Table of Contents
Problem Statement
Version 1 Scope
How RAGarator Works
Key Features
Supported Chunking Strategies
Evaluation Framework
Decision Engine
Backend Architecture
API Endpoints
Tech Stack
Running Locally
Testing
Future Versions
Author
Problem Statement

Chunking is one of the most critical components of a Retrieval-Augmented Generation (RAG) pipeline.

Documents must be divided into smaller chunks before they can be embedded and retrieved. However, selecting an inappropriate chunking strategy can significantly affect the performance of the entire RAG system.

Different chunking strategies influence:

Semantic context preservation
Retrieval accuracy
Information redundancy
Embedding efficiency
Retrieval latency
Context fragmentation
Overall RAG response quality

Currently, developers often manually select chunking strategies based on assumptions or general best practices.

RAGarator aims to make this decision more systematic and document-aware.

Instead of assuming that one strategy is always better, RAGarator evaluates multiple strategies on the actual document and recommends the most suitable one based on measurable evidence.

Version 1 Scope

RAGarator V1 focuses on establishing and validating the core intelligence and decision engine of the platform.

The current version includes:

Document ingestion and preprocessing
Support for PDF, DOCX, and TXT files
Multiple chunking strategies
Embedding generation
Semantic retrieval evaluation
Chunk quality evaluation
Benchmark query generation
Strategy scoring and ranking
Confidence estimation
Explainable recommendations
Document-specific reasoning
REST API using FastAPI
React-based frontend interface

The primary goal of Version 1 is to build a reliable and explainable engine capable of answering the question:

Which chunking strategy is most suitable for this specific document, and why?

How RAGarator Works
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
Key Features
Document Analysis

RAGarator supports the analysis of:

PDF documents
DOCX documents
TXT files

Documents are loaded, cleaned, and processed before entering the chunking evaluation pipeline.

Multiple Chunking Strategies

Each document is processed using multiple chunking strategies rather than relying on a single predefined method.

This allows direct comparison of strategies under the same document conditions.

Chunk Quality Evaluation

Generated chunks are evaluated for characteristics such as:

Semantic quality
Structural consistency
Chunk size distribution
Context preservation
Efficiency
Retrieval Benchmarking

RAGarator evaluates how effectively chunks support semantic retrieval.

The retrieval system uses embeddings and benchmark queries to measure whether relevant information can be retrieved effectively.

Explainable Recommendations

The system does not simply return:

"Use Recursive Chunking."

Instead, it aims to explain:

Why a strategy was selected
Which document characteristics influenced the decision
How competing strategies performed
Which metrics contributed to the final score
How confident the system is in the recommendation
Supported Chunking Strategies
1. Fixed Chunking

Splits documents into chunks of a predefined size.

Advantages
Simple implementation
Predictable chunk sizes
Computationally efficient
Suitable For
Uniform documents
Structured data
Documents with consistent formatting
2. Recursive Chunking

Recursively splits documents using hierarchical separators such as:

Paragraphs
Sections
Sentences
Words
Advantages
Better context preservation
Adapts to document structure
Handles long-form text effectively
Suitable For
Research papers
Technical documentation
Long-form content
Structured documents
3. Sentence-Based Chunking

Groups complete sentences into chunks.

Advantages
Preserves sentence boundaries
Reduces context fragmentation
Maintains natural language structure
Suitable For
Articles
Reports
Narrative documents
Educational content
4. Token-Based Chunking

Splits text according to token limits.

Advantages
Compatible with LLM context limits
Token-aware processing
Useful for production RAG systems
Suitable For
LLM-based applications
Context-window optimization
Token-sensitive pipelines
Evaluation Framework

RAGarator evaluates each chunking strategy across multiple dimensions.

Chunk Quality

Measures whether chunks preserve meaningful and coherent information.

Factors may include:

Chunk coherence
Context preservation
Semantic completeness
Chunk structure
Consistency

Measures how stable the generated chunks are across the document.

Factors include:

Chunk size variation
Structural uniformity
Distribution consistency
Efficiency

Measures the computational characteristics of each strategy.

Factors include:

Processing time
Number of chunks generated
Chunking overhead
Retrieval Quality

Measures how effectively chunks support semantic retrieval.

Factors include:

Retrieval relevance
Similarity scores
Query-to-chunk matching performance
Ranking quality
Benchmarking System

RAGarator generates or processes benchmark queries to evaluate retrieval performance.

For each chunking strategy:

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

This allows chunking strategies to be compared based on retrieval behavior rather than chunk structure alone.

Decision Engine

The Decision Engine is the core intelligence layer of RAGarator V1.

Instead of selecting a strategy based on a single metric, the system combines multiple evaluation signals.

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

The decision engine produces:

Recommended strategy
Ranked alternatives
Overall scores
Individual metric scores
Confidence level
Reasoning behind the recommendation
Document-specific explanation
Explainability

Explainability is an important component of RAGarator.

A recommendation should not behave like a black box.

The system is designed to provide explanations related to:

The characteristics of the uploaded document
The performance of each chunking strategy
Relevant evaluation metrics
Differences between the recommended and alternative strategies

The objective is to provide meaningful reasoning instead of generic statements.

Example:

Recursive chunking was recommended because the document contains long structured sections with varying paragraph lengths. The strategy achieved stronger retrieval performance while preserving more contextual continuity than fixed-size chunking.

Backend Architecture
backend/
│
├── app/
│   │
│   ├── api/
│   │   ├── analyze.py          # Document analysis endpoint
│   │   ├── health.py           # Health check endpoint
│   │   └── upload.py           # File upload endpoint
│   │
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   │
│   ├── services/
│   │
│   │   ├── ingestion/
│   │   │   ├── loaders.py      # PDF/DOCX/TXT loading
│   │   │   ├── cleaner.py      # Text cleaning
│   │   │   └── metadata.py     # Document metadata extraction
│   │
│   │   ├── chunkers/
│   │   │   ├── base.py         # Base chunker interface
│   │   │   ├── fixed.py        # Fixed-size chunking
│   │   │   ├── recursive.py    # Recursive chunking
│   │   │   ├── sentence.py     # Sentence chunking
│   │   │   ├── token.py        # Token-based chunking
│   │   │   └── manager.py      # Chunking strategy orchestration
│   │
│   │   ├── embeddings/
│   │   │   └── embedder.py     # Embedding generation
│   │   │
│   │   ├── retrieval/
│   │   │   ├── retriever.py    # Semantic retrieval
│   │   │   └── evaluator.py    # Retrieval evaluation
│   │   │
│   │   ├── evaluation/
│   │   │   ├── chunk_quality.py
│   │   │   ├── consistency.py
│   │   │   ├── efficiency.py
│   │   │   ├── quality.py
│   │   │   └── retrieval_quality.py
│   │
│   │   ├── benchmark/
│   │   │   ├── evaluator.py
│   │   │   ├── metrics.py
│   │   │   └── queries.py
│   │
│   │   ├── decision/
│   │   │   ├── scoring.py
│   │   │   ├── confidence.py
│   │   │   ├── explanation.py
│   │   │   ├── recommendation.py
│   │   │   └── dashboard.py
│   │
│   │   ├── jobs/
│   │   │   ├── runner.py
│   │   │   └── store.py
│   │
│   │   └── pipeline/
│   │       └── analyzer.py     # Complete analysis pipeline
│   │
│   ├── config.py               # Application configuration
│   └── main.py                 # FastAPI application entry point
│
├── tests/                      # Backend tests
├── uploads/                    # Uploaded documents
├── requirements.txt
└── pytest.ini
Frontend

The frontend provides an interface for users to:

Upload a document
Submit it for analysis
View the recommended chunking strategy
Compare strategy scores
Understand confidence levels
View explanations and evaluation results
Frontend Stack
React
Vite
Tailwind CSS
API Endpoints
Health Check
GET /health

Checks whether the backend service is running.

Upload Document
POST /upload

Uploads a supported document for analysis.

Supported formats:

.pdf
.docx
.txt
Analyze Document
POST /analyze

Runs the complete RAGarator analysis pipeline.

The pipeline performs:

Document loading
Text cleaning
Metadata extraction
Multiple chunking strategies
Embedding generation
Chunk quality evaluation
Retrieval benchmarking
Strategy scoring
Confidence estimation
Recommendation generation
Explainable result generation
Tech Stack
Backend
Python
FastAPI
Pydantic
Uvicorn
Machine Learning and NLP
Sentence Transformers
PyTorch
NumPy
Scikit-learn
Document Processing
PyMuPDF
python-docx
Chunking
LangChain Text Splitters
Frontend
React
Vite
Tailwind CSS
Running Locally
Clone the Repository
git clone https://github.com/geetika-rupani/RAGarator.git
cd RAGarator
Backend Setup

Navigate to the backend directory:

cd backend

Create a virtual environment:

python3.11 -m venv .venv

Activate it:

macOS/Linux
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Start the FastAPI server:

uvicorn app.main:app --reload

Backend:

http://localhost:8000

Swagger API documentation:

http://localhost:8000/docs
Frontend Setup

Open another terminal and navigate to:

cd frontend

Install dependencies:

npm install

Start the development server:

npm run dev

The frontend will run at:

http://localhost:5173
Testing

Run backend tests from the backend directory:

pytest
RAGarator V1 Limitations

RAGarator V1 focuses primarily on building and validating the core chunking decision engine.

Version 1 is not intended to be the final architecture of the platform.

Current limitations may include:

Limited number of chunking strategies
Local embedding generation
Limited benchmark datasets
No persistent vector database integration
Limited asynchronous processing
Initial metric weighting and scoring logic
Single-document focused analysis

These limitations provide opportunities for future versions of the project.

Future Versions

RAGarator is designed to evolve beyond Version 1.

RAGarator V2 — Advanced Intelligence and Optimization

Potential improvements:

Dynamic chunk size optimization
Automatic overlap optimization
Additional chunking strategies
Advanced semantic evaluation
Improved benchmark query generation
More sophisticated confidence estimation
Multi-document analysis
Improved visualization and comparison dashboards
RAGarator V3 — Production RAG Integration

Potential improvements:

Vector database integration
FAISS integration
Pinecone or Weaviate support
End-to-end RAG pipeline testing
LLM-based retrieval evaluation
Automated RAG performance benchmarking
Real-world question-answering evaluation
RAGarator V4 — Intelligent Adaptive Chunking

Potential research directions:

Hybrid chunking strategies
Adaptive chunking based on document sections
Machine learning-based chunking strategy prediction
Reinforcement learning for chunk optimization
LLM-guided semantic chunking
Automatic chunk boundary detection
Domain-aware chunking strategies

The long-term objective is to move from:

"Which existing chunking strategy should I use?"

towards:

"How should this specific document be optimally chunked?"
Long-Term Vision

The long-term vision of RAGarator is to become an intelligent chunking optimization layer for RAG systems.

Rather than treating chunking as a static preprocessing step, RAGarator aims to make it:

Adaptive
Data-driven
Explainable
Document-aware
Performance-oriented

The platform could eventually analyze a document and automatically determine:

Optimal chunking strategy
Optimal chunk size
Optimal overlap
Section-specific chunking behavior
Retrieval configuration

This would allow chunking to become an optimized and measurable component of RAG system design.

Project Status
Current Version: RAGarator V1
Status: Active Development
Core Decision Engine: Implemented
Backend: FastAPI
Frontend: React
Deployment: In Progress

RAGarator V1 represents the first working implementation and foundation of the broader RAGarator platform.

Author

Geetika Rupani

B.Tech — Information Technology
Vellore Institute of Technology

GitHub: @geetika-rupani

License

This project is currently developed for educational, research, and portfolio purposes.
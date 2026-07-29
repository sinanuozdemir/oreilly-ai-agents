# RAG Validation Quickstart Guide

Get started with RAG evaluation in 5 minutes.

## Installation

```bash
cd rag-validation
pip install -r requirements.txt
```

## Set API Keys

```bash
export OPENAI_API_KEY="sk-your-key"
# Optional: export LANGCHAIN_API_KEY="ls-your-key"
```

## Run Basic Evaluation

```bash
python examples/basic_evaluation.py
```

## Run with RAGAS Framework

```bash
python examples/advanced_metrics.py
```

## Create Custom Benchmark

```bash
python examples/custom_benchmark.py
```

## Run via CLI

```bash
python -m src.evaluation --component end-to-end --output results/metrics.json
```

## GitHub Actions Setup

1. Add `OPENAI_API_KEY` to repository secrets
2. Push to trigger automatic evaluation
3. View results in PR comments

## Key Metrics Cheatsheet

| Metric | Target | Measures |
|--------|--------|----------|
| Context Precision | >0.70 | Retrieved doc relevance |
| Context Recall | >0.75 | Coverage of relevant docs |
| Faithfulness | >0.80 | Answer grounded in context |
| Answer Relevance | >0.75 | Answer matches question |
| RAGAS Score | >0.75 | Overall quality |

## Project Structure

```
rag-validation/
├── src/              # Core evaluation code
├── examples/         # Usage examples
├── tests/            # Unit tests
├── config/           # Configuration files
└── .github/workflows/# CI/CD automation
```

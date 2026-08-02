# 🚀 SDE Code Review & Impact Analysis Assistant

> **A practical RAG system for Software Engineers and SDETs**

## What We Build

A real-world RAG system that helps with:
- **Code Review**: "What tests should I add for this change?"
- **Impact Analysis**: "Which APIs are affected by this PR?"
- **Documentation Q&A**: "How does the auth flow work?"
- **Onboarding**: "Where is the payment processing code?"

## Real-World Use Cases

| Scenario | Problem | Solution |
|----------|---------|----------|
| PR Review | New dev doesn't know test patterns | RAG suggests test cases from similar changes |
| Refactoring | "Will this break anything?" | RAG shows affected APIs and components |
| API Changes | "What docs need updating?" | RAG finds related endpoints and specs |
| Onboarding | "How does auth work?" | RAG answers from codebase + docs |

## Architecture

```
Code Repository + API Docs + Test Files
           ↓
    [Chunk & Embed]
           ↓
    Vector Database (Chroma)
           ↓
    RAG Query: "Impact of PR #123"
           ↓
    Retrieved Context:
      - Similar past PRs
      - Affected API specs
      - Related test files
           ↓
    Generated Analysis:
      "This changes the auth middleware.
       Update tests in test_auth.py.
       Similar to PR #456"
```

## Project Structure

```
sde-rag-assistant/
├── step1_setup_vector_db.py       # Set up Chroma locally
├── step2_populate_data.py         # Load code, docs, tests
├── step3_build_rag_pipeline.py    # Create the RAG system
├── step4_code_review_agent.py     # Practical code review use case
├── step5_api_testing_assistant.py # API test generation
├── step6_impact_analyzer.py       # PR impact analysis
├── data/
│   ├── sample_repo/               # Mock codebase
│   ├── api_specs/                 # API documentation
│   └── test_cases/                # Test scenarios
├── vector_db/                     # Local Chroma storage
└── README.md
```

## Prerequisites

```bash
pip install chromadb langchain-openai python-dotenv
```

## Set API Key

```bash
export OPENAI_API_KEY="sk-your-key"
```

## Quick Start

```bash
cd sde-rag-assistant
python step1_setup_vector_db.py
python step2_populate_data.py
python step3_build_rag_pipeline.py
python step4_code_review_agent.py
```

## What You'll Learn

1. **Vector DB Setup**: Local Chroma for code embeddings
2. **Code Chunking**: Smart splitting for code files
3. **Multi-source RAG**: Code + docs + tests together
4. **Structured Output**: JSON responses for automation
5. **CI/CD Integration**: GitHub Actions for code review

## Interview Gold 💰

**Resume bullet:**
> "Built AI-powered code review assistant using RAG that analyzes PR impact, 
> suggests test cases, and retrieves relevant documentation. Reduced review 
> time by 30% and improved code quality consistency."

**Interview talking point:**
> "I built a system that embeddings our entire codebase. When a developer 
> submits a PR, it automatically retrieves similar past changes, identifies 
> affected APIs, and suggests what tests to add. It's like having a senior 
> engineer review every PR instantly."

---

Let's start with **Step 1**!

# RAG Validation: Step-by-Step Beginner's Guide

> **Start here if you're new to RAG evaluation!** We'll go one concept at a time with practical examples.

---

## Table of Contents

1. [Step 0: Understanding RAG (The Big Picture)](#step-0-understanding-rag)
2. [Step 1: Your First Retrieval Metric](#step-1-your-first-retrieval-metric)
3. [Step 2: Measuring Generation Quality](#step-2-measuring-generation-quality)
4. [Step 3: Putting It Together (End-to-End)](#step-3-putting-it-together)
5. [Step 4: Running Your First Evaluation](#step-4-running-your-first-evaluation)
6. [Step 5: Understanding Benchmarks](#step-5-understanding-benchmarks)
7. [Step 6: CI/CD Integration (GitHub Actions)](#step-6-cicd-integration)

---

## Step 0: Understanding RAG

### What is RAG?

**RAG = Retrieval-Augmented Generation**

Instead of asking an AI to answer from memory, RAG:
1. **Retrieves** relevant documents from a knowledge base
2. **Augments** the AI prompt with those documents
3. **Generates** an answer based on the retrieved context

```
User Query → [Retrieve Documents] → [Generate Answer] → Response
```

### Why Validate RAG?

| Problem | Real-World Impact |
|---------|-------------------|
| AI makes up facts | Customer gets wrong refund policy → Angry customer |
| Wrong documents retrieved | Doctor gets wrong treatment info → Patient harm |
| Answer ignores question | User asks "how to reset password" → Gets pricing info |

**Validation = Making sure your RAG system works correctly before deploying**

---

## Step 1: Your First Retrieval Metric

### What is Context Precision?

**Simple definition**: Of the documents you retrieved, how many were actually relevant?

### Real-World Analogy

Imagine a librarian helping you find books about "machine learning":

- **Retrieved 5 books**: 3 about ML, 1 about gardening, 1 about cooking
- **Precision = 3 relevant / 5 total = 60%**

Higher is better. 100% = all retrieved books were about ML.

### Hands-On Example

Create a file called `step1_precision.py`:

```python
"""Step 1: Understanding Context Precision"""

def context_precision(retrieved_docs, relevant_docs):
    """
    Calculate precision: relevant retrieved / total retrieved
    
    Args:
        retrieved_docs: List of documents the system found
        relevant_docs: List of documents that actually answer the question
    """
    if not retrieved_docs:
        return 0.0
    
    # Count matches (simplified exact match)
    retrieved_set = set(d.lower().strip() for d in retrieved_docs)
    relevant_set = set(d.lower().strip() for d in relevant_docs)
    
    matches = len(retrieved_set & relevant_set)
    precision = matches / len(retrieved_docs)
    
    return precision


# ========== EXAMPLE 1: Good Precision ==========
print("=" * 50)
print("EXAMPLE 1: Good Retrieval")
print("=" * 50)

retrieved = [
    "Python is a programming language",
    "Python was created by Guido van Rossum",
    "Python is used for machine learning",
]

relevant = [
    "Python is a programming language",
    "Python was created by Guido van Rossum",
    "Python is used for machine learning",
    "Python has simple syntax",
]

score = context_precision(retrieved, relevant)
print(f"Retrieved: {len(retrieved)} documents")
print(f"Relevant (in ground truth): {len(relevant)} documents")
print(f"Matches: All 3 retrieved are in relevant set")
print(f"Context Precision: {score:.2%}")
print("✅ GOOD: All retrieved documents are relevant")


# ========== EXAMPLE 2: Bad Precision ==========
print("\n" + "=" * 50)
print("EXAMPLE 2: Poor Retrieval")
print("=" * 50)

retrieved = [
    "Python is a programming language",  # ✓ relevant
    "Java is also a programming language",  # ✗ not about Python
    "Snakes are reptiles",  # ✗ wrong topic entirely!
]

relevant = [
    "Python is a programming language",
    "Python was created by Guido van Rossum",
]

score = context_precision(retrieved, relevant)
print(f"Retrieved: {len(retrieved)} documents")
print(f"Only 1 out of 3 is relevant to Python the language")
print(f"Context Precision: {score:.2%}")
print("❌ BAD: Retrieved documents about Java and snakes!")


# ========== EXERCISE ==========
print("\n" + "=" * 50)
print("YOUR TURN!")
print("=" * 50)

# Scenario: User asks "How do I reset my password?"
retrieved_docs = [
    "Click 'Forgot Password' on the login page",
    "Our pricing plans start at $10/month",  # Is this relevant?
    "Enter your email to receive reset instructions",
]

relevant_docs = [
    "Click 'Forgot Password' on the login page",
    "Enter your email to receive reset instructions",
    "Check your spam folder for the reset email",
]

score = context_precision(retrieved_docs, relevant_docs)
print(f"Question: How do I reset my password?")
print(f"Context Precision: {score:.2%}")
print(f"\nWhy? 2 out of 3 retrieved docs are relevant")
print(f"The pricing doc is noise that could confuse the AI")
```

**Run it:**
```bash
cd rag-validation
python step1_precision.py
```

### What You Learned

- **Precision** measures signal-to-noise ratio
- 100% = perfect retrieval
- Low precision = AI gets confused by irrelevant context

---

## Step 2: Measuring Generation Quality

### What is Faithfulness?

**Simple definition**: Does the AI's answer stick to the facts in the retrieved documents?

### Real-World Analogy

You're a student writing an essay using provided sources:

- **Faithful**: "According to Document A, the population is 1 million" (facts match source)
- **Unfaithful (Hallucination)**: "The population is 5 million" (made up, not in source)

### Hands-On Example

Create `step2_faithfulness.py`:

```python
"""Step 2: Understanding Faithfulness"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load a small embedding model (downloads ~80MB first time)
print("Loading model (first time may take a minute)...")
model = SentenceTransformer('all-MiniLM-L6-v2')


def faithfulness_score(answer, context_docs):
    """
    Measure how faithful the answer is to the context.
    Uses semantic similarity (simplified approach).
    """
    # Combine all context
    full_context = " ".join(context_docs)
    
    # Get embeddings
    answer_emb = model.encode([answer])
    context_emb = model.encode([full_context])
    
    # Calculate similarity (0 to 1)
    similarity = cosine_similarity(answer_emb, context_emb)[0][0]
    
    return float(similarity)


# ========== EXAMPLE 1: Faithful Answer ==========
print("\n" + "=" * 60)
print("EXAMPLE 1: Faithful Answer")
print("=" * 60)

context = [
    "Python was created by Guido van Rossum and first released in 1991.",
    "Python is known for its readable syntax and indentation.",
]

answer = "Python was created by Guido van Rossum in 1991."

score = faithfulness_score(answer, context)
print(f"Context: Python created by Guido van Rossum, released 1991")
print(f"Answer: {answer}")
print(f"Faithfulness Score: {score:.3f}")
print("✅ GOOD: Answer matches the context exactly")


# ========== EXAMPLE 2: Hallucination ==========
print("\n" + "=" * 60)
print("EXAMPLE 2: Hallucination (Unfaithful)")
print("=" * 60)

context = [
    "Python was created by Guido van Rossum and first released in 1991.",
]

answer = "Python was created by James Gosling in 1995 at Sun Microsystems."
# This is actually describing Java!

score = faithfulness_score(answer, context)
print(f"Context: Python created by Guido van Rossum, released 1991")
print(f"Answer: {answer}")
print(f"Faithfulness Score: {score:.3f}")
print("❌ BAD: Answer contradicts the context!")
print("   The creator and date are wrong.")


# ========== EXAMPLE 3: Partial Faithfulness ==========
print("\n" + "=" * 60)
print("EXAMPLE 3: Partial Faithfulness")
print("=" * 60)

context = [
    "Our refund policy allows returns within 30 days with receipt.",
    "Sale items cannot be returned.",
]

answer = "You can return items within 30 days, and sale items are refundable too."

score = faithfulness_score(answer, context)
print(f"Context: 30-day returns, NO sale item returns")
print(f"Answer: {answer}")
print(f"Faithfulness Score: {score:.3f}")
print("⚠️  WARNING: Part is true (30 days), part is false (sale items)")


# ========== PRACTICAL TIP ==========
print("\n" + "=" * 60)
print("WHY THIS MATTERS")
print("=" * 60)
print("""
High faithfulness means:
- Your AI isn't making things up
- Users can trust the answers
- Reduces legal liability

Low faithfulness means:
- AI is hallucinating
- Users get wrong information
- Potential harm (medical, legal, financial)

Target: Faithfulness > 0.80 (80% similarity to context)
""")
```

**Run it:**
```bash
pip install sentence-transformers scikit-learn  # if not installed
python step2_faithfulness.py
```

### What You Learned

- **Faithfulness** catches AI hallucinations
- Semantic similarity measures meaning, not just word matching
- Scores range 0-1 (higher = more faithful)

---

## Step 3: Putting It Together

### The Complete RAG Evaluation

Now let's combine retrieval and generation metrics:

Create `step3_complete.py`:

```python
"""Step 3: Complete RAG Evaluation"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')


def evaluate_rag(query, answer, retrieved_docs, relevant_docs):
    """
    Complete RAG evaluation with 4 key metrics.
    """
    results = {}
    
    # 1. Context Precision: Are retrieved docs relevant?
    retrieved_set = set(d.lower() for d in retrieved_docs)
    relevant_set = set(d.lower() for d in relevant_docs)
    matches = len(retrieved_set & relevant_set)
    results['context_precision'] = matches / len(retrieved_docs) if retrieved_docs else 0
    
    # 2. Context Recall: Did we find all relevant docs?
    results['context_recall'] = matches / len(relevant_docs) if relevant_docs else 1.0
    
    # 3. Faithfulness: Does answer match context?
    context_text = " ".join(retrieved_docs)
    ans_emb = model.encode([answer])
    ctx_emb = model.encode([context_text])
    results['faithfulness'] = float(cosine_similarity(ans_emb, ctx_emb)[0][0])
    
    # 4. Answer Relevance: Does answer match query?
    qry_emb = model.encode([query])
    results['answer_relevance'] = float(cosine_similarity(qry_emb, ans_emb)[0][0])
    
    # Overall score (average of above)
    results['ragas_score'] = (
        results['context_precision'] + 
        results['context_recall'] + 
        results['faithfulness'] + 
        results['answer_relevance']
    ) / 4
    
    return results


def print_report(query, results):
    """Pretty print the results."""
    print(f"\nQuery: {query}")
    print("-" * 50)
    
    for metric, score in results.items():
        bar_length = int(score * 30)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        print(f"{metric:20} {score:.3f} {bar}")


# ========== SCENARIO 1: Excellent RAG ==========
print("=" * 60)
print("SCENARIO 1: Excellent RAG System")
print("=" * 60)

query = "Who created Python?"
retrieved = [
    "Python was created by Guido van Rossum.",
    "It was first released in 1991.",
]
relevant = [
    "Python was created by Guido van Rossum.",
    "It was first released in 1991.",
]
answer = "Python was created by Guido van Rossum in 1991."

results = evaluate_rag(query, answer, retrieved, relevant)
print_report(query, results)
print("\n✅ Excellent! High scores across all metrics")


# ========== SCENARIO 2: Good Retrieval, Bad Answer ==========
print("\n" + "=" * 60)
print("SCENARIO 2: Good Retrieval, Hallucinated Answer")
print("=" * 60)

query = "Who created Python?"
retrieved = [
    "Python was created by Guido van Rossum.",  # ✓ Good retrieval
    "It was first released in 1991.",
]
relevant = [
    "Python was created by Guido van Rossum.",
    "It was first released in 1991.",
]
answer = "Python was created by Bill Gates at Microsoft."  # ✗ Wrong!

results = evaluate_rag(query, answer, retrieved, relevant)
print_report(query, results)
print("\n❌ Retrieval worked, but AI hallucinated the answer!")
print("   Faithfulness is low despite good retrieval")


# ========== SCENARIO 3: Bad Retrieval ==========
print("\n" + "=" * 60)
print("SCENARIO 3: Poor Retrieval")
print("=" * 60)

query = "Who created Python?"
retrieved = [
    "Java was created by James Gosling.",  # ✗ Wrong language!
    "JavaScript was created by Brendan Eich.",
]
relevant = [
    "Python was created by Guido van Rossum.",
]
answer = "Python was created by Guido van Rossum."

results = evaluate_rag(query, answer, retrieved, relevant)
print_report(query, results)
print("\n❌ Retrieved wrong documents (Java/JS not Python)")
print("   Even if answer is coincidentally correct,")
print("   the system can't be trusted!")


# ========== INTERPRETATION GUIDE ==========
print("\n" + "=" * 60)
print("HOW TO INTERPRET SCORES")
print("=" * 60)
print("""
RAGAS Score Interpretation:

0.90 - 1.00 🌟 Excellent - Production ready
0.80 - 0.89 ✅ Good - Minor improvements needed
0.70 - 0.79 ⚠️  Fair - Significant issues
0.00 - 0.69 ❌ Poor - Not ready for production

Fix Priority:
1. Context Recall < 0.70 → Improve retrieval (chunking, embeddings)
2. Faithfulness < 0.80 → Check context quality, prompt engineering
3. Answer Relevance < 0.70 → LLM may be ignoring the question
4. Context Precision < 0.70 → Too much noise in retrieval
""")
```

**Run it:**
```bash
python step3_complete.py
```

### What You Learned

- RAG evaluation has 4 key components
- Problems can be in retrieval OR generation
- RAGAS score gives overall health check

---

## Step 4: Running Your First Evaluation

### Using the RAG Validation Toolkit

Now let's use the toolkit we built:

```bash
cd rag-validation

# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key (for LLM-based evaluation)
export OPENAI_API_KEY="sk-your-key-here"
```

### Example: Evaluate a Simple RAG

Create `step4_first_eval.py`:

```python
"""Step 4: Your First Real Evaluation"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.rag_pipeline import RAGPipeline
from src.evaluation import RAGEvaluator, EvalSample

# Step 1: Create a RAG pipeline
print("Step 1: Building RAG pipeline...")

rag = RAGPipeline(chunk_size=256, top_k=3)

# Add some documents
documents = [
    "Machine learning is a subset of AI that learns from data.",
    "Deep learning uses neural networks with many layers.",
    "Python is popular for machine learning.",
    "TensorFlow and PyTorch are ML frameworks.",
    "Supervised learning uses labeled training data.",
]

rag.add_documents(documents)
print(f"✓ Loaded {len(documents)} documents")

# Step 2: Define test questions
print("\nStep 2: Creating test questions...")

test_samples = [
    EvalSample(
        query="What is machine learning?",
        ground_truth_answer="Machine learning is a subset of AI that learns from data.",
        ground_truth_context=[documents[0]],
    ),
    EvalSample(
        query="What is deep learning?",
        ground_truth_answer="Deep learning uses neural networks with many layers.",
        ground_truth_context=[documents[1]],
    ),
]

# Step 3: Run evaluation
print("\nStep 3: Running evaluation...")
print("-" * 50)

evaluator = RAGEvaluator(rag)
results = evaluator.run_evaluation(test_samples, verbose=True)

# Step 4: View results
print("\n" + "=" * 50)
print("RESULTS")
print("=" * 50)

aggregated = evaluator.aggregate_metrics(results)

for metric, stats in aggregated.items():
    if metric == "latency_ms":
        continue
    print(f"{metric:25} {stats['mean']:.3f}")

print("\n" + "=" * 50)
print("INTERPRETATION")
print("=" * 50)

ragas = aggregated['ragas_score']['mean']
if ragas > 0.8:
    print(f"🌟 Excellent! RAGAS Score: {ragas:.3f}")
elif ragas > 0.7:
    print(f"✅ Good! RAGAS Score: {ragas:.3f}")
elif ragas > 0.6:
    print(f"⚠️  Fair. RAGAS Score: {ragas:.3f} - Needs work")
else:
    print(f"❌ Poor. RAGAS Score: {ragas:.3f} - Major issues")

print(f"\nLatency: {aggregated['latency_ms']['mean']:.0f}ms average")
```

**Run it:**
```bash
cd rag-validation
python step4_first_eval.py
```

### What You Learned

- How to structure a real evaluation
- The toolkit handles the complexity
- You get actionable metrics immediately

---

## Step 5: Understanding Benchmarks

### What is a Benchmark?

A **benchmark** = A standardized set of questions with known correct answers.

Think of it like a test for your RAG system.

### Why Use Benchmarks?

| Without Benchmark | With Benchmark |
|-------------------|----------------|
| "Seems to work" | "94% accuracy on test set" |
| Can't compare | Compare different RAG configs |
| Don't know if it broke | Detect regressions |

### Types of Benchmarks

```
┌─────────────────────────────────────────────────────┐
│              BENCHMARK TYPES                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  🌍 General Purpose        🏭 Domain-Specific       │
│  • Natural Questions       • PubMedQA (medical)     │
│  • MS MARCO (search)       • FinQA (finance)        │
│  • HotpotQA (reasoning)    • TechQA (support)       │
│                                                     │
│  📝 Custom                                      │
│  • Your own questions      ✅ Best for production   │
│  • Real user queries       ✅ Match your use case   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Creating a Simple Benchmark

Create `step5_benchmark.py`:

```python
"""Step 5: Creating Your First Benchmark"""

import json

# A benchmark is just a list of test cases
my_benchmark = [
    {
        "id": "test-001",
        "category": "pricing",
        "question": "How much does the basic plan cost?",
        "ground_truth_answer": "The basic plan costs $10 per month.",
        "required_facts": ["basic plan price is $10/month"],
        "difficulty": "easy"
    },
    {
        "id": "test-002", 
        "category": "features",
        "question": "What's included in the enterprise plan?",
        "ground_truth_answer": "Enterprise includes SSO, audit logs, and priority support.",
        "required_facts": ["SSO", "audit logs", "priority support"],
        "difficulty": "medium"
    },
    {
        "id": "test-003",
        "category": "support",
        "question": "How do I contact support?",
        "ground_truth_answer": "Email support@example.com or use the chat widget.",
        "required_facts": ["email support", "chat widget"],
        "difficulty": "easy"
    },
]

# Save it
with open('my_first_benchmark.json', 'w') as f:
    json.dump(my_benchmark, f, indent=2)

print("✅ Created my_first_benchmark.json")
print(f"   Contains {len(my_benchmark)} test cases")

# Load and use it
with open('my_first_benchmark.json') as f:
    loaded = json.load(f)

print("\nBenchmark Contents:")
for test in loaded:
    print(f"\n  [{test['id']}] {test['category']} ({test['difficulty']})")
    print(f"   Q: {test['question']}")
    print(f"   A: {test['ground_truth_answer']}")


print("\n" + "=" * 60)
print("BENCHMARK BEST PRACTICES")
print("=" * 60)
print("""
1. START SMALL
   - 10-20 questions covering key scenarios
   - Add more over time

2. USE REAL QUESTIONS
   - Check your support tickets
   - Use actual user queries from logs

3. COVER EDGE CASES
   - Easy questions
   - Hard questions
   - Questions that previously failed

4. UPDATE REGULARLY
   - Add new questions as features change
   - Remove outdated questions

5. CATEGORIZE
   - Group by topic (pricing, features, etc.)
   - Group by difficulty
   - Track performance per category
""")
```

**Run it:**
```bash
python step5_benchmark.py
```

### What You Learned

- Benchmarks = standardized tests for your RAG
- Start small with real user questions
- Categorize by topic and difficulty

---

## Step 6: CI/CD Integration

### Why Automate Evaluation?

**Manual evaluation:**
- Run once, forget about it
- "Works on my machine"
- No visibility into degradation

**Automated CI/CD evaluation:**
- Run on every code change
- Catch regressions immediately
- Track metrics over time

### The GitHub Actions Workflow

The file `.github/workflows/rag-evaluation.yml` is already set up. Here's what it does:

```yaml
# Simplified view of what happens:

1. TRIGGER: Push code or pull request
        ↓
2. SETUP: Install Python, dependencies
        ↓
3. EVALUATE: Run retrieval + generation tests
        ↓
4. COMPARE: Check against baseline scores
        ↓
5. REPORT: Post results to PR comment
        ↓
6. DECIDE: Pass (✅) or Fail (❌) build
```

### Setting It Up (Step by Step)

**Step 6.1: Add Secrets**

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add `OPENAI_API_KEY` with your API key

**Step 6.2: The Workflow Triggers On:**

- Every Pull Request (that changes RAG code)
- Every night at 2 AM (scheduled regression test)
- Manual button click (workflow_dispatch)

**Step 6.3: What Gets Checked:**

```python
# Thresholds from the config
THRESHOLDS = {
    "context_recall": 0.75,      # Must retrieve relevant docs
    "context_precision": 0.70,   # Don't retrieve noise
    "faithfulness": 0.80,        # Don't hallucinate
    "answer_relevance": 0.75,    # Answer the question
    "ragas_score": 0.75,         # Overall quality
}
```

**If any metric falls below threshold → Build fails ❌**

### Example PR Comment

When you open a PR, the bot posts:

```
## 🔬 RAG Evaluation Results

| Metric | Current | Baseline | Change | Status |
|--------|---------|----------|--------|--------|
| ragas_score | 0.82 | 0.80 | +0.02 (+2.5%) | ✅ |
| context_precision | 0.78 | 0.75 | +0.03 (+4.0%) | ✅ |
| context_recall | 0.85 | 0.82 | +0.03 (+3.7%) | ✅ |

✅ All metrics above thresholds. Build passing!
```

### Running Locally (Before Pushing)

```bash
# Run the same checks locally
cd rag-validation

# Quick test
python -m src.evaluation --test-size 10

# Full test
python -m src.evaluation --test-size 100

# Check against thresholds
python -c "
import json
with open('results/metrics.json') as f:
    m = json.load(f)
    print('RAGAS:', m['ragas_score']['mean'])
    if m['ragas_score']['mean'] < 0.75:
        print('❌ Would fail CI')
    else:
        print('✅ Would pass CI')
"
```

### What You Learned

- CI/CD automates evaluation on every change
- Prevents bad changes from reaching production
- GitHub Actions posts results directly to PRs

---

## Summary: Your Learning Path

```
┌──────────────────────────────────────────────────────┐
│  STEP 0: Understand RAG                              │
│  → Retrieval + Generation                            │
├──────────────────────────────────────────────────────┤
│  STEP 1: Context Precision                           │
│  → Are retrieved docs relevant?                      │
│  → Run: step1_precision.py                           │
├──────────────────────────────────────────────────────┤
│  STEP 2: Faithfulness                                │
│  → Does answer match context?                        │
│  → Run: step2_faithfulness.py                        │
├──────────────────────────────────────────────────────┤
│  STEP 3: Complete Evaluation                         │
│  → Combine all 4 metrics                             │
│  → Run: step3_complete.py                            │
├──────────────────────────────────────────────────────┤
│  STEP 4: Use the Toolkit                             │
│  → Real RAG evaluation                               │
│  → Run: step4_first_eval.py                          │
├──────────────────────────────────────────────────────┤
│  STEP 5: Create Benchmarks                           │
│  → Build your test suite                             │
│  → Run: step5_benchmark.py                           │
├──────────────────────────────────────────────────────┤
│  STEP 6: CI/CD Integration                           │
│  → Automate with GitHub Actions                      │
│  → Add OPENAI_API_KEY secret                         │
└──────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Run all the step files** above to build intuition
2. **Modify the examples** with your own documents
3. **Create a benchmark** for your use case
4. **Set up the GitHub Action** for your repo
5. **Read the full README.md** for advanced topics

---

## Quick Reference

| Metric | What It Measures | Good Score | Fix If Low |
|--------|------------------|------------|------------|
| Context Precision | Signal-to-noise in retrieval | >0.70 | Adjust chunk size, better embeddings |
| Context Recall | Coverage of relevant docs | >0.75 | Increase top_k, query expansion |
| Faithfulness | Answer grounded in context | >0.80 | Better context, prompt engineering |
| Answer Relevance | Answer matches question | >0.75 | Check LLM temperature, prompt |
| RAGAS Score | Overall quality | >0.75 | Review all components |

---

*Questions? Check the main README.md or the examples/ directory!*

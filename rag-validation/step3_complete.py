"""Step 3: Complete RAG Evaluation

WHAT YOU'LL LEARN
-----------------
By the end of this file, you'll understand:
1. The 4 key metrics that make up RAG evaluation
2. How to combine them into an overall score
3. How to diagnose problems in your RAG system

THE 4 KEY METRICS
-----------------
┌─────────────────────────────────────────────────────────────┐
│  RETRIEVAL METRICS                                          │
│  • Context Precision - Signal-to-noise ratio               │
│  • Context Recall - Coverage of relevant docs              │
├─────────────────────────────────────────────────────────────┤
│  GENERATION METRICS                                         │
│  • Faithfulness - Answer matches context                   │
│  • Answer Relevance - Answer matches question              │
└─────────────────────────────────────────────────────────────┘

RAGAS SCORE = Average of all 4 metrics
"""

print("Ready!\n")


def simple_similarity(text1, text2):
    """Simple word overlap similarity (0 to 1)."""
    words1 = set(w.strip(".,!?;:") for w in text1.lower().split() if len(w) > 3)
    words2 = set(w.strip(".,!?;:") for w in text2.lower().split() if len(w) > 3)
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0


def evaluate_rag(query, answer, retrieved_docs, relevant_docs):
    """
    Complete RAG evaluation with all 4 key metrics.
    
    Args:
        query: The user's question
        answer: The AI's generated answer
        retrieved_docs: Documents the system retrieved
        relevant_docs: Ground truth relevant documents
        
    Returns:
        Dictionary with all metrics
    """
    results = {}
    
    # METRIC 1: Context Precision
    # Are the retrieved documents relevant?
    retrieved_set = set(d.lower() for d in retrieved_docs)
    relevant_set = set(d.lower() for d in relevant_docs)
    matches = len(retrieved_set & relevant_set)
    results['context_precision'] = matches / len(retrieved_docs) if retrieved_docs else 0
    
    # METRIC 2: Context Recall  
    # Did we find all the relevant documents?
    results['context_recall'] = matches / len(relevant_docs) if relevant_docs else 1.0
    
    # METRIC 3: Faithfulness
    # Does the answer match the retrieved context?
    context_text = " ".join(retrieved_docs)
    results['faithfulness'] = simple_similarity(answer, context_text)
    
    # METRIC 4: Answer Relevance
    # Does the answer actually address the question?
    results['answer_relevance'] = simple_similarity(query, answer)
    
    # OVERALL RAGAS SCORE
    # Average of the 4 key metrics
    results['ragas_score'] = (
        results['context_precision'] + 
        results['context_recall'] + 
        results['faithfulness'] + 
        results['answer_relevance']
    ) / 4
    
    return results


def print_report(scenario_name, query, results, explanation):
    """Print a nice report card for the evaluation."""
    print("=" * 65)
    print(f"📊 {scenario_name}")
    print("=" * 65)
    print(f"Query: {query}")
    print("-" * 65)
    
    # Print each metric with a visual bar
    for metric, score in results.items():
        bar_length = int(score * 30)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        emoji = "✅" if score > 0.8 else "⚠️ " if score > 0.6 else "❌"
        print(f"{emoji} {metric:20} {score:.3f} {bar}")
    
    print("-" * 65)
    print(f"EXPLANATION:\n{explanation}")
    print()


# ========== SCENARIO 1: Perfect RAG System ==========
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

print_report(
    "SCENARIO 1: Perfect RAG System",
    query,
    results,
    """This is an ideal RAG system:
    • Perfect retrieval (found all relevant docs, no noise)
    • Faithful answer (only used facts from context)
    • Relevant answer (directly addresses the question)
    
    RAGAS Score > 0.90 = Production Ready! 🌟"""
)


# ========== SCENARIO 2: Good Retrieval, Bad Generation ==========
query = "Who created Python?"

retrieved = [
    "Python was created by Guido van Rossum.",  # ✓ Good retrieval
    "It was first released in 1991.",
]

relevant = [
    "Python was created by Guido van Rossum.",
    "It was first released in 1991.",
]

answer = "Python was created by Bill Gates at Microsoft in 1995."  # ✗ Hallucination!

results = evaluate_rag(query, answer, retrieved, relevant)

print_report(
    "SCENARIO 2: Good Retrieval, Bad Generation",
    query,
    results,
    """The retrieval worked perfectly (Precision=1.0, Recall=1.0)
    BUT the AI hallucinated the answer (Faithfulness=0.476)
    
    DIAGNOSIS: Problem is in the GENERATION component
    FIXES:
    • Check LLM temperature (should be 0 for factual tasks)
    • Improve prompt with "Only use the provided context"
    • Add verification step to check answer against context"""
)


# ========== SCENARIO 3: Bad Retrieval, Good Answer (Lucky!) ==========
query = "Who created Python?"

retrieved = [
    "Java was created by James Gosling.",   # ✗ Wrong language!
    "C++ was created by Bjarne Stroustrup.", # ✗ Wrong language!
]

relevant = [
    "Python was created by Guido van Rossum.",
]

answer = "Python was created by Guido van Rossum."  # Correct, but lucky!

results = evaluate_rag(query, answer, retrieved, relevant)

print_report(
    "SCENARIO 3: Bad Retrieval (But Lucky Answer)",
    query,
    results,
    """The AI gave the correct answer, but it's LUCKY - not reliable!
    Context Precision = 0.0 (retrieved docs were about Java/C++, not Python)
    Context Recall = 0.0 (didn't retrieve the Python doc)
    
    DIAGNOSIS: Problem is in the RETRIEVAL component
    FIXES:
    • Improve embedding model (better semantic matching)
    • Adjust chunk size and overlap
    • Check vector database is populated correctly
    • Consider query expansion or HyDE"""
)


# ========== SCENARIO 4: Partial Retrieval ==========
query = "What are the benefits of Python?"

retrieved = [
    "Python has simple syntax.",  # ✓ Found 1 out of 3
]

relevant = [
    "Python has simple syntax.",
    "Python has a large community.",
    "Python has many libraries for AI.",
]

answer = "Python has simple syntax and is easy to learn."

results = evaluate_rag(query, answer, retrieved, relevant)

print_report(
    "SCENARIO 4: Partial Retrieval",
    query,
    results,
    """Only found 1 out of 3 relevant documents
    Context Recall = 0.333 (missing 2/3 of relevant info)
    
    DIAGNOSIS: Retrieval is incomplete
    FIXES:
    • Increase top_k (retrieve more documents)
    • Check if relevant docs are actually in the database
    • Improve embeddings to better match query to docs
    • Use query expansion to find related content"""
)


# ========== SCENARIO 5: Answer Doesn't Match Question ==========
query = "What is Python?"

retrieved = [
    "Python is a programming language.",
    "Python was created in 1991.",
]

relevant = [
    "Python is a programming language.",
    "Python was created in 1991.",
]

answer = "The weather today is sunny with a high of 75 degrees."  # Complete mismatch!

results = evaluate_rag(query, answer, retrieved, relevant)

print_report(
    "SCENARIO 5: Answer Doesn't Match Question",
    query,
    results,
    """Retrieval is perfect, but the answer is about weather!
    Answer Relevance = 0.086 (almost no similarity to question)
    
    DIAGNOSIS: LLM is ignoring the question
    FIXES:
    • Check system prompt is being applied correctly
    • Verify LLM is receiving the query (not a placeholder)
    • Check for prompt injection or formatting issues
    • This might be a serious bug in the pipeline!"""
)


# ========== DIAGNOSTIC GUIDE ==========
print("=" * 65)
print("🔧 DIAGNOSTIC GUIDE: How to Fix Your RAG System")
print("=" * 65)
print("""
STEP 1: Check RAGAS Score
┌──────────────────────────────────────────────────────────────┐
│ 0.90 - 1.00 🌟 Excellent    → Production ready!             │
│ 0.80 - 0.89 ✅ Good         → Minor tuning needed           │
│ 0.70 - 0.79 ⚠️  Fair        → Significant issues            │
│ 0.00 - 0.69 ❌ Poor         → Major problems                │
└──────────────────────────────────────────────────────────────┘

STEP 2: Identify Which Metric is Low

IF Context Precision < 0.70:
  → You're retrieving noise along with signal
  → FIX: Better embeddings, chunking strategy, or reranking

IF Context Recall < 0.75:
  → You're missing relevant documents
  → FIX: Increase top_k, better query expansion

IF Faithfulness < 0.80:
  → AI is hallucinating or ignoring context
  → FIX: Prompt engineering, temperature=0, verification

IF Answer Relevance < 0.75:
  → AI isn't answering the question asked
  → FIX: Check prompt template, verify query passthrough

STEP 3: Prioritize Fixes
  1. Fix retrieval first (Precision & Recall)
  2. Then fix generation (Faithfulness)
  3. Finally tune relevance
""")


# ========== SUMMARY TABLE ==========
print("=" * 65)
print("📋 QUICK REFERENCE TABLE")
print("=" * 65)
print("""
┌──────────────────────┬─────────┬─────────────────────────────┐
│ Metric               │ Target  │ When to Worry               │
├──────────────────────┼─────────┼─────────────────────────────┤
│ Context Precision    │ > 0.70  │ < 0.60 (too much noise)     │
│ Context Recall       │ > 0.75  │ < 0.60 (missing docs)       │
│ Faithfulness         │ > 0.80  │ < 0.70 (hallucinations)     │
│ Answer Relevance     │ > 0.75  │ < 0.60 (off-topic answers)  │
│ RAGAS Score          │ > 0.75  │ < 0.60 (not production)     │
└──────────────────────┴─────────┴─────────────────────────────┘
""")


print("\n✅ Step 3 Complete! You now understand complete RAG evaluation.")
print("   Next: Run 'step4_first_eval.py' to evaluate a real RAG system.")

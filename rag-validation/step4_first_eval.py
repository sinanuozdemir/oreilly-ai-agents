"""Step 4: Your First Real RAG Evaluation

WHAT YOU'LL DO
--------------
1. Build a real RAG pipeline with LangChain
2. Load documents into a vector database
3. Create test questions with known answers
4. Run automated evaluation
5. Interpret the results

WHERE THIS IS APPLIED
---------------------
This is the exact process used in production:
- Customer support chatbots
- Internal knowledge base search
- Documentation Q&A systems
- Legal/medical research assistants
"""

import sys
from pathlib import Path

# Add the parent directory to Python path so we can import our toolkit
sys.path.insert(0, str(Path(__file__).parent))

from src.rag_pipeline import RAGPipeline
from src.evaluation import RAGEvaluator, EvalSample


print("=" * 65)
print("STEP 4: Your First Real RAG Evaluation")
print("=" * 65)

# ============================================================================
# STEP 1: Create a RAG Pipeline
# ============================================================================
print("\n📚 STEP 1: Building RAG Pipeline")
print("-" * 65)

# Create the RAG system
rag = RAGPipeline(
    chunk_size=256,      # Split docs into 256-character chunks
    top_k=3,             # Retrieve top 3 most relevant chunks
    temperature=0.0,     # Deterministic (no randomness)
)

# Documents about programming languages (our "knowledge base")
documents = [
    # Python docs
    "Python is a high-level programming language created by Guido van Rossum in 1991. "
    "It is known for its readable syntax and indentation-based structure. "
    "Python is widely used for web development, data science, and artificial intelligence.",
    
    # JavaScript docs
    "JavaScript is a programming language that enables interactive web pages. "
    "It was created by Brendan Eich in 1995 while working at Netscape. "
    "JavaScript is an essential part of web development alongside HTML and CSS.",
    
    # Machine Learning docs
    "Machine learning is a subset of artificial intelligence that enables computers "
    "to learn from data without being explicitly programmed. It is used for "
    "predictions, classification, and pattern recognition.",
    
    # Deep Learning docs
    "Deep learning is a type of machine learning based on artificial neural networks. "
    "It uses multiple layers to progressively extract higher-level features from raw input. "
    "Deep learning powers technologies like image recognition and natural language processing.",
    
    # TypeScript docs
    "TypeScript is a superset of JavaScript that adds static typing. "
    "It was developed by Microsoft and first released in 2012. "
    "TypeScript compiles to plain JavaScript and can run in any browser.",
]

print(f"Loading {len(documents)} documents...")
rag.add_documents(documents)
print("✓ Documents loaded into vector database")


# ============================================================================
# STEP 2: Create Test Questions
# ============================================================================
print("\n🧪 STEP 2: Creating Test Questions")
print("-" * 65)

# These are our "ground truth" questions with known correct answers
# In production, you'd get these from:
# - Real user questions from logs
# - Manually curated test cases
# - Synthetic generation from documents

test_samples = [
    EvalSample(
        query="Who created Python?",
        ground_truth_answer="Python was created by Guido van Rossum.",
        ground_truth_context=[documents[0]],  # First doc contains the answer
        category="creator",
        difficulty="easy",
    ),
    
    EvalSample(
        query="When was JavaScript created?",
        ground_truth_answer="JavaScript was created by Brendan Eich in 1995.",
        ground_truth_context=[documents[1]],
        category="history",
        difficulty="easy",
    ),
    
    EvalSample(
        query="What is machine learning?",
        ground_truth_answer="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
        ground_truth_context=[documents[2]],
        category="definitions",
        difficulty="easy",
    ),
    
    EvalSample(
        query="What is the difference between deep learning and machine learning?",
        ground_truth_answer="Deep learning is a type of machine learning based on neural networks with multiple layers.",
        ground_truth_context=[documents[2], documents[3]],  # Requires both docs
        category="comparison",
        difficulty="medium",
    ),
    
    EvalSample(
        query="What is TypeScript?",
        ground_truth_answer="TypeScript is a superset of JavaScript that adds static typing.",
        ground_truth_context=[documents[4]],
        category="definitions",
        difficulty="easy",
    ),
]

print(f"Created {len(test_samples)} test samples:")
for i, sample in enumerate(test_samples, 1):
    print(f"  {i}. [{sample.difficulty}] {sample.query}")


# ============================================================================
# STEP 3: Run Evaluation
# ============================================================================
print("\n🔍 STEP 3: Running Evaluation")
print("-" * 65)
print("For each question, we will:")
print("  1. Query the RAG system")
print("  2. Compare retrieved docs to ground truth")
print("  3. Compare generated answer to ground truth")
print("  4. Calculate metrics")
print()

evaluator = RAGEvaluator(rag)
results = evaluator.run_evaluation(test_samples, verbose=True)


# ============================================================================
# STEP 4: Analyze Results
# ============================================================================
print("\n📊 STEP 4: Results Analysis")
print("=" * 65)

aggregated = evaluator.aggregate_metrics(results)

print("\n📈 Overall Metrics:")
print(f"  {'Metric':<25} {'Mean':>8} {'Min':>8} {'Max':>8}")
print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*8}")

for metric_name, stats in aggregated.items():
    if metric_name == "latency_ms":
        continue
    print(f"  {metric_name:<25} {stats['mean']:>8.3f} {stats['min']:>8.3f} {stats['max']:>8.3f}")

print("\n⚡ Performance:")
latency = aggregated["latency_ms"]
print(f"  Mean Latency: {latency['mean']:.1f}ms")
print(f"  P50 Latency:  {latency['p50']:.1f}ms")
print(f"  P95 Latency:  {latency['p95']:.1f}ms")


# ============================================================================
# STEP 5: Interpretation
# ============================================================================
print("\n🎯 STEP 5: Interpretation")
print("=" * 65)

ragas_score = aggregated['ragas_score']['mean']

if ragas_score >= 0.8:
    rating = "🌟 EXCELLENT"
    recommendation = "Production ready!"
elif ragas_score >= 0.7:
    rating = "✅ GOOD"
    recommendation = "Minor improvements possible"
elif ragas_score >= 0.6:
    rating = "⚠️ FAIR"
    recommendation = "Needs significant work"
else:
    rating = "❌ POOR"
    recommendation = "Major issues - not ready"

print(f"\nOverall RAGAS Score: {ragas_score:.3f} - {rating}")
print(f"Recommendation: {recommendation}")

print("\n📋 Detailed Analysis:")

# Check each metric
if aggregated['context_precision']['mean'] < 0.7:
    print("  ⚠️  Context Precision is low")
    print("     → Retrieved documents contain noise")
    print("     → Try: Better embeddings, reranking")
else:
    print("  ✅ Context Precision is good")

if aggregated['context_recall']['mean'] < 0.75:
    print("  ⚠️  Context Recall is low")
    print("     → Missing relevant documents")
    print("     → Try: Increase top_k, better chunking")
else:
    print("  ✅ Context Recall is good")

if aggregated['faithfulness']['mean'] < 0.8:
    print("  ⚠️  Faithfulness is low")
    print("     → AI may be hallucinating")
    print("     → Try: temperature=0, prompt engineering")
else:
    print("  ✅ Faithfulness is good")

if aggregated['answer_relevance']['mean'] < 0.75:
    print("  ⚠️  Answer Relevance is low")
    print("     → Answers don't match questions")
    print("     → Check prompt template")
else:
    print("  ✅ Answer Relevance is good")

if latency['p95'] > 5000:
    print(f"  ⚠️  Latency is high (P95: {latency['p95']:.0f}ms)")
    print("     → May impact user experience")
else:
    print(f"  ✅ Latency is acceptable (P95: {latency['p95']:.0f}ms)")


# ============================================================================
# STEP 6: Per-Question Breakdown
# ============================================================================
print("\n🔬 STEP 6: Per-Question Breakdown")
print("=" * 65)

for i, result in enumerate(results, 1):
    print(f"\nQ{i}: {result.sample.query}")
    print(f"   RAGAS: {result.metrics['ragas_score'].score:.3f} | "
          f"Precision: {result.metrics['context_precision'].score:.2f} | "
          f"Recall: {result.metrics['context_recall'].score:.2f} | "
          f"Faith: {result.metrics['faithfulness'].score:.2f}")
    print(f"   Answer: {result.generated_answer[:80]}...")
    
    # Flag issues
    issues = []
    if result.metrics['context_recall'].score < 0.5:
        issues.append("missing docs")
    if result.metrics['faithfulness'].score < 0.7:
        issues.append("hallucination")
    if result.metrics['answer_relevance'].score < 0.7:
        issues.append("off-topic")
    
    if issues:
        print(f"   ⚠️  Issues: {', '.join(issues)}")


# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)
print(f"""
You just ran your first real RAG evaluation!

WHAT WE DID:
  ✓ Built a RAG pipeline with {len(documents)} documents
  ✓ Created {len(test_samples)} test questions
  ✓ Measured 4 key metrics + overall RAGAS score
  ✓ Identified strengths and weaknesses

NEXT STEPS:
  1. Review the detailed metrics above
  2. Look at individual question results
  3. Identify which component needs work (retrieval or generation)
  4. Make improvements
  5. Re-run evaluation to measure improvement

TRY THIS:
  • Add more documents to the knowledge base
  • Change chunk_size (try 128, 512, 1024)
  • Change top_k (try 2, 5, 10)
  • Add more difficult questions
  • See how scores change!
""")

print("=" * 65)

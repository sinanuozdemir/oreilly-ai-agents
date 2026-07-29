"""Step 5: Creating and Using Benchmarks

WHAT IS A BENCHMARK?
--------------------
A benchmark is a standardized test suite for your RAG system.
It's a collection of questions with known correct answers.

WHY USE BENCHMARKS?
-------------------
• Measure progress over time
• Compare different RAG configurations
• Catch regressions before deployment
• Set quality standards for production

WHERE THIS IS APPLIED
---------------------
• Before/after making changes to your RAG
• Comparing embedding models
• A/B testing different prompts
• Regression testing in CI/CD
"""

import json
from datetime import datetime


# ============================================================================
# PART 1: Creating Your First Benchmark
# ============================================================================
print("=" * 65)
print("PART 1: Creating a Benchmark")
print("=" * 65)

# A benchmark is just a structured list of test cases
my_benchmark = {
    "name": "Programming Languages Q&A",
    "created": datetime.now().isoformat(),
    "description": "Basic questions about programming languages",
    "categories": ["creator", "history", "features"],
    "test_cases": [
        {
            "id": "py-001",
            "category": "creator",
            "difficulty": "easy",
            "question": "Who created Python?",
            "ground_truth_answer": "Python was created by Guido van Rossum.",
            "required_facts": ["Guido van Rossum", "creator"],
            "tags": ["python", "history"]
        },
        {
            "id": "js-001",
            "category": "creator",
            "difficulty": "easy",
            "question": "Who created JavaScript?",
            "ground_truth_answer": "JavaScript was created by Brendan Eich in 1995.",
            "required_facts": ["Brendan Eich", "1995"],
            "tags": ["javascript", "history"]
        },
        {
            "id": "ts-001",
            "category": "features",
            "difficulty": "medium",
            "question": "What is the main difference between TypeScript and JavaScript?",
            "ground_truth_answer": "TypeScript adds static typing to JavaScript.",
            "required_facts": ["static typing", "superset"],
            "tags": ["typescript", "javascript", "comparison"]
        },
        {
            "id": "ml-001",
            "category": "features",
            "difficulty": "medium",
            "question": "What is the difference between machine learning and deep learning?",
            "ground_truth_answer": "Deep learning is a subset of machine learning that uses neural networks with multiple layers.",
            "required_facts": ["subset", "neural networks", "layers"],
            "tags": ["machine-learning", "deep-learning", "comparison"]
        },
        {
            "id": "py-002",
            "category": "history",
            "difficulty": "easy",
            "question": "When was Python first released?",
            "ground_truth_answer": "Python was first released in 1991.",
            "required_facts": ["1991"],
            "tags": ["python", "history"]
        },
    ]
}

# Save it to a file
filename = "my_first_benchmark.json"
with open(filename, 'w') as f:
    json.dump(my_benchmark, f, indent=2)

print(f"✓ Created benchmark: {filename}")
print(f"  Name: {my_benchmark['name']}")
print(f"  Test Cases: {len(my_benchmark['test_cases'])}")
print(f"  Categories: {', '.join(my_benchmark['categories'])}")


# ============================================================================
# PART 2: Loading and Analyzing the Benchmark
# ============================================================================
print("\n" + "=" * 65)
print("PART 2: Analyzing the Benchmark")
print("=" * 65)

# Load it back
with open(filename) as f:
    loaded_benchmark = json.load(f)

# Calculate statistics
test_cases = loaded_benchmark['test_cases']
difficulties = {}
categories = {}

for tc in test_cases:
    diff = tc['difficulty']
    cat = tc['category']
    difficulties[diff] = difficulties.get(diff, 0) + 1
    categories[cat] = categories.get(cat, 0) + 1

print("\nDifficulty Distribution:")
for diff, count in sorted(difficulties.items()):
    bar = "█" * count
    print(f"  {diff:10} {bar} ({count})")

print("\nCategory Distribution:")
for cat, count in sorted(categories.items()):
    bar = "█" * count
    print(f"  {cat:15} {bar} ({count})")


# ============================================================================
# PART 3: Running Evaluation Against Benchmark
# ============================================================================
print("\n" + "=" * 65)
print("PART 3: Using the Benchmark for Evaluation")
print("=" * 65)

# In real use, you'd do this:
# from src.evaluation import RAGEvaluator, EvalSample
# 
# # Convert benchmark to EvalSamples
# samples = []
# for tc in test_cases:
#     samples.append(EvalSample(
#         query=tc['question'],
#         ground_truth_answer=tc['ground_truth_answer'],
#         category=tc['category'],
#         difficulty=tc['difficulty'],
#     ))
# 
# # Run evaluation
# evaluator = RAGEvaluator(rag_pipeline)
# results = evaluator.run_evaluation(samples)

print("""
To use this benchmark with the RAG toolkit:

1. Load the benchmark:
   with open('my_first_benchmark.json') as f:
       benchmark = json.load(f)

2. Convert to EvalSamples:
   samples = []
   for tc in benchmark['test_cases']:
       samples.append(EvalSample(
           query=tc['question'],
           ground_truth_answer=tc['ground_truth_answer'],
           category=tc['category'],
           difficulty=tc['difficulty'],
       ))

3. Run evaluation:
   evaluator = RAGEvaluator(rag)
   results = evaluator.run_evaluation(samples)

4. Analyze by category:
   easy_results = [r for r in results if r.sample.difficulty == 'easy']
   hard_results = [r for r in results if r.sample.difficulty == 'hard']
""")


# ============================================================================
# PART 4: Creating a Domain-Specific Benchmark
# ============================================================================
print("\n" + "=" * 65)
print("PART 4: Domain-Specific Benchmark (Customer Support)")
print("=" * 65)

support_benchmark = {
    "name": "Customer Support FAQ",
    "domain": "customer_support",
    "test_cases": [
        {
            "id": "refund-001",
            "category": "refund",
            "priority": "high",
            "question": "What is your refund policy?",
            "ground_truth_answer": "We offer a 30-day money-back guarantee.",
            "common_misconceptions": [
                "You can get a refund anytime",
                "Refunds are instant",
            ],
            "tags": ["refund", "policy"]
        },
        {
            "id": "account-001",
            "category": "account",
            "priority": "high",
            "question": "How do I reset my password?",
            "ground_truth_answer": "Click 'Forgot Password' on the login page.",
            "edge_cases": [
                "Email not received",
                "Link expired",
            ],
            "tags": ["account", "password"]
        },
        {
            "id": "billing-001",
            "category": "billing",
            "priority": "medium",
            "question": "How do I update my credit card?",
            "ground_truth_answer": "Go to Settings > Billing > Payment Method.",
            "tags": ["billing", "payment"]
        },
    ]
}

print(f"Created support benchmark with {len(support_benchmark['test_cases'])} cases")
print("\nBenefits of domain-specific benchmarks:")
print("  • Test real-world scenarios your users face")
print("  • Include common misconceptions to catch hallucinations")
print("  • Prioritize by business impact")
print("  • Track performance per category")


# ============================================================================
# PART 5: Benchmark Best Practices
# ============================================================================
print("\n" + "=" * 65)
print("PART 5: Benchmark Best Practices")
print("=" * 65)

print("""
┌─────────────────────────────────────────────────────────────┐
│ 1. START SMALL                                              │
│    • Begin with 10-20 key questions                         │
│    • Cover your most common use cases                       │
│    • Add more over time                                     │
├─────────────────────────────────────────────────────────────┤
│ 2. USE REAL DATA                                            │
│    • Check support ticket history                           │
│    • Use actual user queries from logs                      │
│    • Interview customer support staff                       │
├─────────────────────────────────────────────────────────────┤
│ 3. COVER DIFFICULTY LEVELS                                  │
│    • Easy: Direct fact lookup                               │
│    • Medium: Requires synthesis                             │
│    • Hard: Multi-hop reasoning                              │
├─────────────────────────────────────────────────────────────┤
│ 4. INCLUDE EDGE CASES                                       │
│    • Questions with no answer                               │
│    • Ambiguous questions                                    │
│    • Questions requiring multiple docs                      │
├─────────────────────────────────────────────────────────────┤
│ 5. MAINTAIN OVER TIME                                       │
│    • Add questions for new features                         │
│    • Remove outdated questions                              │
│    • Version your benchmarks                                │
└─────────────────────────────────────────────────────────────┘
""")


# ============================================================================
# PART 6: Versioning and Comparison
# ============================================================================
print("\n" + "=" * 65)
print("PART 6: Versioning Your Benchmarks")
print("=" * 65)

# Create a "version 2" of the benchmark
benchmark_v2 = my_benchmark.copy()
benchmark_v2['version'] = '2.0'
benchmark_v2['previous_version'] = '1.0'
benchmark_v2['changes'] = [
    "Added 3 new test cases about TypeScript",
    "Fixed incorrect answer for js-001",
    "Added difficulty ratings",
]
benchmark_v2['test_cases'].append({
    "id": "ts-002",
    "category": "history",
    "difficulty": "hard",
    "question": "What were the design goals of TypeScript?",
    "ground_truth_answer": "TypeScript aimed to add optional static typing to JavaScript for better tooling and scalability.",
    "tags": ["typescript", "design-goals"]
})

print("Version 2.0 changes:")
for change in benchmark_v2['changes']:
    print(f"  • {change}")

print(f"\nTest cases: {len(my_benchmark['test_cases'])} → {len(benchmark_v2['test_cases'])}")

print("""
Why version benchmarks?
• Track how your RAG improves over time
• Compare against previous versions
• Document what changed and why
• Enable reproducible results
""")


# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)
print(f"""
✓ Created your first benchmark ({filename})
✓ Learned to analyze benchmark composition
✓ Understood domain-specific benchmarks
✓ Learned best practices

KEY TAKEAWAYS:
1. A benchmark is a collection of test questions with known answers
2. Start small (10-20 questions) and grow over time
3. Use real user questions from your application
4. Cover different difficulty levels and categories
5. Version your benchmarks to track progress

FILES CREATED:
  • {filename}
  
NEXT STEPS:
  1. Create a benchmark for YOUR use case
  2. Collect real questions from users
  3. Run evaluation using step4_first_eval.py as template
  4. Track scores over time as you improve your RAG
""")

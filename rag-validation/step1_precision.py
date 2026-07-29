"""Step 1: Understanding Context Precision

WHAT IS IT?
-----------
Context Precision measures: Of the documents you retrieved, how many were relevant?

WHY DOES IT MATTER?
-------------------
- Low precision = AI gets confused by irrelevant information
- High precision = AI only sees useful context
- Real impact: Customer asks about refunds, but AI sees pricing docs → wrong answer

THE FORMULA
-----------
Context Precision = (Relevant Retrieved) / (Total Retrieved)

EXAMPLE:
- Retrieved 5 docs, 3 are relevant → Precision = 3/5 = 0.60 (60%)
- Retrieved 5 docs, 5 are relevant → Precision = 5/5 = 1.00 (100%) ✓
"""


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
print("=" * 60)
print("EXAMPLE 1: Good Retrieval (100% Precision)")
print("=" * 60)

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
print(f"Question: What is Python?")
print(f"\nRetrieved {len(retrieved)} documents:")
for i, doc in enumerate(retrieved, 1):
    print(f"  {i}. {doc}")

print(f"\nRelevant matches: All 3 retrieved are relevant ✓")
print(f"Context Precision: {score:.2%}")
print("\n✅ GOOD: All retrieved documents are relevant to the question")


# ========== EXAMPLE 2: Bad Precision ==========
print("\n" + "=" * 60)
print("EXAMPLE 2: Poor Retrieval (33% Precision)")
print("=" * 60)

retrieved = [
    "Python is a programming language",     # ✓ relevant
    "Java is also a programming language",  # ✗ not about Python
    "Snakes are reptiles",                  # ✗ wrong topic entirely!
]

relevant = [
    "Python is a programming language",
    "Python was created by Guido van Rossum",
]

score = context_precision(retrieved, relevant)
print(f"Question: What is Python?")
print(f"\nRetrieved {len(retrieved)} documents:")
print(f"  1. {retrieved[0]} ✓")
print(f"  2. {retrieved[1]} ✗ (about Java, not Python)")
print(f"  3. {retrieved[2]} ✗ (about snakes, not programming)")

print(f"\nRelevant matches: Only 1 out of 3 is relevant")
print(f"Context Precision: {score:.2%}")
print("\n❌ BAD: Retrieved documents about Java and snakes!")
print("   The AI might get confused and mix up information.")


# ========== EXERCISE FOR YOU ==========
print("\n" + "=" * 60)
print("YOUR TURN! Calculate the precision:")
print("=" * 60)

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

print(f"Question: How do I reset my password?")
print(f"\nRetrieved documents:")
for i, doc in enumerate(retrieved_docs, 1):
    mark = "✓" if doc in relevant_docs else "✗"
    print(f"  {i}. {doc} {mark}")

score = context_precision(retrieved_docs, relevant_docs)
print(f"\nHow many are relevant? 2 out of 3")
print(f"Context Precision: {score:.2%}")
print(f"\n💡 The pricing doc is 'noise' - it doesn't help answer the question.")


# ========== WHERE THIS IS APPLIED ==========
print("\n" + "=" * 60)
print("REAL-WORLD APPLICATION")
print("=" * 60)
print("""
Customer Support Chatbot Example:

User: "What's your refund policy?"

BAD RETRIEVAL (33% precision):
  ✓ "Returns accepted within 30 days"
  ✗ "Our company was founded in 2010"
  ✗ "Meet our CEO, John Smith"
  
→ AI might say: "Our CEO was founded in 2010 and returns John Smith"
→ User is confused, support ticket escalated

GOOD RETRIEVAL (100% precision):
  ✓ "Returns accepted within 30 days"
  ✓ "Sale items cannot be returned"
  ✓ "Refunds processed in 5-7 business days"
  
→ AI gives accurate, helpful answer
→ User is satisfied, ticket resolved

TARGET: Context Precision > 70%
""")


# ========== TRY IT YOURSELF ==========
print("\n" + "=" * 60)
print("PRACTICE: Try your own examples!")
print("=" * 60)
print("""
Edit this file and change the retrieved_docs and relevant_docs
to see how precision changes.

EXPERIMENT IDEAS:
1. What happens if you retrieve 10 docs but only 2 are relevant?
2. What precision do you get if all docs are relevant?
3. What if no documents are retrieved at all?

RUN: python step1_precision.py
""")

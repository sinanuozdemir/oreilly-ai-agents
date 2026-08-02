"""Step 2: Understanding Faithfulness

WHAT IS IT?
-----------
Faithfulness measures: Does the AI's answer stick to the facts in the context?

WHY DOES IT MATTER?
-------------------
- Unfaithful answers = AI is "hallucinating" (making things up)
- This is dangerous in medical, legal, financial applications
- Faithful answers = users can trust the information

THE CONCEPT
-----------
Context: "Python was created by Guido van Rossum in 1991"

Faithful Answer: "Python was created by Guido van Rossum"
→ Matches the context ✓

Unfaithful Answer: "Python was created by Bill Gates at Microsoft"
→ Contradicts the context ✗ (This describes Java/C#)

HOW WE MEASURE IT
-----------------
Method 1: Simple keyword overlap (we'll use this - no install needed!)
Method 2: Embeddings - mathematical representations of meaning (advanced)
"""


def simple_faithfulness_score(answer, context_docs):
    """
    Simple faithfulness check using keyword overlap.
    No external libraries needed!
    
    Args:
        answer: The AI's generated answer
        context_docs: List of retrieved documents
        
    Returns:
        Score from 0.0 (unfaithful) to 1.0 (perfectly faithful)
    """
    # Combine all context
    full_context = " ".join(context_docs).lower()
    answer_lower = answer.lower()
    
    # Extract key words from answer (longer words are more meaningful)
    answer_words = set(word.strip(".,!?;:") for word in answer_lower.split() if len(word) > 3)
    
    if not answer_words:
        return 0.0
    
    # Count how many answer words appear in context
    matching_words = sum(1 for word in answer_words if word in full_context)
    
    # Score is the percentage of answer words found in context
    score = matching_words / len(answer_words)
    
    return score


def detailed_faithfulness_check(answer, context_docs):
    """
    Detailed breakdown of faithfulness.
    """
    full_context = " ".join(context_docs).lower()
    answer_lower = answer.lower()
    
    # Get significant words from answer
    answer_words = [word.strip(".,!?;:") for word in answer_lower.split() if len(word) > 3]
    
    found = []
    missing = []
    
    for word in answer_words:
        if word in full_context:
            found.append(word)
        else:
            missing.append(word)
    
    score = len(found) / len(answer_words) if answer_words else 0
    
    return score, found, missing


# ========== EXAMPLE 1: Perfect Faithfulness ==========
print("=" * 60)
print("EXAMPLE 1: Perfectly Faithful Answer")
print("=" * 60)

context = [
    "Python was created by Guido van Rossum and first released in 1991.",
    "Python is known for its readable syntax and indentation.",
]

answer = "Python was created by Guido van Rossum in 1991."

score = simple_faithfulness_score(answer, context)

print("Context provided to AI:")
for doc in context:
    print(f"  • {doc}")

print(f"\nAI's Answer: {answer}")
print(f"Faithfulness Score: {score:.3f} ({score:.1%})")

print("\n✅ EXCELLENT: Answer matches the context exactly")
print("   The AI only stated facts that were in the documents.")


# ========== EXAMPLE 2: Complete Hallucination ==========
print("\n" + "=" * 60)
print("EXAMPLE 2: Hallucination (Unfaithful)")
print("=" * 60)

context = [
    "Python was created by Guido van Rossum and first released in 1991.",
]

answer = "Python was created by James Gosling in 1995 at Sun Microsystems."

score, found, missing = detailed_faithfulness_check(answer, context)

print("Context provided to AI:")
for doc in context:
    print(f"  • {doc}")

print(f"\nAI's Answer: {answer}")
print(f"Faithfulness Score: {score:.3f} ({score:.1%})")
print(f"\nWords FOUND in context: {found}")
print(f"Words NOT in context: {missing}")

print("\n❌ HALLUCINATION: Answer contradicts the context!")
print("   Wrong creator: James Gosling created Java, not Python")
print("   Wrong year: 1995 is when Java came out, Python was 1991")
print("   Wrong company: Sun Microsystems made Java")


# ========== EXAMPLE 3: Partial Faithfulness ==========
print("\n" + "=" * 60)
print("EXAMPLE 3: Partially Faithful (Dangerous!)")
print("=" * 60)

context = [
    "Our refund policy allows returns within 30 days with receipt.",
    "Sale items cannot be returned.",
]

answer = "You can return items within 30 days, and sale items are refundable too."

score, found, missing = detailed_faithfulness_check(answer, context)

print("Context provided to AI:")
for doc in context:
    print(f"  • {doc}")

print(f"\nAI's Answer: {answer}")
print(f"Faithfulness Score: {score:.3f} ({score:.1%})")
print(f"\nWords FOUND in context: {found}")
print(f"Words NOT in context: {missing}")

print("\n⚠️  WARNING: Partially faithful!")
print("   ✓ True: You can return within 30 days")
print("   ✗ FALSE: Sale items are NOT refundable")
print("\n   This is DANGEROUS because it sounds correct")
print("   but contains a critical error about sale items.")


# ========== EXAMPLE 4: Adding Extra (But True) Info ==========
print("\n" + "=" * 60)
print("EXAMPLE 4: Faithful But With Extra Knowledge?")
print("=" * 60)

context = [
    "Python was created by Guido van Rossum and first released in 1991.",
]

# AI adds info NOT in context but is common knowledge
answer = "Python was created by Guido van Rossum in 1991 and is popular for AI."

score, found, missing = detailed_faithfulness_check(answer, context)

print("Context provided to AI:")
for doc in context:
    print(f"  • {doc}")

print(f"\nAI's Answer: {answer}")
print(f"Faithfulness Score: {score:.3f} ({score:.1%})")
print(f"\nWords FOUND in context: {found}")
print(f"Words NOT in context: {missing}")

print("\n⚠️  The AI added 'popular' and 'intelligence' which weren't in the context.")
print("   Even though it's true in real life, it's not in the provided docs.")
print("   In strict RAG, we want the AI to ONLY use the provided context.")


# ========== REAL-WORLD IMPACT ==========
print("\n" + "=" * 60)
print("WHY FAITHFULNESS MATTERS (Real Scenarios)")
print("=" * 60)
print("""
🏥 MEDICAL CHATBOT:
   Context: "Aspirin may cause stomach bleeding in some patients"
   Unfaithful: "Aspirin is safe for everyone"
   → Patient with ulcers takes aspirin → Hospitalized

💰 FINANCIAL ADVISOR:
   Context: "This investment has risks and may lose value"
   Unfaithful: "This investment is guaranteed to double your money"
   → Investor loses savings → Lawsuit

⚖️  LEGAL ASSISTANT:
   Context: "Statute of limitations is 2 years for this claim"
   Unfaithful: "You have 5 years to file your claim"
   → Client misses deadline → Case dismissed

🛒 CUSTOMER SUPPORT:
   Context: "Premium support available for Enterprise plans only"
   Unfaithful: "All customers get premium support"
   → Customer demands premium service → Support chaos

TARGET: Faithfulness > 0.80 (80% similarity to context)
""")


# ========== YOUR TURN ==========
print("\n" + "=" * 60)
print("PRACTICE: Evaluate These Answers")
print("=" * 60)

test_cases = [
    {
        "name": "Medical Example",
        "context": ["Side effects include nausea and headache."],
        "answer": "This medication may cause nausea and headache."
    },
    {
        "name": "Support Example", 
        "context": ["Office hours are 9 AM to 5 PM EST."],
        "answer": "You can reach us anytime, we work 24/7."
    },
    {
        "name": "Product Example",
        "context": ["The Pro plan costs $50/month and includes 10 users."],
        "answer": "The Pro plan is $50 per month for up to 10 team members."
    }
]

for case in test_cases:
    score, found, missing = detailed_faithfulness_check(case["answer"], case["context"])
    print(f"\n{case['name']}:")
    print(f"  Context: {case['context'][0]}")
    print(f"  Answer: {case['answer']}")
    print(f"  Faithfulness: {score:.3f} ({score:.1%})")
    print(f"  Found: {found}")
    print(f"  Missing: {missing}")
    
    if score > 0.8:
        print("  ✅ Faithful")
    elif score > 0.5:
        print("  ⚠️  Partial")
    else:
        print("  ❌ Unfaithful (hallucination)")


# ========== HOW TO IMPROVE FAITHFULNESS ==========
print("\n" + "=" * 60)
print("HOW TO IMPROVE FAITHFULNESS")
print("=" * 60)
print("""
If your faithfulness scores are low:

1. BETTER CONTEXT RETRIEVAL
   → Make sure you're retrieving the RIGHT documents
   → See Step 1 (Context Precision)

2. PROMPT ENGINEERING
   → Add instructions: "Only use the provided context"
   → Add: "If the answer is not in the context, say 'I don't know'"

3. SMALLER CONTEXT WINDOW
   → Don't overwhelm the AI with too many documents
   → Keep only the most relevant chunks

4. TEMPERATURE = 0
   → Set LLM temperature to 0 for more deterministic answers
   → Higher temperature = more creative = more hallucinations

5. CLAIM VERIFICATION
   → Use advanced techniques to verify each claim
   → Check each sentence against the context
""")

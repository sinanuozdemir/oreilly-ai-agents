"""Step 4: Simple RAG Evaluation (No External Dependencies)

This version works without LangChain or sentence-transformers!
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import random


@dataclass
class SimpleRAGResponse:
    """Simple response container."""
    query: str
    answer: str
    retrieved_documents: List[str]


class SimpleRAG:
    """Super simple RAG that works without any external libraries."""
    
    def __init__(self, chunk_size: int = 256, top_k: int = 3):
        self.chunk_size = chunk_size
        self.top_k = top_k
        self.documents = []
        self.chunks = []
    
    def add_documents(self, documents: List[str]):
        """Add documents and split into chunks."""
        self.documents = documents
        self.chunks = []
        
        for doc in documents:
            # Simple chunking by sentence
            sentences = doc.replace(". ", ".").split(".")
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < self.chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        self.chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "
            
            if current_chunk:
                self.chunks.append(current_chunk.strip())
        
        print(f"  Split {len(documents)} documents into {len(self.chunks)} chunks")
    
    def _simple_similarity(self, query: str, chunk: str) -> float:
        """Calculate simple word overlap similarity."""
        query_words = set(query.lower().split())
        chunk_words = set(chunk.lower().split())
        
        if not query_words or not chunk_words:
            return 0.0
        
        # Count matching words
        matches = len(query_words & chunk_words)
        return matches / len(query_words)
    
    def retrieve(self, query: str) -> List[str]:
        """Find most similar chunks."""
        if not self.chunks:
            return []
        
        # Score each chunk
        scored = [(chunk, self._simple_similarity(query, chunk)) 
                  for chunk in self.chunks]
        
        # Sort by score and return top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in scored[:self.top_k]]
    
    def query(self, query_text: str) -> SimpleRAGResponse:
        """Simple RAG query."""
        # Retrieve relevant chunks
        retrieved = self.retrieve(query_text)
        
        # Generate simple answer based on retrieved content
        context = " ".join(retrieved)
        
        # Simple "generation" - extract key sentences
        sentences = context.split(".")
        answer = ". ".join(sentences[:2]) + "." if sentences else "I don't know."
        
        return SimpleRAGResponse(
            query=query_text,
            answer=answer,
            retrieved_documents=retrieved
        )


def evaluate_simple_rag(query: str, answer: str, retrieved: List[str], 
                        relevant: List[str]) -> Dict[str, float]:
    """Simple evaluation without embeddings."""
    results = {}
    
    # Precision
    if retrieved:
        matches = sum(1 for r in retrieved if any(r.lower() in rel.lower() 
                                                   or rel.lower() in r.lower() 
                                                   for rel in relevant))
        results['context_precision'] = matches / len(retrieved)
    else:
        results['context_precision'] = 0.0
    
    # Recall
    if relevant:
        matches = sum(1 for rel in relevant if any(rel.lower() in r.lower() 
                                                    or r.lower() in rel.lower() 
                                                    for r in retrieved))
        results['context_recall'] = matches / len(relevant)
    else:
        results['context_recall'] = 1.0
    
    # Simple faithfulness (word overlap)
    context_text = " ".join(retrieved).lower()
    answer_words = set(answer.lower().split())
    if answer_words:
        matching = sum(1 for word in answer_words if word in context_text)
        results['faithfulness'] = matching / len(answer_words)
    else:
        results['faithfulness'] = 0.0
    
    # Simple relevance (word overlap with query)
    query_words = set(query.lower().split())
    answer_text = answer.lower()
    if query_words:
        matching = sum(1 for word in query_words if word in answer_text)
        results['answer_relevance'] = matching / len(query_words)
    else:
        results['answer_relevance'] = 0.0
    
    # RAGAS score
    results['ragas_score'] = (
        results['context_precision'] + 
        results['context_recall'] + 
        results['faithfulness'] + 
        results['answer_relevance']
    ) / 4
    
    return results


# ============================================================================
# MAIN DEMO
# ============================================================================
print("=" * 65)
print("STEP 4: Simple RAG Evaluation (No Dependencies!)")
print("=" * 65)

# Documents about programming languages
documents = [
    "Python is a high-level programming language created by Guido van Rossum in 1991. "
    "It is known for its readable syntax and indentation-based structure. "
    "Python is widely used for web development, data science, and artificial intelligence.",
    
    "JavaScript is a programming language that enables interactive web pages. "
    "It was created by Brendan Eich in 1995 while working at Netscape. "
    "JavaScript is an essential part of web development alongside HTML and CSS.",
    
    "Machine learning is a subset of artificial intelligence that enables computers "
    "to learn from data without being explicitly programmed. It is used for "
    "predictions, classification, and pattern recognition.",
    
    "Deep learning is a type of machine learning based on artificial neural networks. "
    "It uses multiple layers to progressively extract higher-level features from raw input. "
    "Deep learning powers technologies like image recognition and natural language processing.",
]

print("\n📚 Creating RAG pipeline...")
rag = SimpleRAG(chunk_size=200, top_k=2)
rag.add_documents(documents)

# Test questions
test_cases = [
    {
        "query": "Who created Python?",
        "ground_truth": "Python was created by Guido van Rossum.",
        "relevant": ["Python is a high-level programming language created by Guido van Rossum in 1991."]
    },
    {
        "query": "What is machine learning?",
        "ground_truth": "Machine learning is a subset of artificial intelligence.",
        "relevant": ["Machine learning is a subset of artificial intelligence"]
    },
    {
        "query": "When was JavaScript created?",
        "ground_truth": "JavaScript was created in 1995.",
        "relevant": ["It was created by Brendan Eich in 1995"]
    },
]

print(f"\n🧪 Running {len(test_cases)} test cases...\n")

all_results = []
for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['query']}")
    
    # Query the RAG
    response = rag.query(test['query'])
    
    # Evaluate
    metrics = evaluate_simple_rag(
        test['query'],
        response.answer,
        response.retrieved_documents,
        test['relevant']
    )
    all_results.append(metrics)
    
    print(f"  Retrieved: {len(response.retrieved_documents)} chunks")
    print(f"  Answer: {response.answer[:60]}...")
    print(f"  RAGAS Score: {metrics['ragas_score']:.3f}")
    print()

# Aggregate results
print("=" * 65)
print("📊 SUMMARY")
print("=" * 65)

avg_ragas = sum(r['ragas_score'] for r in all_results) / len(all_results)
avg_precision = sum(r['context_precision'] for r in all_results) / len(all_results)
avg_recall = sum(r['context_recall'] for r in all_results) / len(all_results)
avg_faith = sum(r['faithfulness'] for r in all_results) / len(all_results)

print(f"\nOverall RAGAS Score: {avg_ragas:.3f}")
print(f"  Context Precision: {avg_precision:.3f}")
print(f"  Context Recall:    {avg_recall:.3f}")
print(f"  Faithfulness:      {avg_faith:.3f}")

if avg_ragas > 0.7:
    print("\n✅ Good results! The simple RAG is working.")
else:
    print("\n⚠️  Results could be improved with better chunking or retrieval.")

print("\n" + "=" * 65)
print("WHAT YOU LEARNED:")
print("=" * 65)
print("""
• Documents are split into chunks for retrieval
• Simple word-matching can work for basic RAG
• The 4 metrics tell you what's working/failing
• You can build RAG without complex libraries!

Next: Try step5_benchmark.py to create test suites.
""")

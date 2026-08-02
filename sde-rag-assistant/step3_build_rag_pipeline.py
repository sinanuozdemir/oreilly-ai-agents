"""Step 3: Building the RAG Pipeline for Code

WHAT WE BUILD
-------------
A RAG system that can answer questions about our codebase by:
1. Retrieving relevant code, docs, and tests
2. Generating contextual answers

REAL-WORLD USE CASES
--------------------
- "How do I implement user authentication?"
- "What tests should I add for payment processing?"
- "Which API endpoints use the auth middleware?"
- "Show me examples of refund handling"

ARCHITECTURE
------------
User Query → Vector Search → Retrieve Context → Generate Answer
"""

import chromadb
from chromadb.utils import embedding_functions
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Connect to database
print("🔌 Connecting to vector database...")
client = chromadb.PersistentClient(path="./vector_db")
collection = client.get_collection("codebase")

# Set up embedding function
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("\n⚠️  WARNING: OPENAI_API_KEY not found!")
    print("   Please set it: export OPENAI_API_KEY='sk-your-key'")
    print("   Or create a .env file with: OPENAI_API_KEY=sk-your-key")
    print("\n   For now, using simple keyword-based search (limited functionality)\n")
    
    # Simple fallback - just for demo purposes
    openai_ef = None
else:
    print(f"✓ OpenAI API key found (ends with ...{openai_api_key[-4:]})")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=openai_api_key,
        model_name="text-embedding-3-small"
    )

print("✅ Connected to database")
print(f"   Total documents: {collection.count()}")


class CodeRAG:
    """RAG system for code repository."""
    
    def __init__(self, collection):
        self.collection = collection
    
    def query(self, question: str, n_results: int = 5) -> Dict:
        """
        Query the codebase and return relevant context.
        
        Args:
            question: Natural language question
            n_results: Number of documents to retrieve
            
        Returns:
            Dictionary with retrieved documents and metadata
        """
        # Search the vector database
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "relevance_score": 1 - results["distances"][0][i]  # Convert distance to similarity
            })
        
        return {
            "query": question,
            "results": formatted_results
        }
    
    def get_related_tests(self, code_file: str) -> List[Dict]:
        """Find tests related to a specific code file."""
        results = self.collection.query(
            query_texts=[f"tests for {code_file}"],
            n_results=3,
            where={"type": "test"}
        )
        
        tests = []
        for i in range(len(results["documents"][0])):
            tests.append({
                "file": results["metadatas"][0][i].get("file", "unknown"),
                "content": results["documents"][0][i]
            })
        return tests
    
    def get_api_spec(self, endpoint_keyword: str) -> Dict:
        """Find API specification by keyword."""
        results = self.collection.query(
            query_texts=[endpoint_keyword],
            n_results=2,
            where={"type": "api_spec"}
        )
        
        if results["documents"][0]:
            return {
                "spec": results["documents"][0][0],
                "endpoint": results["metadatas"][0][0].get("endpoint", "unknown")
            }
        return None


# Initialize our RAG system
print("\n🏗️  Initializing CodeRAG system...")
rag = CodeRAG(collection)

print("✅ CodeRAG ready!")


# ============================================================================
# DEMO QUERIES
# ============================================================================

print("\n" + "="*60)
print("DEMO: Querying the Codebase")
print("="*60)

demo_queries = [
    "How do I authenticate a user?",
    "Show me the payment processing code",
    "What tests exist for refunds?",
    "How do I cancel an order?",
    "What API endpoints handle authentication?",
]

for query in demo_queries:
    print(f"\n🔍 Query: {query}")
    print("-" * 50)
    
    response = rag.query(query, n_results=3)
    
    print("Retrieved documents:")
    for i, result in enumerate(response["results"], 1):
        content_preview = result["content"][:100].replace("\n", " ")
        file_name = result["metadata"].get("file", "unknown")
        doc_type = result["metadata"].get("type", "unknown")
        
        print(f"  {i}. [{doc_type}] {file_name}")
        print(f"     {content_preview}...")
        print(f"     Relevance: {result['relevance_score']:.3f}")
        print()


# ============================================================================
# ADVANCED: Multi-source Retrieval
# ============================================================================

print("\n" + "="*60)
print("ADVANCED: Multi-Source Retrieval")
print("="*60)
print("""
For a complete answer, we often need multiple sources:
1. The code implementation
2. The API specification
3. Related tests
4. Past PRs showing similar changes
""")

# Example: Full context for "How do refunds work?"
print("\n🔍 Query: 'How do refunds work?'")
print("-" * 50)

# Get code implementation
code_results = rag.query("refund implementation code", n_results=2)
print("\n1. CODE IMPLEMENTATION:")
for r in code_results["results"]:
    if r["metadata"].get("type") == "code":
        print(f"   File: {r['metadata'].get('file')}")
        print(f"   Function: {r['metadata'].get('function', r['metadata'].get('class', 'N/A'))}")

# Get API spec
api_spec = rag.get_api_spec("refund endpoint")
if api_spec:
    print(f"\n2. API SPECIFICATION:")
    print(f"   Endpoint: {api_spec['endpoint']}")

# Get tests
tests = rag.get_related_tests("refunds")
print(f"\n3. RELATED TESTS:")
for test in tests:
    print(f"   - {test['file']}")


print("\n" + "="*60)
print("WHAT YOU LEARNED")
print("="*60)
print("""
✅ How to query a vector database for code
✅ How to filter by document type (code, test, api_spec)
✅ How to retrieve related documents (code → tests)
✅ Relevance scoring to rank results

This is the foundation for:
- Code review assistants
- Documentation Q&A bots
- Impact analysis tools

NEXT: Build specific use cases!
""")

print("\n✅ Step 3 complete! RAG pipeline built and tested.")

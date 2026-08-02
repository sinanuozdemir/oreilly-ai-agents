"""Step 1: Setting Up Your Local Vector Database

WHAT IS A VECTOR DATABASE?
--------------------------
Think of it like a search engine that understands MEANING, not just keywords.

Traditional Search:
  Query: "authentication"
  Finds: Files with word "authentication" in them
  Misses: Files about "login", "auth", "sign-in" (same meaning, different words)

Vector Search:
  Query: "authentication"
  Finds: Files about "authentication", "login", "auth", "sign-in", "user verification"
  Because: It understands these all mean the same thing!

WHY FOR CODE?
-------------
- Find similar code patterns across your codebase
- Match natural language queries to code ("payment processing" → billing.py)
- Group related files even if they don't share keywords

WHAT WE'LL USE
--------------
ChromaDB - A simple, local vector database perfect for learning.
- No server needed
- Stores data in files on your computer
- Fast and easy to use
"""

import os
from pathlib import Path

# Check if chromadb is installed
try:
    import chromadb
    print("✓ ChromaDB is installed")
except ImportError:
    print("❌ Installing ChromaDB...")
    os.system("pip install chromadb")
    import chromadb

# Create directory for our vector database
DB_PATH = "./vector_db"
os.makedirs(DB_PATH, exist_ok=True)

print(f"\n📁 Vector database will be stored at: {os.path.abspath(DB_PATH)}")

# Initialize Chroma client
# This creates (or connects to) a local database
client = chromadb.PersistentClient(path=DB_PATH)

print("\n✅ Vector database client created!")

# Create a collection for our code repository
# A collection is like a "table" in SQL - it holds related documents
collection = client.create_collection(
    name="codebase",
    metadata={"description": "Code repository embeddings"}
)

print("✅ Created 'codebase' collection")

# Let's verify it worked
collections = client.list_collections()
print(f"\n📊 Collections in database:")
for col in collections:
    print(f"  - {col.name}")

print("\n" + "="*60)
print("WHAT JUST HAPPENED?")
print("="*60)
print("""
1. Created a local ChromaDB database in ./vector_db/
2. Created a "collection" (like a table) called "codebase"
3. This collection will store:
   - Code files (chunked)
   - API documentation
   - Test files
   - Commit messages/PR descriptions

NEXT STEP: We'll add actual code data to this database.
""")

print("\n💡 PRO TIP:")
print("   You can view the database files in ./vector_db/")
print("   Each collection is stored as SQLite + index files")

# Save the path for next steps
with open(".db_path", "w") as f:
    f.write(os.path.abspath(DB_PATH))

print("\n✅ Step 1 complete! Database ready for data.")

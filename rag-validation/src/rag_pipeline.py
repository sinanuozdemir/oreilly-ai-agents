"""Example RAG Pipeline for Evaluation.

This module demonstrates a simple but complete RAG implementation
that can be used for testing and benchmarking.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


@dataclass
class RAGResponse:
    """Container for RAG pipeline response."""
    query: str
    answer: str
    retrieved_documents: List[str]
    metadata: Dict[str, Any]


class RAGPipeline:
    """A simple RAG pipeline for demonstration and evaluation.
    
    Example:
        >>> rag = RAGPipeline()
        >>> rag.add_documents(["Document 1 text...", "Document 2 text..."])
        >>> response = rag.query("What is...?")
        >>> print(response.answer)
    """
    
    def __init__(
        self,
        embedding_model: str = "text-embedding-3-small",
        llm_model: str = "gpt-3.5-turbo",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        top_k: int = 5,
        temperature: float = 0.0,
    ):
        """Initialize the RAG pipeline.
        
        Args:
            embedding_model: OpenAI embedding model name
            llm_model: LLM model name
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
            top_k: Number of documents to retrieve
            temperature: LLM temperature
        """
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature,
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        self.top_k = top_k
        self.vectorstore = None
        self.retriever = None
        self.chain = None
        
    def add_documents(self, documents: List[str], metadatas: Optional[List[Dict]] = None):
        """Add documents to the knowledge base.
        
        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
        """
        # Split documents into chunks
        chunks = self.text_splitter.create_documents(
            documents,
            metadatas=metadatas or [{} for _ in documents]
        )
        
        # Create or update vector store
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
            )
        else:
            self.vectorstore.add_documents(chunks)
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": self.top_k}
        )
        
        # Build the RAG chain
        self._build_chain()
        
    def _build_chain(self):
        """Build the LangChain RAG pipeline."""
        
        template = """Answer the question based only on the following context:

{context}

Question: {question}

Answer:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.chain = (
            {
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
    def query(self, question: str) -> RAGResponse:
        """Query the RAG pipeline.
        
        Args:
            question: User query
            
        Returns:
            RAGResponse with answer and metadata
        """
        if self.chain is None:
            raise ValueError("No documents loaded. Call add_documents() first.")
        
        # Get retrieved documents
        docs = self.retriever.invoke(question)
        retrieved_texts = [doc.page_content for doc in docs]
        
        # Generate answer
        answer = self.chain.invoke(question)
        
        return RAGResponse(
            query=question,
            answer=answer,
            retrieved_documents=retrieved_texts,
            metadata={
                "num_retrieved": len(docs),
                "model": self.llm.model_name,
            }
        )
    
    def get_retriever_only(self, question: str) -> List[str]:
        """Get only retrieved documents without generation.
        
        Useful for evaluating retrieval independently.
        """
        if self.retriever is None:
            raise ValueError("No documents loaded. Call add_documents() first.")
        
        docs = self.retriever.invoke(question)
        return [doc.page_content for doc in docs]


def create_sample_pipeline() -> RAGPipeline:
    """Create a pipeline with sample documents for testing."""
    
    sample_docs = [
        """Machine learning is a subset of artificial intelligence that enables 
        computers to learn and improve from experience without being explicitly 
        programmed. It focuses on developing computer programs that can access 
        data and use it to learn for themselves.""",
        
        """Deep learning is part of machine learning methods based on artificial 
        neural networks with representation learning. The adjective "deep" refers 
        to the use of multiple layers in the network. Deep learning has been 
        applied to computer vision, speech recognition, natural language processing, 
        and more.""",
        
        """Natural language processing (NLP) is a subfield of linguistics, computer 
        science, and artificial intelligence concerned with the interactions between 
        computers and human language. It involves programming computers to process 
        and analyze large amounts of natural language data.""",
        
        """Retrieval-Augmented Generation (RAG) is a technique that enhances large 
        language models by retrieving relevant information from external knowledge 
        sources before generating responses. This helps reduce hallucinations and 
        provides more accurate, up-to-date information.""",
        
        """Vector databases store data as high-dimensional vectors, which are 
        mathematical representations of features or attributes. These databases 
        are optimized for similarity search and are commonly used in RAG systems 
        to find relevant documents based on semantic meaning.""",
    ]
    
    rag = RAGPipeline()
    rag.add_documents(sample_docs)
    return rag


if __name__ == "__main__":
    # Demo usage
    rag = create_sample_pipeline()
    
    # Test queries
    queries = [
        "What is machine learning?",
        "How does RAG work?",
        "What are vector databases used for?",
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        response = rag.query(query)
        print(f"\nAnswer: {response.answer}")
        print(f"\nRetrieved {response.metadata['num_retrieved']} documents")

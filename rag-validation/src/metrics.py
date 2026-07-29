"""RAG Evaluation Metrics Implementation.

This module provides implementations of key RAG evaluation metrics,
including both traditional metrics and LLM-based evaluation.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
import string

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, CrossEncoder
import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


@dataclass
class MetricResult:
    """Container for metric results."""
    name: str
    score: float
    details: Optional[Dict[str, Any]] = None


class RetrievalMetrics:
    """Metrics for evaluating retrieval quality."""
    
    @staticmethod
    def context_precision(
        retrieved_docs: List[str],
        relevant_docs: List[str],
    ) -> MetricResult:
        """Calculate precision of retrieved documents.
        
        Measures what fraction of retrieved documents are relevant.
        
        Args:
            retrieved_docs: List of retrieved document texts
            relevant_docs: List of ground truth relevant document texts
            
        Returns:
            MetricResult with precision score
        """
        if not retrieved_docs:
            return MetricResult("context_precision", 0.0)
        
        # Simple exact match (can be enhanced with semantic similarity)
        relevant_set = set(d.lower().strip() for d in relevant_docs)
        retrieved_set = set(d.lower().strip() for d in retrieved_docs)
        
        matches = len(retrieved_set & relevant_set)
        precision = matches / len(retrieved_docs)
        
        return MetricResult(
            name="context_precision",
            score=precision,
            details={
                "retrieved_count": len(retrieved_docs),
                "relevant_count": len(relevant_docs),
                "matches": matches,
            }
        )
    
    @staticmethod
    def context_recall(
        retrieved_docs: List[str],
        relevant_docs: List[str],
    ) -> MetricResult:
        """Calculate recall of retrieved documents.
        
        Measures what fraction of relevant documents were retrieved.
        
        Args:
            retrieved_docs: List of retrieved document texts
            relevant_docs: List of ground truth relevant document texts
            
        Returns:
            MetricResult with recall score
        """
        if not relevant_docs:
            return MetricResult("context_recall", 1.0)
        
        relevant_set = set(d.lower().strip() for d in relevant_docs)
        retrieved_set = set(d.lower().strip() for d in retrieved_docs)
        
        matches = len(retrieved_set & relevant_set)
        recall = matches / len(relevant_docs)
        
        return MetricResult(
            name="context_recall",
            score=recall,
            details={
                "retrieved_count": len(retrieved_docs),
                "relevant_count": len(relevant_docs),
                "matches": matches,
            }
        )
    
    @staticmethod
    def reciprocal_rank(
        retrieved_docs: List[str],
        relevant_docs: List[str],
    ) -> MetricResult:
        """Calculate reciprocal rank of first relevant document.
        
        Args:
            retrieved_docs: List of retrieved document texts (ordered)
            relevant_docs: List of ground truth relevant document texts
            
        Returns:
            MetricResult with RR score
        """
        relevant_set = set(d.lower().strip() for d in relevant_docs)
        
        for i, doc in enumerate(retrieved_docs, 1):
            if doc.lower().strip() in relevant_set:
                return MetricResult(
                    name="reciprocal_rank",
                    score=1.0 / i,
                    details={"first_relevant_position": i}
                )
        
        return MetricResult("reciprocal_rank", 0.0, {"first_relevant_position": None})
    
    @staticmethod
    def ndcg(
        retrieved_docs: List[str],
        relevance_scores: Dict[str, float],
        k: int = 10,
    ) -> MetricResult:
        """Calculate Normalized Discounted Cumulative Gain.
        
        Args:
            retrieved_docs: List of retrieved document texts
            relevance_scores: Dict mapping doc text to relevance score (0-1)
            k: Number of top documents to consider
            
        Returns:
            MetricResult with nDCG score
        """
        def dcg(scores):
            return sum(
                (2 ** score - 1) / np.log2(i + 2)
                for i, score in enumerate(scores[:k])
            )
        
        retrieved_scores = [
            relevance_scores.get(doc, 0.0)
            for doc in retrieved_docs[:k]
        ]
        
        ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
        
        dcg_val = dcg(retrieved_scores)
        idcg_val = dcg(ideal_scores)
        
        ndcg = dcg_val / idcg_val if idcg_val > 0 else 0.0
        
        return MetricResult(
            name=f"ndcg@{k}",
            score=ndcg,
            details={"dcg": dcg_val, "idcg": idcg_val}
        )


class GenerationMetrics:
    """Metrics for evaluating generation quality."""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize with embedding model for semantic metrics."""
        self.embedding_model = SentenceTransformer(embedding_model)
    
    def faithfulness(
        self,
        answer: str,
        context: List[str],
    ) -> MetricResult:
        """Estimate faithfulness using semantic similarity.
        
        This is a simplified version. Full implementation would use
        claim extraction and NLI (Natural Language Inference).
        
        Args:
            answer: Generated answer
            context: Retrieved context documents
            
        Returns:
            MetricResult with faithfulness estimate
        """
        # Combine all context
        full_context = " ".join(context)
        
        # Get embeddings
        answer_emb = self.embedding_model.encode([answer])
        context_emb = self.embedding_model.encode([full_context])
        
        # Calculate similarity
        similarity = cosine_similarity(answer_emb, context_emb)[0][0]
        
        return MetricResult(
            name="faithfulness",
            score=float(similarity),
            details={"semantic_similarity": float(similarity)}
        )
    
    def answer_relevance(
        self,
        query: str,
        answer: str,
    ) -> MetricResult:
        """Calculate answer relevance to query.
        
        Args:
            query: User query
            answer: Generated answer
            
        Returns:
            MetricResult with relevance score
        """
        query_emb = self.embedding_model.encode([query])
        answer_emb = self.embedding_model.encode([answer])
        
        similarity = cosine_similarity(query_emb, answer_emb)[0][0]
        
        return MetricResult(
            name="answer_relevance",
            score=float(similarity),
            details={"cosine_similarity": float(similarity)}
        )
    
    @staticmethod
    def exact_match(prediction: str, reference: str) -> MetricResult:
        """Calculate exact match score.
        
        Args:
            prediction: Generated answer
            reference: Ground truth answer
            
        Returns:
            MetricResult with binary match
        """
        # Normalize both strings
        def normalize(text):
            text = text.lower().strip()
            text = text.translate(str.maketrans('', '', string.punctuation))
            return ' '.join(text.split())
        
        match = normalize(prediction) == normalize(reference)
        
        return MetricResult(
            name="exact_match",
            score=1.0 if match else 0.0,
            details={"prediction": prediction, "reference": reference}
        )
    
    @staticmethod
    def f1_score(prediction: str, reference: str) -> MetricResult:
        """Calculate token-level F1 score.
        
        Args:
            prediction: Generated answer
            reference: Ground truth answer
            
        Returns:
            MetricResult with F1 score
        """
        def tokenize(text):
            text = text.lower()
            text = text.translate(str.maketrans('', '', string.punctuation))
            return set(text.split())
        
        pred_tokens = tokenize(prediction)
        ref_tokens = tokenize(reference)
        
        if not pred_tokens or not ref_tokens:
            return MetricResult("f1_score", 0.0)
        
        common = pred_tokens & ref_tokens
        
        precision = len(common) / len(pred_tokens)
        recall = len(common) / len(ref_tokens)
        
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return MetricResult(
            name="f1_score",
            score=f1,
            details={"precision": precision, "recall": recall}
        )


class RAGASMetrics:
    """Composite metrics inspired by RAGAS framework."""
    
    def __init__(self):
        self.retrieval = RetrievalMetrics()
        self.generation = GenerationMetrics()
    
    def evaluate(
        self,
        query: str,
        answer: str,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        ground_truth_answer: Optional[str] = None,
    ) -> Dict[str, MetricResult]:
        """Run full RAG evaluation.
        
        Args:
            query: User query
            answer: Generated answer
            retrieved_docs: Retrieved documents
            relevant_docs: Ground truth relevant documents
            ground_truth_answer: Optional ground truth answer
            
        Returns:
            Dictionary of metric results
        """
        results = {}
        
        # Retrieval metrics
        results["context_precision"] = self.retrieval.context_precision(
            retrieved_docs, relevant_docs
        )
        results["context_recall"] = self.retrieval.context_recall(
            retrieved_docs, relevant_docs
        )
        results["reciprocal_rank"] = self.retrieval.reciprocal_rank(
            retrieved_docs, relevant_docs
        )
        
        # Generation metrics
        results["faithfulness"] = self.generation.faithfulness(
            answer, retrieved_docs
        )
        results["answer_relevance"] = self.generation.answer_relevance(
            query, answer
        )
        
        if ground_truth_answer:
            results["exact_match"] = self.generation.exact_match(
                answer, ground_truth_answer
            )
            results["f1_score"] = self.generation.f1_score(
                answer, ground_truth_answer
            )
        
        # Calculate overall RAGAS-like score
        core_metrics = [
            results["context_precision"].score,
            results["context_recall"].score,
            results["faithfulness"].score,
            results["answer_relevance"].score,
        ]
        results["ragas_score"] = MetricResult(
            name="ragas_score",
            score=np.mean(core_metrics),
            details={"component_scores": core_metrics}
        )
        
        return results


def format_results(results: Dict[str, MetricResult]) -> str:
    """Format metric results as a readable string."""
    lines = ["\n📊 RAG Evaluation Results", "=" * 50]
    
    for name, result in results.items():
        bar_length = int(result.score * 30)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        lines.append(f"{name:20} {result.score:.3f} {bar}")
    
    lines.append("=" * 50)
    return "\n".join(lines)


# Convenience functions for direct use
def context_precision(retrieved_docs: List[str], relevant_docs: List[str]) -> float:
    """Quick access to context precision metric."""
    return RetrievalMetrics.context_precision(retrieved_docs, relevant_docs).score


def context_recall(retrieved_docs: List[str], relevant_docs: List[str]) -> float:
    """Quick access to context recall metric."""
    return RetrievalMetrics.context_recall(retrieved_docs, relevant_docs).score


def faithfulness(answer: str, context: List[str]) -> float:
    """Quick access to faithfulness metric."""
    return GenerationMetrics().faithfulness(answer, context).score


def answer_relevancy(query: str, answer: str) -> float:
    """Quick access to answer relevance metric."""
    return GenerationMetrics().answer_relevance(query, answer).score

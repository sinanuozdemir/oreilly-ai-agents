"""Tests for RAG metrics."""

import pytest
from src.metrics import (
    RetrievalMetrics,
    GenerationMetrics,
    RAGASMetrics,
    context_precision,
    context_recall,
)


class TestRetrievalMetrics:
    """Test retrieval evaluation metrics."""
    
    def test_context_precision_perfect(self):
        """Test precision when all retrieved docs are relevant."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc1", "doc2", "doc3", "doc4"]
        
        result = RetrievalMetrics.context_precision(retrieved, relevant)
        assert result.score == 1.0
    
    def test_context_precision_partial(self):
        """Test precision with mixed relevance."""
        retrieved = ["doc1", "doc2", "irrelevant"]
        relevant = ["doc1", "doc2", "doc3"]
        
        result = RetrievalMetrics.context_precision(retrieved, relevant)
        assert result.score == pytest.approx(2/3)
    
    def test_context_precision_empty(self):
        """Test precision with empty retrieval."""
        result = RetrievalMetrics.context_precision([], ["doc1"])
        assert result.score == 0.0
    
    def test_context_recall_perfect(self):
        """Test recall when all relevant docs are retrieved."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc1", "doc2"]
        
        result = RetrievalMetrics.context_recall(retrieved, relevant)
        assert result.score == 1.0
    
    def test_context_recall_partial(self):
        """Test recall with partial retrieval."""
        retrieved = ["doc1"]
        relevant = ["doc1", "doc2", "doc3"]
        
        result = RetrievalMetrics.context_recall(retrieved, relevant)
        assert result.score == pytest.approx(1/3)
    
    def test_context_recall_empty_relevant(self):
        """Test recall with no relevant docs defined."""
        result = RetrievalMetrics.context_recall(["doc1"], [])
        assert result.score == 1.0  # Nothing to retrieve
    
    def test_reciprocal_rank_first(self):
        """Test RR when first doc is relevant."""
        retrieved = ["relevant", "doc2", "doc3"]
        relevant = ["relevant"]
        
        result = RetrievalMetrics.reciprocal_rank(retrieved, relevant)
        assert result.score == 1.0
        assert result.details["first_relevant_position"] == 1
    
    def test_reciprocal_rank_third(self):
        """Test RR when relevant doc is third."""
        retrieved = ["doc1", "doc2", "relevant"]
        relevant = ["relevant"]
        
        result = RetrievalMetrics.reciprocal_rank(retrieved, relevant)
        assert result.score == pytest.approx(1/3)
        assert result.details["first_relevant_position"] == 3
    
    def test_reciprocal_rank_none(self):
        """Test RR when no relevant docs retrieved."""
        retrieved = ["doc1", "doc2"]
        relevant = ["relevant"]
        
        result = RetrievalMetrics.reciprocal_rank(retrieved, relevant)
        assert result.score == 0.0
        assert result.details["first_relevant_position"] is None


class TestGenerationMetrics:
    """Test generation evaluation metrics."""
    
    def test_exact_match(self):
        """Test exact match with identical strings."""
        metrics = GenerationMetrics()
        result = metrics.exact_match("Hello world", "Hello world")
        assert result.score == 1.0
    
    def test_exact_match_case_insensitive(self):
        """Test exact match is case insensitive."""
        metrics = GenerationMetrics()
        result = metrics.exact_match("Hello World", "hello world")
        assert result.score == 1.0
    
    def test_exact_match_punctuation(self):
        """Test exact match ignores punctuation."""
        metrics = GenerationMetrics()
        result = metrics.exact_match("Hello, world!", "hello world")
        assert result.score == 1.0
    
    def test_f1_score_perfect(self):
        """Test F1 with perfect overlap."""
        metrics = GenerationMetrics()
        result = metrics.f1_score("the quick brown fox", "the quick brown fox")
        assert result.score == 1.0
    
    def test_f1_score_partial(self):
        """Test F1 with partial overlap."""
        metrics = GenerationMetrics()
        result = metrics.f1_score("the quick fox", "the brown fox")
        # Common: the, fox (2)
        # Precision: 2/3, Recall: 2/3, F1: 2/3
        assert result.score == pytest.approx(2/3)
    
    def test_f1_score_empty(self):
        """Test F1 with empty prediction."""
        metrics = GenerationMetrics()
        result = metrics.f1_score("", "some answer")
        assert result.score == 0.0
    
    def test_answer_relevance_similar(self):
        """Test relevance with similar texts."""
        metrics = GenerationMetrics()
        result = metrics.answer_relevance(
            "What is machine learning?",
            "Machine learning is a type of AI"
        )
        # Should have decent similarity
        assert result.score > 0.5
    
    def test_answer_relevance_different(self):
        """Test relevance with unrelated texts."""
        metrics = GenerationMetrics()
        result = metrics.answer_relevance(
            "What is machine learning?",
            "The weather is nice today"
        )
        # Should have low similarity
        assert result.score < 0.5


class TestConvenienceFunctions:
    """Test convenience metric functions."""
    
    def test_context_precision_function(self):
        """Test context_precision convenience function."""
        score = context_precision(["doc1", "doc2"], ["doc1"])
        assert score == 0.5
    
    def test_context_recall_function(self):
        """Test context_recall convenience function."""
        score = context_recall(["doc1"], ["doc1", "doc2"])
        assert score == 0.5


class TestRAGASMetrics:
    """Test RAGAS composite metrics."""
    
    def test_full_evaluation(self):
        """Test complete RAG evaluation."""
        ragas = RAGASMetrics()
        
        results = ragas.evaluate(
            query="What is ML?",
            answer="Machine learning is AI",
            retrieved_docs=["ML is machine learning", "AI is artificial intelligence"],
            relevant_docs=["ML is machine learning"],
            ground_truth_answer="Machine learning is a subset of AI",
        )
        
        # Check all expected metrics are present
        expected_metrics = [
            "context_precision",
            "context_recall",
            "reciprocal_rank",
            "faithfulness",
            "answer_relevance",
            "exact_match",
            "f1_score",
            "ragas_score",
        ]
        
        for metric in expected_metrics:
            assert metric in results
            assert isinstance(results[metric].score, float)
        
        # RAGAS score should be average of core metrics
        core_scores = [
            results["context_precision"].score,
            results["context_recall"].score,
            results["faithfulness"].score,
            results["answer_relevance"].score,
        ]
        expected_ragas = sum(core_scores) / len(core_scores)
        assert results["ragas_score"].score == pytest.approx(expected_ragas)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""RAG Validation Toolkit.

A comprehensive toolkit for evaluating Retrieval-Augmented Generation systems.
"""

__version__ = "0.1.0"
__author__ = "AI Agents Team"

from .metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)

from .evaluation import RAGEvaluator

__all__ = [
    "context_precision",
    "context_recall",
    "faithfulness",
    "answer_relevancy",
    "RAGEvaluator",
]

"""RAG Evaluation Runner.

This module provides the main evaluation orchestrator for running
comprehensive RAG benchmarks.
"""

import json
import argparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import time

from .rag_pipeline import RAGPipeline, create_sample_pipeline
from .metrics import RAGASMetrics, MetricResult, format_results


@dataclass
class EvalSample:
    """Single evaluation sample."""
    query: str
    ground_truth_answer: Optional[str]
    ground_truth_context: Optional[List[str]]
    category: str = "general"
    difficulty: str = "medium"


@dataclass
class EvalResult:
    """Complete evaluation result for a sample."""
    sample: EvalSample
    generated_answer: str
    retrieved_documents: List[str]
    metrics: Dict[str, MetricResult]
    latency_ms: float


class RAGEvaluator:
    """Main RAG evaluation orchestrator.
    
    Example:
        >>> evaluator = RAGEvaluator(rag_pipeline)
        >>> samples = [EvalSample("What is ML?", "Machine learning is...", [...])]
        >>> results = evaluator.run_evaluation(samples)
        >>> report = evaluator.generate_report(results)
    """
    
    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        metrics_calculator: Optional[RAGASMetrics] = None,
    ):
        """Initialize evaluator.
        
        Args:
            rag_pipeline: RAG pipeline to evaluate
            metrics_calculator: Metrics calculator (creates default if None)
        """
        self.rag = rag_pipeline
        self.metrics = metrics_calculator or RAGASMetrics()
    
    def run_evaluation(
        self,
        samples: List[EvalSample],
        verbose: bool = True,
    ) -> List[EvalResult]:
        """Run evaluation on a list of samples.
        
        Args:
            samples: List of evaluation samples
            verbose: Print progress
            
        Returns:
            List of evaluation results
        """
        results = []
        
        for i, sample in enumerate(samples):
            if verbose:
                print(f"\n[{i+1}/{len(samples)}] Evaluating: {sample.query[:50]}...")
            
            # Time the query
            start = time.time()
            response = self.rag.query(sample.query)
            latency_ms = (time.time() - start) * 1000
            
            # Calculate metrics
            metrics = self.metrics.evaluate(
                query=sample.query,
                answer=response.answer,
                retrieved_docs=response.retrieved_documents,
                relevant_docs=sample.ground_truth_context or [],
                ground_truth_answer=sample.ground_truth_answer,
            )
            
            result = EvalResult(
                sample=sample,
                generated_answer=response.answer,
                retrieved_documents=response.retrieved_documents,
                metrics=metrics,
                latency_ms=latency_ms,
            )
            results.append(result)
            
            if verbose:
                print(f"  RAGAS Score: {metrics['ragas_score'].score:.3f}")
                print(f"  Latency: {latency_ms:.1f}ms")
        
        return results
    
    def aggregate_metrics(self, results: List[EvalResult]) -> Dict[str, Any]:
        """Aggregate metrics across all results.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Dictionary with aggregated statistics
        """
        if not results:
            return {}
        
        # Collect all metric names
        metric_names = list(results[0].metrics.keys())
        
        aggregated = {}
        for metric_name in metric_names:
            scores = [r.metrics[metric_name].score for r in results]
            latencies = [r.latency_ms for r in results]
            
            aggregated[metric_name] = {
                "mean": sum(scores) / len(scores),
                "min": min(scores),
                "max": max(scores),
                "median": sorted(scores)[len(scores) // 2],
            }
        
        # Add latency statistics
        aggregated["latency_ms"] = {
            "mean": sum(latencies) / len(latencies),
            "p50": sorted(latencies)[len(latencies) // 2],
            "p95": sorted(latencies)[int(len(latencies) * 0.95)],
            "p99": sorted(latencies)[int(len(latencies) * 0.99)],
        }
        
        return aggregated
    
    def generate_report(
        self,
        results: List[EvalResult],
        output_format: str = "markdown",
    ) -> str:
        """Generate evaluation report.
        
        Args:
            results: List of evaluation results
            output_format: 'markdown', 'json', or 'html'
            
        Returns:
            Report string
        """
        aggregated = self.aggregate_metrics(results)
        
        if output_format == "json":
            return json.dumps(aggregated, indent=2)
        
        elif output_format == "markdown":
            lines = [
                "# RAG Evaluation Report",
                "",
                f"**Total Samples:** {len(results)}",
                "",
                "## Overall Metrics",
                "",
                "| Metric | Mean | Min | Max | Median |",
                "|--------|------|-----|-----|--------|",
            ]
            
            for metric_name, stats in aggregated.items():
                if metric_name == "latency_ms":
                    continue
                lines.append(
                    f"| {metric_name} | "
                    f"{stats['mean']:.3f} | "
                    f"{stats['min']:.3f} | "
                    f"{stats['max']:.3f} | "
                    f"{stats['median']:.3f} |"
                )
            
            lines.extend([
                "",
                "## Latency Statistics",
                "",
                f"- **Mean:** {aggregated['latency_ms']['mean']:.1f}ms",
                f"- **P50:** {aggregated['latency_ms']['p50']:.1f}ms",
                f"- **P95:** {aggregated['latency_ms']['p95']:.1f}ms",
                f"- **P99:** {aggregated['latency_ms']['p99']:.1f}ms",
                "",
                "## Per-Sample Results",
                "",
            ])
            
            for i, result in enumerate(results, 1):
                lines.extend([
                    f"### Sample {i}: {result.sample.category}",
                    f"**Query:** {result.sample.query}",
                    f"**Generated Answer:** {result.generated_answer[:200]}...",
                    f"**RAGAS Score:** {result.metrics['ragas_score'].score:.3f}",
                    "",
                ])
            
            return "\n".join(lines)
        
        elif output_format == "html":
            # Simple HTML report
            html = ["<html><body><h1>RAG Evaluation Report</h1>"]
            html.append(f"<p>Total Samples: {len(results)}</p>")
            html.append("<h2>Metrics</h2><table border='1'>")
            html.append("<tr><th>Metric</th><th>Mean</th><th>Min</th><th>Max</th></tr>")
            
            for metric_name, stats in aggregated.items():
                if metric_name == "latency_ms":
                    continue
                html.append(
                    f"<tr><td>{metric_name}</td>"
                    f"<td>{stats['mean']:.3f}</td>"
                    f"<td>{stats['min']:.3f}</td>"
                    f"<td>{stats['max']:.3f}</td></tr>"
                )
            
            html.append("</table></body></html>")
            return "\n".join(html)
        
        else:
            raise ValueError(f"Unknown output format: {output_format}")


def load_test_dataset() -> List[EvalSample]:
    """Load a sample test dataset for demonstration."""
    return [
        EvalSample(
            query="What is machine learning?",
            ground_truth_answer="Machine learning is a subset of artificial intelligence that enables computers to learn from experience without being explicitly programmed.",
            ground_truth_context=["Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed."],
            category="definitions",
            difficulty="easy",
        ),
        EvalSample(
            query="How does RAG improve LLM performance?",
            ground_truth_answer="RAG improves LLM performance by retrieving relevant information from external knowledge sources before generating responses, reducing hallucinations and providing more accurate information.",
            ground_truth_context=["Retrieval-Augmented Generation (RAG) is a technique that enhances large language models by retrieving relevant information from external knowledge sources before generating responses."],
            category="concepts",
            difficulty="medium",
        ),
        EvalSample(
            query="What are vector databases used for?",
            ground_truth_answer="Vector databases are used for storing data as high-dimensional vectors and performing similarity search, commonly used in RAG systems.",
            ground_truth_context=["Vector databases store data as high-dimensional vectors and are optimized for similarity search, commonly used in RAG systems."],
            category="applications",
            difficulty="easy",
        ),
        EvalSample(
            query="Explain the difference between deep learning and machine learning.",
            ground_truth_answer="Deep learning is a subset of machine learning that uses multiple layers in neural networks, while machine learning is a broader field that includes various algorithms for learning from data.",
            ground_truth_context=[
                "Machine learning is a subset of artificial intelligence that enables computers to learn from experience.",
                "Deep learning is part of machine learning methods based on artificial neural networks with multiple layers."
            ],
            category="comparison",
            difficulty="medium",
        ),
    ]


def main():
    """CLI entry point for evaluation."""
    parser = argparse.ArgumentParser(description="RAG Evaluation Runner")
    parser.add_argument(
        "--component",
        choices=["retrieval", "generation", "end-to-end"],
        default="end-to-end",
        help="Which component to evaluate",
    )
    parser.add_argument(
        "--test-size",
        type=int,
        default=None,
        help="Number of test samples to run",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/evaluation_results.json",
        help="Output file path",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "html"],
        default="json",
        help="Output format",
    )
    
    args = parser.parse_args()
    
    # Create sample pipeline and dataset
    print("🔄 Initializing RAG pipeline...")
    rag = create_sample_pipeline()
    
    print("📊 Loading test dataset...")
    samples = load_test_dataset()
    if args.test_size:
        samples = samples[:args.test_size]
    
    print(f"🧪 Running {args.component} evaluation on {len(samples)} samples...")
    evaluator = RAGEvaluator(rag)
    results = evaluator.run_evaluation(samples)
    
    # Generate report
    print("📋 Generating report...")
    report = evaluator.generate_report(results, output_format=args.format)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        if args.format == "json":
            # Save aggregated metrics as JSON
            aggregated = evaluator.aggregate_metrics(results)
            json.dump(aggregated, f, indent=2)
        else:
            f.write(report)
    
    print(f"✅ Results saved to {output_path}")
    
    # Print summary
    aggregated = evaluator.aggregate_metrics(results)
    print("\n📊 Summary:")
    print(f"  RAGAS Score: {aggregated['ragas_score']['mean']:.3f}")
    print(f"  Context Precision: {aggregated['context_precision']['mean']:.3f}")
    print(f"  Context Recall: {aggregated['context_recall']['mean']:.3f}")
    print(f"  Faithfulness: {aggregated['faithfulness']['mean']:.3f}")
    print(f"  Answer Relevance: {aggregated['answer_relevance']['mean']:.3f}")
    print(f"  Mean Latency: {aggregated['latency_ms']['mean']:.1f}ms")


if __name__ == "__main__":
    main()

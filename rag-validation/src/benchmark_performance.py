"""Performance Benchmarking for RAG Pipeline.

Measures latency, throughput, and resource utilization.
"""

import time
import json
import argparse
from typing import List, Dict
import statistics

from .rag_pipeline import create_sample_pipeline


def benchmark_latency(
    queries: List[str],
    iterations: int = 100,
) -> Dict[str, float]:
    """Benchmark RAG pipeline latency.
    
    Args:
        queries: List of test queries
        iterations: Number of iterations to run
        
    Returns:
        Dictionary with latency statistics
    """
    rag = create_sample_pipeline()
    
    latencies = []
    
    print(f"Running {iterations} iterations...")
    
    for i in range(iterations):
        query = queries[i % len(queries)]
        
        start = time.time()
        response = rag.query(query)
        latency = (time.time() - start) * 1000  # Convert to ms
        
        latencies.append(latency)
        
        if (i + 1) % 10 == 0:
            print(f"  Completed {i+1}/{iterations}")
    
    # Calculate statistics
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    
    return {
        "mean_latency": statistics.mean(latencies),
        "median_latency": statistics.median(latencies),
        "std_latency": statistics.stdev(latencies) if n > 1 else 0,
        "min_latency": min(latencies),
        "max_latency": max(latencies),
        "p50_latency": sorted_latencies[int(n * 0.50)],
        "p95_latency": sorted_latencies[int(n * 0.95)],
        "p99_latency": sorted_latencies[int(n * 0.99)],
        "iterations": iterations,
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark RAG performance")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--output", type=str, default="results/performance.json")
    
    args = parser.parse_args()
    
    test_queries = [
        "What is machine learning?",
        "How does RAG work?",
        "What are vector databases?",
        "Explain deep learning vs machine learning",
        "What is natural language processing?",
    ]
    
    print("🔬 Starting performance benchmark...")
    results = benchmark_latency(test_queries, args.iterations)
    
    # Save results
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to {args.output}")
    print(f"\n📊 Latency Summary:")
    print(f"  Mean: {results['mean_latency']:.1f}ms")
    print(f"  P50:  {results['p50_latency']:.1f}ms")
    print(f"  P95:  {results['p95_latency']:.1f}ms")
    print(f"  P99:  {results['p99_latency']:.1f}ms")


if __name__ == "__main__":
    main()

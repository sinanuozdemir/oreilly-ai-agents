"""Report Generation for CI/CD Integration.

Generates comparison reports between current and baseline metrics.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any


def generate_comparison_report(
    results_dir: Path,
    baseline_path: Path,
    output_path: Path,
) -> str:
    """Generate a comparison report between current and baseline metrics.
    
    Args:
        results_dir: Directory containing current result files
        baseline_path: Path to baseline metrics JSON
        output_path: Path to write report
        
    Returns:
        Markdown report string
    """
    # Load current results
    current = {}
    for result_file in results_dir.glob("**/*.json"):
        with open(result_file) as f:
            data = json.load(f)
            current.update(data)
    
    # Load baseline
    baseline = {}
    if baseline_path.exists():
        with open(baseline_path) as f:
            baseline = json.load(f)
    
    # Generate markdown report
    lines = [
        "## 🔬 RAG Evaluation Results",
        "",
        "### 📊 Metrics Summary",
        "",
        "| Metric | Current | Baseline | Change | Status |",
        "|--------|---------|----------|--------|--------|",
    ]
    
    for metric in ["ragas_score", "context_precision", "context_recall", "faithfulness", "answer_relevance"]:
        current_val = current.get(metric, {}).get("mean", 0.0)
        baseline_val = baseline.get(metric, {}).get("mean", 0.0) if baseline else 0.0
        
        change = current_val - baseline_val
        change_pct = (change / baseline_val * 100) if baseline_val > 0 else 0
        
        if change >= 0:
            status = "✅"
            change_str = f"+{change:.3f} (+{change_pct:.1f}%)"
        else:
            status = "⚠️"
            change_str = f"{change:.3f} ({change_pct:.1f}%)"
        
        lines.append(
            f"| {metric} | {current_val:.3f} | {baseline_val:.3f} | {change_str} | {status} |"
        )
    
    # Add latency info
    latency = current.get("latency_ms", {})
    lines.extend([
        "",
        "### ⚡ Latency Statistics",
        "",
        f"- **Mean:** {latency.get('mean', 0):.1f}ms",
        f"- **P50:** {latency.get('p50', 0):.1f}ms",
        f"- **P95:** {latency.get('p95', 0):.1f}ms",
        f"- **P99:** {latency.get('p99', 0):.1f}ms",
    ])
    
    # Add detailed breakdown
    lines.extend([
        "",
        "### 📈 Detailed Metrics",
        "",
        "```",
        json.dumps(current, indent=2),
        "```",
    ])
    
    report = "\n".join(lines)
    
    # Write to file
    with open(output_path, "w") as f:
        f.write(report)
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate comparison report")
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, default="baseline_metrics.json")
    parser.add_argument("--output", type=Path, default="report.md")
    
    args = parser.parse_args()
    
    report = generate_comparison_report(
        args.results_dir,
        args.baseline,
        args.output,
    )
    
    print(report)


if __name__ == "__main__":
    main()

"""
Quality Metrics & Reporting - Track AI Test Quality Over Time

This module demonstrates how to:
- Collect quality metrics from the evaluation pipeline
- Build dashboards for stakeholders
- Track before/after improvement
- Generate reports for leadership

Ping Identity Relevance:
- Job requires "measurable before-and-after impact"
- "Use data to improve SDLC effectiveness"
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


@dataclass
class DailyMetrics:
    """Metrics for a single day"""
    date: str
    total_tests: int
    accepted: int
    rejected: int
    needs_review: int
    avg_quality_score: float
    avg_processing_time_ms: int
    rejection_by_stage: Dict[str, int]
    
    @property
    def acceptance_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.accepted / self.total_tests * 100
    
    @property
    def rejection_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.rejected / self.total_tests * 100


class QualityMetricsCollector:
    """
    Collect and analyze quality metrics over time.
    
    Demonstrates how to prove "40% reduction in bad tests"
    with actual data.
    """
    
    def __init__(self):
        self.daily_metrics: List[DailyMetrics] = []
        self.test_history: List[Dict] = []
    
    def record_evaluation(self, result: Dict[str, Any]):
        """Record a single test evaluation"""
        self.test_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "test_id": result.get("test_id"),
            "status": result.get("status"),
            "quality_score": result.get("quality_score"),
            "recommendation": result.get("recommendation"),
            "processing_time_ms": result.get("processing_time_ms")
        })
    
    def aggregate_daily(self, date: Optional[str] = None) -> DailyMetrics:
        """Aggregate metrics for a specific day"""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Filter tests for this date
        day_tests = [
            t for t in self.test_history
            if t["timestamp"].startswith(date)
        ]
        
        if not day_tests:
            return DailyMetrics(
                date=date,
                total_tests=0,
                accepted=0,
                rejected=0,
                needs_review=0,
                avg_quality_score=0.0,
                avg_processing_time_ms=0,
                rejection_by_stage={}
            )
        
        # Calculate metrics
        total = len(day_tests)
        accepted = len([t for t in day_tests if t["status"] == "accepted"])
        rejected = len([t for t in day_tests if t["status"] == "rejected"])
        needs_review = len([t for t in day_tests if t["status"] == "needs_review"])
        
        scores = [t["quality_score"] for t in day_tests]
        avg_score = sum(scores) / len(scores)
        
        times = [t["processing_time_ms"] for t in day_tests]
        avg_time = int(sum(times) / len(times))
        
        return DailyMetrics(
            date=date,
            total_tests=total,
            accepted=accepted,
            rejected=rejected,
            needs_review=needs_review,
            avg_quality_score=avg_score,
            avg_processing_time_ms=avg_time,
            rejection_by_stage={}  # Simplified
        )
    
    def calculate_improvement(
        self,
        before_date: str,
        after_date: str
    ) -> Dict[str, Any]:
        """
        Calculate before/after improvement metrics.
        
        This is how you prove "40% reduction in bad tests"!
        """
        before = self.aggregate_daily(before_date)
        after = self.aggregate_daily(after_date)
        
        improvement = {
            "before_date": before_date,
            "after_date": after_date,
            "metrics": {
                "rejection_rate": {
                    "before": before.rejection_rate,
                    "after": after.rejection_rate,
                    "improvement_pct": (
                        (before.rejection_rate - after.rejection_rate) 
                        / before.rejection_rate * 100
                        if before.rejection_rate > 0 else 0
                    )
                },
                "acceptance_rate": {
                    "before": before.acceptance_rate,
                    "after": after.acceptance_rate,
                    "improvement_pct": (
                        (after.acceptance_rate - before.acceptance_rate)
                        / before.acceptance_rate * 100
                        if before.acceptance_rate > 0 else 0
                    )
                },
                "avg_quality_score": {
                    "before": before.avg_quality_score,
                    "after": after.avg_quality_score,
                    "improvement_pct": (
                        (after.avg_quality_score - before.avg_quality_score)
                        / before.avg_quality_score * 100
                        if before.avg_quality_score > 0 else 0
                    )
                }
            }
        }
        
        return improvement
    
    def generate_report(self, days: int = 30) -> str:
        """Generate a text report of quality metrics"""
        lines = []
        lines.append("=" * 70)
        lines.append("AI TEST QUALITY METRICS REPORT")
        lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("=" * 70)
        
        # Get last N days
        end_date = datetime.utcnow()
        metrics_by_day = []
        
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            metrics = self.aggregate_daily(date)
            if metrics.total_tests > 0:
                metrics_by_day.append(metrics)
        
        if not metrics_by_day:
            lines.append("\nNo data available for the specified period.")
            return "\n".join(lines)
        
        # Summary
        total_tests = sum(m.total_tests for m in metrics_by_day)
        total_accepted = sum(m.accepted for m in metrics_by_day)
        total_rejected = sum(m.rejected for m in metrics_by_day)
        
        lines.append(f"\n📊 SUMMARY (Last {len(metrics_by_day)} days with data)")
        lines.append("-" * 70)
        lines.append(f"Total Tests Evaluated: {total_tests}")
        lines.append(f"  ✅ Accepted: {total_accepted} ({total_accepted/total_tests*100:.1f}%)")
        lines.append(f"  ❌ Rejected: {total_rejected} ({total_rejected/total_tests*100:.1f}%)")
        lines.append(f"  ⚠️  Needs Review: {sum(m.needs_review for m in metrics_by_day)}")
        
        avg_score = sum(m.avg_quality_score for m in metrics_by_day) / len(metrics_by_day)
        lines.append(f"\n📈 Average Quality Score: {avg_score:.1f}/40")
        
        # Daily breakdown
        lines.append(f"\n📅 DAILY BREAKDOWN")
        lines.append("-" * 70)
        lines.append(f"{'Date':<12} {'Total':<8} {'Accept':<8} {'Reject':<8} {'Score':<8}")
        lines.append("-" * 70)
        
        for m in reversed(metrics_by_day):
            lines.append(
                f"{m.date:<12} {m.total_tests:<8} {m.accepted:<8} "
                f"{m.rejected:<8} {m.avg_quality_score:<8.1f}"
            )
        
        # Recommendations
        lines.append(f"\n💡 RECOMMENDATIONS")
        lines.append("-" * 70)
        
        recent = metrics_by_day[0]
        if recent.rejection_rate > 30:
            lines.append("⚠️  High rejection rate detected. Consider:")
            lines.append("   - Reviewing AI test generation prompts")
            lines.append("   - Improving training data quality")
            lines.append("   - Adjusting evaluation thresholds")
        
        if recent.avg_quality_score < 25:
            lines.append("⚠️  Low average quality score. Consider:")
            lines.append("   - Human review of borderline cases")
            lines.append("   - LLM judge prompt calibration")
        
        if recent.avg_quality_score > 32:
            lines.append("✅ Quality scores are good!")
            lines.append("   - Consider accepting more tests automatically")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
    
    def export_json(self, filepath: str):
        """Export metrics to JSON for dashboards"""
        data = {
            "generated_at": datetime.utcnow().isoformat(),
            "daily_metrics": [asdict(m) for m in self.daily_metrics],
            "summary": {
                "total_tests": len(self.test_history),
                "avg_quality_score": (
                    sum(t["quality_score"] for t in self.test_history) / len(self.test_history)
                    if self.test_history else 0
                )
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Metrics exported to {filepath}")


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class QualityDashboard:
    """
    Generate visualizations for quality metrics.
    
    Shows trends over time - critical for proving improvement!
    """
    
    def __init__(self, collector: QualityMetricsCollector):
        self.collector = collector
    
    def plot_quality_trend(self, days: int = 30, output_file: str = "quality_trend.png"):
        """Plot quality score trend over time"""
        dates = []
        scores = []
        
        end_date = datetime.utcnow()
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            metrics = self.collector.aggregate_daily(date)
            if metrics.total_tests > 0:
                dates.append(date)
                scores.append(metrics.avg_quality_score)
        
        if not dates:
            print("⚠️  No data to plot")
            return
        
        plt.figure(figsize=(12, 6))
        plt.plot(reversed(dates), reversed(scores), marker='o', linewidth=2)
        plt.axhline(y=32, color='g', linestyle='--', label='Accept Threshold')
        plt.axhline(y=28, color='r', linestyle='--', label='Reject Threshold')
        plt.xlabel('Date')
        plt.ylabel('Average Quality Score')
        plt.title('AI Test Quality Trend')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_file)
        print(f"✅ Quality trend plot saved to {output_file}")
    
    def plot_rejection_breakdown(self, output_file: str = "rejection_breakdown.png"):
        """Plot rejection reasons breakdown"""
        # Aggregate rejection by stage
        stage_counts = defaultdict(int)
        
        for test in self.collector.test_history:
            if test["status"] == "rejected":
                # Determine stage (simplified)
                if test["quality_score"] == 0:
                    stage_counts["Schema"] += 1
                elif test["quality_score"] < 28:
                    stage_counts["Semantic"] += 1
                else:
                    stage_counts["Execution"] += 1
        
        if not stage_counts:
            print("⚠️  No rejection data to plot")
            return
        
        plt.figure(figsize=(8, 8))
        plt.pie(
            stage_counts.values(),
            labels=stage_counts.keys(),
            autopct='%1.1f%%',
            startangle=90
        )
        plt.title('Test Rejections by Stage')
        plt.savefig(output_file)
        print(f"✅ Rejection breakdown plot saved to {output_file}")


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demonstrate quality metrics collection"""
    print("\n" + "="*70)
    print("QUALITY METRICS & REPORTING DEMO")
    print("="*70)
    
    collector = QualityMetricsCollector()
    
    # Simulate some test evaluations
    print("\n📊 Simulating test evaluations...")
    
    # Simulate "before" period - lower quality
    for i in range(20):
        collector.record_evaluation({
            "test_id": f"before-{i}",
            "status": "accepted" if i < 10 else "rejected",
            "quality_score": 25 if i < 10 else 15,
            "processing_time_ms": 1500
        })
    
    # Simulate "after" period - higher quality (after pipeline implemented)
    for i in range(20):
        collector.record_evaluation({
            "test_id": f"after-{i}",
            "status": "accepted" if i < 16 else "rejected",
            "quality_score": 33 if i < 16 else 20,
            "processing_time_ms": 1200
        })
    
    # Generate report
    print("\n" + collector.generate_report())
    
    # Calculate improvement
    print("\n📈 BEFORE/AFTER COMPARISON")
    print("-" * 70)
    
    # Simulate dates
    today = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    improvement = collector.calculate_improvement(yesterday, today)
    
    print(f"Comparing: {improvement['before_date']} → {improvement['after_date']}")
    print()
    
    for metric, values in improvement['metrics'].items():
        print(f"{metric.replace('_', ' ').title()}:")
        print(f"  Before: {values['before']:.1f}")
        print(f"  After:  {values['after']:.1f}")
        print(f"  Improvement: {values['improvement_pct']:+.1f}%")
        print()
    
    print("="*70)
    print("INTERVIEW GOLD:")
    print("  'I built a metrics pipeline that tracked our 40% reduction")
    print("   in bad tests, with automated reports showing quality trends")
    print("   to engineering leadership.'")
    print("="*70)


if __name__ == "__main__":
    demo()

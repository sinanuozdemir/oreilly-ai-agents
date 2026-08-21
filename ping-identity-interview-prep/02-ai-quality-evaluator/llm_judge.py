"""
LLM-as-Judge - Semantic Evaluation of AI-Generated Tests

This module implements the LLM-as-Judge pattern for evaluating
the semantic quality of AI-generated tests.

Key Concepts:
- Use an LLM to evaluate another LLM's output
- Calibrated scoring rubric (0-10 per dimension)
- Consistent, scalable evaluation
- Explainable results
"""

import json
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class EvaluationVerdict(Enum):
    """Final verdict for test evaluation"""
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    NEEDS_IMPROVEMENT = "NEEDS_IMPROVEMENT"


@dataclass
class QualityScores:
    """Quality scores across dimensions"""
    coverage: int
    assertions: int
    edge_cases: int
    maintainability: int
    
    @property
    def total(self) -> int:
        return self.coverage + self.assertions + self.edge_cases + self.maintainability


@dataclass
class EvaluationResult:
    """Complete evaluation result"""
    scores: QualityScores
    verdict: EvaluationVerdict
    reasoning: str
    confidence: float
    suggestions: List[str]


class LLMJudge:
    """
    LLM-as-Judge implementation for test quality evaluation.
    
    In production, this would call OpenAI/Anthropic API.
    For learning, we simulate with rule-based evaluation.
    """
    
    # Scoring thresholds
    REJECT_THRESHOLD = 28  # Out of 40
    ACCEPT_THRESHOLD = 32  # Out of 40
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.evaluation_history: List[Dict] = []
    
    def evaluate(self, test_code: str) -> EvaluationResult:
        """
        Evaluate test code quality using LLM-as-judge.
        
        Returns structured evaluation with scores and reasoning.
        """
        # In production: Call OpenAI/Anthropic API with prompt
        # For demo: Simulate with rule-based scoring
        
        scores = self._calculate_scores(test_code)
        verdict = self._determine_verdict(scores)
        reasoning = self._generate_reasoning(test_code, scores)
        suggestions = self._generate_suggestions(test_code, scores)
        
        result = EvaluationResult(
            scores=scores,
            verdict=verdict,
            reasoning=reasoning,
            confidence=0.85,  # Simulated confidence
            suggestions=suggestions
        )
        
        # Track history
        self.evaluation_history.append({
            "test_code_sample": test_code[:200],
            "scores": {
                "coverage": scores.coverage,
                "assertions": scores.assertions,
                "edge_cases": scores.edge_cases,
                "maintainability": scores.maintainability,
                "total": scores.total
            },
            "verdict": verdict.value
        })
        
        return result
    
    def _calculate_scores(self, test_code: str) -> QualityScores:
        """
        Calculate quality scores (0-10 per dimension).
        
        In production, this uses actual LLM evaluation.
        """
        # Coverage scoring (0-10)
        coverage = self._score_coverage(test_code)
        
        # Assertions scoring (0-10)
        assertions = self._score_assertions(test_code)
        
        # Edge cases scoring (0-10)
        edge_cases = self._score_edge_cases(test_code)
        
        # Maintainability scoring (0-10)
        maintainability = self._score_maintainability(test_code)
        
        return QualityScores(
            coverage=coverage,
            assertions=assertions,
            edge_cases=edge_cases,
            maintainability=maintainability
        )
    
    def _score_coverage(self, test_code: str) -> int:
        """Score test coverage quality (0-10)"""
        score = 5  # Baseline
        
        # Bonus: Multiple test methods
        test_count = len(re.findall(r'def test_', test_code))
        if test_count >= 3:
            score += 2
        elif test_count >= 2:
            score += 1
        
        # Bonus: Tests error cases
        if any(kw in test_code.lower() for kw in ['error', 'exception', 'invalid', 'fail']):
            score += 2
        
        # Bonus: Tests edge cases
        if any(kw in test_code.lower() for kw in ['none', 'null', 'empty', 'boundary']):
            score += 1
        
        return min(score, 10)
    
    def _score_assertions(self, test_code: str) -> int:
        """Score assertion quality (0-10)"""
        score = 5  # Baseline
        
        # Count assertions
        assert_patterns = [
            r'assertEqual', r'assert_equals',
            r'assertTrue', r'assert_true',
            r'assertFalse', r'assert_false',
            r'assertIn', r'assert_in',
            r'assertIsNotNone', r'assert_is_not_none',
            r'assertRaises', r'assert_raises'
        ]
        
        assertion_count = sum(
            len(re.findall(pattern, test_code))
            for pattern in assert_patterns
        )
        
        if assertion_count >= 3:
            score += 3
        elif assertion_count >= 2:
            score += 2
        elif assertion_count >= 1:
            score += 1
        else:
            score -= 3  # Penalty for no assertions
        
        # Bonus: Specific assertions (not just assertTrue)
        specific_assertions = len(re.findall(
            r'assertEqual|assertIn|assertIsNotNone|assertRaises',
            test_code
        ))
        if specific_assertions > 0:
            score += 2
        
        return min(max(score, 0), 10)
    
    def _score_edge_cases(self, test_code: str) -> int:
        """Score edge case coverage (0-10)"""
        score = 3  # Lower baseline - edge cases are often missed
        
        # Check for edge case patterns
        edge_patterns = {
            'none_null': ['None', 'null', 'nil'],
            'empty': ['empty', '""', "''", '[]', '{}'],
            'boundary': ['min', 'max', 'limit', 'boundary'],
            'invalid': ['invalid', 'malformed', 'corrupt'],
            'concurrent': ['thread', 'async', 'concurrent', 'race']
        }
        
        for category, patterns in edge_patterns.items():
            if any(p in test_code for p in patterns):
                score += 1
        
        # Bonus: Parameterized tests (test many values)
        if '@pytest.mark.parametrize' in test_code or 'test cases' in test_code.lower():
            score += 2
        
        return min(score, 10)
    
    def _score_maintainability(self, test_code: str) -> int:
        """Score code maintainability (0-10)"""
        score = 5  # Baseline
        
        # Bonus: Has docstrings
        if '"""' in test_code or "'''" in test_code:
            score += 2
        
        # Bonus: Uses setUp/tearDown
        if 'setUp' in test_code or 'set_up' in test_code.lower():
            score += 1
        
        # Bonus: Clear variable names
        if re.search(r'self\.assert.*response', test_code):
            score += 1  # Using descriptive names like 'response'
        
        # Penalty: Too long
        lines = len(test_code.split('\n'))
        if lines > 50:
            score -= 1
        if lines > 100:
            score -= 2
        
        # Penalty: Hardcoded values without context
        if re.search(r'assertEqual\([^,]+, \d+\)', test_code):
            # Magic numbers without explanation
            score -= 1
        
        return min(max(score, 0), 10)
    
    def _determine_verdict(self, scores: QualityScores) -> EvaluationVerdict:
        """Determine final verdict based on total score"""
        total = scores.total
        
        if total < self.REJECT_THRESHOLD:
            return EvaluationVerdict.REJECT
        elif total >= self.ACCEPT_THRESHOLD:
            return EvaluationVerdict.ACCEPT
        else:
            return EvaluationVerdict.NEEDS_IMPROVEMENT
    
    def _generate_reasoning(self, test_code: str, scores: QualityScores) -> str:
        """Generate human-readable reasoning"""
        points = []
        
        # Coverage feedback
        if scores.coverage >= 7:
            points.append("Good functional coverage with multiple test scenarios.")
        elif scores.coverage <= 4:
            points.append("Limited coverage - consider adding more test cases.")
        
        # Assertions feedback
        if scores.assertions >= 7:
            points.append("Strong assertions validate expected behavior.")
        elif scores.assertions <= 4:
            points.append("Weak assertions - may give false confidence.")
        
        # Edge cases feedback
        if scores.edge_cases >= 7:
            points.append("Comprehensive edge case testing.")
        elif scores.edge_cases <= 3:
            points.append("Missing edge case coverage - add tests for None, empty, boundary values.")
        
        # Maintainability feedback
        if scores.maintainability >= 7:
            points.append("Clean, readable test code.")
        elif scores.maintainability <= 4:
            points.append("Code could be improved for readability and maintainability.")
        
        return " ".join(points)
    
    def _generate_suggestions(self, test_code: str, scores: QualityScores) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if scores.coverage < 7:
            suggestions.append("Add tests for error cases and invalid inputs")
            suggestions.append("Test both success and failure paths")
        
        if scores.assertions < 7:
            suggestions.append("Use specific assertions (assertEqual, assertIn) instead of assertTrue")
            suggestions.append("Validate response structure, not just status codes")
        
        if scores.edge_cases < 5:
            suggestions.append("Add tests for None/empty inputs")
            suggestions.append("Test boundary values (min, max limits)")
        
        if scores.maintainability < 7:
            suggestions.append("Add docstrings explaining test purpose")
            suggestions.append("Use descriptive variable names")
        
        return suggestions[:3]  # Top 3 suggestions
    
    def get_calibration_report(self) -> Dict[str, Any]:
        """Get report for human calibration"""
        if not self.evaluation_history:
            return {"message": "No evaluations yet"}
        
        total = len(self.evaluation_history)
        accepts = len([e for e in self.evaluation_history if e["verdict"] == "ACCEPT"])
        rejects = len([e for e in self.evaluation_history if e["verdict"] == "REJECT"])
        
        avg_score = sum(e["scores"]["total"] for e in self.evaluation_history) / total
        
        return {
            "total_evaluated": total,
            "accept_rate": accepts / total * 100,
            "reject_rate": rejects / total * 100,
            "avg_total_score": avg_score,
            "recommendation": "Calibration looks good" if 25 <= avg_score <= 32 else "Consider adjusting thresholds"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Demonstrate LLM-as-Judge evaluation"""
    print("\n" + "="*70)
    print("LLM-as-JUDGE - SEMANTIC EVALUATION DEMO")
    print("="*70)
    
    judge = LLMJudge()
    
    # Example 1: Good test
    good_test = '''
import unittest
import requests

class TestUserAPI(unittest.TestCase):
    """Test user management API"""
    
    def setUp(self):
        self.base_url = "https://api.example.com"
        self.headers = {"Authorization": "Bearer test-token"}
    
    def test_create_user_success(self):
        """Test successful user creation"""
        response = requests.post(
            f"{self.base_url}/users",
            json={"email": "test@example.com", "name": "Test"},
            headers=self.headers
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["email"], "test@example.com")
        self.assertIn("id", data)
        self.assertIsNotNone(data["id"])
    
    def test_create_user_invalid_email(self):
        """Test user creation with invalid email fails"""
        response = requests.post(
            f"{self.base_url}/users",
            json={"email": "not-an-email", "name": "Test"},
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
    
    def test_create_user_duplicate_email(self):
        """Test duplicate email returns conflict"""
        # Create first user
        requests.post(
            f"{self.base_url}/users",
            json={"email": "dup@example.com", "name": "First"},
            headers=self.headers
        )
        # Try duplicate
        response = requests.post(
            f"{self.base_url}/users",
            json={"email": "dup@example.com", "name": "Second"},
            headers=self.headers
        )
        self.assertEqual(response.status_code, 409)
'''
    
    print("\n📋 EVALUATING: Good Test (well-structured, comprehensive)")
    print("-" * 70)
    result = judge.evaluate(good_test)
    
    print(f"Verdict: {result.verdict.value}")
    print(f"Total Score: {result.scores.total}/40")
    print(f"\nBreakdown:")
    print(f"  Coverage:        {result.scores.coverage}/10")
    print(f"  Assertions:      {result.scores.assertions}/10")
    print(f"  Edge Cases:      {result.scores.edge_cases}/10")
    print(f"  Maintainability: {result.scores.maintainability}/10")
    print(f"\nReasoning: {result.reasoning}")
    if result.suggestions:
        print(f"\nSuggestions:")
        for s in result.suggestions:
            print(f"  • {s}")
    
    # Example 2: Bad test
    bad_test = '''
import unittest

class TestAPI(unittest.TestCase):
    def test_api(self):
        response = requests.get("/api/users")
        self.assertEqual(response.status_code, 200)
'''
    
    print("\n" + "="*70)
    print("\n📋 EVALUATING: Bad Test (minimal, weak assertions)")
    print("-" * 70)
    result2 = judge.evaluate(bad_test)
    
    print(f"Verdict: {result2.verdict.value}")
    print(f"Total Score: {result2.scores.total}/40")
    print(f"\nBreakdown:")
    print(f"  Coverage:        {result2.scores.coverage}/10")
    print(f"  Assertions:      {result2.scores.assertions}/10")
    print(f"  Edge Cases:      {result2.scores.edge_cases}/10")
    print(f"  Maintainability: {result2.scores.maintainability}/10")
    print(f"\nReasoning: {result2.reasoning}")
    if result2.suggestions:
        print(f"\nSuggestions:")
        for s in result2.suggestions:
            print(f"  • {s}")
    
    # Calibration report
    print("\n" + "="*70)
    print("\n📊 CALIBRATION REPORT")
    print("-" * 70)
    report = judge.get_calibration_report()
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    
    print("\n🎓 Key Takeaways:")
    print("  ✅ LLM-as-judge provides consistent, scalable evaluation")
    print("  ✅ Four dimensions: coverage, assertions, edge cases, maintainability")
    print("  ✅ Thresholds: REJECT <28, NEEDS_IMPROVEMENT 28-31, ACCEPT ≥32")
    print("  ✅ Results include actionable suggestions for improvement")


if __name__ == "__main__":
    demo()

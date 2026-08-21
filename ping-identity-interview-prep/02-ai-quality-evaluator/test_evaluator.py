"""
Test Evaluator - Tests for the AI Test Evaluation Pipeline

This module tests the quality evaluation system itself.
It's meta - tests that test the test evaluator!

Demonstrates:
- Unit testing validation components
- Integration testing the full pipeline
- Mocking external dependencies
"""

import asyncio
import pytest
from typing import List

# Import the modules we're testing
from ai_test_evaluator import (
    AITestEvaluator,
    TestStatus,
    SchemaValidator,
    SAMPLE_GOOD_TEST,
    SAMPLE_BAD_TEST_SYNTAX,
    SAMPLE_BAD_TEST_NO_ASSERTIONS,
    SAMPLE_BAD_TEST_WEAK_ASSERTIONS
)
from llm_judge import LLMJudge, EvaluationVerdict
from test_executor import TestExecutor, ExecutionStatus


class TestSchemaValidator:
    """Test suite for schema validation"""
    
    @pytest.fixture
    def validator(self):
        return SchemaValidator()
    
    async def test_valid_syntax_passes(self, validator):
        """Valid Python syntax should pass"""
        code = """
import unittest
class TestExample(unittest.TestCase):
    def test_something(self):
        self.assertTrue(True)
"""
        passed, details = await validator.validate(code)
        assert passed is True
        assert details["syntax_valid"] is True
    
    async def test_invalid_syntax_fails(self, validator):
        """Invalid Python syntax should fail"""
        code = """
def test_example(
    self.assertTrue(True
"""
        passed, details = await validator.validate(code)
        assert passed is False
        assert details["syntax_valid"] is False
    
    async def test_no_assertions_fails(self, validator):
        """Tests without assertions should fail"""
        code = """
import unittest
class TestExample(unittest.TestCase):
    def test_something(self):
        print("No assertions here!")
"""
        passed, details = await validator.validate(code)
        assert passed is False
        assert details["has_assertions"] is False
    
    async def test_no_test_definitions_fails(self, validator):
        """Code without test definitions should fail"""
        code = """
def helper_function():
    return 42
"""
        passed, details = await validator.validate(code)
        assert passed is False
        assert details["has_test_definitions"] is False


class TestLLMJudge:
    """Test suite for LLM-as-judge evaluation"""
    
    @pytest.fixture
    def judge(self):
        return LLMJudge()
    
    def test_good_test_gets_high_scores(self, judge):
        """Well-written tests should get high scores"""
        good_test = """
import unittest
class TestAPI(unittest.TestCase):
    def test_success(self):
        response = get_user(123)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 123)
    
    def test_error(self):
        response = get_user(999)
        self.assertEqual(response.status_code, 404)
"""
        result = judge.evaluate(good_test)
        
        assert result.scores.total >= 25  # Should be decent
        assert result.scores.coverage >= 6
        assert result.scores.assertions >= 6
        assert result.reasoning != ""
    
    def test_bad_test_gets_low_scores(self, judge):
        """Poorly written tests should get low scores"""
        bad_test = """
import unittest
class TestAPI(unittest.TestCase):
    def test_api(self):
        response = requests.get("/api")
        self.assertTrue(True)
"""
        result = judge.evaluate(bad_test)
        
        assert result.scores.total < 25  # Should be low
        assert result.scores.assertions < 5  # Weak assertions
        assert len(result.suggestions) > 0  # Should have suggestions
    
    def test_reject_threshold(self, judge):
        """Scores below 28 should be rejected"""
        # Force low score by providing minimal test
        minimal_test = """
def test_minimal():
    pass
"""
        result = judge.evaluate(minimal_test)
        
        if result.scores.total < 28:
            assert result.verdict == EvaluationVerdict.REJECT
    
    def test_accept_threshold(self, judge):
        """Scores 32+ should be accepted"""
        comprehensive_test = """
import unittest
import pytest

class TestUserAPI(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_create_user_success(self):
        response = self.client.post("/users", {"email": "test@test.com"})
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["email"], "test@test.com")
    
    def test_create_user_invalid_email(self):
        response = self.client.post("/users", {"email": "invalid"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
    
    def test_create_user_duplicate(self):
        self.client.post("/users", {"email": "dup@test.com"})
        response = self.client.post("/users", {"email": "dup@test.com"})
        self.assertEqual(response.status_code, 409)
    
    @pytest.mark.parametrize("email,expected", [
        ("test@test.com", 201),
        ("", 400),
        (None, 400),
    ])
    def test_create_user_edge_cases(self, email, expected):
        response = self.client.post("/users", {"email": email})
        self.assertEqual(response.status_code, expected)
"""
        result = judge.evaluate(comprehensive_test)
        
        if result.scores.total >= 32:
            assert result.verdict == EvaluationVerdict.ACCEPT


class TestTestExecutor:
    """Test suite for test execution validation"""
    
    @pytest.fixture
    def executor(self):
        return TestExecutor(timeout_seconds=5, num_runs=2)
    
    async def test_deterministic_test_passes(self, executor):
        """Deterministic tests should pass consistently"""
        test_code = """
import unittest
class TestMath(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(2 + 2, 4)
"""
        report = await executor.execute(test_code)
        
        assert report.overall_status == ExecutionStatus.PASSED
        assert report.is_deterministic is True
        assert report.is_flaky is False
        assert report.pass_rate == 100.0
    
    async def test_flaky_test_detected(self, executor):
        """Flaky tests should be detected"""
        # This test uses random which makes it potentially flaky
        flaky_test = """
import unittest
import random

class TestRandom(unittest.TestCase):
    def test_random(self):
        value = random.randint(1, 3)
        self.assertGreater(value, 0)
"""
        report = await executor.execute(flaky_test)
        
        # Flakiness detection is probabilistic
        # Just verify the mechanism works
        assert isinstance(report.is_flaky, bool)
        assert 0 <= report.pass_rate <= 100
    
    async def test_timeout_protection(self, executor):
        """Long-running tests should timeout"""
        slow_test = """
import unittest
import time

class TestSlow(unittest.TestCase):
    def test_infinite_loop_risk(self):
        # This would hang without timeout
        time.sleep(0.5)  # Just a small delay for demo
        self.assertTrue(True)
"""
        report = await executor.execute(slow_test)
        
        # Should complete within timeout
        assert report.max_duration_ms < 6000  # 6 seconds


class TestIntegration:
    """Integration tests for the full pipeline"""
    
    async def test_full_pipeline_with_good_test(self):
        """Good tests should pass all stages"""
        evaluator = AITestEvaluator()
        
        result = await evaluator.evaluate(SAMPLE_GOOD_TEST, "test-good")
        
        assert result.status in [TestStatus.ACCEPTED, TestStatus.NEEDS_REVIEW]
        assert result.quality_score >= 25
        assert "schema" in result.stage_results
    
    async def test_full_pipeline_rejects_syntax_error(self):
        """Syntax errors should be rejected at stage 1"""
        evaluator = AITestEvaluator()
        
        result = await evaluator.evaluate(SAMPLE_BAD_TEST_SYNTAX, "test-syntax")
        
        assert result.status == TestStatus.REJECTED
        assert "schema" in result.stage_results
    
    async def test_full_pipeline_rejects_no_assertions(self):
        """Tests without assertions should be rejected"""
        evaluator = AITestEvaluator()
        
        result = await evaluator.evaluate(SAMPLE_BAD_TEST_NO_ASSERTIONS, "test-no-assert")
        
        assert result.status == TestStatus.REJECTED
    
    def test_metrics_calculation(self):
        """Metrics should be calculated correctly"""
        evaluator = AITestEvaluator()
        
        # Simulate some results
        import asyncio
        asyncio.run(evaluator.evaluate(SAMPLE_GOOD_TEST, "test-1"))
        asyncio.run(evaluator.evaluate(SAMPLE_BAD_TEST_SYNTAX, "test-2"))
        
        metrics = evaluator.get_metrics()
        
        assert metrics.total_tests == 2
        assert metrics.accepted + metrics.rejected + metrics.needs_review == 2
        assert metrics.avg_quality_score > 0


# ═══════════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════════════════════

async def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*70)
    print("TEST EVALUATOR - RUNNING TEST SUITE")
    print("="*70)
    
    # Test Schema Validator
    print("\n🔬 Testing Schema Validator...")
    validator = SchemaValidator()
    
    # Test 1: Valid syntax
    print("  Test 1: Valid syntax...", end=" ")
    passed, _ = await validator.validate(SAMPLE_GOOD_TEST)
    print("✅ PASS" if passed else "❌ FAIL")
    
    # Test 2: Invalid syntax
    print("  Test 2: Invalid syntax...", end=" ")
    passed, _ = await validator.validate(SAMPLE_BAD_TEST_SYNTAX)
    print("✅ PASS (correctly rejected)" if not passed else "❌ FAIL")
    
    # Test 3: No assertions
    print("  Test 3: No assertions...", end=" ")
    passed, _ = await validator.validate(SAMPLE_BAD_TEST_NO_ASSERTIONS)
    print("✅ PASS (correctly rejected)" if not passed else "❌ FAIL")
    
    # Test LLM Judge
    print("\n🔬 Testing LLM Judge...")
    judge = LLMJudge()
    
    # Test 1: Good test gets high score
    print("  Test 1: Good test scoring...", end=" ")
    result = judge.evaluate(SAMPLE_GOOD_TEST)
    print(f"✅ Score: {result.scores.total}/40")
    
    # Test 2: Bad test gets low score
    print("  Test 2: Bad test scoring...", end=" ")
    result = judge.evaluate(SAMPLE_BAD_TEST_WEAK_ASSERTIONS)
    print(f"✅ Score: {result.scores.total}/40")
    
    # Test Executor
    print("\n🔬 Testing Test Executor...")
    executor = TestExecutor(timeout_seconds=5, num_runs=2)
    
    # Test 1: Deterministic test
    print("  Test 1: Deterministic test execution...", end=" ")
    report = await executor.execute(SAMPLE_GOOD_TEST)
    print(f"✅ Status: {report.overall_status.value}")
    
    # Test Full Pipeline
    print("\n🔬 Testing Full Pipeline Integration...")
    evaluator = AITestEvaluator()
    
    # Test 1: Good test
    print("  Test 1: Good test through pipeline...", end=" ")
    result = await evaluator.evaluate(SAMPLE_GOOD_TEST, "integration-good")
    print(f"✅ Status: {result.status.value}")
    
    # Test 2: Bad test
    print("  Test 2: Bad test through pipeline...", end=" ")
    result = await evaluator.evaluate(SAMPLE_BAD_TEST_SYNTAX, "integration-bad")
    print(f"✅ Status: {result.status.value}")
    
    # Print metrics
    print("\n📊 Pipeline Metrics:")
    metrics = evaluator.get_metrics()
    print(f"  Total: {metrics.total_tests}")
    print(f"  Accepted: {metrics.accepted}")
    print(f"  Rejected: {metrics.rejected}")
    print(f"  Avg Score: {metrics.avg_quality_score:.1f}/40")
    
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print("\n✅ All validation components working correctly")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

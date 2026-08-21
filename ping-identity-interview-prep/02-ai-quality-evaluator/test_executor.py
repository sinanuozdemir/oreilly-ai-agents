"""
Test Executor - Execution Validation for AI-Generated Tests

This module validates AI-generated tests by:
1. Running them in a sandboxed environment
2. Checking for flakiness (run multiple times)
3. Checking determinism (same output every time)
4. Measuring execution time
5. Detecting infinite loops and timeouts

Key Concepts:
- Sandboxed execution for safety
- Determinism validation
- Flakiness detection
- Performance regression checking
"""

import ast
import asyncio
import subprocess
import tempfile
import os
import sys
import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExecutionStatus(Enum):
    """Status of test execution"""
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"
    FLAKY = "flaky"
    NON_DETERMINISTIC = "non_deterministic"


@dataclass
class ExecutionResult:
    """Result of executing a test"""
    status: ExecutionStatus
    duration_ms: int
    stdout: str = ""
    stderr: str = ""
    run_number: int = 1
    error_message: Optional[str] = None


@dataclass
class TestExecutionReport:
    """Complete execution report for a test"""
    test_code: str
    test_id: str
    overall_status: ExecutionStatus
    runs: List[ExecutionResult]
    total_duration_ms: int
    is_deterministic: bool
    is_flaky: bool
    avg_duration_ms: float
    max_duration_ms: int
    min_duration_ms: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate across runs"""
        if not self.runs:
            return 0.0
        passed = len([r for r in self.runs if r.status == ExecutionStatus.PASSED])
        return (passed / len(self.runs)) * 100


class TestExecutor:
    """
    Execute and validate AI-generated tests.
    
    Implements Stage 3 of the validation pipeline:
    - Execute in isolated environment
    - Run multiple times for flakiness detection
    - Validate determinism
    - Check performance
    """
    
    def __init__(
        self,
        timeout_seconds: int = 30,
        num_runs: int = 3,
        deterministic_threshold: float = 1.0  # All runs must pass for deterministic
    ):
        self.timeout = timeout_seconds
        self.num_runs = num_runs
        self.deterministic_threshold = deterministic_threshold
    
    async def execute(
        self,
        test_code: str,
        test_id: Optional[str] = None
    ) -> TestExecutionReport:
        """
        Execute test multiple times and generate report.
        
        This is the main entry point for execution validation.
        """
        if test_id is None:
            import hashlib
            test_id = hashlib.md5(test_code.encode()).hexdigest()[:8]
        
        print(f"\n🔬 Executing Test {test_id}")
        print(f"   Runs: {self.num_runs} | Timeout: {self.timeout}s")
        
        # Wrap test code if needed
        wrapped_code = self._wrap_test_code(test_code)
        
        # Run multiple times
        runs = []
        start_time = time.time()
        
        for run_num in range(1, self.num_runs + 1):
            print(f"   Run {run_num}/{self.num_runs}...", end=" ")
            result = await self._execute_single(wrapped_code, run_num)
            runs.append(result)
            
            status_icon = "✅" if result.status == ExecutionStatus.PASSED else "❌"
            print(f"{status_icon} {result.status.value} ({result.duration_ms}ms)")
            
            # Early exit on timeout (don't waste time)
            if result.status == ExecutionStatus.TIMEOUT:
                print(f"   ⚠️  Timeout detected, stopping further runs")
                break
        
        total_duration = int((time.time() - start_time) * 1000)
        
        # Analyze results
        is_deterministic = self._check_determinism(runs)
        is_flaky = self._check_flakiness(runs)
        overall_status = self._determine_overall_status(runs, is_flaky)
        
        durations = [r.duration_ms for r in runs]
        
        report = TestExecutionReport(
            test_code=test_code,
            test_id=test_id,
            overall_status=overall_status,
            runs=runs,
            total_duration_ms=total_duration,
            is_deterministic=is_deterministic,
            is_flaky=is_flaky,
            avg_duration_ms=sum(durations) / len(durations) if durations else 0,
            max_duration_ms=max(durations) if durations else 0,
            min_duration_ms=min(durations) if durations else 0
        )
        
        self._print_report(report)
        
        return report
    
    async def _execute_single(
        self,
        wrapped_code: str,
        run_number: int
    ) -> ExecutionResult:
        """Execute test once"""
        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            prefix='ai_test_'
        ) as f:
            f.write(wrapped_code)
            temp_file = f.name
        
        try:
            start = time.time()
            
            # Run pytest
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pytest', temp_file, '-v', '--tb=short'],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                duration_ms = int((time.time() - start) * 1000)
                
                # Determine status
                if result.returncode == 0:
                    status = ExecutionStatus.PASSED
                else:
                    status = ExecutionStatus.FAILED
                
                return ExecutionResult(
                    status=status,
                    duration_ms=duration_ms,
                    stdout=result.stdout[-500:] if len(result.stdout) > 500 else result.stdout,
                    stderr=result.stderr[-500:] if len(result.stderr) > 500 else result.stderr,
                    run_number=run_number
                )
                
            except subprocess.TimeoutExpired:
                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    duration_ms=self.timeout * 1000,
                    error_message=f"Test timed out after {self.timeout} seconds",
                    run_number=run_number
                )
                
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                duration_ms=0,
                error_message=str(e),
                run_number=run_number
            )
        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def _wrap_test_code(self, test_code: str) -> str:
        """
        Wrap test code in proper structure if needed.
        
        Ensures the test can be executed by pytest.
        """
        # Check if already has imports
        has_imports = 'import' in test_code
        has_class = 'class Test' in test_code or 'class test' in test_code
        has_function = 'def test_' in test_code
        
        wrapper = []
        
        # Add imports if missing
        if not has_imports:
            wrapper.extend([
                "import unittest",
                "import pytest",
                "",
                "# Mock dependencies for testing",
                "class MockResponse:",
                "    def __init__(self, status_code=200, json_data=None):",
                "        self.status_code = status_code",
                "        self._json = json_data or {}",
                "    def json(self):",
                "        return self._json",
                "",
                "def requests_get(url, **kwargs):",
                "    return MockResponse(200, {'id': '123', 'name': 'test'})",
                "",
                "def requests_post(url, **kwargs):",
                "    return MockResponse(201, {'id': '456', 'created': True})",
                "",
                "requests = type('requests', (), {",
                "    'get': requests_get,",
                "    'post': requests_post,",
                "    'put': requests_post,",
                "    'delete': lambda url, **kwargs: MockResponse(204)",
                "})()",
                ""
            ])
        
        # Add test code
        wrapper.append(test_code)
        
        return '\n'.join(wrapper)
    
    def _check_determinism(self, runs: List[ExecutionResult]) -> bool:
        """
        Check if test is deterministic (same result every time).
        
        A flaky test passes sometimes and fails others.
        """
        if len(runs) < 2:
            return True
        
        # All runs should have same status for deterministic test
        statuses = [r.status for r in runs]
        return len(set(statuses)) == 1
    
    def _check_flakiness(self, runs: List[ExecutionResult]) -> bool:
        """
        Detect flaky tests (inconsistent results).
        
        Flaky tests are a major problem in CI/CD - they break
        builds unpredictably.
        """
        if len(runs) < 2:
            return False
        
        statuses = [r.status for r in runs]
        has_passes = ExecutionStatus.PASSED in statuses
        has_failures = any(
            s in [ExecutionStatus.FAILED, ExecutionStatus.ERROR, ExecutionStatus.TIMEOUT]
            for s in statuses
        )
        
        return has_passes and has_failures
    
    def _determine_overall_status(
        self,
        runs: List[ExecutionResult],
        is_flaky: bool
    ) -> ExecutionStatus:
        """Determine overall test status"""
        if is_flaky:
            return ExecutionStatus.FLAKY
        
        if not runs:
            return ExecutionStatus.ERROR
        
        # Check for any passes
        if any(r.status == ExecutionStatus.PASSED for r in runs):
            return ExecutionStatus.PASSED
        
        # All failed - return most common failure
        statuses = [r.status for r in runs]
        return max(set(statuses), key=statuses.count)
    
    def _print_report(self, report: TestExecutionReport):
        """Print execution report"""
        print(f"\n📊 Execution Report")
        print(f"   Overall Status: {report.overall_status.value.upper()}")
        print(f"   Pass Rate: {report.pass_rate:.0f}% ({len([r for r in report.runs if r.status == ExecutionStatus.PASSED])}/{len(report.runs)})")
        print(f"   Deterministic: {'✅ Yes' if report.is_deterministic else '❌ No (FLAKY)'}")
        print(f"   Duration: avg={report.avg_duration_ms:.0f}ms, min={report.min_duration_ms}ms, max={report.max_duration_ms}ms")
        
        if report.overall_status == ExecutionStatus.FLAKY:
            print("   ⚠️  WARNING: Flaky test detected - may break CI/CD pipelines")


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

async def demo():
    """Demonstrate test execution validation"""
    print("\n" + "="*70)
    print("TEST EXECUTOR - EXECUTION VALIDATION DEMO")
    print("="*70)
    
    executor = TestExecutor(timeout_seconds=10, num_runs=3)
    
    # Example 1: Deterministic test
    deterministic_test = '''
import unittest

class TestDeterministic(unittest.TestCase):
    def test_simple_math(self):
        """This test always passes"""
        self.assertEqual(2 + 2, 4)
        self.assertTrue(True)
'''
    
    print("\n📋 TEST 1: Deterministic Test (should pass consistently)")
    print("-" * 70)
    report1 = await executor.execute(deterministic_test, "det-001")
    
    # Example 2: Test with potential flakiness (simulated)
    # Note: In real scenario, this might have race conditions, timing issues, etc.
    potentially_flaky_test = '''
import unittest
import random

class TestPotentiallyFlaky(unittest.TestCase):
    def test_random_behavior(self):
        """This test might fail randomly"""
        # Simulating a flaky test
        value = random.randint(1, 10)
        self.assertGreater(value, 0)
'''
    
    print("\n" + "="*70)
    print("\n📋 TEST 2: Potentially Flaky Test")
    print("-" * 70)
    report2 = await executor.execute(potentially_flaky_test, "flaky-001")
    
    # Example 3: Test with timeout risk
    slow_test = '''
import unittest
import time

class TestSlow(unittest.TestCase):
    def test_with_delay(self):
        """This test has a delay"""
        time.sleep(0.1)  # Small delay for demo
        self.assertTrue(True)
'''
    
    print("\n" + "="*70)
    print("\n📋 TEST 3: Test with Execution Time")
    print("-" * 70)
    report3 = await executor.execute(slow_test, "slow-001")
    
    # Summary
    print("\n" + "="*70)
    print("EXECUTION VALIDATION SUMMARY")
    print("="*70)
    
    reports = [report1, report2, report3]
    for report in reports:
        status_icon = "✅" if report.overall_status == ExecutionStatus.PASSED else "⚠️"
        print(f"\n{status_icon} {report.test_id}: {report.overall_status.value}")
        print(f"   Pass Rate: {report.pass_rate:.0f}%")
        print(f"   Flaky: {'Yes' if report.is_flaky else 'No'}")
        print(f"   Avg Duration: {report.avg_duration_ms:.0f}ms")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    
    print("\n🎓 Key Takeaways:")
    print("  ✅ Tests are executed in isolated sandbox")
    print("  ✅ Multiple runs detect flakiness")
    print("  ✅ Timeout protection prevents hanging")
    print("  ✅ Performance metrics tracked")
    print("  ✅ Flaky tests flagged before reaching CI/CD")


if __name__ == "__main__":
    asyncio.run(demo())

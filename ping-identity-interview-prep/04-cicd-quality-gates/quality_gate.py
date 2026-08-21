"""
Shift-Left Quality Gates - CI/CD Quality Transformation

This module implements the shift-left quality transformation
required for Ping Identity's AI-first SDLC:

1. Pre-commit Checks (<2 min)
2. Pre-PR Checks (<5 min)
3. Pre-merge Checks (<15 min)
4. Pre-prod Checks (<30 min)

Key Concepts:
- Fast feedback loops
- Risk-based validation
- AI-assisted quality checks
- Developer-owned quality
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class CheckStatus(Enum):
    """Status of a quality check"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GateLevel(Enum):
    """Quality gate levels"""
    PRE_COMMIT = "pre_commit"    # <2 min target
    PRE_PR = "pre_pr"            # <5 min target
    PRE_MERGE = "pre_merge"      # <15 min target
    PRE_PROD = "pre_prod"        # <30 min target


@dataclass
class QualityCheck:
    """Individual quality check"""
    name: str
    description: str
    status: CheckStatus = CheckStatus.PENDING
    duration_ms: int = 0
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityGateResult:
    """Result of running a quality gate"""
    gate_level: GateLevel
    passed: bool
    checks: List[QualityCheck]
    total_duration_ms: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage"""
        if not self.checks:
            return 0.0
        passed = len([c for c in self.checks if c.status == CheckStatus.PASSED])
        return (passed / len(self.checks)) * 100


# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY CHECK IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class QualityChecks:
    """
    Library of quality checks organized by gate level.
    
    Demonstrates the tiered validation approach:
    - Fast checks first (fail fast)
    - Expensive checks later
    - AI-specific checks integrated throughout
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # PRE-COMMIT CHECKS (<2 min target)
    # ═══════════════════════════════════════════════════════════════════════
    
    @staticmethod
    async def check_syntax(code: str) -> QualityCheck:
        """Validate Python syntax"""
        import ast
        
        start = time.time()
        check = QualityCheck(
            name="syntax_validation",
            description="Validate Python syntax"
        )
        
        try:
            ast.parse(code)
            check.status = CheckStatus.PASSED
        except SyntaxError as e:
            check.status = CheckStatus.FAILED
            check.error_message = str(e)
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    @staticmethod
    async def check_linting(code: str) -> QualityCheck:
        """Check code style and basic issues"""
        start = time.time()
        check = QualityCheck(
            name="linting",
            description="Code style and basic quality checks"
        )
        
        # Simulate linting
        issues = []
        
        # Check line length
        for i, line in enumerate(code.split('\n'), 1):
            if len(line) > 100:
                issues.append(f"Line {i}: Line too long ({len(line)} chars)")
        
        # Check for debug statements
        if 'print(' in code or 'debugger' in code:
            issues.append("Debug statements found")
        
        if issues:
            check.status = CheckStatus.FAILED
            check.error_message = "; ".join(issues)
            check.details = {"issues": issues}
        else:
            check.status = CheckStatus.PASSED
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    @staticmethod
    async def check_unit_tests(test_files: List[str]) -> QualityCheck:
        """Run unit tests"""
        start = time.time()
        check = QualityCheck(
            name="unit_tests",
            description="Run unit test suite"
        )
        
        # Simulate test execution
        # In production, this would actually run pytest
        await asyncio.sleep(0.5)  # Simulate test time
        
        check.status = CheckStatus.PASSED
        check.details = {
            "tests_run": 42,
            "tests_passed": 42,
            "coverage": 87.5
        }
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    @staticmethod
    async def check_ai_test_schema(ai_tests: List[str]) -> QualityCheck:
        """
        NEW: Validate AI-generated tests meet schema requirements.
        
        This is the key innovation for AI-first SDLC - validating
        AI-generated artifacts before they enter the codebase.
        """
        start = time.time()
        check = QualityCheck(
            name="ai_test_schema",
            description="Validate AI-generated test structure"
        )
        
        issues = []
        
        for test in ai_tests:
            # Check 1: Has test functions
            if 'def test_' not in test:
                issues.append("Test file missing test functions")
            
            # Check 2: Has assertions
            if 'assert' not in test:
                issues.append("Test file missing assertions")
            
            # Check 3: Valid Python
            try:
                import ast
                ast.parse(test)
            except SyntaxError as e:
                issues.append(f"Syntax error: {e}")
        
        if issues:
            check.status = CheckStatus.FAILED
            check.error_message = f"AI test validation failed: {issues[:3]}"
            check.details = {"failed_tests": len(issues)}
        else:
            check.status = CheckStatus.PASSED
            check.details = {"ai_tests_validated": len(ai_tests)}
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    # ═══════════════════════════════════════════════════════════════════════
    # PRE-PR CHECKS (<5 min target)
    # ═══════════════════════════════════════════════════════════════════════
    
    @staticmethod
    async def check_integration_tests() -> QualityCheck:
        """Run integration tests"""
        start = time.time()
        check = QualityCheck(
            name="integration_tests",
            description="Run integration test suite"
        )
        
        await asyncio.sleep(1.0)  # Simulate integration test time
        
        check.status = CheckStatus.PASSED
        check.details = {
            "tests_run": 15,
            "tests_passed": 15,
            "services_tested": ["user-service", "auth-service", "sso-service"]
        }
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    @staticmethod
    async def check_ai_test_semantic(ai_tests: List[str]) -> QualityCheck:
        """
        NEW: Semantic evaluation of AI-generated tests.
        
        Uses LLM-as-judge pattern to evaluate test quality.
        """
        start = time.time()
        check = QualityCheck(
            name="ai_test_semantic",
            description="Semantic quality evaluation of AI tests"
        )
        
        # Simulate LLM evaluation
        scores = []
        for test in ai_tests:
            # Simulate scoring (in production, call LLM API)
            score = min(40, 25 + len(test) // 100)  # Fake scoring
            scores.append(score)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score < 28:
            check.status = CheckStatus.FAILED
            check.error_message = f"AI tests quality score too low: {avg_score:.1f}/40 (min: 28)"
        else:
            check.status = CheckStatus.PASSED
        
        check.details = {
            "avg_quality_score": avg_score,
            "tests_evaluated": len(ai_tests),
            "min_score": 28,
            "accept_threshold": 32
        }
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    @staticmethod
    async def check_contract_tests() -> QualityCheck:
        """Validate API contracts"""
        start = time.time()
        check = QualityCheck(
            name="contract_tests",
            description="Validate API contracts and compatibility"
        )
        
        await asyncio.sleep(0.3)
        
        check.status = CheckStatus.PASSED
        check.details = {
            "contracts_validated": 8,
            "breaking_changes": 0
        }
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    # ═══════════════════════════════════════════════════════════════════════
    # PRE-MERGE CHECKS (<15 min target)
    # ═══════════════════════════════════════════════════════════════════════
    
    @staticmethod
    async def check_e2e_critical() -> QualityCheck:
        """Run critical path E2E tests"""
        start = time.time()
        check = QualityCheck(
            name="e2e_critical",
            description="End-to-end tests for critical user flows"
        )
        
        # Simulate longer E2E test
        await asyncio.sleep(2.0)
        
        check.status = CheckStatus.PASSED
        check.details = {
            "scenarios": [
                "user_login",
                "sso_configuration",
                "password_reset",
                "mfa_enrollment"
            ],
            "all_passed": True
        }
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    @staticmethod
    async def check_ai_test_execution(ai_tests: List[str]) -> QualityCheck:
        """
        NEW: Execute AI-generated tests and validate behavior.
        
        Catches flaky tests, timeouts, and runtime issues.
        """
        start = time.time()
        check = QualityCheck(
            name="ai_test_execution",
            description="Execute and validate AI-generated tests"
        )
        
        # Simulate test execution
        await asyncio.sleep(1.5)
        
        # Simulate results
        executed = len(ai_tests)
        passed = executed - 1  # One flaky test
        
        check.status = CheckStatus.PASSED if passed == executed else CheckStatus.FAILED
        check.details = {
            "executed": executed,
            "passed": passed,
            "failed": executed - passed,
            "flaky_detected": 1 if passed < executed else 0
        }
        
        if passed < executed:
            check.error_message = f"AI tests failed: {executed - passed} failures detected"
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    @staticmethod
    async def check_performance_regression() -> QualityCheck:
        """Check for performance regressions"""
        start = time.time()
        check = QualityCheck(
            name="performance_regression",
            description="Performance regression testing"
        )
        
        await asyncio.sleep(1.0)
        
        check.status = CheckStatus.PASSED
        check.details = {
            "baseline_p95_ms": 150,
            "current_p95_ms": 145,
            "regression_pct": -3.3  # Actually improved!
        }
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check
    
    @staticmethod
    async def check_security_review(changed_files: List[str]) -> QualityCheck:
        """Security review for high-risk changes"""
        start = time.time()
        check = QualityCheck(
            name="security_review",
            description="Security review of changed code"
        )
        
        # Check for high-risk file changes
        high_risk_patterns = ['auth', 'password', 'sso', 'admin', 'permission']
        high_risk_files = [
            f for f in changed_files
            if any(pattern in f.lower() for pattern in high_risk_patterns)
        ]
        
        if high_risk_files:
            check.status = CheckStatus.FAILED
            check.error_message = f"High-risk files changed, requires manual security review: {high_risk_files}"
            check.details = {"high_risk_files": high_risk_files}
        else:
            check.status = CheckStatus.PASSED
            check.details = {"files_reviewed": len(changed_files)}
        
        check.duration_ms = int((time.time() - start) * 1000)
        return check


# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY GATE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class QualityGate:
    """
    Main quality gate orchestrator.
    
    Implements the shift-left philosophy:
    - Fast checks first (fail fast)
    - Expensive checks later
    - Parallel execution where possible
    """
    
    TARGET_DURATIONS = {
        GateLevel.PRE_COMMIT: 120_000,   # 2 min
        GateLevel.PRE_PR: 300_000,       # 5 min
        GateLevel.PRE_MERGE: 900_000,    # 15 min
        GateLevel.PRE_PROD: 1_800_000    # 30 min
    }
    
    def __init__(self):
        self.history: List[QualityGateResult] = []
    
    async def run_pre_commit(
        self,
        code: str,
        ai_tests: List[str] = None
    ) -> QualityGateResult:
        """
        Run pre-commit quality gate.
        
        Target: <2 minutes
        Must be fast or developers will skip it!
        """
        print("\n" + "="*70)
        print("RUNNING PRE-COMMIT QUALITY GATE")
        print("="*70)
        print("Target: <2 minutes | Fail fast on basic issues")
        
        ai_tests = ai_tests or []
        start_time = time.time()
        
        checks = []
        
        # Run checks in parallel (they're independent)
        results = await asyncio.gather(
            QualityChecks.check_syntax(code),
            QualityChecks.check_linting(code),
            QualityChecks.check_unit_tests([]),
            QualityChecks.check_ai_test_schema(ai_tests) if ai_tests else asyncio.sleep(0),
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, Exception):
                check = QualityCheck(
                    name="error",
                    description="Check failed with exception",
                    status=CheckStatus.FAILED,
                    error_message=str(result)
                )
            else:
                check = result
            
            checks.append(check)
            status_icon = "✅" if check.status == CheckStatus.PASSED else "❌"
            print(f"  {status_icon} {check.name}: {check.duration_ms}ms - {check.status.value}")
        
        # Gate passes if all checks pass
        passed = all(c.status == CheckStatus.PASSED for c in checks)
        
        total_duration = int((time.time() - start_time) * 1000)
        target = self.TARGET_DURATIONS[GateLevel.PRE_COMMIT]
        
        print(f"\nResult: {'✅ PASSED' if passed else '❌ FAILED'}")
        print(f"Duration: {total_duration}ms / Target: {target}ms")
        
        if total_duration > target:
            print("⚠️  WARNING: Exceeded target duration!")
        
        result = QualityGateResult(
            gate_level=GateLevel.PRE_COMMIT,
            passed=passed,
            checks=checks,
            total_duration_ms=total_duration
        )
        
        self.history.append(result)
        return result
    
    async def run_pre_pr(
        self,
        ai_tests: List[str] = None
    ) -> QualityGateResult:
        """
        Run pre-PR quality gate.
        
        Target: <5 minutes
        Validates before requesting human review.
        """
        print("\n" + "="*70)
        print("RUNNING PRE-PR QUALITY GATE")
        print("="*70)
        print("Target: <5 minutes | Validate before human review")
        
        ai_tests = ai_tests or []
        start_time = time.time()
        
        checks = []
        
        results = await asyncio.gather(
            QualityChecks.check_integration_tests(),
            QualityChecks.check_ai_test_semantic(ai_tests) if ai_tests else asyncio.sleep(0),
            QualityChecks.check_contract_tests(),
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, Exception):
                check = QualityCheck(
                    name="error",
                    description="Check failed",
                    status=CheckStatus.FAILED,
                    error_message=str(result)
                )
            else:
                check = result
            
            checks.append(check)
            status_icon = "✅" if check.status == CheckStatus.PASSED else "❌"
            print(f"  {status_icon} {check.name}: {check.duration_ms}ms - {check.status.value}")
        
        passed = all(c.status == CheckStatus.PASSED for c in checks)
        
        total_duration = int((time.time() - start_time) * 1000)
        
        print(f"\nResult: {'✅ PASSED' if passed else '❌ FAILED'}")
        print(f"Duration: {total_duration}ms")
        
        result = QualityGateResult(
            gate_level=GateLevel.PRE_PR,
            passed=passed,
            checks=checks,
            total_duration_ms=total_duration
        )
        
        self.history.append(result)
        return result
    
    async def run_pre_merge(
        self,
        changed_files: List[str],
        ai_tests: List[str] = None
    ) -> QualityGateResult:
        """
        Run pre-merge quality gate.
        
        Target: <15 minutes
        Comprehensive validation before merging to main.
        """
        print("\n" + "="*70)
        print("RUNNING PRE-MERGE QUALITY GATE")
        print("="*70)
        print("Target: <15 minutes | Comprehensive validation")
        
        ai_tests = ai_tests or []
        start_time = time.time()
        
        checks = []
        
        results = await asyncio.gather(
            QualityChecks.check_e2e_critical(),
            QualityChecks.check_ai_test_execution(ai_tests) if ai_tests else asyncio.sleep(0),
            QualityChecks.check_performance_regression(),
            QualityChecks.check_security_review(changed_files),
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, Exception):
                check = QualityCheck(
                    name="error",
                    description="Check failed",
                    status=CheckStatus.FAILED,
                    error_message=str(result)
                )
            else:
                check = result
            
            checks.append(check)
            status_icon = "✅" if check.status == CheckStatus.PASSED else "❌"
            print(f"  {status_icon} {check.name}: {check.duration_ms}ms - {check.status.value}")
        
        passed = all(c.status == CheckStatus.PASSED for c in checks)
        
        total_duration = int((time.time() - start_time) * 1000)
        
        print(f"\nResult: {'✅ PASSED' if passed else '❌ FAILED'}")
        print(f"Duration: {total_duration}ms")
        
        result = QualityGateResult(
            gate_level=GateLevel.PRE_MERGE,
            passed=passed,
            checks=checks,
            total_duration_ms=total_duration
        )
        
        self.history.append(result)
        return result
    
    def generate_report(self) -> str:
        """Generate quality gate report"""
        lines = []
        lines.append("\n" + "="*70)
        lines.append("QUALITY GATE EXECUTION REPORT")
        lines.append("="*70)
        
        for result in self.history:
            lines.append(f"\n{result.gate_level.value.upper()}")
            lines.append("-" * 70)
            lines.append(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
            lines.append(f"Duration: {result.total_duration_ms}ms")
            lines.append(f"Pass Rate: {result.pass_rate:.1f}%")
            lines.append("\nChecks:")
            for check in result.checks:
                icon = "✅" if check.status == CheckStatus.PASSED else "❌"
                lines.append(f"  {icon} {check.name} ({check.duration_ms}ms)")
                if check.error_message:
                    lines.append(f"      Error: {check.error_message}")
        
        lines.append("\n" + "="*70)
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

async def demo():
    """Demonstrate quality gates"""
    print("\n" + "="*70)
    print("SHIFT-LEFT CI/CD QUALITY GATES - DEMONSTRATION")
    print("="*70)
    
    print("\nThis demonstrates the tiered quality validation system:")
    print("  - Pre-commit: Fast validation on developer machine")
    print("  - Pre-PR: Integration and AI test validation")
    print("  - Pre-merge: Comprehensive E2E and security validation")
    print("\nKey Innovation: AI-specific quality checks integrated at each stage")
    
    gate = QualityGate()
    
    # Sample code and AI tests
    sample_code = """
import unittest

class TestUserAPI(unittest.TestCase):
    def test_get_user(self):
        response = get_user(123)
        self.assertEqual(response.status_code, 200)
"""
    
    sample_ai_tests = [
        """
import unittest
class TestAuth(unittest.TestCase):
    def test_login(self):
        result = login("user", "pass")
        self.assertTrue(result.success)
        self.assertEqual(result.token_type, "Bearer")
        self.assertIn("expires_in", result)
""",
        """
import unittest
class TestSSO(unittest.TestCase):
    def test_sso_config(self):
        config = get_sso_config("tenant-123")
        self.assertIsNotNone(config)
        self.assertEqual(config.provider, "Okta")
"""
    ]
    
    # Run pre-commit gate
    await gate.run_pre_commit(sample_code, sample_ai_tests)
    
    # Run pre-PR gate
    await gate.run_pre_pr(sample_ai_tests)
    
    # Run pre-merge gate
    changed_files = ["src/auth/login.py", "src/sso/config.py", "tests/test_auth.py"]
    await gate.run_pre_merge(changed_files, sample_ai_tests)
    
    # Print final report
    print(gate.generate_report())
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    
    print("\n🎓 Key Concepts Demonstrated:")
    print("  ✅ Tiered validation (fail fast, expensive later)")
    print("  ✅ Parallel execution for speed")
    print("  ✅ AI-specific quality checks at each stage")
    print("  ✅ Risk-based security reviews")
    print("  ✅ Performance regression detection")
    
    print("\n💼 Interview Gold:")
    print("  'I built a shift-left quality system with tiered gates:")
    print("   pre-commit (<2min), pre-PR (<5min), pre-merge (<15min).")
    print("   AI-generated code gets validated at each stage with")
    print("   schema checks, semantic evaluation, and execution testing.'")


if __name__ == "__main__":
    asyncio.run(demo())

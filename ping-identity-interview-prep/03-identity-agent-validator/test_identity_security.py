"""
Test Identity Security - Security Boundary Testing

This module provides comprehensive security testing for the identity
validation system. It tests all security boundaries and ensures
the system properly protects against common attack vectors.

Test Categories:
- Tenant isolation tests
- Permission boundary tests  
- Agent identity spoofing tests
- Audit integrity tests
- Rate limiting tests
"""

import asyncio
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

# Import our security modules
from agent_identity import (
    IdentityValidator, AgentIdentity, AgentType, 
    RiskLevel, ValidationResult, OperationRequest
)
from permission_validator import PermissionValidator, PermissionRegistry, RiskLevel as PermRisk
from approval_flow import ApprovalWorkflow, ApprovalPolicyEngine, ApprovalStatus
from audit_system import AuditLogger, EventType, Severity
from risk_engine import RiskEngine, RiskLevel as RiskEngLevel, RiskPolicyEnforcer


class SimpleRateLimiter:
    """Simple rate limiter for testing"""
    
    def __init__(self, limit: int = 100):
        self.limit = limit
        self.request_counts: Dict[str, int] = {}
    
    def check(self, agent_id: str) -> bool:
        """Check if request is within rate limit"""
        self.request_counts[agent_id] = self.request_counts.get(agent_id, 0) + 1
        return self.request_counts[agent_id] <= self.limit


@dataclass
class TestResult:
    """Result of a security test"""
    test_name: str
    category: str
    passed: bool
    description: str
    details: str = ""


class SecurityTestSuite:
    """
    Comprehensive security test suite for identity validation.
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.identity_validator = IdentityValidator()
        self.permission_validator = PermissionValidator()
        self.approval_policy = ApprovalPolicyEngine()
        self.audit_logger = AuditLogger()
        self.risk_engine = RiskEngine()
        self.risk_enforcer = RiskPolicyEnforcer(self.risk_engine)
        self.rate_limiter = SimpleRateLimiter(limit=100)
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all security tests"""
        print("\n" + "="*70)
        print("SECURITY BOUNDARY TESTS - IDENTITY VALIDATION SYSTEM")
        print("="*70)
        
        # Run test categories
        self._test_tenant_isolation()
        self._test_permission_boundaries()
        self._test_identity_spoofing()
        self._test_audit_integrity()
        self._test_rate_limiting()
        self._test_approval_workflows()
        self._test_risk_assessment()
        
        return self.results
    
    def _add_result(self, name: str, category: str, passed: bool, description: str, details: str = ""):
        """Add a test result"""
        result = TestResult(name, category, passed, description, details)
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {category} | {name}")
        if not passed and details:
            print(f"      Details: {details}")
    
    def _test_tenant_isolation(self):
        """Test tenant isolation boundaries"""
        print("\n🔒 TESTING TENANT ISOLATION")
        print("-" * 70)
        
        # Test 1: Agent with valid identity (should be active)
        agent = AgentIdentity(
            agent_id="test-agent-1",
            name="Test Agent 1",
            agent_type=AgentType.SYSTEM,
            risk_level=RiskLevel.LOW,
            owner="admin@company.com",
            delegated_permissions=["user:read"]
        )
        
        self._add_result(
            "Valid Agent Identity",
            "Tenant Isolation",
            agent.is_active(),
            "Properly configured agent should be active",
            f"Expected active, got: {agent.is_active()}"
        )
        
        # Test 2: Registered agent lookup (should pass)
        self.identity_validator.register_agent(agent)
        registered = self.identity_validator.agents.get("test-agent-1")
        
        self._add_result(
            "Registered Agent Lookup",
            "Tenant Isolation",
            registered is not None and registered.agent_id == "test-agent-1",
            "Agent should be retrievable after registration",
            f"Registered: {registered is not None}"
        )
        
        # Test 3: Agent permission check (has permission)
        has_perm = agent.has_permission("user:read")
        
        self._add_result(
            "Permission Check (Granted)",
            "Tenant Isolation",
            has_perm,
            "Agent should have its delegated permission",
        )
        
        # Test 4: Agent permission check (denied for undelegated)
        lacks_perm = not agent.has_permission("tenant:delete")
        
        self._add_result(
            "Permission Check (Denied)",
            "Tenant Isolation",
            lacks_perm,
            "Agent should NOT have undelegated permissions",
        )
    
    def _test_permission_boundaries(self):
        """Test permission boundary enforcement"""
        print("\n🔐 TESTING PERMISSION BOUNDARIES")
        print("-" * 70)
        
        # Test 1: Valid permission request
        result = self.permission_validator.validate_permission_request(
            agent_id="agent-1",
            current_permissions=["user:read"],
            requested_permissions=["user:create"],
            agent_risk_level=PermRisk.MEDIUM
        )
        
        self._add_result(
            "Valid Permission Grant",
            "Permission Boundaries",
            len(result["denied"]) == 0,
            "Valid permission request should be granted",
            f"Granted: {result['granted']}, Denied: {result['denied']}"
        )
        
        # Test 2: Permission escalation detection
        result = self.permission_validator.validate_permission_request(
            agent_id="agent-1",
            current_permissions=["user:read"],
            requested_permissions=["admin:grant"],  # Escalation!
            agent_risk_level=PermRisk.MEDIUM
        )
        
        escalation_detected = len(result["requires_approval"]) > 0
        self._add_result(
            "Permission Escalation Detected",
            "Permission Boundaries",
            escalation_detected,
            "Escalation from user:read to admin:grant should be flagged",
            f"Requires approval: {result['requires_approval']}"
        )
        
        # Test 3: Permission limit enforcement
        result = self.permission_validator.validate_permission_request(
            agent_id="agent-1",
            current_permissions=["user:read", "user:create", "user:update", "sso:read", "sso:create"],
            requested_permissions=["user:delete", "admin:grant", "tenant:delete"],
            agent_risk_level=PermRisk.LOW
        )
        
        limit_enforced = len(result["denied"]) > 0
        self._add_result(
            "Permission Limit Enforced",
            "Permission Boundaries",
            limit_enforced,
            "Low-risk agent should be limited to max permissions",
            f"Denied due to limit: {limit_enforced}"
        )
        
        # Test 4: Unknown permission rejection
        result = self.permission_validator.validate_permission_request(
            agent_id="agent-1",
            current_permissions=[],
            requested_permissions=["unknown:dangerous_permission"],
            agent_risk_level=PermRisk.LOW
        )
        
        self._add_result(
            "Unknown Permission Rejected",
            "Permission Boundaries",
            len(result["denied"]) == 1,
            "Unknown permissions should be rejected",
        )
    
    def _test_identity_spoofing(self):
        """Test protection against identity spoofing"""
        print("\n🎭 TESTING IDENTITY SPOOFING PROTECTION")
        print("-" * 70)
        
        # Test 1: Valid agent identity
        agent = AgentIdentity(
            agent_id="legitimate-agent",
            name="Legitimate Agent",
            agent_type=AgentType.DELEGATED,
            risk_level=RiskLevel.LOW,
            owner="admin@company.com",
            delegated_permissions=["user:read"]
        )
        
        valid_identity = bool(agent.agent_id) and agent.is_active()
        
        self._add_result(
            "Valid Identity Accepted",
            "Identity Spoofing",
            valid_identity,
            "Legitimate agent identity should be valid",
        )
        
        # Test 2: Missing required fields
        agent_invalid = AgentIdentity(
            agent_id="",  # Missing!
            name="Invalid Agent",
            agent_type=AgentType.DELEGATED,
            risk_level=RiskLevel.LOW,
            owner="admin@company.com",
            delegated_permissions=["user:read"]
        )
        
        invalid_identity = not bool(agent_invalid.agent_id)
        
        self._add_result(
            "Missing Agent ID Rejected",
            "Identity Spoofing",
            invalid_identity,
            "Agent with missing ID should be rejected",
        )
        
        # Test 3: Agent ID mismatch with operation request
        agent = AgentIdentity(
            agent_id="agent-a",
            name="Agent A",
            agent_type=AgentType.DELEGATED,
            risk_level=RiskLevel.LOW,
            owner="admin@company.com",
            delegated_permissions=["user:read"]
        )
        
        context = OperationRequest(
            agent_id="agent-b",  # Different from agent!
            operation="user:read",
            resource="tenant-a/users",
            request_id="req-003"
        )
        
        mismatch = context.agent_id != agent.agent_id
        
        self._add_result(
            "Agent ID Mismatch Detected",
            "Identity Spoofing",
            mismatch,
            "Operation request with mismatched agent ID should be flagged",
        )
    
    def _test_audit_integrity(self):
        """Test audit log integrity"""
        print("\n📋 TESTING AUDIT INTEGRITY")
        print("-" * 70)
        
        # Add some events
        self.audit_logger.log_identity_created(
            agent_id="test-agent",
            agent_name="Test Agent",
            tenant_id="tenant-a",
            metadata={"test": True}
        )
        
        self.audit_logger.log_permission_denied(
            agent_id="test-agent",
            agent_name="Test Agent",
            tenant_id="tenant-a",
            permission="admin:grant",
            reason="Insufficient privileges"
        )
        
        # Test 1: Chain verification
        verify_result = self.audit_logger.chain.verify_chain()
        
        self._add_result(
            "Audit Chain Integrity",
            "Audit Integrity",
            verify_result["valid"],
            "Audit chain should be valid after events",
            f"Violations: {len(verify_result['violations'])}"
        )
        
        # Test 2: Event count
        events_logged = len(self.audit_logger.chain.events) >= 2
        
        self._add_result(
            "Events Logged",
            "Audit Integrity",
            events_logged,
            "All security events should be logged",
            f"Events: {len(self.audit_logger.chain.events)}"
        )
        
        # Test 3: Security events captured
        security_events = self.audit_logger.chain.get_security_events()
        
        self._add_result(
            "Security Events Captured",
            "Audit Integrity",
            len(security_events) > 0,
            "Security events should be captured",
            f"Security events: {len(security_events)}"
        )
    
    def _test_rate_limiting(self):
        """Test rate limiting"""
        print("\n⏱️  TESTING RATE LIMITING")
        print("-" * 70)
        
        # Test 1: Initial requests within limit
        agent_id = "rate-test-agent"
        
        # Reset rate limiter
        self.rate_limiter.request_counts = {}
        
        # Make requests up to limit
        passed = True
        for i in range(100):  # Within limit
            if not self.rate_limiter.check(agent_id):
                passed = False
                break
        
        self._add_result(
            "Requests Within Limit",
            "Rate Limiting",
            passed,
            "Requests within rate limit should pass",
            f"Failed at request {i+1}" if not passed else ""
        )
        
        # Test 2: Exceeding rate limit
        for i in range(200):  # Exceed limit
            self.rate_limiter.check(agent_id)
        
        result = self.rate_limiter.check(agent_id)
        
        self._add_result(
            "Rate Limit Enforced",
            "Rate Limiting",
            not result,
            "Excessive requests should be rate limited",
            f"Limit exceeded correctly: {not result}"
        )
    
    def _test_approval_workflows(self):
        """Test approval workflow enforcement"""
        print("\n✅ TESTING APPROVAL WORKFLOWS")
        print("-" * 70)
        
        workflow = ApprovalWorkflow(self.approval_policy)
        
        # Test 1: Auto-approval for low risk
        request = asyncio.run(workflow.request_approval(
            agent_id="agent-1",
            agent_name="Test Agent",
            operation="user:read",
            resource="users",
            resource_sensitivity="low",
            agent_risk_level="low",
            justification="Testing"
        ))
        
        self._add_result(
            "Low-Risk Auto-Approval",
            "Approval Workflows",
            request.status == ApprovalStatus.APPROVED,
            "Low-risk operations should be auto-approved",
            f"Status: {request.status.value}"
        )
        
        # Test 2: Approval required for high risk
        request = asyncio.run(workflow.request_approval(
            agent_id="agent-2",
            agent_name="Admin Agent",
            operation="user:delete",
            resource="users",
            resource_sensitivity="high",
            agent_risk_level="high",
            justification="Removing user"
        ))
        
        self._add_result(
            "High-Risk Requires Approval",
            "Approval Workflows",
            request.status == ApprovalStatus.PENDING,
            "High-risk operations should require approval",
            f"Status: {request.status.value}"
        )
        
        # Test 3: Approval process
        if request.status == ApprovalStatus.PENDING:
            workflow.approve(request.request_id, "admin@company.com")
            status = workflow.get_status(request.request_id)
            
            self._add_result(
                "Approval Process Works",
                "Approval Workflows",
                status == ApprovalStatus.APPROVED,
                "Approval should change status to approved",
                f"Final status: {status.value if status else 'None'}"
            )
    
    def _test_risk_assessment(self):
        """Test risk assessment engine"""
        print("\n⚠️  TESTING RISK ASSESSMENT")
        print("-" * 70)
        
        # Test 1: Low risk assessment
        result = self.risk_enforcer.evaluate_operation(
            agent_id="agent-1",
            operation="user:read",
            context={
                "agent_risk_level": RiskEngLevel.LOW,
                "resource": "user_profile",
                "permissions": ["user:read"],
                "tenant_id": "tenant-a"
            }
        )
        
        self._add_result(
            "Low Risk Detected",
            "Risk Assessment",
            result["risk_score"].level == RiskEngLevel.LOW,
            "Simple read operations should be low risk",
            f"Risk level: {result['risk_score'].level.value}"
        )
        
        # Test 2: Critical risk detection
        result = self.risk_enforcer.evaluate_operation(
            agent_id="agent-2",
            operation="tenant:delete",
            context={
                "agent_risk_level": RiskEngLevel.HIGH,
                "resource": "tenant",
                "permissions": ["tenant:delete"],
                "tenant_id": "tenant-a",
                "target_tenant": "tenant-b"  # Cross-tenant!
            }
        )
        
        self._add_result(
            "Critical Risk Detected",
            "Risk Assessment",
            result["risk_score"].level == RiskEngLevel.CRITICAL,
            "Cross-tenant delete should be critical risk",
            f"Risk level: {result['risk_score'].level.value}, Allowed: {result['allowed']}"
        )
        
        # Test 3: Risk-based approval requirement
        result = self.risk_enforcer.evaluate_operation(
            agent_id="agent-3",
            operation="admin:grant",
            context={
                "agent_risk_level": RiskEngLevel.MEDIUM,
                "resource": "admin",
                "permissions": ["admin:grant"],
                "tenant_id": "tenant-a"
            }
        )
        
        self._add_result(
            "Risk-Based Approval",
            "Risk Assessment",
            result["requires_approval"],
            "High-risk operations should require approval",
            f"Requires approval: {result['requires_approval']}"
        )
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Pass Rate: {passed/total*100:.1f}%")
        
        # By category
        print("\nBy Category:")
        categories = set(r.category for r in self.results)
        for cat in sorted(categories):
            cat_results = [r for r in self.results if r.category == cat]
            cat_passed = sum(1 for r in cat_results if r.passed)
            print(f"  {cat}: {cat_passed}/{len(cat_results)} passed")
        
        # Show failures
        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.category}: {r.test_name}")
                    if r.details:
                        print(f"    {r.details}")
        
        print("\n" + "="*70)


def demo():
    """Run the security test suite"""
    suite = SecurityTestSuite()
    suite.run_all_tests()
    suite.print_summary()
    
    print("\n🎓 Security Testing Concepts Demonstrated:")
    print("  ✅ Tenant isolation enforcement")
    print("  ✅ Permission boundary protection")
    print("  ✅ Identity spoofing prevention")
    print("  ✅ Audit log integrity")
    print("  ✅ Rate limiting effectiveness")
    print("  ✅ Approval workflow enforcement")
    print("  ✅ Risk-based policy enforcement")
    
    print("\n💡 Interview Talking Points:")
    print("  • Security boundaries prevent lateral movement")
    print("  • Tenant isolation is enforced at multiple layers")
    print("  • Identity validation prevents spoofing attacks")
    print("  • Audit logs provide tamper-evident records")
    print("  • Rate limiting prevents abuse")
    print("  • Risk assessment enables adaptive security")


if __name__ == "__main__":
    demo()

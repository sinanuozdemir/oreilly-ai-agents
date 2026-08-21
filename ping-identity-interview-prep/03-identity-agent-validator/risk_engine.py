"""
Risk Engine - Dynamic Risk Assessment for AI Agents

This module implements real-time risk scoring and assessment for AI agents.
It evaluates risk based on behavior patterns, requested permissions, and
operational context.

Key Concepts:
- Dynamic risk scoring
- Behavioral analysis
- Risk-based policy enforcement
- Anomaly detection
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math


class RiskLevel(Enum):
    """Risk levels for agents and operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFactor(Enum):
    """Types of risk factors"""
    PERMISSION_SCOPE = "permission_scope"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    DATA_SENSITIVITY = "data_sensitivity"
    OPERATION_COMPLEXITY = "operation_complexity"
    TENANT_ISOLATION = "tenant_isolation"
    RATE_ANOMALY = "rate_anomaly"
    TIME_ANOMALY = "time_anomaly"


@dataclass
class RiskScore:
    """Represents a calculated risk score"""
    overall_score: float  # 0.0 to 1.0
    level: RiskLevel
    factors: Dict[RiskFactor, float] = field(default_factory=dict)
    explanation: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Ensure score is bounded"""
        self.overall_score = max(0.0, min(1.0, self.overall_score))


class RiskEngine:
    """
    Dynamic risk assessment engine for AI agents.
    
    Evaluates risk across multiple dimensions:
    1. Permission scope - How extensive are the agent's permissions?
    2. Behavioral patterns - Is the agent behaving normally?
    3. Data sensitivity - What data is being accessed?
    4. Operation complexity - How complex is the operation?
    5. Tenant isolation - Is tenant isolation maintained?
    """
    
    # Risk thresholds
    LOW_THRESHOLD = 0.25
    MEDIUM_THRESHOLD = 0.50
    HIGH_THRESHOLD = 0.75
    
    # Weights for different risk factors
    FACTOR_WEIGHTS = {
        RiskFactor.PERMISSION_SCOPE: 0.25,
        RiskFactor.BEHAVIORAL_ANOMALY: 0.20,
        RiskFactor.DATA_SENSITIVITY: 0.20,
        RiskFactor.OPERATION_COMPLEXITY: 0.15,
        RiskFactor.TENANT_ISOLATION: 0.15,
        RiskFactor.RATE_ANOMALY: 0.05,
    }
    
    def __init__(self):
        # Store behavioral baselines per agent
        self.behavioral_baselines: Dict[str, Dict] = {}
        
        # Store recent activity for anomaly detection
        self.activity_history: Dict[str, List[Dict]] = {}
        
        # Known patterns for classification
        self.high_risk_operations = {
            "delete", "revoke", "grant", "admin", "configure"
        }
        
        self.sensitive_resources = {
            "admin", "tenant", "sso", "api_key", "credential"
        }
    
    def assess_permission_scope_risk(
        self,
        permissions: List[str],
        agent_risk_level: RiskLevel
    ) -> float:
        """
        Assess risk based on permission scope.
        
        Higher risk if:
        - Many permissions requested
        - Mix of read/write/admin permissions
        - Critical permissions included
        """
        if not permissions:
            return 0.0
        
        score = 0.0
        
        # Count by type
        admin_count = sum(1 for p in permissions if "admin" in p)
        write_count = sum(1 for p in permissions 
                         if any(op in p for op in ["create", "update", "delete"]))
        critical_count = sum(1 for p in permissions 
                            if any(r in p for r in ["tenant", "admin"]))
        
        # Base score on count (diminishing returns after 5)
        count_score = min(len(permissions) / 10, 0.3)
        
        # Admin permissions add significant risk
        admin_score = min(admin_count * 0.2, 0.3)
        
        # Critical permissions
        critical_score = min(critical_count * 0.25, 0.4)
        
        score = count_score + admin_score + critical_score
        
        # Escalation: high-risk agent with many permissions
        if agent_risk_level == RiskLevel.HIGH and len(permissions) > 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def assess_behavioral_risk(
        self,
        agent_id: str,
        current_action: str,
        recent_actions: List[str]
    ) -> float:
        """
        Assess risk based on behavioral patterns.
        
        Detects:
        - New/unusual actions
        - Rapid sequences of different actions
        - Permission probing patterns
        """
        score = 0.0
        
        # Get or create baseline
        if agent_id not in self.behavioral_baselines:
            self.behavioral_baselines[agent_id] = {
                "common_actions": set(),
                "action_frequency": {}
            }
        
        baseline = self.behavioral_baselines[agent_id]
        
        # New action detection
        if current_action not in baseline["common_actions"]:
            if len(baseline["common_actions"]) > 0:
                score += 0.2  # New action after baseline established
            baseline["common_actions"].add(current_action)
        
        # Permission probing pattern
        if len(recent_actions) >= 3:
            unique_actions = len(set(recent_actions[-3:]))
            if unique_actions == 3:  # Three different actions in sequence
                score += 0.15
        
        # Rapid action detection (many actions in short time)
        action_count = len(self.activity_history.get(agent_id, []))
        if action_count > 20:  # High activity
            score += 0.1
        
        return min(score, 1.0)
    
    def assess_data_sensitivity_risk(
        self,
        resource: str,
        operation: str,
        data_classification: str = "internal"
    ) -> float:
        """
        Assess risk based on data sensitivity.
        
        Considers:
        - Resource type (admin, tenant, user)
        - Operation type (read vs write)
        - Data classification
        """
        score = 0.0
        
        # Resource sensitivity
        if any(r in resource for r in self.sensitive_resources):
            score += 0.3
        elif "user" in resource:
            score += 0.15
        elif "analytics" in resource:
            score += 0.05
        
        # Operation type multiplier
        if operation in ["delete", "revoke"]:
            score *= 1.5
        elif operation in ["update", "create"]:
            score *= 1.2
        
        # Data classification
        classification_scores = {
            "public": 0.0,
            "internal": 0.1,
            "confidential": 0.2,
            "restricted": 0.3
        }
        score += classification_scores.get(data_classification, 0.1)
        
        return min(score, 1.0)
    
    def assess_operation_complexity_risk(
        self,
        operation: str,
        parameters: Optional[Dict] = None
    ) -> float:
        """
        Assess risk based on operation complexity.
        
        Complex operations (bulk, multi-step) have higher risk.
        """
        score = 0.0
        
        if not parameters:
            return score
        
        # Bulk operations
        if "bulk" in operation or parameters.get("batch_size", 0) > 10:
            score += 0.2
        
        # Multi-tenant operations
        if parameters.get("affects_multiple_tenants"):
            score += 0.3
        
        # Cascading operations
        if parameters.get("cascade"):
            score += 0.15
        
        # Script/ automation operations
        if parameters.get("automated"):
            score += 0.1
        
        return min(score, 1.0)
    
    def assess_tenant_isolation_risk(
        self,
        agent_tenant: str,
        target_tenant: Optional[str],
        cross_tenant_access: bool = False
    ) -> float:
        """
        Assess risk related to tenant isolation.
        
        Cross-tenant access is a critical risk.
        """
        score = 0.0
        
        if cross_tenant_access:
            score += 0.5  # Major violation
        
        if target_tenant and agent_tenant != target_tenant:
            score += 0.5  # Critical violation
        
        return min(score, 1.0)
    
    def calculate_risk_score(
        self,
        agent_id: str,
        agent_risk_level: RiskLevel,
        operation: str,
        resource: str,
        permissions: List[str],
        tenant_id: str,
        target_tenant: Optional[str] = None,
        parameters: Optional[Dict] = None,
        recent_actions: Optional[List[str]] = None
    ) -> RiskScore:
        """
        Calculate overall risk score for an operation.
        """
        factors = {}
        
        # Calculate individual factor scores
        factors[RiskFactor.PERMISSION_SCOPE] = self.assess_permission_scope_risk(
            permissions, agent_risk_level
        )
        
        factors[RiskFactor.BEHAVIORAL_ANOMALY] = self.assess_behavioral_risk(
            agent_id, operation, recent_actions or []
        )
        
        factors[RiskFactor.DATA_SENSITIVITY] = self.assess_data_sensitivity_risk(
            resource, operation, parameters.get("data_classification", "internal") if parameters else "internal"
        )
        
        factors[RiskFactor.OPERATION_COMPLEXITY] = self.assess_operation_complexity_risk(
            operation, parameters
        )
        
        factors[RiskFactor.TENANT_ISOLATION] = self.assess_tenant_isolation_risk(
            tenant_id, target_tenant, parameters.get("cross_tenant", False) if parameters else False
        )
        
        # Calculate weighted overall score
        overall = sum(
            score * self.FACTOR_WEIGHTS.get(factor, 0.1)
            for factor, score in factors.items()
        )
        
        # Tenant isolation violations are always critical.
        # Some security invariants must not be diluted by weighted averaging -
        # a cross-tenant access attempt is critical regardless of other factors.
        if factors[RiskFactor.TENANT_ISOLATION] >= 0.5:
            overall = max(overall, self.HIGH_THRESHOLD)
        
        # Determine risk level
        level = self._score_to_level(overall)
        
        # Generate explanation
        explanation = self._generate_explanation(factors)
        
        return RiskScore(
            overall_score=overall,
            level=level,
            factors=factors,
            explanation=explanation
        )
    
    def _score_to_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level"""
        if score >= self.HIGH_THRESHOLD:
            return RiskLevel.CRITICAL
        elif score >= self.MEDIUM_THRESHOLD:
            return RiskLevel.HIGH
        elif score >= self.LOW_THRESHOLD:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def _generate_explanation(self, factors: Dict[RiskFactor, float]) -> str:
        """Generate human-readable explanation of risk factors"""
        # Sort factors by score
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        
        explanations = []
        for factor, score in sorted_factors[:3]:  # Top 3 factors
            if score > 0.3:
                explanations.append(f"{factor.value}: high ({score:.2f})")
            elif score > 0.15:
                explanations.append(f"{factor.value}: elevated ({score:.2f})")
        
        if not explanations:
            return "Risk factors within normal range"
        
        return "; ".join(explanations)
    
    def record_activity(self, agent_id: str, action: str, resource: str):
        """Record agent activity for behavioral analysis"""
        if agent_id not in self.activity_history:
            self.activity_history[agent_id] = []
        
        self.activity_history[agent_id].append({
            "timestamp": datetime.utcnow(),
            "action": action,
            "resource": resource
        })
        
        # Keep only recent history (last 100 actions)
        self.activity_history[agent_id] = self.activity_history[agent_id][-100:]
    
    def should_require_approval(self, risk_score: RiskScore) -> bool:
        """Determine if operation requires human approval"""
        return risk_score.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def should_escalate(self, risk_score: RiskScore) -> bool:
        """Determine if risk should be escalated to security team"""
        return risk_score.level == RiskLevel.CRITICAL


class RiskPolicyEnforcer:
    """
    Enforces risk-based policies on agent operations.
    """
    
    # Operations that always require approval, regardless of calculated score.
    # Destructive and privilege-escalating actions should never be silent.
    ALWAYS_APPROVE_OPERATIONS = {
        "user:delete",
        "tenant:delete",
        "admin:grant",
        "admin:revoke",
        "sso:delete",
    }
    
    def __init__(self, risk_engine: RiskEngine):
        self.risk_engine = risk_engine
        self.policy_violations: List[Dict] = []
    
    def evaluate_operation(
        self,
        agent_id: str,
        operation: str,
        context: Dict
    ) -> Dict:
        """
        Evaluate if operation complies with risk policies.
        
        Returns decision with required actions.
        """
        # Calculate risk
        risk_score = self.risk_engine.calculate_risk_score(
            agent_id=agent_id,
            agent_risk_level=context.get("agent_risk_level", RiskLevel.MEDIUM),
            operation=operation,
            resource=context.get("resource", "unknown"),
            permissions=context.get("permissions", []),
            tenant_id=context.get("tenant_id", "unknown"),
            target_tenant=context.get("target_tenant"),
            parameters=context.get("parameters"),
            recent_actions=context.get("recent_actions", [])
        )
        
        # Determine actions required
        decision = {
            "allowed": True,
            "requires_approval": False,
            "requires_escalation": False,
            "risk_score": risk_score,
            "actions": []
        }
        
        # Policy checks
        if risk_score.level == RiskLevel.CRITICAL:
            decision["allowed"] = False
            decision["requires_escalation"] = True
            decision["actions"].append("block_operation")
            decision["actions"].append("alert_security_team")
            self._log_violation(agent_id, operation, risk_score, "CRITICAL_RISK")
        
        elif risk_score.level == RiskLevel.HIGH:
            decision["requires_approval"] = True
            decision["actions"].append("request_approval")
        
        elif risk_score.level == RiskLevel.MEDIUM:
            decision["actions"].append("log_with_caution")
        
        else:
            decision["actions"].append("log_standard")
        
        # Destructive/admin operations always require approval,
        # even if the numeric risk score happens to be low
        if operation in self.ALWAYS_APPROVE_OPERATIONS and decision["allowed"]:
            if not decision["requires_approval"]:
                decision["requires_approval"] = True
                decision["actions"].append("request_approval")
        
        # Record activity
        self.risk_engine.record_activity(
            agent_id, operation, context.get("resource", "unknown")
        )
        
        return decision
    
    def _log_violation(self, agent_id: str, operation: str, risk_score: RiskScore, reason: str):
        """Log a policy violation"""
        self.policy_violations.append({
            "timestamp": datetime.utcnow(),
            "agent_id": agent_id,
            "operation": operation,
            "risk_score": risk_score.overall_score,
            "risk_level": risk_score.level.value,
            "reason": reason
        })


def demo():
    """Demonstrate risk engine"""
    print("\n" + "="*70)
    print("RISK ENGINE - DYNAMIC RISK ASSESSMENT")
    print("="*70)
    
    engine = RiskEngine()
    enforcer = RiskPolicyEnforcer(engine)
    
    # Scenario 1: Low risk operation
    print("\n📋 SCENARIO 1: Low-risk operation (read user data)")
    print("-" * 70)
    
    result = enforcer.evaluate_operation(
        agent_id="agent-001",
        operation="user:read",
        context={
            "agent_risk_level": RiskLevel.LOW,
            "resource": "user_profile",
            "permissions": ["user:read"],
            "tenant_id": "tenant-abc"
        }
    )
    
    print(f"Risk Score: {result['risk_score'].overall_score:.2f}")
    print(f"Risk Level: {result['risk_score'].level.value}")
    print(f"Allowed: {result['allowed']}")
    print(f"Requires Approval: {result['requires_approval']}")
    print(f"Explanation: {result['risk_score'].explanation}")
    
    # Scenario 2: Medium risk operation
    print("\n📋 SCENARIO 2: Medium-risk operation (create user)")
    print("-" * 70)
    
    result = enforcer.evaluate_operation(
        agent_id="agent-002",
        operation="user:create",
        context={
            "agent_risk_level": RiskLevel.MEDIUM,
            "resource": "user_account",
            "permissions": ["user:read", "user:create"],
            "tenant_id": "tenant-abc"
        }
    )
    
    print(f"Risk Score: {result['risk_score'].overall_score:.2f}")
    print(f"Risk Level: {result['risk_score'].level.value}")
    print(f"Requires Approval: {result['requires_approval']}")
    print(f"Explanation: {result['risk_score'].explanation}")
    
    # Scenario 3: High risk operation
    print("\n📋 SCENARIO 3: High-risk operation (delete tenant)")
    print("-" * 70)
    
    result = enforcer.evaluate_operation(
        agent_id="agent-003",
        operation="tenant:delete",
        context={
            "agent_risk_level": RiskLevel.HIGH,
            "resource": "tenant",
            "permissions": ["tenant:delete", "admin:grant"],
            "tenant_id": "tenant-abc",
            "parameters": {"cascade": True}
        }
    )
    
    print(f"Risk Score: {result['risk_score'].overall_score:.2f}")
    print(f"Risk Level: {result['risk_score'].level.value}")
    print(f"Requires Approval: {result['requires_approval']}")
    print(f"Factors:")
    for factor, score in result['risk_score'].factors.items():
        if score > 0.1:
            print(f"  - {factor.value}: {score:.2f}")
    
    # Scenario 4: Critical risk (tenant isolation breach)
    print("\n📋 SCENARIO 4: Critical risk (cross-tenant access)")
    print("-" * 70)
    
    result = enforcer.evaluate_operation(
        agent_id="agent-004",
        operation="user:read",
        context={
            "agent_risk_level": RiskLevel.HIGH,
            "resource": "user_profile",
            "permissions": ["user:read"],
            "tenant_id": "tenant-abc",
            "target_tenant": "tenant-xyz",  # Different tenant!
            "parameters": {"crossTenant": True}
        }
    )
    
    print(f"Risk Score: {result['risk_score'].overall_score:.2f}")
    print(f"Risk Level: {result['risk_score'].level.value}")
    print(f"Allowed: {result['allowed']}")
    print(f"Requires Escalation: {result['requires_escalation']}")
    print(f"Actions: {result['actions']}")
    
    # Scenario 5: Behavioral anomaly detection
    print("\n📋 SCENARIO 5: Behavioral anomaly detection")
    print("-" * 70)
    
    # Establish baseline
    for _ in range(5):
        engine.record_activity("agent-005", "user:read", "users")
    
    # Now request something unusual
    result = enforcer.evaluate_operation(
        agent_id="agent-005",
        operation="admin:grant",
        context={
            "agent_risk_level": RiskLevel.MEDIUM,
            "resource": "admin",
            "permissions": ["user:read", "admin:grant"],
            "tenant_id": "tenant-abc",
            "recent_actions": ["user:read", "user:read", "user:create"]
        }
    )
    
    print(f"Risk Score: {result['risk_score'].overall_score:.2f}")
    print(f"Risk Level: {result['risk_score'].level.value}")
    print(f"Explanation: {result['risk_score'].explanation}")
    
    # Show summary
    print("\n📊 RISK ASSESSMENT SUMMARY")
    print("-" * 70)
    print(f"Policy Violations: {len(enforcer.policy_violations)}")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    
    print("\n🎓 Key Takeaways:")
    print("  ✅ Multi-factor risk assessment")
    print("  ✅ Permission scope evaluation")
    print("  ✅ Behavioral anomaly detection")
    print("  ✅ Tenant isolation breach detection")
    print("  ✅ Risk-based policy enforcement")


if __name__ == "__main__":
    demo()

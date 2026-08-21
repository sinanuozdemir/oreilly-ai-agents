"""
Permission Validator - Least-Privilege Enforcement for AI Agents

This module implements permission validation and risk assessment
for AI agent operations. It ensures agents only get the minimum
permissions needed for their tasks.

Key Concepts:
- Least privilege principle
- Permission risk classification
- Dynamic permission validation
- Privilege escalation prevention
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk levels for permissions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PermissionType(Enum):
    """Types of permissions"""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass
class Permission:
    """Represents a single permission"""
    resource: str  # e.g., "user", "sso", "admin"
    action: PermissionType
    risk_level: RiskLevel
    description: str
    
    def __str__(self):
        return f"{self.resource}:{self.action.value}"


class PermissionRegistry:
    """
    Central registry of all permissions and their risk levels.
    
    This defines what operations are available and how risky they are.
    """
    
    # Define all known permissions
    PERMISSIONS = {
        # User management permissions
        "user:read": Permission("user", PermissionType.READ, RiskLevel.LOW, "Read user profiles"),
        "user:create": Permission("user", PermissionType.CREATE, RiskLevel.MEDIUM, "Create new users"),
        "user:update": Permission("user", PermissionType.UPDATE, RiskLevel.MEDIUM, "Update user information"),
        "user:delete": Permission("user", PermissionType.DELETE, RiskLevel.HIGH, "Delete users"),
        
        # SSO permissions
        "sso:read": Permission("sso", PermissionType.READ, RiskLevel.LOW, "Read SSO configurations"),
        "sso:create": Permission("sso", PermissionType.CREATE, RiskLevel.MEDIUM, "Create SSO connections"),
        "sso:update": Permission("sso", PermissionType.UPDATE, RiskLevel.HIGH, "Update SSO configurations"),
        "sso:delete": Permission("sso", PermissionType.DELETE, RiskLevel.HIGH, "Delete SSO connections"),
        
        # Admin permissions
        "admin:grant": Permission("admin", PermissionType.ADMIN, RiskLevel.CRITICAL, "Grant permissions to others"),
        "admin:revoke": Permission("admin", PermissionType.ADMIN, RiskLevel.CRITICAL, "Revoke permissions"),
        "admin:configure": Permission("admin", PermissionType.ADMIN, RiskLevel.CRITICAL, "System configuration"),
        
        # Audit permissions
        "audit:read": Permission("audit", PermissionType.READ, RiskLevel.LOW, "Read audit logs"),
        "audit:export": Permission("audit", PermissionType.READ, RiskLevel.MEDIUM, "Export audit logs"),
        
        # Tenant permissions
        "tenant:read": Permission("tenant", PermissionType.READ, RiskLevel.LOW, "Read tenant information"),
        "tenant:update": Permission("tenant", PermissionType.UPDATE, RiskLevel.HIGH, "Update tenant settings"),
        "tenant:delete": Permission("tenant", PermissionType.DELETE, RiskLevel.CRITICAL, "Delete tenant"),
    }
    
    @classmethod
    def get_permission(cls, permission_str: str) -> Optional[Permission]:
        """Get permission details by string"""
        return cls.PERMISSIONS.get(permission_str)
    
    @classmethod
    def get_risk_level(cls, permission_str: str) -> RiskLevel:
        """Get risk level for a permission"""
        perm = cls.PERMISSIONS.get(permission_str)
        return perm.risk_level if perm else RiskLevel.MEDIUM
    
    @classmethod
    def is_destructive(cls, permission_str: str) -> bool:
        """Check if permission is destructive (delete/revoke)"""
        perm = cls.PERMISSIONS.get(permission_str)
        if not perm:
            return False
        return perm.action in [PermissionType.DELETE, PermissionType.ADMIN]
    
    @classmethod
    def is_administrative(cls, permission_str: str) -> bool:
        """Check if permission is administrative"""
        perm = cls.PERMISSIONS.get(permission_str)
        if not perm:
            return False
        return perm.action == PermissionType.ADMIN or perm.risk_level == RiskLevel.CRITICAL
    
    @classmethod
    def get_permissions_by_risk(cls, risk_level: RiskLevel) -> List[str]:
        """Get all permissions with a specific risk level"""
        return [
            key for key, perm in cls.PERMISSIONS.items()
            if perm.risk_level == risk_level
        ]


class PermissionValidator:
    """
    Validates permission requests against security policies.
    
    Implements least-privilege enforcement:
    1. Agents can only request permissions within their classification
    2. High-risk permissions require additional approval
    3. Permission escalation is detected and flagged
    """
    
    # Maximum permissions by agent risk level
    MAX_PERMISSIONS = {
        RiskLevel.LOW: 5,
        RiskLevel.MEDIUM: 10,
        RiskLevel.HIGH: 3,  # High-risk agents get fewer permissions
    }
    
    # Permissions that always require approval
    ALWAYS_APPROVE = {
        "user:delete",
        "sso:delete",
        "admin:grant",
        "admin:revoke",
        "tenant:delete",
    }
    
    def __init__(self):
        self.permission_history: Dict[str, List[str]] = {}
    
    def validate_permission_request(
        self,
        agent_id: str,
        current_permissions: List[str],
        requested_permissions: List[str],
        agent_risk_level: RiskLevel
    ) -> Dict[str, any]:
        """
        Validate a permission request.
        
        Returns:
            {
                "valid": bool,
                "granted": List[str],
                "denied": List[str],
                "requires_approval": List[str],
                "reasons": List[str]
            }
        """
        granted = []
        denied = []
        requires_approval = []
        reasons = []
        
        # Check 1: Maximum permissions limit
        total_requested = len(current_permissions) + len(requested_permissions)
        max_allowed = self.MAX_PERMISSIONS.get(agent_risk_level, 5)
        
        if total_requested > max_allowed:
            reasons.append(
                f"Permission limit exceeded: {total_requested} requested, "
                f"max {max_allowed} for {agent_risk_level.value} risk agents"
            )
            return {
                "valid": False,
                "granted": [],
                "denied": requested_permissions,
                "requires_approval": [],
                "reasons": reasons
            }
        
        # Check each requested permission
        for perm_str in requested_permissions:
            permission = PermissionRegistry.get_permission(perm_str)
            
            if not permission:
                denied.append(perm_str)
                reasons.append(f"Unknown permission: {perm_str}")
                continue
            
            # Check 2: Is it an escalation?
            if self._is_escalation(current_permissions, perm_str):
                requires_approval.append(perm_str)
                reasons.append(f"Permission escalation: {perm_str} requires approval")
                continue
            
            # Check 3: Always requires approval?
            if perm_str in self.ALWAYS_APPROVE:
                requires_approval.append(perm_str)
                reasons.append(f"High-risk permission requires approval: {perm_str}")
                continue
            
            # Check 4: Risk level appropriate for agent?
            if permission.risk_level == RiskLevel.CRITICAL and agent_risk_level != RiskLevel.HIGH:
                requires_approval.append(perm_str)
                reasons.append(f"Critical permission requires approval for {agent_risk_level.value} risk agent")
                continue
            
            # Permission granted
            granted.append(perm_str)
        
        valid = len(denied) == 0
        
        return {
            "valid": valid,
            "granted": granted,
            "denied": denied,
            "requires_approval": requires_approval,
            "reasons": reasons
        }
    
    def _is_escalation(self, current_permissions: List[str], requested: str) -> bool:
        """
        Detect if requested permission is an escalation.
        
        Escalation examples:
        - Having read, requesting write
        - Having user permissions, requesting admin
        """
        current_risks = [
            PermissionRegistry.get_risk_level(p)
            for p in current_permissions
        ]
        
        requested_risk = PermissionRegistry.get_risk_level(requested)
        
        # If requesting higher risk than currently held, it's escalation
        if current_risks:
            max_current = max(current_risks, key=lambda r: self._risk_value(r))
            if self._risk_value(requested_risk) > self._risk_value(max_current):
                return True
        
        # Administrative permissions are always escalation from non-admin
        if PermissionRegistry.is_administrative(requested):
            current_admin = any(
                PermissionRegistry.is_administrative(p)
                for p in current_permissions
            )
            if not current_admin:
                return True
        
        return False
    
    def _risk_value(self, risk: RiskLevel) -> int:
        """Convert risk level to numeric value for comparison"""
        values = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        return values.get(risk, 0)
    
    def track_permission_usage(self, agent_id: str, permission: str):
        """Track how permissions are used for anomaly detection"""
        if agent_id not in self.permission_history:
            self.permission_history[agent_id] = []
        
        self.permission_history[agent_id].append(permission)
    
    def detect_anomalous_permissions(
        self,
        agent_id: str,
        requested_permissions: List[str]
    ) -> List[str]:
        """
        Detect if requested permissions are anomalous for this agent.
        
        Returns list of anomalies detected.
        """
        anomalies = []
        history = self.permission_history.get(agent_id, [])
        
        if not history:
            return anomalies
        
        # Check for permissions never used before
        for perm in requested_permissions:
            if perm not in history:
                anomalies.append(f"New permission requested: {perm}")
        
        # Check for permission diversity spike
        unique_permissions = set(history + requested_permissions)
        if len(unique_permissions) > len(history) * 1.5:
            anomalies.append(
                f"Permission diversity spike: requesting {len(requested_permissions)} "
                f"new permissions (historically uses {len(set(history))})"
            )
        
        # Check for high-risk permission pattern
        high_risk_count = sum(
            1 for p in requested_permissions
            if PermissionRegistry.get_risk_level(p) in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )
        if high_risk_count > 2:
            anomalies.append(f"Multiple high-risk permissions: {high_risk_count}")
        
        return anomalies


class PermissionCache:
    """
    Cache for permission validations to improve performance.
    
    In production, this would use Redis or similar.
    """
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached validation result"""
        import time
        
        entry = self.cache.get(key)
        if not entry:
            return None
        
        # Check TTL
        if time.time() - entry["timestamp"] > self.ttl:
            del self.cache[key]
            return None
        
        return entry["result"]
    
    def set(self, key: str, result: Dict):
        """Cache validation result"""
        import time
        
        self.cache[key] = {
            "result": result,
            "timestamp": time.time()
        }


def demo():
    """Demonstrate permission validation"""
    print("\n" + "="*70)
    print("PERMISSION VALIDATOR - LEAST PRIVILEGE ENFORCEMENT")
    print("="*70)
    
    validator = PermissionValidator()
    
    # Scenario 1: Low-risk agent requesting appropriate permissions
    print("\n📋 SCENARIO 1: Low-risk agent requesting basic permissions")
    print("-" * 70)
    
    result = validator.validate_permission_request(
        agent_id="agent-001",
        current_permissions=["user:read"],
        requested_permissions=["user:create", "user:update"],
        agent_risk_level=RiskLevel.LOW
    )
    
    print(f"Valid: {result['valid']}")
    print(f"Granted: {result['granted']}")
    print(f"Denied: {result['denied']}")
    print(f"Requires Approval: {result['requires_approval']}")
    
    # Scenario 2: Permission escalation
    print("\n📋 SCENARIO 2: Permission escalation detected")
    print("-" * 70)
    
    result = validator.validate_permission_request(
        agent_id="agent-002",
        current_permissions=["user:read", "user:create"],
        requested_permissions=["admin:grant"],
        agent_risk_level=RiskLevel.MEDIUM
    )
    
    print(f"Valid: {result['valid']}")
    print(f"Granted: {result['granted']}")
    print(f"Requires Approval: {result['requires_approval']}")
    if result['reasons']:
        print(f"Reasons: {result['reasons']}")
    
    # Scenario 3: Too many permissions
    print("\n📋 SCENARIO 3: Permission limit exceeded")
    print("-" * 70)
    
    result = validator.validate_permission_request(
        agent_id="agent-003",
        current_permissions=["user:read", "user:create", "user:update", "sso:read", "sso:create"],
        requested_permissions=["user:delete", "sso:delete", "admin:grant"],
        agent_risk_level=RiskLevel.LOW
    )
    
    print(f"Valid: {result['valid']}")
    print(f"Denied: {result['denied']}")
    if result['reasons']:
        print(f"Reason: {result['reasons'][0]}")
    
    # Scenario 4: Anomalous permission request
    print("\n📋 SCENARIO 4: Anomalous permission pattern")
    print("-" * 70)
    
    # First establish history
    validator.track_permission_usage("agent-004", "user:read")
    validator.track_permission_usage("agent-004", "user:read")
    validator.track_permission_usage("agent-004", "user:read")
    
    anomalies = validator.detect_anomalous_permissions(
        "agent-004",
        ["admin:grant", "tenant:delete", "sso:delete"]
    )
    
    print(f"Anomalies detected: {len(anomalies)}")
    for anomaly in anomalies:
        print(f"  ⚠️  {anomaly}")
    
    # Show all permission risk levels
    print("\n📊 PERMISSION RISK CLASSIFICATION")
    print("-" * 70)
    
    for risk in RiskLevel:
        perms = PermissionRegistry.get_permissions_by_risk(risk)
        print(f"{risk.value.upper()}: {len(perms)} permissions")
        for perm in perms[:3]:  # Show first 3
            p = PermissionRegistry.get_permission(perm)
            print(f"  - {perm}: {p.description}")
        if len(perms) > 3:
            print(f"  ... and {len(perms) - 3} more")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    
    print("\n🎓 Key Takeaways:")
    print("  ✅ Permissions classified by risk level")
    print("  ✅ Agents limited by maximum permission count")
    print("  ✅ Escalation detected and flagged for approval")
    print("  ✅ Anomalous patterns identified")
    print("  ✅ Least-privilege enforced automatically")


if __name__ == "__main__":
    demo()

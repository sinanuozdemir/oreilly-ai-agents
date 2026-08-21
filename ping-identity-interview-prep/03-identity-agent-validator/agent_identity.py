"""
Agent Identity & Security Validator - Identity for AI

This module implements the core security concepts for Ping Identity's
"Identity for AI" initiative:

1. Agent Identity Model - How AI agents are represented
2. Permission Validation - Least-privilege enforcement
3. Approval Flows - Human-in-the-loop for high-risk actions
4. Audit Logging - Complete compliance trails

Key Concepts:
- Delegation (not impersonation)
- Least privilege access
- Time-bounded permissions
- Risk-based approval
"""

import uuid
import json
import hashlib
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class AgentType(Enum):
    """Types of AI agents"""
    STANDALONE = "standalone"  # Independent workers (CI/CD, etc.)
    DELEGATED = "delegated"    # Act on behalf of user (email assistant)
    SYSTEM = "system"          # Backend automation (logs, backups)


class RiskLevel(Enum):
    """Risk classification for agents"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApprovalStatus(Enum):
    """Status of approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class AgentIdentity:
    """
    Identity model for AI agents.
    
    Similar to user identity but designed for autonomous agents.
    Implements the "Know Your Agents" principle.
    """
    agent_id: str
    name: str
    agent_type: AgentType
    risk_level: RiskLevel
    owner: str  # Human responsible for this agent
    
    # Capabilities and permissions
    capabilities: List[str] = field(default_factory=list)
    delegated_permissions: List[str] = field(default_factory=list)
    permission_expiry: Optional[datetime] = None
    
    # Security settings
    auth_method: str = "jwt"  # jwt | mtls | api_key
    allowed_ip_ranges: List[str] = field(default_factory=list)
    mfa_required: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    version: str = "1.0"
    
    def is_active(self) -> bool:
        """Check if agent identity is still valid"""
        if self.permission_expiry and datetime.utcnow() > self.permission_expiry:
            return False
        return True
    
    def has_permission(self, permission: str) -> bool:
        """Check if agent has specific permission"""
        return permission in self.delegated_permissions
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type.value,
            "risk_level": self.risk_level.value,
            "owner": self.owner,
            "capabilities": self.capabilities,
            "delegated_permissions": self.delegated_permissions,
            "permission_expiry": self.permission_expiry.isoformat() if self.permission_expiry else None,
            "auth_method": self.auth_method,
            "mfa_required": self.mfa_required,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active()
        }


@dataclass
class OperationRequest:
    """
    Represents a request from an agent to perform an operation.
    
    This is what gets validated by the security system.
    """
    request_id: str
    agent_id: str
    operation: str  # e.g., "user:create", "sso:delete"
    resource: str   # e.g., "tenant-123/users"
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Context
    client_ip: Optional[str] = None
    request_hash: Optional[str] = None  # For integrity
    
    def compute_hash(self) -> str:
        """Compute hash of request for integrity checking"""
        data = f"{self.agent_id}:{self.operation}:{self.resource}:{self.timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class ApprovalRequest:
    """Human approval request for high-risk operations"""
    approval_id: str
    operation_request: OperationRequest
    requested_permissions: List[str]
    justification: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.expires_at is None:
            # Default 5 minute expiry
            self.expires_at = datetime.utcnow() + timedelta(minutes=5)


# ═══════════════════════════════════════════════════════════════════════════════
# PERMISSION & RISK SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class PermissionRegistry:
    """
    Central registry of permissions and their risk levels.
    
    Implements risk classification for least-privilege enforcement.
    """
    
    PERMISSION_RISKS = {
        # Low Risk - Read operations
        "user:read": RiskLevel.LOW,
        "user:list": RiskLevel.LOW,
        "sso:read": RiskLevel.LOW,
        "sso:list": RiskLevel.LOW,
        "logs:read": RiskLevel.LOW,
        "config:read": RiskLevel.LOW,
        
        # Medium Risk - Create/Update operations
        "user:create": RiskLevel.MEDIUM,
        "user:update": RiskLevel.MEDIUM,
        "sso:create": RiskLevel.MEDIUM,
        "sso:update": RiskLevel.MEDIUM,
        "config:update": RiskLevel.MEDIUM,
        
        # High Risk - Destructive/Administrative operations
        "user:delete": RiskLevel.HIGH,
        "sso:delete": RiskLevel.HIGH,
        "admin:grant": RiskLevel.HIGH,
        "admin:revoke": RiskLevel.HIGH,
        "permissions:escalate": RiskLevel.HIGH,
        "system:configure": RiskLevel.HIGH,
    }
    
    @classmethod
    def get_risk_level(cls, permission: str) -> RiskLevel:
        """Get risk level for a permission"""
        return cls.PERMISSION_RISKS.get(permission, RiskLevel.MEDIUM)
    
    @classmethod
    def is_destructive(cls, permission: str) -> bool:
        """Check if permission is destructive"""
        return ":delete" in permission or ":revoke" in permission
    
    @classmethod
    def is_administrative(cls, permission: str) -> bool:
        """Check if permission is administrative"""
        return permission.startswith("admin:") or permission.startswith("system:")


class AgentRiskPolicy:
    """
    Risk policies based on agent type.
    
    Different agent types have different default permissions
    and approval requirements.
    """
    
    POLICIES = {
        AgentType.STANDALONE: {
            "max_permissions": 10,
            "default_risk": RiskLevel.MEDIUM,
            "mfa_required": True,
            "require_approval_for": ["delete", "grant_permissions", "system"],
            "permission_duration_minutes": 60
        },
        AgentType.DELEGATED: {
            "max_permissions": 5,
            "default_risk": RiskLevel.LOW,
            "mfa_required": False,
            "require_approval_for": ["delete", "admin"],
            "permission_duration_minutes": 30
        },
        AgentType.SYSTEM: {
            "max_permissions": 3,
            "default_risk": RiskLevel.HIGH,
            "mfa_required": True,
            "require_approval_for": ["all"],  # All operations need approval
            "permission_duration_minutes": 15
        }
    }
    
    @classmethod
    def get_policy(cls, agent_type: AgentType) -> Dict:
        """Get policy for agent type"""
        return cls.POLICIES.get(agent_type, cls.POLICIES[AgentType.DELEGATED])
    
    @classmethod
    def requires_approval(cls, agent_type: AgentType, permission: str) -> bool:
        """Check if operation requires approval for this agent type"""
        policy = cls.get_policy(agent_type)
        approval_list = policy.get("require_approval_for", [])
        
        if "all" in approval_list:
            return True
        
        for pattern in approval_list:
            if pattern in permission:
                return True
        
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ValidationResult:
    """Result of security validation"""
    def __init__(self, allowed: bool, reason: str = "", details: Optional[Dict] = None):
        self.allowed = allowed
        self.reason = reason
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def __bool__(self):
        return self.allowed
    
    def __repr__(self):
        status = "✅ ALLOWED" if self.allowed else "❌ DENIED"
        return f"{status}: {self.reason}"


class IdentityValidator:
    """
    Main validation engine for agent operations.
    
    Implements the 5-layer security model:
    1. Agent identity validation
    2. Permission checking (least privilege)
    3. Risk assessment
    4. Approval flow (human-in-the-loop)
    5. Audit logging
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentIdentity] = {}
        self.audit_logs: List[Dict] = []
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.permission_history: Dict[str, List[Dict]] = {}  # Track permission usage
    
    def register_agent(self, agent: AgentIdentity):
        """Register an agent in the system"""
        self.agents[agent.agent_id] = agent
        self._audit_log("agent.registered", agent.agent_id, {
            "agent_type": agent.agent_type.value,
            "owner": agent.owner,
            "risk_level": agent.risk_level.value
        })
    
    async def validate_operation(
        self,
        request: OperationRequest
    ) -> ValidationResult:
        """
        Validate an operation request from an agent.
        
        This is the main entry point - validates all 5 layers.
        """
        print(f"\n🔍 Validating Operation: {request.operation}")
        print(f"   Agent: {request.agent_id}")
        print(f"   Resource: {request.resource}")
        
        # Layer 1: Validate Agent Identity
        agent = self.agents.get(request.agent_id)
        if not agent:
            return ValidationResult(
                allowed=False,
                reason="Agent not registered",
                details={"agent_id": request.agent_id}
            )
        
        if not agent.is_active():
            return ValidationResult(
                allowed=False,
                reason="Agent identity expired",
                details={"expiry": agent.permission_expiry.isoformat() if agent.permission_expiry else None}
            )
        
        print(f"   ✅ Agent identity valid ({agent.agent_type.value}, {agent.risk_level.value} risk)")
        
        # Layer 2: Check Permission (Least Privilege)
        if not agent.has_permission(request.operation):
            self._audit_log("permission.denied", request.agent_id, {
                "operation": request.operation,
                "has_permissions": agent.delegated_permissions
            })
            return ValidationResult(
                allowed=False,
                reason=f"Agent lacks permission: {request.operation}",
                details={
                    "required": request.operation,
                    "has": agent.delegated_permissions
                }
            )
        
        print(f"   ✅ Permission granted: {request.operation}")
        
        # Layer 3: Risk Assessment
        permission_risk = PermissionRegistry.get_risk_level(request.operation)
        policy = AgentRiskPolicy.get_policy(agent.agent_type)
        
        # Check if this is high-risk
        is_high_risk = (
            permission_risk == RiskLevel.HIGH or
            PermissionRegistry.is_destructive(request.operation) or
            AgentRiskPolicy.requires_approval(agent.agent_type, request.operation)
        )
        
        # Layer 4: Human-in-the-Loop for high-risk
        if is_high_risk:
            print(f"   ⚠️  High-risk operation - approval required")
            
            approval_result = await self._request_approval(request, agent)
            
            if not approval_result:
                return ValidationResult(
                    allowed=False,
                    reason="Approval required but not obtained",
                    details={"requires_human_approval": True}
                )
            
            print(f"   ✅ Human approval obtained")
        
        # Layer 5: Audit Logging
        self._audit_log("operation.allowed", request.agent_id, {
            "operation": request.operation,
            "resource": request.resource,
            "risk_level": permission_risk.value,
            "approval_required": is_high_risk
        })
        
        # Track permission usage
        self._track_permission_usage(request)
        
        print(f"   ✅ Operation ALLOWED")
        
        return ValidationResult(
            allowed=True,
            reason="All validations passed",
            details={
                "agent_type": agent.agent_type.value,
                "risk_level": permission_risk.value,
                "approval_required": is_high_risk
            }
        )
    
    async def _request_approval(
        self,
        request: OperationRequest,
        agent: AgentIdentity
    ) -> bool:
        """
        Request human approval for high-risk operation.
        
        In production, this would:
        1. Send push notification to agent owner
        2. Wait for response (with timeout)
        3. Log the approval decision
        """
        approval_id = str(uuid.uuid4())[:8]
        
        approval_req = ApprovalRequest(
            approval_id=approval_id,
            operation_request=request,
            requested_permissions=[request.operation],
            justification=f"Agent {agent.name} ({agent.agent_id}) requests {request.operation} on {request.resource}"
        )
        
        self.pending_approvals[approval_id] = approval_req
        
        print(f"\n   📧 Approval Request Sent to {agent.owner}")
        print(f"      Request ID: {approval_id}")
        print(f"      Justification: {approval_req.justification}")
        print(f"      Expires: {approval_req.expires_at.isoformat()}")
        
        # Simulate approval (in production, wait for human response)
        # For demo, auto-approve after short delay
        await asyncio.sleep(0.5)
        
        approval_req.status = ApprovalStatus.APPROVED
        approval_req.approved_by = agent.owner
        approval_req.approved_at = datetime.utcnow()
        
        self._audit_log("approval.granted", agent.agent_id, {
            "approval_id": approval_id,
            "operation": request.operation,
            "approved_by": agent.owner
        })
        
        return True
    
    def _audit_log(self, event_type: str, agent_id: str, details: Dict):
        """Write audit log entry"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "agent_id": agent_id,
            "details": details
        }
        self.audit_logs.append(entry)
        print(f"   📝 Audit: {event_type}")
    
    def _track_permission_usage(self, request: OperationRequest):
        """Track how permissions are being used"""
        if request.agent_id not in self.permission_history:
            self.permission_history[request.agent_id] = []
        
        self.permission_history[request.agent_id].append({
            "timestamp": request.timestamp.isoformat(),
            "operation": request.operation,
            "resource": request.resource
        })
    
    def get_audit_trail(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Get audit trail for compliance"""
        if agent_id:
            return [log for log in self.audit_logs if log["agent_id"] == agent_id]
        return self.audit_logs
    
    def detect_anomalies(self, agent_id: str) -> List[Dict]:
        """
        Detect anomalous behavior patterns.
        
        Looks for:
        - Unusual permission usage
        - Operations outside normal hours
        - Sudden spikes in activity
        """
        anomalies = []
        history = self.permission_history.get(agent_id, [])
        
        if len(history) < 3:
            return anomalies
        
        # Check for unusual operations
        recent_ops = [h["operation"] for h in history[-10:]]
        unique_ops = set(recent_ops)
        
        # If agent suddenly using many different operations, flag it
        if len(unique_ops) > 5:
            anomalies.append({
                "type": "permission_diversity_spike",
                "message": f"Agent using {len(unique_ops)} different operations recently",
                "severity": "medium"
            })
        
        # Check for destructive operations
        destructive = [op for op in recent_ops if PermissionRegistry.is_destructive(op)]
        if len(destructive) > 2:
            anomalies.append({
                "type": "destructive_operation_spike",
                "message": f"Agent performed {len(destructive)} destructive operations recently",
                "severity": "high"
            })
        
        return anomalies


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

async def demo():
    """Demonstrate Identity for AI security concepts"""
    print("\n" + "="*70)
    print("IDENTITY FOR AI - SECURITY VALIDATION DEMO")
    print("="*70)
    print("\nDemonstrating Ping Identity's Identity for AI principles:")
    print("  1. Know Your Agents")
    print("  2. Delegation, Not Impersonation")
    print("  3. Least Privilege")
    print("  4. Human-in-the-Loop")
    print("  5. Monitor Everything")
    
    # Initialize validator
    validator = IdentityValidator()
    
    # Create agent identities
    print("\n" + "-"*70)
    print("Creating Agent Identities")
    print("-"*70)
    
    # 1. Standalone Agent (CI/CD bot)
    cicd_agent = AgentIdentity(
        agent_id="agent-cicd-001",
        name="CI/CD Pipeline Agent",
        agent_type=AgentType.STANDALONE,
        risk_level=RiskLevel.MEDIUM,
        owner="devops@company.com",
        capabilities=["deploy", "test", "build"],
        delegated_permissions=["config:read", "config:update"],
        mfa_required=True
    )
    validator.register_agent(cicd_agent)
    print(f"✅ Registered: {cicd_agent.name} ({cicd_agent.agent_type.value})")
    
    # 2. Delegated Agent (Email assistant)
    email_agent = AgentIdentity(
        agent_id="agent-email-001",
        name="Email Assistant",
        agent_type=AgentType.DELEGATED,
        risk_level=RiskLevel.LOW,
        owner="user@company.com",
        capabilities=["read_email", "send_email", "schedule"],
        delegated_permissions=["user:read", "logs:read"],
        mfa_required=False
    )
    validator.register_agent(email_agent)
    print(f"✅ Registered: {email_agent.name} ({email_agent.agent_type.value})")
    
    # 3. System Agent (High risk - admin operations)
    admin_agent = AgentIdentity(
        agent_id="agent-admin-001",
        name="System Administrator Agent",
        agent_type=AgentType.SYSTEM,
        risk_level=RiskLevel.HIGH,
        owner="admin@company.com",
        capabilities=["user_manage", "permissions", "system_config"],
        delegated_permissions=["user:read", "user:create", "admin:grant"],
        mfa_required=True
    )
    validator.register_agent(admin_agent)
    print(f"✅ Registered: {admin_agent.name} ({admin_agent.agent_type.value})")
    
    # Scenario 1: Legitimate operation
    print("\n" + "-"*70)
    print("SCENARIO 1: Legitimate Operation (Delegated Agent - Read)")
    print("-"*70)
    
    request1 = OperationRequest(
        request_id="req-001",
        agent_id="agent-email-001",
        operation="user:read",
        resource="tenant-123/users"
    )
    
    result1 = await validator.validate_operation(request1)
    print(f"\nResult: {result1}")
    
    # Scenario 2: Unauthorized operation
    print("\n" + "-"*70)
    print("SCENARIO 2: Unauthorized Operation (No Permission)")
    print("-"*70)
    
    request2 = OperationRequest(
        request_id="req-002",
        agent_id="agent-email-001",
        operation="user:delete",  # Email agent doesn't have this!
        resource="tenant-123/users/456"
    )
    
    result2 = await validator.validate_operation(request2)
    print(f"\nResult: {result2}")
    
    # Scenario 3: High-risk operation requiring approval
    print("\n" + "-"*70)
    print("SCENARIO 3: High-Risk Operation (Admin Agent - Delete)")
    print("-"*70)
    
    request3 = OperationRequest(
        request_id="req-003",
        agent_id="agent-admin-001",
        operation="user:delete",
        resource="tenant-123/users/789"
    )
    
    result3 = await validator.validate_operation(request3)
    print(f"\nResult: {result3}")
    
    # Scenario 4: Unknown agent
    print("\n" + "-"*70)
    print("SCENARIO 4: Unknown Agent (Security Risk)")
    print("-"*70)
    
    request4 = OperationRequest(
        request_id="req-004",
        agent_id="agent-unknown-999",
        operation="user:read",
        resource="tenant-123/users"
    )
    
    result4 = await validator.validate_operation(request4)
    print(f"\nResult: {result4}")
    
    # Scenario 5: Anomaly detection
    print("\n" + "-"*70)
    print("SCENARIO 5: Anomaly Detection")
    print("-"*70)
    
    # Simulate suspicious activity
    for i in range(5):
        req = OperationRequest(
            request_id=f"req-anomaly-{i}",
            agent_id="agent-admin-001",
            operation="user:delete",
            resource=f"tenant-123/users/{i}"
        )
        await validator.validate_operation(req)
    
    anomalies = validator.detect_anomalies("agent-admin-001")
    if anomalies:
        print(f"\n⚠️  Anomalies Detected:")
        for a in anomalies:
            print(f"   - {a['type']}: {a['message']} (severity: {a['severity']})")
    
    # Print audit trail
    print("\n" + "="*70)
    print("AUDIT TRAIL SUMMARY")
    print("="*70)
    
    print(f"\nTotal audit events: {len(validator.audit_logs)}")
    
    event_types = {}
    for log in validator.audit_logs:
        et = log["event_type"]
        event_types[et] = event_types.get(et, 0) + 1
    
    print("\nEvent breakdown:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count}")
    
    # Print final summary
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    
    print("\n🎓 Key Concepts Demonstrated:")
    print("  ✅ Agent Identity - Each agent has unique identity and classification")
    print("  ✅ Delegation - Agents have scoped permissions, not full user access")
    print("  ✅ Least Privilege - Agents denied operations without explicit permission")
    print("  ✅ Human-in-the-Loop - High-risk operations require approval")
    print("  ✅ Audit Logging - All actions logged for compliance")
    print("  ✅ Anomaly Detection - System detects unusual behavior patterns")
    
    print("\n💼 Interview Gold:")
    print("  'I implemented a 5-layer security model for AI agents based on")
    print("   Identity for AI principles: identity validation, least-privilege")
    print("   enforcement, risk-based approval, and comprehensive audit trails.'")


if __name__ == "__main__":
    asyncio.run(demo())

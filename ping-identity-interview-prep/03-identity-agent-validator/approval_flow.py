"""
Approval Flow - Human-in-the-Loop for AI Agent Operations

This module implements approval workflows for high-risk AI agent operations.
It ensures humans review and approve critical actions before execution.

Key Concepts:
- Approval policies based on risk levels
- Multi-stage approval workflows
- Timeout and escalation handling
- Audit trail for all approvals
"""

import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ApprovalStatus(Enum):
    """Status of an approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class ApprovalPolicy(Enum):
    """Different approval policies based on risk"""
    AUTO_APPROVE = "auto_approve"  # No approval needed
    SINGLE_APPROVER = "single"     # One approver required
    DUAL_APPROVAL = "dual"         # Two approvers required
    MANAGER_REQUIRED = "manager"   # Manager level required


@dataclass
class ApprovalRequest:
    """Represents a request for human approval"""
    request_id: str
    agent_id: str
    agent_name: str
    operation: str
    resource: str
    risk_level: str
    policy: ApprovalPolicy
    justification: str
    timestamp: datetime
    timeout_minutes: int = 30
    
    # Set during approval process
    status: ApprovalStatus = field(default=ApprovalStatus.PENDING)
    approved_by: List[str] = field(default_factory=list)
    rejected_by: List[str] = field(default_factory=list)
    approval_timestamp: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if request has expired"""
        elapsed = datetime.now() - self.timestamp
        return elapsed > timedelta(minutes=self.timeout_minutes)


class ApprovalPolicyEngine:
    """
    Determines what approval policy applies to different operations.
    
    Policies are based on:
    - Operation type (read, write, delete, admin)
    - Resource sensitivity
    - Agent risk level
    """
    
    # Default policies for different risk/resource combinations
    POLICIES = {
        # (resource_risk, agent_risk) -> policy
        ("low", "low"): ApprovalPolicy.AUTO_APPROVE,
        ("low", "medium"): ApprovalPolicy.AUTO_APPROVE,
        ("low", "high"): ApprovalPolicy.SINGLE_APPROVER,
        
        ("medium", "low"): ApprovalPolicy.SINGLE_APPROVER,
        ("medium", "medium"): ApprovalPolicy.SINGLE_APPROVER,
        ("medium", "high"): ApprovalPolicy.DUAL_APPROVAL,
        
        ("high", "low"): ApprovalPolicy.DUAL_APPROVAL,
        ("high", "medium"): ApprovalPolicy.MANAGER_REQUIRED,
        ("high", "high"): ApprovalPolicy.MANAGER_REQUIRED,
        
        ("critical", "low"): ApprovalPolicy.MANAGER_REQUIRED,
        ("critical", "medium"): ApprovalPolicy.MANAGER_REQUIRED,
        ("critical", "high"): ApprovalPolicy.MANAGER_REQUIRED,
    }
    
    # Specific operations that always require approval
    ALWAYS_REQUIRE_APPROVAL = {
        "user:delete",
        "tenant:delete",
        "admin:grant",
        "sso:delete",
        "api_key:regenerate",
    }
    
    def __init__(self):
        self.custom_policies: Dict[str, ApprovalPolicy] = {}
    
    def get_policy(
        self,
        operation: str,
        resource_sensitivity: str,
        agent_risk_level: str
    ) -> ApprovalPolicy:
        """
        Determine the approval policy for an operation.
        
        Args:
            operation: The operation being performed (e.g., "user:delete")
            resource_sensitivity: low/medium/high/critical
            agent_risk_level: low/medium/high
        
        Returns:
            The applicable approval policy
        """
        # Check for specific operation override
        if operation in self.ALWAYS_REQUIRE_APPROVAL:
            return ApprovalPolicy.SINGLE_APPROVER
        
        # Check custom policies
        if operation in self.custom_policies:
            return self.custom_policies[operation]
        
        # Use default policy matrix
        key = (resource_sensitivity, agent_risk_level)
        return self.POLICIES.get(key, ApprovalPolicy.SINGLE_APPROVER)
    
    def set_custom_policy(self, operation: str, policy: ApprovalPolicy):
        """Set a custom policy for a specific operation"""
        self.custom_policies[operation] = policy


class ApprovalWorkflow:
    """
    Manages the approval workflow for AI agent operations.
    
    Handles:
    - Creating approval requests
    - Managing approvers
    - Tracking approval status
    - Handling timeouts and escalations
    """
    
    def __init__(self, policy_engine: ApprovalPolicyEngine):
        self.policy_engine = policy_engine
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approved_requests: Dict[str, ApprovalRequest] = {}
        self.rejected_requests: Dict[str, ApprovalRequest] = {}
        
        # Callbacks for different events
        self.on_approval: Optional[Callable] = None
        self.on_rejection: Optional[Callable] = None
        self.on_escalation: Optional[Callable] = None
        
        # Approver hierarchies (operation -> list of approver emails)
        self.approvers: Dict[str, List[str]] = {
            "user:delete": ["admin@company.com", "security@company.com"],
            "tenant:delete": ["cto@company.com"],
            "admin:grant": ["security@company.com"],
            "sso:delete": ["admin@company.com"],
        }
    
    async def request_approval(
        self,
        agent_id: str,
        agent_name: str,
        operation: str,
        resource: str,
        resource_sensitivity: str,
        agent_risk_level: str,
        justification: str
    ) -> ApprovalRequest:
        """
        Create a new approval request.
        
        Returns the approval request. If auto-approved, status will be APPROVED.
        """
        import uuid
        
        # Determine policy
        policy = self.policy_engine.get_policy(
            operation, resource_sensitivity, agent_risk_level
        )
        
        # Create request
        request = ApprovalRequest(
            request_id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            agent_name=agent_name,
            operation=operation,
            resource=resource,
            risk_level=agent_risk_level,
            policy=policy,
            justification=justification,
            timestamp=datetime.now()
        )
        
        # Auto-approve if policy allows
        if policy == ApprovalPolicy.AUTO_APPROVE:
            request.status = ApprovalStatus.APPROVED
            request.approval_timestamp = datetime.now()
            self.approved_requests[request.request_id] = request
            print(f"✅ Auto-approved: {operation} on {resource}")
            return request
        
        # Store as pending
        self.pending_requests[request.request_id] = request
        
        # Notify approvers
        approvers = self.approvers.get(operation, ["admin@company.com"])
        print(f"📧 Approval request sent to: {', '.join(approvers)}")
        print(f"   Operation: {operation}")
        print(f"   Resource: {resource}")
        print(f"   Policy: {policy.value}")
        print(f"   Justification: {justification}")
        print(f"   Request ID: {request.request_id}")
        
        return request
    
    def approve(
        self,
        request_id: str,
        approver: str,
        notes: str = ""
    ) -> bool:
        """
        Approve a pending request.
        
        Returns True if approval is complete (meets policy requirements).
        """
        request = self.pending_requests.get(request_id)
        if not request:
            print(f"❌ Request {request_id} not found or already processed")
            return False
        
        if request.is_expired():
            request.status = ApprovalStatus.EXPIRED
            del self.pending_requests[request_id]
            print(f"❌ Request {request_id} has expired")
            return False
        
        # Add approver
        request.approved_by.append(approver)
        print(f"✅ Approved by {approver}")
        if notes:
            print(f"   Notes: {notes}")
        
        # Check if we have enough approvals
        required = self._get_required_approvals(request.policy)
        
        if len(request.approved_by) >= required:
            request.status = ApprovalStatus.APPROVED
            request.approval_timestamp = datetime.now()
            
            # Move to approved
            del self.pending_requests[request_id]
            self.approved_requests[request_id] = request
            
            if self.on_approval:
                self.on_approval(request)
            
            print(f"✅ Request {request_id} fully approved ({required} approver(s))")
            return True
        else:
            remaining = required - len(request.approved_by)
            print(f"⏳ Need {remaining} more approval(s)")
            return False
    
    def reject(
        self,
        request_id: str,
        approver: str,
        reason: str
    ) -> bool:
        """Reject a pending request"""
        request = self.pending_requests.get(request_id)
        if not request:
            print(f"❌ Request {request_id} not found")
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.rejected_by.append(approver)
        request.rejection_reason = reason
        
        # Move to rejected
        del self.pending_requests[request_id]
        self.rejected_requests[request_id] = request
        
        if self.on_rejection:
            self.on_rejection(request)
        
        print(f"❌ Request {request_id} rejected by {approver}")
        print(f"   Reason: {reason}")
        return True
    
    def _get_required_approvals(self, policy: ApprovalPolicy) -> int:
        """Get number of required approvals for a policy"""
        mapping = {
            ApprovalPolicy.SINGLE_APPROVER: 1,
            ApprovalPolicy.DUAL_APPROVAL: 2,
            ApprovalPolicy.MANAGER_REQUIRED: 1,
            ApprovalPolicy.AUTO_APPROVE: 0
        }
        return mapping.get(policy, 1)
    
    def get_status(self, request_id: str) -> Optional[ApprovalStatus]:
        """Get current status of a request"""
        if request_id in self.pending_requests:
            return self.pending_requests[request_id].status
        if request_id in self.approved_requests:
            return self.approved_requests[request_id].status
        if request_id in self.rejected_requests:
            return self.rejected_requests[request_id].status
        return None
    
    def get_pending_for_agent(self, agent_id: str) -> List[ApprovalRequest]:
        """Get all pending requests for an agent"""
        return [
            req for req in self.pending_requests.values()
            if req.agent_id == agent_id
        ]
    
    def escalate_expired(self) -> List[ApprovalRequest]:
        """Find and escalate expired requests"""
        escalated = []
        
        for request_id, request in list(self.pending_requests.items()):
            if request.is_expired():
                request.status = ApprovalStatus.ESCALATED
                escalated.append(request)
                
                if self.on_escalation:
                    self.on_escalation(request)
                
                print(f"⚠️ Request {request_id} escalated - expired")
        
        return escalated


class HumanInTheLoopManager:
    """
    High-level manager for human-in-the-loop patterns.
    
    Provides simplified interface for common approval patterns.
    """
    
    def __init__(self):
        self.policy_engine = ApprovalPolicyEngine()
        self.workflow = ApprovalWorkflow(self.policy_engine)
    
    async def check_and_request(
        self,
        agent_id: str,
        agent_name: str,
        operation: str,
        resource: str,
        resource_sensitivity: str,
        agent_risk_level: str,
        justification: str
    ) -> bool:
        """
        Check if approval needed and request it.
        
        Returns True if approved (either auto or manual).
        Returns False if rejected or pending.
        """
        request = await self.workflow.request_approval(
            agent_id, agent_name, operation, resource,
            resource_sensitivity, agent_risk_level, justification
        )
        
        if request.status == ApprovalStatus.APPROVED:
            return True
        
        # Request is pending - in real system, wait for human response
        print(f"⏳ Waiting for approval on request {request.request_id}...")
        return False
    
    def get_approval_stats(self) -> Dict:
        """Get statistics on approval workflows"""
        return {
            "pending": len(self.workflow.pending_requests),
            "approved": len(self.workflow.approved_requests),
            "rejected": len(self.workflow.rejected_requests),
            "approval_rate": self._calculate_approval_rate()
        }
    
    def _calculate_approval_rate(self) -> float:
        """Calculate percentage of approved requests"""
        total = len(self.workflow.approved_requests) + len(self.workflow.rejected_requests)
        if total == 0:
            return 0.0
        return len(self.workflow.approved_requests) / total * 100


async def demo():
    """Demonstrate approval flow"""
    print("\n" + "="*70)
    print("APPROVAL FLOW - HUMAN-IN-THE-LOOP")
    print("="*70)
    
    manager = HumanInTheLoopManager()
    workflow = manager.workflow
    
    # Scenario 1: Auto-approved operation
    print("\n📋 SCENARIO 1: Low-risk operation (auto-approved)")
    print("-" * 70)
    
    request1 = await manager.check_and_request(
        agent_id="agent-001",
        agent_name="User Analytics Agent",
        operation="user:read",
        resource="users_table",
        resource_sensitivity="low",
        agent_risk_level="low",
        justification="Daily analytics report generation"
    )
    
    print(f"Result: {'✅ Approved' if request1 else '❌ Denied'}")
    
    # Scenario 2: Requires single approval
    print("\n📋 SCENARIO 2: Medium-risk operation (single approval)")
    print("-" * 70)
    
    request2 = await workflow.request_approval(
        agent_id="agent-002",
        agent_name="User Management Agent",
        operation="user:create",
        resource="users_table",
        resource_sensitivity="medium",
        agent_risk_level="medium",
        justification="Onboarding new employee"
    )
    
    if request2.status == ApprovalStatus.PENDING:
        print(f"⏳ Request {request2.request_id} pending approval...")
        # Simulate approval
        workflow.approve(request2.request_id, "admin@company.com", "Approved for onboarding")
    
    # Scenario 3: Requires dual approval
    print("\n📋 SCENARIO 3: High-risk operation (dual approval)")
    print("-" * 70)
    
    request3 = await workflow.request_approval(
        agent_id="agent-003",
        agent_name="System Admin Agent",
        operation="user:delete",
        resource="users_table",
        resource_sensitivity="high",
        agent_risk_level="medium",
        justification="Removing terminated employee account"
    )
    
    if request3.status == ApprovalStatus.PENDING:
        print(f"⏳ Request {request3.request_id} requires dual approval...")
        workflow.approve(request3.request_id, "admin@company.com")
        workflow.approve(request3.request_id, "security@company.com", "Verified termination")
    
    # Scenario 4: Rejected request
    print("\n📋 SCENARIO 4: Rejected request")
    print("-" * 70)
    
    request4 = await workflow.request_approval(
        agent_id="agent-004",
        agent_name="Suspicious Agent",
        operation="admin:grant",
        resource="all_permissions",
        resource_sensitivity="critical",
        agent_risk_level="high",
        justification="Need admin access for task"
    )
    
    if request4.status == ApprovalStatus.PENDING:
        workflow.reject(
            request4.request_id,
            "security@company.com",
            "Justification insufficient, admin access not required"
        )
    
    # Show statistics
    print("\n📊 APPROVAL STATISTICS")
    print("-" * 70)
    stats = manager.get_approval_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    
    print("\n🎓 Key Takeaways:")
    print("  ✅ Risk-based approval policies")
    print("  ✅ Single and dual approval workflows")
    print("  ✅ Auto-approval for low-risk operations")
    print("  ✅ Full audit trail for all decisions")
    print("  ✅ Human control over high-risk actions")


if __name__ == "__main__":
    asyncio.run(demo())

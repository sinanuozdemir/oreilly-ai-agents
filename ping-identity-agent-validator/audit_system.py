"""
Audit System - Compliance Logging for AI Agent Operations

This module implements comprehensive audit logging for all AI agent
activities. It ensures every action is tracked for compliance,
forensics, and performance monitoring.

Key Concepts:
- Immutable audit logs
- Structured event recording
- Tamper-evident logging
- Compliance reporting
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import asyncio


class EventType(Enum):
    """Types of audit events"""
    # Identity events
    IDENTITY_CREATED = "identity_created"
    IDENTITY_UPDATED = "identity_updated"
    IDENTITY_DELETED = "identity_deleted"
    IDENTITY_ACCESSED = "identity_accessed"
    
    # Permission events
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    PERMISSION_DENIED = "permission_denied"
    PERMISSION_CHECKED = "permission_checked"
    
    # Action events
    ACTION_EXECUTED = "action_executed"
    ACTION_FAILED = "action_failed"
    ACTION_BLOCKED = "action_blocked"
    
    # Approval events
    APPROVAL_REQUESTED = "approval_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    
    # Security events
    SECURITY_VIOLATION = "security_violation"
    RISK_DETECTED = "risk_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    
    # System events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    RATE_LIMIT_HIT = "rate_limit_hit"


class Severity(Enum):
    """Event severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Represents a single audit event.
    
    All events include:
    - Timestamp (UTC)
    - Event type and severity
    - Agent and tenant context
    - Action details
    - Outcome and result
    - Chain hash for tamper detection
    """
    # Event identification
    event_id: str
    timestamp: datetime
    event_type: EventType
    severity: Severity
    
    # Actor information
    agent_id: str
    agent_name: str
    tenant_id: str
    user_id: Optional[str] = None  # Human user if applicable
    
    # Event details
    action: str
    resource: str
    resource_id: Optional[str] = None
    
    # Outcome
    success: bool
    result: Optional[str] = None
    error_message: Optional[str] = None
    
    # Context
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Chain hash for tamper detection
    previous_hash: Optional[str] = None
    chain_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def compute_hash(self) -> str:
        """Compute hash of this event for chain verification"""
        data = self.to_dict()
        # Remove chain_hash from data before computing
        data.pop('chain_hash', None)
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]


class AuditLogChain:
    """
    Implements a tamper-evident audit log using blockchain-like chaining.
    
    Each event includes the hash of the previous event, creating a
    chain that detects any modification to historical records.
    """
    
    def __init__(self):
        self.events: List[AuditEvent] = []
        self.last_hash: Optional[str] = None
    
    def append(self, event: AuditEvent) -> AuditEvent:
        """
        Add an event to the chain with tamper-evident hashing.
        """
        # Set chain references
        event.previous_hash = self.last_hash
        event.chain_hash = event.compute_hash()
        
        # Store event
        self.events.append(event)
        self.last_hash = event.chain_hash
        
        return event
    
    def verify_chain(self) -> Dict[str, any]:
        """
        Verify the integrity of the audit chain.
        
        Returns verification result with any tampering detected.
        """
        violations = []
        
        for i, event in enumerate(self.events):
            # Verify chain hash
            computed = event.compute_hash()
            if computed != event.chain_hash:
                violations.append({
                    "index": i,
                    "event_id": event.event_id,
                    "issue": "hash_mismatch",
                    "computed": computed,
                    "stored": event.chain_hash
                })
            
            # Verify chain linkage (skip first event)
            if i > 0:
                prev_event = self.events[i - 1]
                if event.previous_hash != prev_event.chain_hash:
                    violations.append({
                        "index": i,
                        "event_id": event.event_id,
                        "issue": "chain_broken",
                        "expected_previous": prev_event.chain_hash,
                        "actual_previous": event.previous_hash
                    })
        
        return {
            "valid": len(violations) == 0,
            "total_events": len(self.events),
            "violations": violations
        }
    
    def get_events_for_agent(self, agent_id: str) -> List[AuditEvent]:
        """Get all events for a specific agent"""
        return [e for e in self.events if e.agent_id == agent_id]
    
    def get_events_for_tenant(self, tenant_id: str) -> List[AuditEvent]:
        """Get all events for a specific tenant"""
        return [e for e in self.events if e.tenant_id == tenant_id]
    
    def get_security_events(self) -> List[AuditEvent]:
        """Get all security-related events"""
        security_types = {
            EventType.SECURITY_VIOLATION,
            EventType.RISK_DETECTED,
            EventType.ANOMALY_DETECTED,
            EventType.PERMISSION_DENIED
        }
        return [e for e in self.events if e.event_type in security_types]


class AuditLogger:
    """
    Main audit logging system.
    
    Provides:
    - Structured event logging
    - Chain-based tamper detection
    - Compliance reporting
    - Real-time monitoring
    """
    
    def __init__(self):
        self.chain = AuditLogChain()
        self.event_counter = 0
        
        # Handlers for different outputs
        self.console_handler = True
        self.file_handler: Optional[str] = None
        self.external_handlers: List[callable] = []
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        self.event_counter += 1
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"EVT-{timestamp}-{self.event_counter:06d}"
    
    def log(
        self,
        event_type: EventType,
        severity: Severity,
        agent_id: str,
        agent_name: str,
        tenant_id: str,
        action: str,
        resource: str,
        success: bool,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> AuditEvent:
        """
        Log an audit event.
        """
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            agent_id=agent_id,
            agent_name=agent_name,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            success=success,
            result=result,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        # Add to chain
        self.chain.append(event)
        
        # Output to console
        if self.console_handler:
            self._output_to_console(event)
        
        # Output to file if configured
        if self.file_handler:
            self._output_to_file(event)
        
        # Call external handlers
        for handler in self.external_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"External handler error: {e}")
        
        return event
    
    def _output_to_console(self, event: AuditEvent):
        """Output event to console"""
        status = "✅" if event.success else "❌"
        print(f"[{event.timestamp.strftime('%H:%M:%S')}] "
              f"{status} {event.event_type.value} | "
              f"{event.agent_name} | {event.action}")
        
        if event.error_message:
            print(f"   Error: {event.error_message}")
    
    def _output_to_file(self, event: AuditEvent):
        """Output event to file"""
        if self.file_handler:
            with open(self.file_handler, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
    
    def log_identity_created(self, agent_id: str, agent_name: str, tenant_id: str, metadata: Dict):
        """Log identity creation"""
        return self.log(
            event_type=EventType.IDENTITY_CREATED,
            severity=Severity.INFO,
            agent_id=agent_id,
            agent_name=agent_name,
            tenant_id=tenant_id,
            action="create_identity",
            resource="agent_identity",
            success=True,
            metadata=metadata
        )
    
    def log_permission_denied(
        self,
        agent_id: str,
        agent_name: str,
        tenant_id: str,
        permission: str,
        reason: str
    ):
        """Log permission denial"""
        return self.log(
            event_type=EventType.PERMISSION_DENIED,
            severity=Severity.WARNING,
            agent_id=agent_id,
            agent_name=agent_name,
            tenant_id=tenant_id,
            action="check_permission",
            resource=permission,
            success=False,
            error_message=reason
        )
    
    def log_security_violation(
        self,
        agent_id: str,
        agent_name: str,
        tenant_id: str,
        violation_type: str,
        details: str
    ):
        """Log security violation"""
        return self.log(
            event_type=EventType.SECURITY_VIOLATION,
            severity=Severity.CRITICAL,
            agent_id=agent_id,
            agent_name=agent_name,
            tenant_id=tenant_id,
            action="security_check",
            resource="system",
            success=False,
            error_message=violation_type,
            metadata={"details": details}
        )
    
    def generate_compliance_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Generate a compliance report for a tenant.
        
        Includes:
        - Event counts by type
        - Security incidents
        - Chain integrity verification
        """
        events = [
            e for e in self.chain.events
            if e.tenant_id == tenant_id
            and start_date <= e.timestamp <= end_date
        ]
        
        # Count by type
        type_counts = {}
        for e in events:
            type_counts[e.event_type.value] = type_counts.get(e.event_type.value, 0) + 1
        
        # Security events
        security_events = [e for e in events if e.severity in (Severity.ERROR, Severity.CRITICAL)]
        
        # Verify chain
        chain_verify = self.chain.verify_chain()
        
        return {
            "tenant_id": tenant_id,
            "period": f"{start_date.date()} to {end_date.date()}",
            "total_events": len(events),
            "event_breakdown": type_counts,
            "security_incidents": len(security_events),
            "chain_integrity": chain_verify,
            "generated_at": datetime.utcnow().isoformat()
        }


class AuditAnalyzer:
    """
    Analyzes audit logs for patterns and anomalies.
    """
    
    def __init__(self, logger: AuditLogger):
        self.logger = logger
    
    def get_failed_actions(self, agent_id: Optional[str] = None) -> List[AuditEvent]:
        """Get all failed actions, optionally filtered by agent"""
        events = self.logger.chain.events
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        return [e for e in events if not e.success]
    
    def get_permission_failures(self) -> List[AuditEvent]:
        """Get all permission denied events"""
        return [
            e for e in self.logger.chain.events
            if e.event_type == EventType.PERMISSION_DENIED
        ]
    
    def detect_repeated_failures(self, threshold: int = 5) -> List[Dict]:
        """
        Detect agents with repeated failures (possible attack).
        """
        failure_counts = {}
        
        for event in self.logger.chain.events:
            if not event.success:
                key = (event.agent_id, event.action)
                failure_counts[key] = failure_counts.get(key, 0) + 1
        
        repeated = []
        for (agent_id, action), count in failure_counts.items():
            if count >= threshold:
                repeated.append({
                    "agent_id": agent_id,
                    "action": action,
                    "failure_count": count
                })
        
        return repeated
    
    def get_activity_summary(self, hours: int = 24) -> Dict:
        """Get activity summary for the last N hours"""
        cutoff = datetime.utcnow() - __import__('datetime').timedelta(hours=hours)
        recent = [e for e in self.logger.chain.events if e.timestamp >= cutoff]
        
        return {
            "period_hours": hours,
            "total_events": len(recent),
            "unique_agents": len(set(e.agent_id for e in recent)),
            "success_rate": sum(1 for e in recent if e.success) / len(recent) * 100 if recent else 0,
            "security_events": len([e for e in recent if e.severity == Severity.CRITICAL])
        }


def demo():
    """Demonstrate audit system"""
    print("\n" + "="*70)
    print("AUDIT SYSTEM - COMPLIANCE LOGGING")
    print("="*70)
    
    logger = AuditLogger()
    
    # Simulate various events
    print("\n📋 LOGGING EVENTS")
    print("-" * 70)
    
    # 1. Identity creation
    logger.log_identity_created(
        agent_id="agent-001",
        agent_name="User Analytics Agent",
        tenant_id="tenant-abc",
        metadata={"permissions": ["user:read", "analytics:read"]}
    )
    
    # 2. Successful permission check
    logger.log(
        event_type=EventType.PERMISSION_CHECKED,
        severity=Severity.DEBUG,
        agent_id="agent-001",
        agent_name="User Analytics Agent",
        tenant_id="tenant-abc",
        action="check_permission",
        resource="user:read",
        success=True,
        result="granted"
    )
    
    # 3. Permission denied
    logger.log_permission_denied(
        agent_id="agent-002",
        agent_name="Unauthorized Agent",
        tenant_id="tenant-abc",
        permission="admin:grant",
        reason="Agent lacks required risk classification"
    )
    
    # 4. Action executed
    logger.log(
        event_type=EventType.ACTION_EXECUTED,
        severity=Severity.INFO,
        agent_id="agent-001",
        agent_name="User Analytics Agent",
        tenant_id="tenant-abc",
        action="generate_report",
        resource="analytics_db",
        success=True,
        result="Report generated: user_activity_2024.pdf"
    )
    
    # 5. Security violation
    logger.log_security_violation(
        agent_id="agent-003",
        agent_name="Suspicious Agent",
        tenant_id="tenant-abc",
        violation_type="TENANT_ISOLATION_BREACH",
        details="Attempted to access resources from different tenant"
    )
    
    # Show chain verification
    print("\n🔒 CHAIN VERIFICATION")
    print("-" * 70)
    
    verify_result = logger.chain.verify_chain()
    print(f"Chain Valid: {verify_result['valid']}")
    print(f"Total Events: {verify_result['total_events']}")
    
    if verify_result['violations']:
        print(f"Violations: {len(verify_result['violations'])}")
        for v in verify_result['violations']:
            print(f"  ⚠️  {v['issue']} at index {v['index']}")
    
    # Analyzer
    print("\n📊 AUDIT ANALYSIS")
    print("-" * 70)
    
    analyzer = AuditAnalyzer(logger)
    
    failed = analyzer.get_failed_actions()
    print(f"Failed Actions: {len(failed)}")
    
    perm_denied = analyzer.get_permission_failures()
    print(f"Permission Denials: {len(perm_denied)}")
    
    # Show event chain
    print("\n🔗 EVENT CHAIN (last 3)")
    print("-" * 70)
    for event in logger.chain.events[-3:]:
        print(f"Event: {event.event_id}")
        print(f"  Type: {event.event_type.value}")
        print(f"  Hash: {event.chain_hash}")
        if event.previous_hash:
            print(f"  Previous: {event.previous_hash}")
        print()
    
    # Compliance report
    print("📋 COMPLIANCE REPORT")
    print("-" * 70)
    
    report = logger.generate_compliance_report(
        tenant_id="tenant-abc",
        start_date=datetime.utcnow().replace(hour=0, minute=0, second=0),
        end_date=datetime.utcnow()
    )
    
    print(f"Tenant: {report['tenant_id']}")
    print(f"Period: {report['period']}")
    print(f"Total Events: {report['total_events']}")
    print(f"Security Incidents: {report['security_incidents']}")
    print("\nEvent Breakdown:")
    for event_type, count in report['event_breakdown'].items():
        print(f"  {event_type}: {count}")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    
    print("\n🎓 Key Takeaways:")
    print("  ✅ Every action logged with tamper-evident chain")
    print("  ✅ Structured events for compliance reporting")
    print("  ✅ Chain verification detects modifications")
    print("  ✅ Security events highlighted")
    print("  ✅ Full audit trail for forensics")


if __name__ == "__main__":
    demo()

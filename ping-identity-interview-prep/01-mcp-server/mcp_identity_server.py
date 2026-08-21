"""
MCP Identity Server - Secure MCP Server for Identity Management

This demonstrates how Ping Identity might build MCP servers for their
PingOne platform with proper security validation.

Key Concepts:
- MCP (Model Context Protocol) for AI agent communication
- Multi-layer security validation
- Tenant isolation in multi-tenant SaaS
- Audit logging for compliance
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, validator

# MCP imports (simulated for learning - real implementation uses mcp library)
class MCPServer:
    """Simplified MCP Server for learning purposes"""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = {}
        
    def tool(self):
        """Decorator to register a tool"""
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a registered tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return await self.tools[tool_name](**kwargs)


class AgentContext(BaseModel):
    """
    Context for an AI agent making requests.
    
    This represents the security context of the agent including:
    - Who the agent is
    - What permissions it has been granted
    - Risk classification
    - Audit trail information
    """
    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_type: str = Field(..., description="Type: 'standalone', 'delegated', 'system'")
    tenant_id: str = Field(..., description="Tenant the agent belongs to")
    delegated_by: Optional[str] = Field(None, description="User who delegated permissions")
    permissions: List[str] = Field(default_factory=list, description="Granted permissions")
    risk_level: str = Field("medium", description="low/medium/high risk classification")
    session_id: str = Field(..., description="Session for audit trail")
    
    class Config:
        validate_assignment = True


class SSOConnectionRequest(BaseModel):
    """
    Request to create an SSO connection.
    
    Demonstrates input validation using Pydantic.
    This is Layer 1 of our security: Schema Validation
    """
    tenant_id: str = Field(..., min_length=1, description="Tenant ID")
    provider_name: str = Field(..., description="Identity Provider name (e.g., 'Okta', 'AzureAD')")
    metadata_url: str = Field(..., description="SAML/OIDC metadata URL")
    callback_url: str = Field(..., description="Callback URL for SSO flow")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional config")
    
    @validator('metadata_url')
    def validate_metadata_url(cls, v):
        """Validate URL format and security"""
        if not v.startswith(('https://', 'http://')):
            raise ValueError("Metadata URL must be HTTP(S)")
        if 'localhost' in v or '127.0.0.1' in v:
            raise ValueError("Localhost URLs not allowed in production")
        return v
    
    @validator('provider_name')
    def validate_provider(cls, v):
        """Validate IdP is supported"""
        allowed = {'Okta', 'AzureAD', 'PingFederate', 'Auth0', 'OneLogin'}
        if v not in allowed:
            raise ValueError(f"Provider must be one of: {allowed}")
        return v


class UserCreationRequest(BaseModel):
    """Request to create a user - MEDIUM RISK operation"""
    tenant_id: str
    email: str
    first_name: str
    last_name: str
    roles: List[str] = Field(default_factory=list)
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError("Invalid email format")
        return v
    
    @validator('roles')
    def validate_roles(cls, v):
        """Prevent creation of super-admin users via API"""
        forbidden = {'superadmin', 'root', 'system'}
        for role in v:
            if role.lower() in forbidden:
                raise ValueError(f"Cannot assign role: {role}")
        return v


# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY LAYER
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityValidator:
    """
    Multi-layer security validation for MCP operations.
    
    This implements:
    - Layer 1: Schema validation (via Pydantic models above)
    - Layer 2: Permission checking
    - Layer 3: Tenant isolation
    - Layer 4: Rate limiting
    - Layer 5: Audit logging
    """
    
    def __init__(self):
        self.audit_logs = []
        self.rate_limits = {}  # Simple in-memory rate limiting
        
    async def validate_tenant_access(self, ctx: AgentContext, target_tenant: str):
        """
        CRITICAL: Ensure agent can only access its own tenant's data.
        
        This prevents cross-tenant data leakage - a critical security bug
        in multi-tenant SaaS systems.
        """
        if ctx.tenant_id != target_tenant:
            await self._log_security_event(
                "tenant_isolation.violation",
                ctx,
                {"attempted_tenant": target_tenant}
            )
            raise PermissionError(
                f"Agent {ctx.agent_id} from tenant {ctx.tenant_id} "
                f"cannot access tenant {target_tenant}"
            )
        
        await self._log_security_event(
            "tenant_isolation.passed",
            ctx,
            {"target_tenant": target_tenant}
        )
    
    async def validate_permission(self, ctx: AgentContext, required_permission: str):
        """
        Check if agent has the required permission.
        
        Implements "Least Privilege" - agents only get permissions
        explicitly granted, not full user access.
        """
        if required_permission not in ctx.permissions:
            await self._log_security_event(
                "permission.denied",
                ctx,
                {"required": required_permission, "has": ctx.permissions}
            )
            raise PermissionError(
                f"Agent lacks permission: {required_permission}. "
                f"Has: {ctx.permissions}"
            )
        
        await self._log_security_event(
            "permission.granted",
            ctx,
            {"permission": required_permission}
        )
    
    async def check_rate_limit(self, ctx: AgentContext, operation: str, max_requests: int = 10):
        """
        Prevent abuse through rate limiting.
        
        Different limits for different risk levels:
        - Low risk: 100 req/min
        - Medium risk: 50 req/min  
        - High risk: 10 req/min (requires human approval anyway)
        """
        key = f"{ctx.agent_id}:{operation}"
        current = self.rate_limits.get(key, 0)
        
        risk_multipliers = {"low": 10, "medium": 5, "high": 1}
        limit = max_requests * risk_multipliers.get(ctx.risk_level, 1)
        
        if current >= limit:
            await self._log_security_event(
                "rate_limit.exceeded",
                ctx,
                {"operation": operation, "limit": limit}
            )
            raise RateLimitExceeded(f"Rate limit exceeded: {limit} requests")
        
        self.rate_limits[key] = current + 1
    
    async def require_human_approval(self, ctx: AgentContext, operation: str):
        """
        HIGH-RISK operations require human-in-the-loop approval.
        
        This implements the "Human-in-the-Loop" security principle
        from Ping's Identity for AI guidelines.
        """
        if ctx.risk_level == "high":
            await self._log_security_event(
                "approval.required",
                ctx,
                {"operation": operation}
            )
            # In production, this would:
            # 1. Send approval request to delegated_by user
            # 2. Wait for explicit approval
            # 3. Time out if no response
            # For demo, we'll simulate approval
            print(f"[APPROVAL REQUIRED] Agent {ctx.agent_id} requests {operation}")
            print(f"[APPROVAL REQUIRED] Delegated by: {ctx.delegated_by}")
            # Simulate approved after check
            await asyncio.sleep(0.1)
    
    async def _log_security_event(self, event_type: str, ctx: AgentContext, details: dict):
        """
        Comprehensive audit logging for compliance.
        
        All security events are logged with:
        - Timestamp
        - Agent identity
        - Operation attempted
        - Success/failure
        - Context for investigation
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "agent_id": ctx.agent_id,
            "agent_type": ctx.agent_type,
            "tenant_id": ctx.tenant_id,
            "session_id": ctx.session_id,
            "delegated_by": ctx.delegated_by,
            "details": details
        }
        self.audit_logs.append(log_entry)
        
        # In production, send to SIEM (Splunk, Datadog, etc.)
        print(f"[AUDIT] {event_type}: {json.dumps(log_entry, indent=2)}")


class RateLimitExceeded(Exception):
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# MCP SERVER IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

# Create server instance
mcp = MCPServer("PingOne Identity Server")
security = SecurityValidator()

# Simulated database (in production, this is PingOne's actual backend)
class MockDatabase:
    def __init__(self):
        self.users = {}
        self.sso_connections = {}
        self.tenants = {
            "tenant-1": {"name": "Acme Corp", "plan": "enterprise"},
            "tenant-2": {"name": "TechStart Inc", "plan": "starter"},
        }
    
    def get_tenant(self, tenant_id: str):
        return self.tenants.get(tenant_id)

db = MockDatabase()


@mcp.tool()
async def create_sso_connection(
    request: SSOConnectionRequest,
    ctx: AgentContext
) -> Dict[str, Any]:
    """
    Create an SSO connection - HIGH RISK operation.
    
    This demonstrates full security validation for a critical identity operation.
    """
    print(f"\n{'='*60}")
    print(f"TOOL: create_sso_connection")
    print(f"Agent: {ctx.agent_id} ({ctx.agent_type})")
    print(f"Tenant: {request.tenant_id}")
    print(f"Provider: {request.provider_name}")
    print(f"{'='*60}\n")
    
    # Layer 1: Schema validation (already done via Pydantic)
    
    # Layer 2: Tenant isolation
    await security.validate_tenant_access(ctx, request.tenant_id)
    
    # Layer 3: Permission check
    await security.validate_permission(ctx, "sso:create")
    
    # Layer 4: Rate limiting
    await security.check_rate_limit(ctx, "sso:create", max_requests=5)
    
    # Layer 5: Human approval for high-risk
    await security.require_human_approval(ctx, "sso:create")
    
    # Layer 6: Semantic validation (business logic)
    tenant = db.get_tenant(request.tenant_id)
    if not tenant:
        raise ValueError(f"Tenant not found: {request.tenant_id}")
    
    # Check plan limits
    existing_connections = len([
        c for c in db.sso_connections.values()
        if c["tenant_id"] == request.tenant_id
    ])
    if tenant["plan"] == "starter" and existing_connections >= 1:
        raise ValueError("Starter plan limited to 1 SSO connection")
    
    # Create the connection
    connection_id = f"sso-{len(db.sso_connections) + 1}"
    connection = {
        "id": connection_id,
        "tenant_id": request.tenant_id,
        "provider": request.provider_name,
        "metadata_url": request.metadata_url,
        "callback_url": request.callback_url,
        "status": "active",
        "created_by": ctx.agent_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    db.sso_connections[connection_id] = connection
    
    # Log success
    await security._log_security_event(
        "sso.create.success",
        ctx,
        {"connection_id": connection_id}
    )
    
    return {
        "success": True,
        "connection_id": connection_id,
        "message": f"SSO connection to {request.provider_name} created successfully"
    }


@mcp.tool()
async def create_user(
    request: UserCreationRequest,
    ctx: AgentContext
) -> Dict[str, Any]:
    """
    Create a user - MEDIUM RISK operation.
    """
    print(f"\n{'='*60}")
    print(f"TOOL: create_user")
    print(f"Agent: {ctx.agent_id}")
    print(f"Email: {request.email}")
    print(f"{'='*60}\n")
    
    # Security layers
    await security.validate_tenant_access(ctx, request.tenant_id)
    await security.validate_permission(ctx, "user:create")
    await security.check_rate_limit(ctx, "user:create", max_requests=20)
    
    # Create user
    user_id = f"user-{len(db.users) + 1}"
    user = {
        "id": user_id,
        "tenant_id": request.tenant_id,
        "email": request.email,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "roles": request.roles,
        "created_by": ctx.agent_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    db.users[user_id] = user
    
    await security._log_security_event(
        "user.create.success",
        ctx,
        {"user_id": user_id, "email": request.email}
    )
    
    return {
        "success": True,
        "user_id": user_id,
        "message": f"User {request.email} created successfully"
    }


@mcp.tool()
async def list_users(
    tenant_id: str,
    ctx: AgentContext
) -> Dict[str, Any]:
    """
    List users - LOW RISK read operation.
    """
    # Even reads need tenant isolation!
    await security.validate_tenant_access(ctx, tenant_id)
    await security.validate_permission(ctx, "user:read")
    
    users = [
        u for u in db.users.values()
        if u["tenant_id"] == tenant_id
    ]
    
    return {
        "success": True,
        "count": len(users),
        "users": users
    }


@mcp.tool()
async def delete_user(
    tenant_id: str,
    user_id: str,
    ctx: AgentContext
) -> Dict[str, Any]:
    """
    Delete a user - HIGH RISK destructive operation.
    """
    print(f"\n{'='*60}")
    print(f"TOOL: delete_user - DESTRUCTIVE OPERATION")
    print(f"Agent: {ctx.agent_id}")
    print(f"Target User: {user_id}")
    print(f"{'='*60}\n")
    
    # All security layers
    await security.validate_tenant_access(ctx, tenant_id)
    await security.validate_permission(ctx, "user:delete")
    await security.check_rate_limit(ctx, "user:delete", max_requests=3)
    await security.require_human_approval(ctx, "user:delete")
    
    # Verify user exists and belongs to tenant
    user = db.users.get(user_id)
    if not user:
        raise ValueError(f"User not found: {user_id}")
    if user["tenant_id"] != tenant_id:
        raise PermissionError("User does not belong to tenant")
    
    # Prevent self-deletion
    if user.get("created_by") == ctx.agent_id:
        raise ValueError("Agents cannot delete users they created (prevent loop)")
    
    del db.users[user_id]
    
    await security._log_security_event(
        "user.delete.success",
        ctx,
        {"user_id": user_id}
    )
    
    return {
        "success": True,
        "message": f"User {user_id} deleted"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

async def demo():
    """
    Run through scenarios demonstrating security concepts.
    """
    print("\n" + "="*70)
    print("PING IDENTITY MCP SERVER - SECURITY DEMONSTRATION")
    print("="*70)
    
    # Create agent contexts with different permission levels
    admin_agent = AgentContext(
        agent_id="admin-agent-001",
        agent_type="delegated",
        tenant_id="tenant-1",
        delegated_by="admin@acme.com",
        permissions=["sso:create", "user:create", "user:read", "user:delete"],
        risk_level="medium",
        session_id="session-001"
    )
    
    limited_agent = AgentContext(
        agent_id="limited-agent-001",
        agent_type="delegated",
        tenant_id="tenant-1",
        delegated_by="user@acme.com",
        permissions=["user:read"],  # Can only read!
        risk_level="low",
        session_id="session-002"
    )
    
    attacker_agent = AgentContext(
        agent_id="attacker-agent-001",
        agent_type="standalone",
        tenant_id="tenant-2",  # Different tenant!
        permissions=["sso:create", "user:create"],
        risk_level="high",
        session_id="session-003"
    )
    
    # Scenario 1: Successful SSO creation
    print("\n📋 SCENARIO 1: Admin agent creates SSO connection")
    try:
        result = await mcp.call_tool(
            "create_sso_connection",
            request=SSOConnectionRequest(
                tenant_id="tenant-1",
                provider_name="Okta",
                metadata_url="https://acme.okta.com/metadata.xml",
                callback_url="https://app.acme.com/callback"
            ),
            ctx=admin_agent
        )
        print(f"✅ SUCCESS: {result['message']}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # Scenario 2: Limited agent tries unauthorized action
    print("\n📋 SCENARIO 2: Limited agent tries to create SSO (should fail)")
    try:
        result = await mcp.call_tool(
            "create_sso_connection",
            request=SSOConnectionRequest(
                tenant_id="tenant-1",
                provider_name="AzureAD",
                metadata_url="https://acme.azure.com/metadata",
                callback_url="https://app.acme.com/callback"
            ),
            ctx=limited_agent
        )
        print(f"✅ SUCCESS: {result}")
    except PermissionError as e:
        print(f"✅ CORRECTLY BLOCKED: {e}")
    
    # Scenario 3: Cross-tenant attack attempt
    print("\n📋 SCENARIO 3: Cross-tenant access attempt (should fail)")
    try:
        result = await mcp.call_tool(
            "create_user",
            request=UserCreationRequest(
                tenant_id="tenant-1",  # Trying to access different tenant!
                email="hacker@evil.com",
                first_name="Bad",
                last_name="Actor"
            ),
            ctx=attacker_agent
        )
        print(f"✅ SUCCESS: {result}")
    except PermissionError as e:
        print(f"✅ CORRECTLY BLOCKED: {e}")
    
    # Scenario 4: Create users
    print("\n📋 SCENARIO 4: Create multiple users")
    for i in range(3):
        try:
            result = await mcp.call_tool(
                "create_user",
                request=UserCreationRequest(
                    tenant_id="tenant-1",
                    email=f"user{i}@acme.com",
                    first_name=f"User",
                    last_name=f"{i}",
                    roles=["user"]
                ),
                ctx=admin_agent
            )
            print(f"✅ Created: {result['user_id']}")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    # Scenario 5: List users (should work for limited agent)
    print("\n📋 SCENARIO 5: List users with limited agent")
    try:
        result = await mcp.call_tool(
            "list_users",
            tenant_id="tenant-1",
            ctx=limited_agent
        )
        print(f"✅ Found {result['count']} users")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Print audit log summary
    print("\n" + "="*70)
    print("AUDIT LOG SUMMARY")
    print("="*70)
    print(f"Total security events logged: {len(security.audit_logs)}")
    
    event_types = {}
    for log in security.audit_logs:
        et = log["event_type"]
        event_types[et] = event_types.get(et, 0) + 1
    
    print("\nEvent breakdown:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count}")
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nKey Takeaways:")
    print("1. ✅ Tenant isolation prevents cross-tenant data leakage")
    print("2. ✅ Permission checks enforce least privilege")
    print("3. ✅ Rate limiting prevents abuse")
    print("4. ✅ Human approval required for high-risk operations")
    print("5. ✅ Complete audit trail for compliance")


if __name__ == "__main__":
    asyncio.run(demo())

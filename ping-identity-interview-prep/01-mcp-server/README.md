# Hour 1-1.5: MCP Server Security & Validation

## Learning Objectives

By the end of this module, you will:
1. Understand what MCP (Model Context Protocol) is and why it matters for Identity
2. Build a secure MCP server that validates AI agent actions
3. Implement tenant isolation in multi-tenant systems
4. Create security validators for identity operations

## Why This Matters for Ping Identity

Ping Identity has **MCP Servers** that let AI agents:
- Configure SSO connections
- Manage user identities  
- Set up authentication flows
- Modify authorization policies

**The Risk:** An AI agent with too much power can misconfigure identity systems, creating security holes for Fortune 100 customers.

**Your Job:** Build validation systems that ensure AI agents act safely.

---

## Concept 1: What is MCP?

**MCP (Model Context Protocol)** is a standard way for AI agents to:
1. **Discover** what tools/actions are available
2. **Call** those tools with structured parameters
3. **Receive** results back in a standard format

Think of it like REST APIs, but designed specifically for AI agents.

### MCP Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   AI Agent      │────►│   MCP Server     │────►│  Identity       │
│   (Claude,      │     │   (Your Code)    │     │  System         │
│    GPT-4, etc)  │◄────│                  │◄────│  (PingOne)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Security        │
                        │  Validator       │
                        │  (Your Code)     │
                        └──────────────────┘
```

---

## Concept 2: Security Principles for AI Agents

### 🔐 The 5 Security Principles (from Ping's Identity for AI)

1. **Know Your Agents** - Classify agents by risk level
2. **Delegation, Not Impersonation** - Agents get scoped tokens, not user credentials
3. **Least Privilege** - Minimum permissions for the task
4. **Human-in-the-Loop** - Human approval for high-risk actions
5. **Monitor Everything** - Complete audit trails

### 🏢 Multi-Tenant Security

In SaaS systems like PingOne, multiple customers (tenants) share infrastructure:

```python
# ❌ WRONG: No tenant isolation
def delete_user(user_id: str):
    db.execute(f"DELETE FROM users WHERE id = {user_id}")
    # DANGER: Could delete users from other tenants!

# ✅ RIGHT: Strict tenant isolation  
def delete_user(tenant_id: str, user_id: str):
    db.execute(
        "DELETE FROM users WHERE tenant_id = %s AND id = %s",
        (tenant_id, user_id)
    )
    # Safe: Can only delete from your own tenant
```

---

## Hands-On: Build a Secure MCP Identity Server

### Step 1: Project Structure

```
01-mcp-server/
├── README.md (this file)
├── mcp_identity_server.py    # Main MCP server
├── security_validators.py     # Security validation layer
├── tenant_isolation.py        # Multi-tenant security
├── audit_logger.py           # Compliance logging
└── test_mcp_security.py      # Tests (learn by testing!)
```

### Step 2: Understanding the Code

Open `mcp_identity_server.py` and follow along:

```bash
# Read the main server code
cat mcp_identity_server.py
```

**Key Concepts to Notice:**
- **Tool Registration:** How capabilities are exposed to AI agents
- **Input Validation:** Schema validation before any action
- **Tenant Context:** Every operation includes tenant isolation
- **Audit Logging:** Everything is logged for compliance

### Step 3: Security Deep Dive

Open `security_validators.py`:

```bash
cat security_validators.py
```

**Learn These Patterns:**
1. **Schema Validation** - Reject malformed inputs immediately
2. **Semantic Validation** - Does this action make business sense?
3. **Permission Checking** - Does the agent have the right to do this?
4. **Rate Limiting** - Prevent abuse and accidents

### Step 4: Run the Examples

```bash
cd 01-mcp-server

# Run the MCP server
python mcp_identity_server.py

# In another terminal, run the tests
python test_mcp_security.py
```

### Step 5: Complete the Challenges

See `CHALLENGES.md` for hands-on exercises.

---

## Interview Gold: Key Talking Points

### When They Ask: "How would you validate an MCP server?"

**Your Answer:**
> "I'd implement a 4-layer defense:
> 
> 1. **Schema Layer:** JSON Schema validation on all inputs - reject malformed requests immediately
> 2. **Semantic Layer:** Business logic validation - 'does this SSO config make sense?'
> 3. **Permission Layer:** Check agent's delegated permissions against requested action
> 4. **Audit Layer:** Log everything for compliance and anomaly detection
> 
> For multi-tenant systems like PingOne, every validation must include tenant context to prevent cross-tenant data leakage."

### When They Ask: "What's the difference between delegation and impersonation?"

**Your Answer:**
> "Impersonation means the agent acts as the user with all their permissions - dangerous because agents make mistakes faster than humans.
> 
> Delegation means the user grants specific, scoped permissions to the agent for a specific task. Like OAuth scopes - 'this agent can create SSO configs but cannot delete users.'
> 
> In MCP servers, I implement this by requiring explicit permission grants in the tool call context, not inheriting the user's full privileges."

---

## Key Files to Study

| File | What It Teaches |
|------|-----------------|
| `mcp_identity_server.py` | MCP protocol implementation, tool registration |
| `security_validators.py` | Multi-layer validation patterns |
| `tenant_isolation.py` | SaaS tenant isolation strategies |
| `audit_logger.py` | Compliance logging, non-repudiation |
| `test_mcp_security.py` | Testing security boundaries |

---

## Next Steps

After completing this module:
1. ✅ You can explain MCP architecture
2. ✅ You understand tenant isolation
3. ✅ You know 4-layer security validation
4. ✅ You can discuss delegation vs impersonation

**Move to:** `02-ai-quality-evaluator/README.md`

---

## Quick Reference: MCP Concepts

```python
# Tool Definition
@mcp.tool()
async def create_sso_connection(
    tenant_id: str,           # Tenant isolation
    provider_name: str,       # Input parameter
    metadata_url: str,        # Input parameter
    ctx: Context              # Agent context & permissions
) -> dict:
    """Create an SSO connection - HIGH RISK operation"""
    
    # Layer 1: Schema validation (automatic via type hints)
    
    # Layer 2: Security validation
    await validate_tenant_access(ctx, tenant_id)
    await validate_permission(ctx, "sso:create")
    await validate_url_safety(metadata_url)  # Prevent SSRF
    
    # Layer 3: Semantic validation
    if not await is_valid_idp_provider(provider_name):
        raise ValueError(f"Unknown IdP: {provider_name}")
    
    # Layer 4: Audit logging
    await audit_log.info(
        "sso.create.attempt",
        tenant_id=tenant_id,
        agent_id=ctx.agent_id,
        provider=provider_name
    )
    
    # Execute with human approval for high-risk
    if ctx.risk_level == "high":
        await request_human_approval(ctx, "sso.create")
    
    # Perform operation
    result = await sso_service.create_connection(...)
    
    # Log outcome
    await audit_log.info("sso.create.success", ...)
    
    return result
```

**Remember:** Every MCP tool for identity systems should follow this pattern!

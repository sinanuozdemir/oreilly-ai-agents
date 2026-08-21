# 🎯 MCP Server Coding Challenges

Complete these challenges to master MCP security concepts.

---

## Challenge 1: Implement Multi-Factor Authentication Check

**Difficulty:** ⭐⭐⭐

**Scenario:** High-risk operations should require MFA verification.

**Task:** Add an MFA check to the `delete_user` operation.

```python
# TODO: Implement in mcp_identity_server.py

async def verify_mfa(ctx: AgentContext, operation: str) -> bool:
    """
    Verify MFA for high-risk operations.
    
    In production, this would:
    1. Send push notification to delegated_by user
    2. Wait for approval/rejection
    3. Time out after 5 minutes
    4. Log the MFA event
    
    For this challenge, simulate with a simple check.
    """
    # YOUR CODE HERE
    pass

# Then modify delete_user to call verify_mfa()
```

**Success Criteria:**
- [ ] MFA check function implemented
- [ ] delete_user calls verify_mfa()
- [ ] Test shows MFA verification prompt
- [ ] Audit log records MFA event

---

## Challenge 2: Implement IP Whitelisting

**Difficulty:** ⭐⭐

**Scenario:** Some agents should only be allowed from specific IP ranges.

**Task:** Add IP-based access control.

```python
# TODO: Add to AgentContext

class AgentContext(BaseModel):
    # ... existing fields ...
    allowed_ip_ranges: List[str] = Field(default_factory=list)
    
# TODO: Implement validator

async def validate_ip_address(ctx: AgentContext, client_ip: str):
    """
    Verify request comes from allowed IP range.
    
    Support CIDR notation (e.g., "10.0.0.0/8").
    """
    # YOUR CODE HERE
    pass
```

**Success Criteria:**
- [ ] IP validation function works
- [ ] CIDR notation supported
- [ ] Test shows blocked/allowed IPs
- [ ] Audit log records IP check

---

## Challenge 3: Implement Request Signing

**Difficulty:** ⭐⭐⭐⭐

**Scenario:** Prevent replay attacks by requiring signed requests.

**Task:** Add HMAC request signing.

```python
# TODO: Implement request signing

import hmac
import hashlib

def sign_request(payload: dict, secret: str) -> str:
    """Create HMAC signature of request"""
    # YOUR CODE HERE
    pass

def verify_signature(payload: dict, signature: str, secret: str) -> bool:
    """Verify HMAC signature"""
    # YOUR CODE HERE
    pass

# Add to each tool:
# - Extract signature from request headers
# - Verify before processing
# - Reject if signature invalid
```

**Success Criteria:**
- [ ] sign_request() creates valid HMAC
- [ ] verify_signature() correctly validates
- [ ] Tools reject unsigned requests
- [ ] Test shows signature validation

---

## Challenge 4: Implement Dynamic Risk Scoring

**Difficulty:** ⭐⭐⭐⭐⭐

**Scenario:** Risk levels should adjust based on behavior patterns.

**Task:** Build adaptive risk scoring.

```python
# TODO: Implement risk engine

class RiskEngine:
    """
    Dynamically score operation risk based on:
    - Agent history
    - Time of day
    - Operation type
    - Data sensitivity
    - Anomaly detection
    """
    
    def __init__(self):
        self.agent_history = {}
    
    async def calculate_risk(
        self,
        ctx: AgentContext,
        operation: str,
        data: dict
    ) -> dict:
        """
        Calculate risk score (0-100).
        
        Return:
        {
            "score": 75,
            "level": "high",
            "factors": ["unusual_time", "sensitive_data"],
            "recommendation": "require_approval"
        }
        """
        # YOUR CODE HERE
        pass
```

**Success Criteria:**
- [ ] Risk score calculated from multiple factors
- [ ] Unusual patterns increase risk
- [ ] Risk level affects approval requirements
- [ ] Audit log records risk assessment

---

## Challenge 5: Build a Tenant Isolation Test Suite

**Difficulty:** ⭐⭐⭐

**Scenario:** Prove tenant isolation works under edge cases.

**Task:** Write comprehensive tests.

```python
# TODO: Add to test_mcp_security.py

class TestAdvancedTenantIsolation:
    """Advanced tenant isolation tests"""
    
    async def test_tenant_in_url_parameter(self):
        """Tenant ID in URL should still be validated"""
        # YOUR TEST HERE
        pass
    
    async def test_tenant_in_request_body(self):
        """Tenant ID in body should match agent"""
        # YOUR TEST HERE
        pass
    
    async def test_nested_object_tenant_isolation(self):
        """Nested objects should respect tenant boundaries"""
        # YOUR TEST HERE
        pass
    
    async def test_bulk_operations_tenant_check(self):
        """Bulk operations should validate each item's tenant"""
        # YOUR TEST HERE
        pass
```

**Success Criteria:**
- [ ] 4+ new test cases added
- [ ] All tests pass
- [ ] Edge cases covered
- [ ] Clear documentation of each test

---

## Challenge 6: Implement Data Masking for Logs

**Difficulty:** ⭐⭐⭐

**Scenario:** Audit logs shouldn't contain PII/sensitive data.

**Task:** Add automatic data masking.

```python
# TODO: Implement masking

class DataMasker:
    """Mask sensitive data in logs"""
    
    SENSITIVE_FIELDS = ['password', 'ssn', 'credit_card', 'api_key']
    
    @staticmethod
    def mask(data: dict) -> dict:
        """
        Recursively mask sensitive fields.
        
        Example:
        Input: {"email": "user@test.com", "password": "secret123"}
        Output: {"email": "u***@test.com", "password": "***MASKED***"}
        """
        # YOUR CODE HERE
        pass
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email: user@example.com -> u***@example.com"""
        # YOUR CODE HERE
        pass
```

**Success Criteria:**
- [ ] Sensitive fields automatically masked
- [ ] Emails partially masked
- [ ] Passwords fully masked
- [ ] Audit logs use masking

---

## How to Submit

1. Complete the challenge
2. Run tests to verify: `python test_mcp_security.py`
3. Add a comment at the top of your solution:
   ```python
   # CHALLENGE X: [Name]
   # Completed by: [Your Name]
   # Date: [Date]
   # Notes: [Any notes]
   ```

---

## Hint System

Stuck? Here are progressive hints:

<details>
<summary>Challenge 1 Hint 1</summary>
Use a simple boolean flag to simulate MFA for testing.
</details>

<details>
<summary>Challenge 1 Hint 2</summary>
The ipaddress module in Python handles CIDR notation.
</details>

<details>
<summary>Challenge 3 Hint</summary>
HMAC requires: hmac.new(secret, message, hashlib.sha256)
</details>

<details>
<summary>Challenge 4 Hint</summary>
Track agent actions in a dict, score based on frequency + anomaly.
</details>

---

## Interview Gold

After completing these challenges, you can say:

> "I implemented multi-layer security for MCP servers including MFA, 
> IP whitelisting, request signing, and adaptive risk scoring. Each 
> layer catches different attack vectors, following defense-in-depth 
> principles critical for identity systems."

---

Good luck! 🚀

"""
Security Validators - Multi-Layer Security for MCP Operations

This module demonstrates defense-in-depth validation patterns
essential for securing AI agent access to identity systems.

Ping Identity Interview Topics:
- Multi-layer validation
- Schema validation
- Semantic validation  
- Permission validation
- Rate limiting
"""

import re
import json
import hashlib
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from abc import ABC, abstractmethod
import jsonschema


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════════════

class ValidationResult:
    """Result of a validation check"""
    def __init__(self, passed: bool, message: str = "", details: Optional[Dict] = None):
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def __bool__(self):
        return self.passed
    
    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.message}"


class Validator(ABC):
    """Abstract base class for validators"""
    
    @abstractmethod
    async def validate(self, context: Dict[str, Any], data: Any) -> ValidationResult:
        """Perform validation and return result"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Validator name for logging"""
        pass


class ValidationPipeline:
    """
    Pipeline of validators that run in sequence.
    
    Demonstrates "fail-fast" pattern - stop at first failure.
    This is critical for security: don't waste resources on
    subsequent validations if basic ones fail.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.validators: List[Validator] = []
        self.on_failure: Optional[Callable] = None
    
    def add(self, validator: Validator):
        """Add validator to pipeline"""
        self.validators.append(validator)
        return self  # Enable chaining
    
    async def validate(self, context: Dict[str, Any], data: Any) -> List[ValidationResult]:
        """
        Run all validators in sequence.
        
        Returns list of results. If any validator fails,
        subsequent validators may be skipped (configurable).
        """
        results = []
        
        for validator in self.validators:
            result = await validator.validate(context, data)
            results.append(result)
            
            # Fail fast - stop on first failure
            if not result.passed:
                if self.on_failure:
                    await self.on_failure(validator, result, context)
                break
        
        return results
    
    def all_passed(self, results: List[ValidationResult]) -> bool:
        """Check if all validations passed"""
        return all(r.passed for r in results)


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1: SCHEMA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class SchemaValidator(Validator):
    """
    Layer 1: Schema Validation
    
    Validates that input matches expected structure.
    Prevents injection attacks and malformed data.
    """
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
    
    @property
    def name(self) -> str:
        return "SchemaValidator"
    
    async def validate(self, context: Dict[str, Any], data: Any) -> ValidationResult:
        """Validate data against JSON Schema"""
        try:
            jsonschema.validate(instance=data, schema=self.schema)
            return ValidationResult(
                passed=True,
                message="Schema validation passed",
                details={"schema_version": self.schema.get("$schema", "unknown")}
            )
        except jsonschema.ValidationError as e:
            return ValidationResult(
                passed=False,
                message=f"Schema validation failed: {e.message}",
                details={"field": list(e.path), "validator": e.validator}
            )


# Example schemas for Ping Identity operations
SSO_CONNECTION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["tenant_id", "provider_name", "metadata_url"],
    "properties": {
        "tenant_id": {
            "type": "string",
            "pattern": "^tenant-[a-z0-9]+$",
            "minLength": 8
        },
        "provider_name": {
            "type": "string",
            "enum": ["Okta", "AzureAD", "PingFederate", "Auth0", "OneLogin"]
        },
        "metadata_url": {
            "type": "string",
            "format": "uri",
            "pattern": "^https://"
        },
        "callback_url": {
            "type": "string",
            "format": "uri",
            "pattern": "^https://"
        }
    },
    "additionalProperties": False  # Reject unknown fields
}

USER_CREATION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["tenant_id", "email", "first_name", "last_name"],
    "properties": {
        "tenant_id": {"type": "string"},
        "email": {
            "type": "string",
            "format": "email"
        },
        "first_name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50,
            "pattern": "^[a-zA-Z\\s-]+$"  # No special chars
        },
        "last_name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50,
            "pattern": "^[a-zA-Z\\s-]+$"
        },
        "roles": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 10  # Prevent abuse
        }
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2: SEMANTIC VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticValidator(Validator):
    """
    Layer 2: Semantic Validation
    
    Validates that the operation makes business sense.
    Catches logical errors that schema validation misses.
    """
    
    FORBIDDEN_DOMAINS = [
        "tempmail.com", "throwaway.com", "guerrillamail.com"
    ]
    
    SUSPICIOUS_PATTERNS = [
        r"(password|passwd|pwd)\s*[=:]",  # Hardcoded passwords
        r"(api[_-]?key|secret)\s*[=:]",    # API keys in config
        r"(aws_access|aws_secret)",         # AWS credentials
    ]
    
    @property
    def name(self) -> str:
        return "SemanticValidator"
    
    async def validate(self, context: Dict[str, Any], data: Any) -> ValidationResult:
        """Validate business logic"""
        issues = []
        
        # Check for disposable email domains
        if "email" in data:
            email = data["email"].lower()
            domain = email.split("@")[-1]
            if domain in self.FORBIDDEN_DOMAINS:
                issues.append(f"Disposable email domain not allowed: {domain}")
        
        # Check for suspicious patterns in URLs
        if "metadata_url" in data:
            url = data["metadata_url"]
            for pattern in self.SUSPICIOUS_PATTERNS:
                if re.search(pattern, url, re.IGNORECASE):
                    issues.append(f"Suspicious pattern in URL: {pattern}")
        
        # Check for localhost in production
        if "callback_url" in data:
            url = data["callback_url"].lower()
            if "localhost" in url or "127.0.0.1" in url:
                issues.append("Localhost URLs not allowed in production")
        
        # Validate provider-specific rules
        if "provider_name" in data and "metadata_url" in data:
            provider = data["provider_name"]
            url = data["metadata_url"]
            
            provider_domains = {
                "Okta": ["okta.com", "okta-emea.com"],
                "AzureAD": ["microsoft.com", "windows.net"],
                "Auth0": ["auth0.com"],
                "PingFederate": ["pingidentity.com"]
            }
            
            if provider in provider_domains:
                allowed = provider_domains[provider]
                if not any(domain in url for domain in allowed):
                    issues.append(
                        f"{provider} metadata URL should contain one of: {allowed}"
                    )
        
        if issues:
            return ValidationResult(
                passed=False,
                message="Semantic validation failed",
                details={"issues": issues}
            )
        
        return ValidationResult(
            passed=True,
            message="Semantic validation passed"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3: SECURITY VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityValidatorLayer(Validator):
    """
    Layer 3: Security Validation
    
    Checks for security-specific issues:
    - SQL injection attempts
    - XSS attempts
    - Path traversal
    - Command injection
    """
    
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b.*\b(FROM|INTO|TABLE)\b)",
        r"(--|#|/\*|\*/)",  # SQL comments
        r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",  # OR 1=1
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",  # onclick, onload, etc.
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e",  # URL encoded ..
    ]
    
    @property
    def name(self) -> str:
        return "SecurityValidator"
    
    async def validate(self, context: Dict[str, Any], data: Any) -> ValidationResult:
        """Check for injection attacks"""
        threats = []
        
        # Convert data to string for pattern matching
        data_str = json.dumps(data)
        
        # Check for SQL injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                threats.append(f"Potential SQL injection: {pattern}")
        
        # Check for XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                threats.append(f"Potential XSS: {pattern}")
        
        # Check for path traversal
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, data_str):
                threats.append(f"Potential path traversal: {pattern}")
        
        if threats:
            return ValidationResult(
                passed=False,
                message="Security validation failed - potential injection attack",
                details={"threats_detected": len(threats), "patterns": threats}
            )
        
        return ValidationResult(
            passed=True,
            message="Security validation passed"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 4: RATE LIMITING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RateLimitEntry:
    """Track rate limit usage"""
    count: int
    window_start: datetime
    
class RateLimitValidator(Validator):
    """
    Layer 4: Rate Limiting
    
    Prevents abuse through request throttling.
    Different limits for different operations and risk levels.
    """
    
    def __init__(self):
        self.limits: Dict[str, Dict] = {}
        self.usage: Dict[str, RateLimitEntry] = {}
    
    @property
    def name(self) -> str:
        return "RateLimitValidator"
    
    def set_limit(self, operation: str, max_requests: int, window_seconds: int):
        """Configure rate limit for an operation"""
        self.limits[operation] = {
            "max": max_requests,
            "window": window_seconds
        }
    
    async def validate(self, context: Dict[str, Any], data: Any) -> ValidationResult:
        """Check rate limit"""
        operation = context.get("operation", "default")
        agent_id = context.get("agent_id", "unknown")
        risk_level = context.get("risk_level", "medium")
        
        # Get limit config
        limit_config = self.limits.get(operation, {"max": 100, "window": 60})
        
        # Apply risk multiplier
        risk_multipliers = {"low": 2.0, "medium": 1.0, "high": 0.5}
        multiplier = risk_multipliers.get(risk_level, 1.0)
        max_requests = int(limit_config["max"] * multiplier)
        window = limit_config["window"]
        
        # Check usage
        key = f"{agent_id}:{operation}"
        now = datetime.utcnow()
        
        entry = self.usage.get(key)
        if entry and (now - entry.window_start).seconds > window:
            # Window expired, reset
            entry = None
        
        if not entry:
            entry = RateLimitEntry(count=0, window_start=now)
            self.usage[key] = entry
        
        if entry.count >= max_requests:
            return ValidationResult(
                passed=False,
                message=f"Rate limit exceeded: {max_requests} requests per {window}s",
                details={
                    "limit": max_requests,
                    "window": window,
                    "retry_after": window - (now - entry.window_start).seconds
                }
            )
        
        # Increment counter
        entry.count += 1
        
        return ValidationResult(
            passed=True,
            message="Rate limit check passed",
            details={
                "limit": max_requests,
                "used": entry.count,
                "remaining": max_requests - entry.count
            }
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 5: PERMISSION VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class PermissionValidator(Validator):
    """
    Layer 5: Permission Validation
    
    Ensures agent has required permissions.
    Implements least-privilege principle.
    """
    
    def __init__(self):
        self.permission_hierarchy = {
            "admin": ["*"],  # Wildcard - all permissions
            "sso:admin": ["sso:create", "sso:read", "sso:update", "sso:delete"],
            "user:admin": ["user:create", "user:read", "user:update", "user:delete"],
        }
    
    @property
    def name(self) -> str:
        return "PermissionValidator"
    
    def expand_permissions(self, permissions: List[str]) -> List[str]:
        """Expand hierarchical permissions"""
        expanded = set()
        for perm in permissions:
            if perm in self.permission_hierarchy:
                expanded.update(self.permission_hierarchy[perm])
            else:
                expanded.add(perm)
        return list(expanded)
    
    async def validate(self, context: Dict[str, Any], data: Any) -> ValidationResult:
        """Check required permission"""
        required = context.get("required_permission")
        agent_permissions = context.get("agent_permissions", [])
        
        if not required:
            return ValidationResult(
                passed=True,
                message="No permission required"
            )
        
        # Expand agent permissions
        expanded = self.expand_permissions(agent_permissions)
        
        # Check for wildcard
        if "*" in expanded:
            return ValidationResult(
                passed=True,
                message="Admin access granted"
            )
        
        # Check specific permission
        if required in expanded:
            return ValidationResult(
                passed=True,
                message=f"Permission granted: {required}"
            )
        
        return ValidationResult(
            passed=False,
            message=f"Permission denied: {required}",
            details={
                "required": required,
                "has": agent_permissions,
                "expanded": expanded
            }
        )


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLETE VALIDATION PIPELINE FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

def create_sso_validation_pipeline() -> ValidationPipeline:
    """
    Factory function to create validation pipeline for SSO operations.
    
    This demonstrates how to compose validators for a specific use case.
    """
    pipeline = ValidationPipeline("SSO Connection Validation")
    
    # Layer 1: Schema
    pipeline.add(SchemaValidator(SSO_CONNECTION_SCHEMA))
    
    # Layer 2: Semantic
    pipeline.add(SemanticValidator())
    
    # Layer 3: Security
    pipeline.add(SecurityValidatorLayer())
    
    # Layer 4: Rate limiting
    rate_limiter = RateLimitValidator()
    rate_limiter.set_limit("sso:create", max_requests=10, window_seconds=60)
    pipeline.add(rate_limiter)
    
    # Layer 5: Permissions
    pipeline.add(PermissionValidator())
    
    return pipeline


def create_user_validation_pipeline() -> ValidationPipeline:
    """Factory for user creation validation"""
    pipeline = ValidationPipeline("User Creation Validation")
    
    pipeline.add(SchemaValidator(USER_CREATION_SCHEMA))
    pipeline.add(SemanticValidator())
    pipeline.add(SecurityValidatorLayer())
    
    rate_limiter = RateLimitValidator()
    rate_limiter.set_limit("user:create", max_requests=30, window_seconds=60)
    pipeline.add(rate_limiter)
    
    pipeline.add(PermissionValidator())
    
    return pipeline


# ═══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

async def demo():
    """Demonstrate validation pipeline"""
    print("\n" + "="*70)
    print("SECURITY VALIDATORS - MULTI-LAYER VALIDATION DEMO")
    print("="*70)
    
    # Create pipeline
    pipeline = create_sso_validation_pipeline()
    
    # Test Case 1: Valid request
    print("\n📋 TEST 1: Valid SSO Connection Request")
    context = {
        "operation": "sso:create",
        "agent_id": "agent-001",
        "risk_level": "medium",
        "required_permission": "sso:create",
        "agent_permissions": ["sso:create", "user:read"]
    }
    data = {
        "tenant_id": "tenant-abc123",
        "provider_name": "Okta",
        "metadata_url": "https://acme.okta.com/metadata.xml",
        "callback_url": "https://app.acme.com/callback"
    }
    
    results = await pipeline.validate(context, data)
    for result in results:
        print(f"  {result}")
    print(f"  Overall: {'✅ ALL PASSED' if pipeline.all_passed(results) else '❌ FAILED'}")
    
    # Test Case 2: Invalid schema
    print("\n📋 TEST 2: Invalid Schema (missing required field)")
    data_invalid = {
        "tenant_id": "tenant-abc123",
        # Missing provider_name!
        "metadata_url": "https://acme.okta.com/metadata.xml"
    }
    
    results = await pipeline.validate(context, data_invalid)
    for result in results:
        print(f"  {result}")
    print(f"  Overall: {'✅ ALL PASSED' if pipeline.all_passed(results) else '❌ FAILED (expected)'}")
    
    # Test Case 3: SQL injection attempt
    print("\n📋 TEST 3: SQL Injection Attempt")
    data_sql = {
        "tenant_id": "tenant-abc123",
        "provider_name": "Okta",
        "metadata_url": "https://acme.okta.com/metadata.xml'; DROP TABLE users; --",
        "callback_url": "https://app.acme.com/callback"
    }
    
    results = await pipeline.validate(context, data_sql)
    for result in results:
        print(f"  {result}")
    
    # Test Case 4: Semantic issue (localhost in production)
    print("\n📋 TEST 4: Semantic Violation (localhost URL)")
    data_localhost = {
        "tenant_id": "tenant-abc123",
        "provider_name": "Okta",
        "metadata_url": "https://acme.okta.com/metadata.xml",
        "callback_url": "http://localhost:3000/callback"  # Not allowed!
    }
    
    results = await pipeline.validate(context, data_localhost)
    for result in results:
        print(f"  {result}")
    
    # Test Case 5: Permission denied
    print("\n📋 TEST 5: Permission Denied")
    context_no_perm = {
        "operation": "sso:create",
        "agent_id": "agent-002",
        "risk_level": "medium",
        "required_permission": "sso:create",
        "agent_permissions": ["user:read"]  # No SSO permission!
    }
    
    results = await pipeline.validate(context_no_perm, data)
    for result in results:
        print(f"  {result}")
    
    print("\n" + "="*70)
    print("VALIDATION DEMO COMPLETE")
    print("="*70)
    print("\nKey Takeaways:")
    print("1. ✅ Multi-layer validation catches different threat types")
    print("2. ✅ Fail-fast prevents wasted resources")
    print("3. ✅ Each layer has specific responsibility")
    print("4. ✅ Detailed logging enables security investigations")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())

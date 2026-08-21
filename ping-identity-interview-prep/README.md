# 🎯 Ping Identity Interview Prep - 6 Hour Coding Program

> **Goal:** Master the technical concepts for Senior Manager, SaaS Quality Engineering (AI-First SDLC)

## What You'll Build

This program teaches you 4 critical skill areas through hands-on coding:

1. **MCP Server Security & Validation** (90 min)
   - Build a Model Context Protocol server
   - Implement security validation for AI agent actions
   - Learn tenant isolation patterns

2. **AI Test Quality Evaluator** (90 min)
   - Build a multi-stage validation pipeline
   - Implement LLM-as-judge pattern
   - Measure and reduce "bad test" rates

3. **Identity for AI Validator** (90 min)
   - Build security validators for AI agents
   - Implement least-privilege checking
   - Create audit logging systems

4. **Shift-Left CI/CD Quality Gates** (90 min)
   - Build pre-commit quality checks
   - Implement feature flag validation
   - Create quality dashboards

## Why These Projects Matter for Ping Identity

| Project | Ping Identity Relevance |
|---------|------------------------|
| MCP Server | They have AIC & DaVinci MCP servers for identity management |
| AI Evaluator | Job requires "agentic quality workflows" and measurable outcomes |
| Identity Validator | Core to "Identity for AI" initiative - securing AI agents |
| CI/CD Gates | Job requires "shift-left transformation" and "developer-owned quality" |

## Prerequisites

```bash
# Python 3.9+
python --version

# Install dependencies
pip install -r requirements.txt
```

## Program Schedule

### Hour 1-1.5: MCP Server Foundation
Learn how AI agents interact with systems via MCP, and how to validate those interactions securely.

### Hour 1.5-3: AI Quality Evaluation Pipeline
Build the "40% reduction" system - multi-stage validation for AI-generated artifacts.

### Hour 3-4.5: Identity-Aware Security Validation
Implement security validators for AI agents accessing identity systems.

### Hour 4.5-6: CI/CD Integration & Quality Gates
Bring it all together with automated quality gates and monitoring.

---

## Key Concepts You'll Master

### 🔐 Security Concepts
- **Tenant Isolation:** Multi-tenant SaaS security patterns
- **Least Privilege:** Just-in-time access for AI agents
- **Delegation vs Impersonation:** Secure agent authentication
- **Audit Trails:** Non-repudiable logging for compliance

### 🤖 AI Quality Concepts
- **LLM-as-Judge:** Using AI to evaluate AI outputs
- **Multi-Stage Validation:** Defense in depth for AI systems
- **Deterministic Replay:** Reproducible AI testing
- **Shadow Mode:** Safe AI rollout patterns

### 🏗️ Architecture Concepts
- **MCP (Model Context Protocol):** Standard for AI tool calling
- **Shift-Left Testing:** Moving quality earlier in SDLC
- **Feature Flags:** Safe deployment patterns
- **SLO/SLI-Driven Quality:** Metrics-based validation

---

Let's get started! Open `01-mcp-server/README.md` for Hour 1.

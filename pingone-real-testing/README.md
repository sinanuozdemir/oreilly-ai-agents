# PingOne Real Testing — Round 2

> **Goal:** Everything from Modules 1-4 was simulated. Here we do it for
> real against a live PingOne trial tenant — learning identity protocols,
> platform-specific QA strategies, and AI-assisted testing step by step.

## 📖 How to Use This Folder

Every step follows the same rhythm:

```
📖 CONCEPTS   →  read first — deep explanations, diagrams,
                 testing angles, interview lines
      │
      ▼
🖱️ PORTAL     →  click-through work in the PingOne console
      │
      ▼
💻 CODE       →  run the scripts, see the concepts for real
      │
      ▼
✅ CHECKPOINT →  questions you should be able to answer
                 before moving on
```

## 🗺️ Curriculum Map

| Step | Folder | What You Build | Key Concepts |
|------|--------|----------------|--------------|
| 0 | [step0_setup/](step0_setup/) | First authenticated API call | OAuth roles, grants, PKCE, JWT, the two PingOne APIs |
| 1 | [step1_protocols/](step1_protocols/) | Protocol playground | OIDC login flow live, SAML vs OIDC, SCIM |
| 2 | [step2_api_testing/](step2_api_testing/) | 8-test API suite on live tenant | Assertions, negative tests, status-code contract, self-cleaning tests |
| 3 | [step3_ai_generation/](step3_ai_generation/) | AI-generated specs → 3-stage evaluator → live execution | Test specs not code, grounding, rejection metrics |
| 4 | [step4_cicd/](step4_cicd/) | GitHub Actions quality gate | Shift-left, CI secrets, gating vs informational steps |

## 🧠 The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PINGONE TENANT (trial)                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Environment: │    │ Environment: │    │ Worker App   │       │
│  │ Administrators│   │ ai-test-lab  │    │ (our agent)  │       │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘       │
│                             │                   │               │
│                      Users, Groups,      Client ID + Secret     │
│                      Populations,        (OAuth client_         │
│                      Applications         credentials grant)    │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTPS + JSON (REST)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUR CODE (this folder)                       │
│  ping_client.py → MCP tools → AI test gen → CI gate             │
└─────────────────────────────────────────────────────────────────┘
```

## 🔗 How It Connects to Round 1

| Round 1 (simulated) | Round 2 (real) |
|---------------------|----------------|
| Module 1: MCP server with fake tools | Real MCP tools calling PingOne Management API |
| Module 2: Evaluator validating sample tests | Evaluator validating tests that hit a live tenant |
| Module 3: Simulated agent identity & tenant isolation | Real Worker app identity & real environment isolation |
| Module 4: Quality gate concept | Real GitHub Action gating on live test results |

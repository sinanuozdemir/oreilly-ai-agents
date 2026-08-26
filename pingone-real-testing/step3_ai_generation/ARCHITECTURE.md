# 🗺️ Architecture: Step 0 → Step 3

> One picture of everything you've built. Print it. Refer to it in interviews.

---

## 1. The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR WORKSTATION                                │
│                                                                         │
│   step0_setup/          step1_protocols/         step2_api_testing/     │
│   ┌──────────────┐      ┌─────────────────┐      ┌─────────────────┐    │
│   │ ping_client  │      │ oidc_playground │      │ test_pingone_api│    │
│   │  .py         │      │  .py            │      │  .py            │    │
│   │              │      │                 │      │                 │    │
│   │ • get_token()│      │ • PKCE pair     │      │ • 8 tests       │    │
│   │ • CRUD users │      │ • loopback srv  │      │ • CRUD lifecycle│    │
│   │ • list pops  │      │ • token decode  │      │ • negative tests│    │
│   └──────┬───────┘      └────────┬────────┘      └────────┬────────┘    │
│          │                       │                        │             │
│          │                       │                        │             │
│          ▼                       ▼                        ▼             │
│   ┌──────────────────────────────────────────────────────────────┐      │
│   │              PINGONE TENANT (your trial account)             │      │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │      │
│   │  │ Environment │  │ Worker App  │  │   oidc-playground   │  │      │
│   │  │ ai-test-lab │  │ admin-worker│  │   (OIDC Web App)    │  │      │
│   │  └─────────────┘  └─────────────┘  └─────────────────────┘  │      │
│   │  ┌─────────────┐  ┌─────────────┐                           │      │
│   │  │ Populations │  │ test.user1  │                           │      │
│   │  │ (2 created) │  │ (human)     │                           │      │
│   │  └─────────────┘  └─────────────┘                           │      │
│   └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
│   step3_ai_generation/                                                  │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  test_generator.py    →    evaluator.py    →    run_pipeline.py │   │
│   │  • Kimi (LLM)            • schema gate          • orchestrates    │   │
│   │  • fallback templates    • semantic rules       • prints report   │   │
│   │                          • live execution                         │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step 0: The Foundation (Machine-to-Machine)

```
YOUR CODE                     PINGONE
   │                             │
   │  POST /token                │
   │  {grant_type: client_creds} │
   │ ───────────────────────────►│
   │                             │
   │  ◄── {access_token: JWT}    │
   │                             │
   │  GET /users                 │
   │  Authorization: Bearer JWT  │
   │ ───────────────────────────►│
   │                             │
   │  ◄── {users: [...]}         │
   │                             │
```

**What you learned:** Client credentials = no human, no browser, just the app proving itself. The token is a JWT with `client_id` (not `sub`).

---

## 3. Step 1: The Human Flow (OIDC + PKCE)

```
YOUR SCRIPT              BROWSER                PINGONE
   │                       │                       │
   │ 1. create verifier    │                       │
   │    + challenge        │                       │
   │                       │                       │
   │ 2. open URL ─────────►│ 3. GET /authorize     │
   │    ?code_challenge    │    (front channel)    │
   │                       │──────────────────────►│ stores hash
   │                       │                       │
   │                       │ 4. 🔐 test.user1 logs in
   │                       │                       │
   │                       │ 5. redirect localhost │
   │ 6. code arrives ◄─────│    ?code=XYZ          │
   │    in terminal        │    (front channel)    │
   │                       │                       │
   │ 7. POST /token {code, verifier} ─────────────►│
   │         (back channel — direct, no browser)   │
   │                       │                       │
   │                       │          8. hash match? ✅
   │ 9. ◄── {id_token, access_token}               │
   │         (back channel)                        │
```

**What you learned:** Two channels. Front = browser (visible, safe for hashes/codes). Back = server-to-server (secrets, tokens). PKCE proves the same party started and finished.

---

## 4. Step 2: Testing the Contract

```
test_pingone_api.py
        │
        ├──► 1. Token acquisition        ──► 200 ✅
        ├──► 2. Token claims             ──► client_id check ✅
        ├──► 3. CRUD lifecycle           ──► 201→200→204→404 ✅
        ├──► 4. Duplicate username       ──► 400 + UNIQUENESS ✅
        ├──► 5. Unknown population       ──► 400 ✅
        ├──► 6. Garbage token            ──► 401 ✅
        ├──► 7. List populations         ──► 200 ✅
        └──► 8. Cleanup verification     ──► no debris ✅

        Each test: setup → exercise → assert → teardown
        Golden rule: tests leave no trace
```

**What you learned:** Scripts observe; tests assert. Status codes are the contract. Teardown runs in `finally`.

---

## 5. Step 3: The AI Pipeline (The Main Event)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STEP 3 PIPELINE                              │
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────────────┐  │
│  │   GENERATE    │────►│   EVALUATE    │────►│   EXECUTE (live)    │  │
│  │               │     │               │     │                     │  │
│  │ Kimi (LLM)    │     │ 3-stage       │     │ PingOne tenant      │  │
│  │ or templates  │     │ gauntlet      │     │ (self-cleaning)     │  │
│  └──────────────┘     └──────────────┘     └─────────────────────┘  │
│         │                    │                       │              │
│         ▼                    ▼                       ▼              │
│    8 JSON specs        ┌─────────┐            ┌──────────┐          │
│    (structured)        │ Stage 1 │            │ 201 ✅   │          │
│                        │ SCHEMA  │───────────►│ 400 ✅   │          │
│                        └─────────┘            │ 404 ❌   │          │
│                             │               │ (reject) │          │
│                        ┌─────────┐            └──────────┘          │
│                        │ Stage 2 │                                  │
│                        │ SEMANTIC│──► grounded rules                │
│                        │         │    (email optional? 400 vs 409?) │
│                        └─────────┘                                  │
│                             │                                       │
│                        ┌─────────┐                                  │
│                        │ Stage 3 │                                  │
│                        │EXECUTION│──► only survivors run live       │
│                        └─────────┘                                  │
│                                                                     │
│  REJECTION RATE: 50-70% on raw generation                           │
│  (that's the system WORKING)                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. The Data Flow: One Spec's Journey

```
KIMI GENERATES:
{
  "name": "create_user_minimal",
  "type": "happy",
  "endpoint": "POST /users",
  "payload": {"username": "tc_minimal_<RUN_ID>", "population": {"id": "<POPULATION_ID>"}},
  "expected_status": 201,
  "rationale": "catches regressions where email becomes accidentally mandatory",
  "cleanup": "delete_if_created"
}
        │
        ▼
┌─────────────────┐
│  STAGE 1: SCHEMA │  name is snake_case? ✅
│                 │  endpoint in ALLOWED list? ✅
│                 │  expected_status is 100-599? ✅
│                 │  cleanup is valid? ✅
│                 │  → PASS
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ STAGE 2: SEMANTIC│  happy type + 2xx status? ✅
│                 │  contradicts known facts? 
│                 │    email optional → but expected_status is 201, not 4xx ✅
│                 │  rationale > 15 chars? ✅
│                 │  → PASS
└─────────────────┘
        │
        ▼
┌─────────────────┐
│ STAGE 3: EXECUTION│  resolve <RUN_ID> → "1787674469"
│                 │  resolve <POPULATION_ID> → real id
│                 │  POST /users {username: "tc_minimal_1787674469", ...}
│                 │  ← 201 from tenant
│                 │  expected 201 == got 201? ✅
│                 │  cleanup: delete_if_created → DELETE /users/{id}
│                 │  → ACCEPT
└─────────────────┘
        │
        ▼
   🏆 SURVIVOR — enters regression suite
```

---

## 7. The Grounding Flywheel (How It Gets Smarter)

```
STEP 2 (yesterday)                    STEP 3 (today)
┌─────────────────┐                  ┌─────────────────┐
│ Test fails:     │                  │ GROUNDING_FACTS │
│ "expected 409   │ ────────────────►│ • 400 not 409   │
│  got 400"       │   becomes fact   │ • email optional│
└─────────────────┘                  │ • client_id     │
                                     └────────┬────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │ Kimi prompt:    │
                                     │ "VERIFIED FACTS:│
                                     │  - 400 not 409  │
                                     │  - email opt..."│
                                     └─────────────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │ Kimi generates: │
                                     │ "duplicate → 400│
                                     │  (not 409!)"    │
                                     └─────────────────┘
```

**Tests teach tests.** The failures from Step 2 become the facts that make Step 3 smarter.

---

## 8. The Interview Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────┐
│  ONE-LINER:                                                     │
│  "I built a self-cleaning API test suite against a live         │
│   PingOne tenant, then added an AI generation pipeline with     │
│   a 3-stage evaluator — schema, grounded semantics, live        │
│   execution — that rejects 50-70% of raw LLM output."           │
├─────────────────────────────────────────────────────────────────┤
│  THE NUMBERS:                                                   │
│  • 8 tests, 21 assertions, exit code 0                          │
│  • 3 contract quirks discovered (400 vs 409, email optional,    │
│    client_id vs sub)                                            │
│  • 62% rejection rate on Kimi's first grounded batch            │
│  • 1 data leak caught and fixed (unconditional cleanup)         │
├─────────────────────────────────────────────────────────────────┤
│  THE ARCHITECTURE:                                              │
│  • Specs not code (safe, validatable, deterministic)            │
│  • 3-stage gauntlet (cheap → expensive, filter hard early)      │
│  • Grounding flywheel (test failures → facts → smarter gen)     │
│  • Self-cleaning (finally blocks, unique names, no debris)      │
└─────────────────────────────────────────────────────────────────┘
```

# Step 3: AI-Generated Tests — Generation Is Cheap, Validation Is the Product

> Step 2 proved you can test a live tenant by hand. Step 3 asks the
> uncomfortable question: *what happens when an AI writes the tests?*
> Answer: it generates brilliant edge cases **and** confident nonsense —
> in the same batch. Your job as an AI-native QE is to build the
> machine that tells them apart.

---

## 1. The Core Loop

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. GENERATE  │───►│  2. EVALUATE │───►│  3. EXECUTE  │───►│  4. MEASURE  │
│  LLM writes   │    │  3-stage     │    │  survivors   │    │  rejection   │
│  test specs   │    │  gauntlet    │    │  on tenant   │    │  rates       │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │                   │
    cheap              the product         ground truth        the proof
```

**The one-sentence thesis:** anyone can prompt an LLM to write tests.
The differentiator — and the interview story — is the *evaluator* that
decides which generated tests deserve to run.

---

## 2. Why Test *Specs*, Not Test *Code*?

Step 2 wrote Python by hand. The naive Step 3 is "ask the LLM for
Python test files." Don't. Generate **structured JSON specs** instead:

```json
{
  "name": "create_user_empty_username",
  "type": "negative",
  "endpoint": "POST /users",
  "payload": {"username": "", "population": "<id>"},
  "expected_status": 400,
  "rationale": "Empty string username should be rejected",
  "cleanup": "delete_if_created"
}
```

| | Generate Python code | Generate JSON specs |
|---|---|---|
| Validation | Parse AST, guess intent | Schema-check in 10 lines |
| Execution safety | `exec()` arbitrary LLM code 😱 | Your runner controls every call |
| Hallucination blast radius | Broken imports, wrong APIs | One bad field, caught by schema |
| Determinism | Same spec → different code | Same spec → identical HTTP call |

**Interview line:**

> "I constrained generation to a structured schema. The LLM gets
> creative about *what* to test; my code controls *how* it executes.
> That's the same reason you don't let an agent run arbitrary SQL —
> you give it a query builder."

---

## 3. The 3-Stage Evaluator — Defense in Depth

Each stage catches a *different failure mode*. Order matters:
cheapest first.

```
GENERATED SPEC
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│ STAGE 1: SCHEMA                                          │
│ "Is this even a well-formed spec?"                       │
│ • required fields present?                               │
│ • endpoint exists in the ALLOWED list?                   │
│ • expected_status is a real HTTP code?                   │
│ Catches: malformed JSON, hallucinated endpoints          │
│ Cost: microseconds. Rejects ~half the garbage.           │
└─────────────────────────────────────────────────────────┘
      │ pass
      ▼
┌─────────────────────────────────────────────────────────┐
│ STAGE 2: SEMANTIC (grounded rules + LLM judge)           │
│ "Does this test make sense FOR THIS API?"                │
│ • contradicts a KNOWN FACT? (email optional in PingOne   │
│   → a 'missing email → 400' test is WRONG)               │
│ • negative test expecting 2xx? nonsense                  │
│ • rationale matches the payload?                         │
│ Catches: plausible-looking but factually wrong tests     │
│ Cost: rules are free; LLM judge call ~$0.001             │
└─────────────────────────────────────────────────────────┘
      │ pass
      ▼
┌─────────────────────────────────────────────────────────┐
│ STAGE 3: EXECUTION                                       │
│ "Does reality agree?"                                    │
│ Run it against the live tenant (sandboxed, self-         │
│ cleaning — the Step 2 discipline).                       │
│ Catches: everything the first two stages missed          │
│ Cost: real API calls. This is why stages 1-2 exist.      │
└─────────────────────────────────────────────────────────┘
      │
      ▼
  ACCEPTED TEST (enters the regression suite)
```

### Why this order?

```
Schema:     1000 specs × $0.000  = $0     ← filter hard, here
Semantic:    500 specs × $0.001  = $0.50  ← rules first, judge iffy ones
Execution:   200 specs × 2s API  = ~7 min ← only survivors cost time
```

Reverse the order and you're executing hallucinations against prod.
This **is** the "40% reduction" architecture from your case study —
same three stages, now pointed at a real tenant.

---

## 4. Grounding — The Antidote to Hallucination

An LLM generating tests for "the PingOne API" runs on *generic REST
assumptions* — the exact assumptions that failed in Step 2! The fix
is **grounding**: inject verified facts into both the generation
prompt AND the evaluator.

```
VERIFIED FACTS (learned by Step 2's failures — tests teaching tests):

  1. Duplicate username → 400 + UNIQUENESS_VIOLATION  (NOT 409)
  2. Email is OPTIONAL on user creation               (NOT required)
  3. Worker tokens carry client_id, not sub
  4. Real endpoints: /users, /populations, /groups
```

Notice the flywheel:

```
Step 2 tests FAIL → reveal real contract → becomes GROUNDING
→ Step 3 generation gets smarter → Step 3 evaluation gets teeth
→ new failures → new grounding facts → ...
```

This is the answer to "how do you keep AI-generated tests aligned with
reality?" — *the test suite itself maintains the fact sheet.*

---

## 5. Measuring It — The Numbers That Make the Story

```
📊 PIPELINE REPORT (what run_pipeline.py prints)

Generated:              10 specs
Stage 1 rejected:        3  (schema: hallucinated endpoint, bad field)
Stage 2 rejected:        3  (semantic: contradicts known facts)
Stage 3 rejected:        1  (execution: expected 400, tenant said 201)
Accepted:                3

Rejection rate: 70%      ← on raw, ungrounded generation this is NORMAL
```

Don't flinch at high rejection — that's the system *working*. The
metric that matters over time: **does rejection rate drop as grounding
improves?** That's "measurable before-and-after impact" in one graph.

**Interview line:**

> "My first batch had a 70% rejection rate — schema stage caught
> hallucinated endpoints, semantic stage caught tests contradicting
> facts we'd verified by hand, execution caught the rest. After feeding
> those failures back as grounding, rejection dropped to ~35%. The
> evaluator didn't just filter tests — it made the generator better."

---

## 💻 The Three Files

| File | Role |
|------|------|
| [test_generator.py](test_generator.py) | Prompts Kimi (OpenAI-compatible) for JSON specs. No API key? Deterministic template fallback — pipeline still runs |
| [evaluator.py](evaluator.py) | The 3-stage gauntlet: schema → grounded semantics → live execution |
| [run_pipeline.py](run_pipeline.py) | Orchestrator: generate → evaluate → execute → print the metrics report |

Run it:

```bash
cd pingone-real-testing/step3_ai_generation
python run_pipeline.py
```

**What to notice while it runs:**

1. **Which stage kills which spec** — schema deaths are instant,
   semantic deaths cite a violated fact, execution deaths show the
   tenant's actual response.
2. **The grounding block** printed at the start — those facts came
   from YOUR Step 2 failures yesterday.
3. **The final number** — rejection rate. Whatever it is, that number
   is your baseline for the "before/after" story.

---

## ✅ Checkpoint

**1. Why generate JSON test specs instead of Python test code?**

> **Answer:** Specs are schema-validatable in microseconds, execute
> through *your* runner (no arbitrary LLM code on a live tenant), and
> are deterministic. The LLM gets creative about *what* to test; your
> code controls *how* it runs.

**2. Why is execution the LAST stage instead of the first?**

> **Answer:** Cost and safety. Schema validation is free, semantic
> checks cost fractions of a cent, execution costs real API calls
> against a real tenant. Filtering 80% of garbage before stage 3 means
> you never execute hallucinations against production systems.

**3. What is "grounding" and where do the facts come from?**

> **Answer:** Grounding = injecting *verified* contract facts into
> generation prompts and evaluation rules. The facts come from the
> test suite's own failures (Step 2 discovered: email optional,
> 400-not-409, client_id-not-sub). Tests teach tests.

**4. Your evaluator rejects 70% of generated tests. Good or bad?**

> **Answer:** Good — that's the system working on raw, ungrounded
> generation. The metric that matters is the *trend*: rejection rate
> should drop as failures feed back into grounding. A 0% rejection
> rate would mean your evaluator has no teeth.

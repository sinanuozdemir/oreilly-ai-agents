# Step 4: CI/CD Quality Gate — From "I Run It" to "It Runs Itself"

> Steps 0-3 happened when *you* decided to run them. Step 4 removes you
> from the loop: every pull request runs the API suite AND the AI
> evaluator gauntlet against the live tenant. Green = mergeable.
> Red = blocked. This is **shift-left** — quality at commit time,
> not release time.

---

## 1. What a Quality Gate Actually Is

```
WITHOUT A GATE:                    WITH A GATE:

code → merge → deploy → test       code → TEST → merge → deploy
             (too late 🔥)                    (cheap ✅)

PR opened                            PR opened
   │                                    │
   ▼                                    ▼
human reviews                      🤖 gate runs:
"looks fine"                       • Step 2 suite (8 tests)
   │                               • Step 3 pipeline (gauntlet)
   ▼                                    │
merge 🚢                                ▼
   │                              exit 0? ──no──► ❌ merge blocked
   ▼                                    │
prod breaks 💥                    yes   │
                                        ▼
                                   ✅ merge allowed
```

A gate is just **a script whose exit code controls the merge button**.
You already built both scripts — Step 2 returns 0/1, Step 3 returns
0/1. Step 4 is plumbing: run them on every PR, automatically.

---

## 2. The #1 Rule of CI: Secrets Never Live in Code

Your local `.env` has the client secret. If that file reaches git,
the secret is compromised **forever** (git history is forever —
deleting the file in a later commit doesn't help).

```
LOCAL (your laptop):              CI (GitHub's runners):
─────────────────                 ─────────────────────
.env file  ──► dotenv loads       GitHub repo → Settings →
  into os.environ                    Secrets → Actions ──► injected
                                    as env vars at runtime

  gitignored ✅                    encrypted at rest ✅
  never committed                  masked in logs ✅
                                   never in the repo ✅

THE MAGIC: your code never changes.
os.environ["PINGONE_CLIENT_SECRET"] works in BOTH places.
```

That's why [ping_client.py](../step0_setup/ping_client.py) was written
the way it was: `_load_root_env()` tries dotenv, and if there's no
`.env` (like in CI), it just falls through to real environment
variables. **Design for CI from line one.**

### Setting it up (2 minutes in the GitHub UI)

Repo → **Settings** → **Secrets and variables** → **Actions** →
**New repository secret**, one per key:

```
PINGONE_ENVIRONMENT_ID      (from your root .env)
PINGONE_CLIENT_ID           (the admin-worker Worker app)
PINGONE_CLIENT_SECRET       (the sensitive one)
PINGONE_REGION              (com)
MOONSHOT_API_KEY            (optional — without it, Step 3 uses
                             its deterministic fallback specs)
```

---

## 3. Anatomy of the Workflow File

The gate lives at [.github/workflows/pingone-quality-gate.yml](../../.github/workflows/pingone-quality-gate.yml).
GitHub finds anything in `.github/workflows/` — that exact path is
convention, not choice.

```yaml
on:                        # WHEN does the gate run?
  pull_request:            #   every PR (opened, updated)
  push:                    #   every push to main
    branches: [main]

jobs:
  quality-gate:
    runs-on: ubuntu-latest # WHERE: a fresh VM, every time
    env:                   # SECRETS → env vars (your code reads these)
      PINGONE_CLIENT_SECRET: ${{ secrets.PINGONE_CLIENT_SECRET }}

    steps:                 # WHAT: same commands you ran by hand
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install requests openai python-dotenv
      - run: python test_pingone_api.py   # Step 2 — its exit code gates
      - run: python run_pipeline.py       # Step 3 — same
```

**The key insight:** there's nothing magic in CI. It's *your terminal
commands*, on *a clean machine*, *triggered by git events*. If it
works locally, it works in CI — as long as secrets are injected.

---

## 4. Why a Fresh VM Matters (and Hurts)

```
YOUR LAPTOP:              CI RUNNER:
───────────               ─────────
requests installed ✅     nothing installed — install it every run
.env exists ✅            no .env — secrets come from GitHub
your network ✅           GitHub's network — your tenant must be
                          reachable from the internet (it is)
warm caches               cold start every time (~1 min)
```

This is a **feature**: the VM is the ultimate "works on my machine"
detector. If your pipeline only passes on your laptop, it doesn't pass.

---

## 5. Gating Strategy — What Should Block a Merge?

Not everything deserves gate power. The pyramid from Step 2 applies:

```
BLOCKS THE MERGE (must be fast + deterministic):
  ✅ Step 2 API suite — seconds, no randomness, no LLM cost
  
INFORMATIONAL (runs, reports, doesn't block):
  📊 Step 3 with live Kimi — LLM latency + non-determinism
     make it a flaky gate. Run it, post the rejection rate
     as a comment/log, but gate on the deterministic parts.

NEVER IN CI:
  🚫 Step 1's oidc_playground.py — needs a human in a browser.
     Browser-based login gets Playwright + a stored session
     (that's the next level after this course).
```

Our workflow encodes exactly this: Step 2 gates; Step 3 runs in
`continue-on-error` mode so its report is visible without blocking.

**Interview trap:**

```
❌ "We run all tests in CI and block on everything"
✅ "Gates must be deterministic. LLM-in-the-loop steps run
    informational-only — you gate on what you can reproduce,
    you observe what you can't. A flaky gate teaches teams
    to ignore red — which is worse than no gate."
```

---

## 6. The Badge — Making Quality Visible

Once the workflow runs, add the status badge to the README:

```markdown
![Quality Gate](https://github.com/sinanuozdemir/oreilly-ai-agents/actions/workflows/pingone-quality-gate.yml/badge.svg)
```

Trivial? No. **Visible quality is cultural infrastructure** — the
badge turns "we have tests" into a public commitment.

---

## 🖱️ Portal Work (5 min — GitHub this time)

1. Repo → **Settings** → **Secrets and variables** → **Actions**
2. Add the 5 secrets from the table in §2
3. Push this branch (or open/update PR #14) → watch the
   **Actions** tab: the gate runs live
4. Click into the run → read the Step 2 output in the log —
   it's the same ✅/❌ output you've seen locally, now running
   on GitHub's machines

**Notice what you just configured:** the tenant credentials your
Worker app uses are now *build infrastructure*. Who can edit those
secrets? Who can see the logs? Those are the questions a security
team asks about CI — and now you've touched the system they're
asking about.

---

## ✅ Checkpoint

**1. Why does the same `os.environ` code work locally AND in CI?**

> **Answer:** Both paths end at environment variables. Locally,
> dotenv loads `.env` into `os.environ`; in CI, GitHub injects
> secrets as env vars directly. The code reads `os.environ` either
> way — it neither knows nor cares where the values came from.

**2. A secret was committed to git, then deleted in the next commit. Safe?**

> **Answer:** No — git history keeps it forever. Anyone with repo
> access (or a cloned fork) can check out the old commit. The only
> fix is **rotating the secret** (revoke + reissue), then optionally
> scrubbing history. This is why secrets live in CI secret stores
> from day one.

**3. Why shouldn't the LLM generation step block merges?**

> **Answer:** Non-determinism. Kimi may return different specs each
> run, and LLM latency/outages shouldn't freeze your team's merges.
> Gate on deterministic suites (Step 2), run AI steps as
> informational reports. A flaky gate trains people to ignore red.

**4. What does "shift-left" actually mean?**

> **Answer:** Moving quality checks earlier in the timeline — from
> after deploy, to before merge, to (ultimately) the developer's
> IDE. Every step left makes bugs cheaper: a bug caught in CI costs
> a failed build; the same bug in prod costs an incident.

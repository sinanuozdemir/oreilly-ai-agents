# Step 2: API Testing — From "It Works" to "It's Proven"

> Step 0 proved you *can* call the PingOne API. Step 1 proved a *human*
> can log in. Step 2 is where you stop being a user and start being a
> **QE engineer**: every API call becomes an *assertion*, every happy
> path gets a *negative twin*, and the whole suite runs in seconds —
> no browser, no human, fully CI-ready.

---

## 1. What Makes an API Call a *Test*?

### The Formula

```
SCRIPT (Step 0/1):        TEST (Step 2):

response = call_api()     response = call_api()
print(response)    →      assert response.status_code == 201
                          assert response.json()["email"] == expected
                          # cleanup so the next run is identical
```

A script **observes**. A test **asserts** — it has an opinion about
what *should* happen and fails loudly when reality disagrees.

| | Script | Test |
|---|--------|------|
| Output | Prints for a human to eyeball | Pass/fail, no eyeballing |
| Failure mode | You notice something looks wrong | Non-zero exit code, CI turns red |
| State | Leaves junk behind | Cleans up after itself |
| Run count | "I ran it once, it worked" | Runs 1,000 times, same result |

### The Testing Angle

Every endpoint you tested by hand has **three families of tests**:

```
✅ HAPPY PATH     — create user with valid data → 201, fields match
❌ NEGATIVE       — duplicate username → 409 (not 500, not silent success!)
🔒 SECURITY       — token from Worker-A can't touch Environment-B
```

The negative and security tests are where the *value* is. Happy paths
rarely break in prod — **error handling and cross-tenant boundaries do.**

---

## 2. The Golden Rule: Tests Leave No Trace

### The Problem

Your test creates `qe-test-user` in the tenant. Run it again tomorrow —
now there are 47 copies, the "create user" test fails because the
username already exists, and nobody trusts the suite anymore.

```
❌ FLAKY TEST (depends on leftover state):
   create user → assert created → (leaves user behind)
   next run: "user already exists" → FAIL — but the API is fine!

✅ DETERMINISTIC TEST (self-cleaning):
   create user → assert created → delete user → assert gone
   next run: identical. ALWAYS.
```

### The Pattern: Setup → Exercise → Assert → **Teardown**

```
┌──────────────────────────────────────────────────────────┐
│  setup()      →  get token, generate UNIQUE username     │
│                  (timestamp suffix = no collisions ever) │
│  test body    →  the actual API calls + assertions       │
│  teardown()   →  delete everything created, EVEN IF      │
│                  the test failed (try/finally!)          │
└──────────────────────────────────────────────────────────┘
```

**Interview trap:**

```
❌ "Our tests clean up after themselves when they pass"
✅ "Teardown runs in a finally-block — a failing test still
    cleans up. Otherwise failures compound into data rot,
    and tomorrow's failures are caused by yesterday's."
```

---

## 3. Status Codes Are the Contract

You're not just testing *that* the API responds — you're testing that
it responds with the **right contract**. PingOne (like every serious
REST API) encodes meaning in status codes:

| Code | Meaning | Your test asserts |
|------|---------|-------------------|
| `200` | Read/update succeeded | GET user returns the user |
| `201` | Created | POST user returns the new user *with an `id`* |
| `204` | Deleted (no body) | DELETE returns empty |
| `400` | Bad request — *client's* fault | Missing email → 400 with error detail |
| `401` | No/invalid token | Garbage `Bearer` → 401 |
| `403` | Valid token, insufficient *roles* | Worker without Identity Data Admin → 403 |
| `404` | Doesn't exist | GET deleted user → 404 |
| `409` | Conflict | Duplicate username → 409 |

**The subtle one:** `401` vs `403`.

```
401 = "I don't know who you are"        (authentication failed)
403 = "I know who you are — and NO."    (authorization failed)

Test both. A Worker app with a valid token but missing roles
MUST get 403, never 401 — otherwise your monitoring can't tell
"expired token" from "misconfigured permissions."
```

---

## 4. Negative Tests — Where QE Earns Its Salary

Anyone can test that valid input works. The bugs live in the edges:

```
ENDPOINT: POST /users

✅ happy:        valid username + email + population → 201
❌ duplicate:    same username twice → 409
❌ missing:      no email → 400
❌ malformed:    email = "not-an-email" → 400
❌ wrong pop:    population id from ANOTHER env → 400/403/404
❌ giant input:  10MB username → 400 (not a crash!)
```

### The AI Connection (preview of Step 3)

Look at that list — a human wrote it by *thinking about failure modes*.
An LLM is genuinely good at generating these variations ("give me 10
ways this request could be malformed"). But it also generates nonsense:
tests for fields that don't exist, wrong expected codes. That's exactly
why Step 3 pairs generation with an **evaluator**. You heard it here
first: *generation is cheap, validation is the product.*

---

## 5. CRUD Lifecycle Testing — The Full Circle

The most valuable API test isn't one call — it's a **lifecycle**,
because it proves the system stays consistent across operations:

```
CREATE  ──►  READ  ──►  UPDATE  ──►  DELETE  ──►  VERIFY GONE
  │           │           │            │              │
 201          200         200          204            404
 has id     fields      new value   empty body    "not found"
            match       persisted
```

Each arrow is a potential failure: create says 201 but read returns
stale data? Update returns 200 but the change didn't persist?
Delete returns 204 but the user still shows up in list calls?
**These are real bugs that single-call tests never catch.**

---

## 6. Where Playwright Fits (and Where It Doesn't)

```
API TESTS (this step)              BROWSER TESTS (Playwright, later)
─────────────────────────          ─────────────────────────────────
requests → JSON → assert           real browser → clicks → assert
seconds for 50 tests               seconds for ONE test
runs in CI with zero setup         needs browser binaries, more flake
tests the CONTRACT                 tests the EXPERIENCE
                                   
"the API enforces 409 on           "test.user1 can actually log in
 duplicate username"                and lands on the right page"
```

**The rule:** test everything you can at the API level. Reserve the
browser for what *only* a browser can prove — the actual login UX,
redirects, cookie behavior. A good suite is a **pyramid**: hundreds of
API tests at the base, a handful of browser tests at the peak.

---

## 💻 The Test Script — What You're About to Run

[test_pingone_api.py](test_pingone_api.py) runs **8 real tests**
against your live tenant using plain Python (no pytest needed — just
run it). It covers:

```
1  ✅ token acquisition        — client credentials still valid?
2  ✅ token claims             — is 'sub' our Worker app, not a user?
3  ✅ user CRUD lifecycle      — create → read → delete → verify 404
4  ❌ duplicate username       — must be 409, not 201, not 500
5  ❌ missing required field   — must be 400
6  ❌ bad token                — garbage Bearer must be 401
7  ✅ populations readable     — the list test
8  ✅ cleanup verification     — no test users left behind
```

Run it:

```bash
cd pingone-real-testing/step2_api_testing
python test_pingone_api.py
```

**What to notice while it runs:**

1. **Every test prints the status code it expected AND got** — watch
   the negative tests: you're hoping to see 4xx codes. In API testing,
   a 400 can be a *pass*.
2. **The CRUD test creates a real user** in your tenant — then deletes
   it. Open the PingOne console (Directory → Users) in another tab and
   run the script twice: the user count should return to baseline.
3. **Exit code matters:** `echo $?` after the run. `0` = green,
   `1` = red. That number is literally what CI reads in Step 4.

---

## 🖱️ Portal Work (2 min — optional but illuminating)

While the suite runs, open **Directory → Users** in the console and
keep it visible. You'll see `qe-test-<timestamp>` appear and vanish.
That's the setup/teardown pattern made visible — the same pattern
your Playwright tests will need later.

---

## ✅ Checkpoint

**1. A test creates a user, asserts 201, and exits. What's wrong?**

> **Answer:** No teardown — the user stays in the tenant. Next run may
> fail on duplicate username, and over time the tenant fills with test
> debris. Teardown must run even on failure (`try/finally`), and
> usernames should be unique per run (timestamp suffix).

**2. Your Worker app's token is valid but lacks the role to create
users. What status code should the API return — and why not the other one?**

> **Answer:** **403** — the token authenticated fine (so not 401), but
> the *role* is insufficient. 401 means "who are you?", 403 means
> "I know you, and no." Testing this distinction lets monitoring tell
> expired tokens apart from permission misconfigurations.

**3. Why prefer API tests over Playwright tests for most coverage?**

> **Answer:** Speed and determinism. 50 API tests run in seconds with
> zero browser setup; one Playwright test needs a real browser and is
> inherently flakier. Pyramid: many API tests at the base, few browser
> tests at the peak — reserve the browser for what only it can prove.

**4. Why does the CRUD lifecycle test catch bugs that single-call tests miss?**

> **Answer:** It tests *consistency across operations*: create-then-read
> catches stale reads, update-then-read catches non-persisted writes,
> delete-then-list catches soft-delete leaks. Each arrow between
> operations is a failure mode invisible to isolated calls.

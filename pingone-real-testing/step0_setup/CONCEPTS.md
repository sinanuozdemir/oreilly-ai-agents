# Step 0: Concepts You Must Know Before Touching the API

> Read this first. Everything else builds on these ideas.
> Each section ends with: a **testing angle** (what a QE team does with it)
> and an **interview line** (how to say it in the room).

---

## 1. OAuth 2.0 — The Authorization Framework

### The Problem It Solves

How does an application get permission to call an API *without holding
the user's password*?

Before OAuth, apps literally asked for your username and password and
stored them. If that app was breached, your credentials were gone —
and the app could do *anything* as you, forever. OAuth replaced
"hand over your password" with "hand over a limited, revocable pass."

### The Analogy: The Hotel Key Card

```
You arrive at a hotel
     │
     ▼
Front desk checks your ID (authentication)
     │
     ▼
Desk gives you a KEY CARD (access token)
     │
     ├── Opens YOUR room      (scope: read your data)
     ├── Opens the gym        (scope: access shared resources)
     ├── Does NOT open other rooms  (no cross-tenant access!)
     └── Stops working at checkout  (expiry)
```

You never show your ID to every door. The card *is* the proof.
If you lose the card, the front desk revokes it — your actual
identity (and other guests) are never at risk.

### The 4 Roles (memorize these — interviewers ask)

```
┌──────────────────┐         ┌────────────────────────┐
│  RESOURCE OWNER  │         │  AUTHORIZATION SERVER  │
│  (who owns data) │         │  (issues tokens)       │
└────────┬─────────┘         └───────────┬────────────┘
         │ grants                        │ verifies, issues
         ▼                               ▼
┌──────────────────┐         ┌────────────────────────┐
│  CLIENT          │────────►│  RESOURCE SERVER       │
│  (the app)       │ token   │  (the API, checks      │
└──────────────────┘         │   token on each call)  │
                             └────────────────────────┘
```

| Role | Generic | **In OUR setup** |
|------|---------|------------------|
| Resource Owner | The user (or org) | Our trial organization |
| Client | The app asking for access | Our Worker app / `ping_client.py` |
| Authorization Server | Issues tokens | `auth.pingone.com/{envID}/as` |
| Resource Server | API holding the data | `api.pingone.com/v1` |

### Grant Types — THE Classic Interview Topic

A "grant type" is just **which dance steps** the client and server do
to produce a token. Different situations need different dances.

| Grant | Who uses it | Flow | User involved? |
|-------|-------------|------|----------------|
| **Client Credentials** | Machine-to-machine: CI jobs, daemons, **AI agents** | client_id + secret → token | ❌ No |
| **Authorization Code + PKCE** | Web apps, mobile, desktop, SPAs | browser redirect → login → code → token | ✅ Yes |
| **Device Authorization** | TVs, consoles, CLI tools | show code on screen, approve on phone | ✅ Yes |
| **Refresh Token** | All of the above | exchange old token for new silently | ❌ No |

Why so many? Because **a secret can only be kept secret on a server.**

```
Can this thing keep a secret?
        │
        ├── YES (backend server) ──► Client Credentials or
        │                            Auth Code + client_secret
        │
        └── NO (phone, browser, desktop binary) ──► Auth Code + PKCE
                                                    (PKCE replaces the secret)
```

Our Worker app uses **Client Credentials** — it's a machine acting as
itself. When we test end-user login (Step 1-2), we use
**Authorization Code + PKCE** — a human is involved.

> 🎤 **Interview line:** *"We use client credentials for service-to-service,*
> *and authorization code with PKCE for anything with a user interface —*
> *PKCE protects public clients that can't keep a secret."*

---

## 2. PKCE — The Secret Substitute

**PKCE** ("pixie") = **Proof Key for Code Exchange**. An extension to
the Authorization Code flow.

### The Problem It Solves

Mobile and desktop apps **ship their code to users**. Anyone can
decompile your app and extract a `client_secret`. So public clients
can't have secrets... but then what stops an attacker who *intercepts
the authorization code* mid-redirect (e.g., a malicious app that
registered the same `myapp://` deep-link on the victim's phone)
from exchanging it for tokens?

PKCE closes that hole **without needing a pre-shared secret at all** —
the client invents a *one-time* secret per login attempt.

### The Flow

```
APP                                     PINGONE
 │                                         │
 │  1. invent code_verifier (random)       │
 │  2. code_challenge = SHA256(verifier)   │
 │                                         │
 │  3. GET /authorize?code_challenge=xxx ─►│ stores the challenge
 │                                         │
 │  4.            (user logs in)           │
 │                                         │
 │  5. ◄── redirect: myapp://cb?code=abc   │ attacker can see this!
 │                                         │
 │  6. POST /token {code, verifier} ──────►│ checks: SHA256(verifier)
 │                                         │         == challenge? ✅
 │  7. ◄── access token                    │
```

The attacker at step 5 has the `code` but **not** the `code_verifier` —
it never left the app until step 6, sent directly over TLS. The
attacker's exchange fails.

**Analogy:** You phone a restaurant and make a reservation using a
phrase only you know (challenge). When you arrive (code exchange),
they ask you to repeat the phrase. Someone who overheard "table for
two" can't claim your table without the phrase.

### Why It Matters for Testing (Step 2 preview)

| Platform | Client type | PKCE? |
|----------|-------------|-------|
| Web app with backend | Confidential (has secret) | Optional but recommended |
| SPA (no backend) | Public | **Required** |
| Mobile | Public | **Required** |
| Desktop | Public | **Required** |

Modern guidance (OAuth 2.1 draft): use Auth Code + PKCE for
**everything**, and never use the old Implicit flow (which put tokens
in URLs — browser history, referer headers, logs. Yikes.)

> 🎤 **Interview line:** *"PKCE turns the authorization code into a*
> *one-time, sender-bound credential. That's why current best practice*
> *is Authorization Code + PKCE everywhere — even for confidential*
> *clients — and the Implicit flow is dead."*

---

## 3. JWT — The Token Format

### OAuth vs JWT — The Distinction Everyone Fumbles

| | OAuth 2.0 | JWT |
|---|-----------|-----|
| **What it is** | A **framework** — flows for getting permission | A **format** — a way to encode + sign data |
| **Answers** | "How do I get access?" | "How do I prove what was granted?" |
| **Analogy** | The process of getting the key card | The key card itself |

**OAuth is the dance. JWT is the ticket the dance produces.**

And a nuance: OAuth doesn't *require* JWTs. Access tokens come in
two flavors:

```
ACCESS TOKEN
     │
     ├── OPAQUE:  "a94f3bc1..."  (random string)
     │            API must CALL the auth server to check it
     │            (introspection) — extra network hop, but
     │            instantly revocable
     │
     └── JWT:     eyJhbGci...  (self-contained, signed)
                  API verifies the SIGNATURE locally — no
                  network call — but revocation needs to wait
                  for expiry (or a revocation list)
```

PingOne issues **JWTs**.

### Anatomy of a JWT

Three base64url parts, dot-separated:

```
eyJhbGciOiJSUzI1NiJ9 . eyJpc3MiOiJodHRw... . SflKxwRJSMeKKF2QT4fwpMe...
└────── HEADER ──────┘   └──── PAYLOAD ──┘   └────── SIGNATURE ───────┘
  {"alg":"RS256"}          the claims         proves nobody tampered
```

Decoded payload from a real PingOne client-credentials token:

```json
{
  "iss": "https://auth.pingone.com/<env-id>/as",  // who ISSUED it
  "sub": "<client-id>",                            // who it REPRESENTS
  "aud": "api.pingone.com",                        // who it's FOR
  "exp": 1755561600,                               // when it DIES (~1hr)
  "scope": "p1:read:user p1:create:user"           // what it can DO
}
```

### "In My Previous Org We Generated JWTs for Mobile Testing"

You were doing one of these — all common QE patterns:

1. **"Skip the flow" tokens** — a test utility calls the token endpoint
   directly (client credentials) and mints real JWTs, so API tests
   don't automate a fragile login UI on every run. *That's still OAuth —
   just the browser part bypassed.* ← **exactly what our
   `ping_client.py` does**

2. **Hand-crafted JWTs** — a mock server signs its own JWTs with a
   test key so you control every claim: expiry, roles, tenant.
   Perfect for negative testing.

3. **OIDC id_tokens** — in OpenID Connect (the identity layer *on top
   of* OAuth), the `id_token` is *always* a JWT. If your mobile tests
   verified "user is logged in," you were inspecting these.

### Testing Angle — Your First Real Test Scenarios

```
✅ Token expired by 1 second          → expect 401
✅ Valid signature, wrong audience    → expect 403
✅ Token from env A → API of env B    → expect 403 (tenant isolation!)
✅ Tampered payload (re-signed wrong) → expect 401
✅ Valid token, missing scope         → expect 403 (least privilege)
```

> 🎤 **Interview line:** *"OAuth is how you obtain authorization; JWT*
> *is the format it often arrives in. In mobile testing I minted test*
> *JWTs to decouple API suites from the UI login flow — same pattern*
> *as a Worker app token for service-level tests."*

---

## 4. PingOne's Two APIs — The Critical Distinction

This trips up everyone new to PingOne. There are **two separate API
surfaces** with different jobs:

```
┌─────────────────────────────────────────────────────────────┐
│  MANAGEMENT API          vs          AUTHENTICATION API     │
│  api.pingone.com/v1                auth.pingone.com/{env}   │
│                                                             │
│  "Operate ON the tenant"           "Operate AS a user"      │
│                                                             │
│  • create users                  • /authorize (login page)  │
│  • manage groups                 • /token (exchange code)   │
│  • configure apps                • /userinfo (who am I)     │
│  • set policies                  • MFA challenges           │
│                                                             │
│  Auth: Worker app token          Auth: OIDC flows (human)   │
│  Used by: admins, CI, agents     Used by: your app's users  │
└─────────────────────────────────────────────────────────────┘
```

**Rule of thumb:** if a *machine* is doing it, Management API.
If a *human* is logging in, Authentication API.

Our Step 0 script uses the Management API. Step 1's login flow
uses the Authentication API.

---

## 5. How a QE Team Approaches Identity Testing

Identity isn't one feature — it's a **stack**, and each layer has its
own failure modes:

```
Layer 1: CONTRACT    Does the API accept/reject the right shapes?
                     → schema validation, required fields, types
                     → (this is Module 2's Stage 1!)

Layer 2: AUTHZ       Does the token allow EXACTLY what's scoped?
                     → least-privilege tests, scope escalation probes
                     → (Module 3's permission boundaries!)

Layer 3: WORKFLOW    Do multi-step flows hold together?
                     → create user → assign group → login → access

Layer 4: NEGATIVE    What happens when things go wrong?
                     → expired tokens, revoked users, cross-tenant

Layer 5: PLATFORM    Same flows, different surfaces
                     → web vs desktop vs mobile (Step 2)
```

A mature team automates Layers 1-4 in CI and pushes platform-specific
risk (Layer 5) into targeted device/browser matrices — not running
everything everywhere.

### Platform Challenges (deep dive in Step 2)

| Challenge | Web | Desktop | Mobile |
|-----------|-----|---------|--------|
| **Redirect handling** | Browser redirects, cookies | Loopback server or device flow | Deep links / claimed HTTPS URLs |
| **Token storage** | Memory > localStorage (XSS risk) | OS keychain | Keychain / Keystore |
| **Client secret** | Backend only | Can't keep one → PKCE | Can't keep one → PKCE |
| **Session** | Cookies, silent renew | Token refresh daemon | Background refresh, biometrics |
| **Attack surface** | XSS, CSRF, CORS | Binary tampering | Rooted devices, app cloning |

---

## 6. Where AI Fits (Preview of Step 3)

PingOne's API surface is huge — users, groups, populations, apps,
MFA, sign-on policies, password policies... Writing every test
scenario by hand doesn't scale. Our approach:

```
┌─────────────┐   generate   ┌──────────────┐   validate   ┌─────────────┐
│ PingOne API │─────────────►│ LLM writes   │─────────────►│ Module 2    │
│ operations  │  scenarios   │ test cases   │  3 stages    │ evaluator   │
└─────────────┘              └──────────────┘              └──────┬──────┘
                                                                  │
                                        schema → semantic → exec  ▼
                                                          ┌─────────────┐
                                                          │ Good tests  │
                                                          │ run against │
                                                          │ REAL tenant │
                                                          └──────┬──────┘
                                                                  ▼
                                                          ┌─────────────┐
                                                          │ Step 4: CI  │
                                                          │ quality gate│
                                                          └─────────────┘
```

This is **agentic quality engineering** in practice — and it's
literally in the Ping job description.

---

## ✅ Checkpoint — Test Yourself, Then Check the Answer

**1. What are OAuth's 4 roles, and which is our Worker app?**

> **Answer:** Resource Owner (our trial org), Client (the app asking for
> access), Authorization Server (`auth.pingone.com` — issues tokens),
> Resource Server (`api.pingone.com` — checks tokens).
> **Our Worker app = the Client** — a machine acting as itself via the
> client credentials grant.

**2. Why does a mobile app need PKCE but a backend server doesn't?**

> **Answer:** A mobile app **can't keep a secret** — anyone can decompile
> the binary and extract it, and the authorization code can be intercepted
> via deep-link hijacking. PKCE replaces the pre-shared secret with a
> one-time verifier/challenge pair: the hash rides the redirect, the raw
> verifier rides the back-channel POST, so an intercepted code is useless.
> A backend server *can* keep a secret — it never leaves the data center —
> so the plain client_secret suffices (though PKCE is still recommended).

**3. What's the difference between OAuth and JWT?**

> **Answer:** **OAuth is the framework** (the flows for obtaining access);
> **JWT is a token format** (the signed, self-contained credential a flow
> often produces). OAuth can also issue opaque tokens; JWTs can exist
> outside OAuth. *The dance vs. the ticket.*

**4. Which PingOne API creates a user? Which one logs a user in?**

> **Answer:** **Management API** (`api.pingone.com/v1`) creates a user —
> machine/admin operations with a Worker app token.
> **Authentication API** (`auth.pingone.com/{envID}`) logs a user in —
> human OIDC flows (`/authorize`, `/token`, `/userinfo`).

**5. Name the 5 testing layers. Which one do expired-token tests live in?**

> **Answer:** **Contract → AuthZ → Workflow → Negative → Platform.**
> Expired-token tests live in **Layer 4: Negative** (with a contract
> element — you're asserting the correct 401 shape).

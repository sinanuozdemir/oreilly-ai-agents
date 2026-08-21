# Step 1: Protocols — OIDC, SAML, and SCIM in the Real World

> Step 0 proved a *machine* can authenticate. Step 1 is about *humans*
> logging in — and the three protocols PingOne (and every enterprise IdP)
> uses to make that happen. You'll run a real login flow against your
> tenant and inspect every artifact it produces.

---

## 1. OIDC — The Identity Layer on Top of OAuth

### The Problem It Solves

OAuth answers *"what is this app allowed to do?"* — but deliberately says
**nothing about who the user is**. An access token alone doesn't tell your
app the user's name, email, or even that a login happened at all.

Early products abused OAuth for login anyway ("Sign in with X" v1), with
predictable chaos: every provider invented its own `/me` endpoint, and
apps confused "has a token" with "is authenticated."

**OpenID Connect (OIDC)** fixed this by adding a thin, standard identity
layer on top of OAuth 2.0:

```
┌─────────────────────────────────────────────┐
│  OIDC                                       │
│  "WHO is the user?"                         │
│  • id_token (always a JWT)                  │
│  • /userinfo endpoint                       │
│  • standard scopes: openid profile email    │
│  • discovery document (.well-known)         │
├─────────────────────────────────────────────┤
│  OAuth 2.0                                  │
│  "WHAT may the app do?"                     │
│  • access tokens, grants, scopes            │
└─────────────────────────────────────────────┘
```

**One-sentence version:** OAuth delegates *authorization*; OIDC adds
*authentication* — the `id_token` is the proof a login happened.

### The Three Tokens of an OIDC Login

When our playground script completes a login, PingOne returns all three:

| Token | Format | Purpose | Where it goes |
|-------|--------|---------|---------------|
| **id_token** | JWT (always) | "This is who logged in, when, and how" | Stays in the client — never sent to APIs |
| **access_token** | JWT (PingOne) | "This session may call these APIs" | Sent to resource servers as `Bearer` |
| **refresh_token** | Opaque | "Get new tokens without re-login" | Stored securely, sent only to `/token` |

The single most common interview trap:

```
❌ "We validate the user by sending the id_token to our API"
✅ "id_token is FOR the client — proof of login. APIs get the
    access_token. Mixing them is an authz vulnerability."
```

### The Discovery Document — OIDC's Killer Feature

Every OIDC provider publishes a machine-readable menu of its endpoints:

```
GET https://auth.pingone.com/{envID}/as/.well-known/openid-configuration

{
  "issuer": "https://auth.pingone.com/{envID}/as",
  "authorization_endpoint": ".../authorize",
  "token_endpoint": ".../token",
  "userinfo_endpoint": ".../userinfo",
  "jwks_uri": ".../jwks",          ← public keys for verifying JWTs
  "scopes_supported": [...],
  "grant_types_supported": [...]
}
```

**Why this matters for QE:** you never hardcode endpoints. A test can
discover the whole surface from one URL — which also means *your AI test
generator (Step 3) can bootstrap itself from the discovery document.*

---

## 2. SAML — The Enterprise Veteran

### What It Is

**SAML 2.0** (2005) does the same job as OIDC — federated login — but
with XML, in the browser, for an era of enterprise web apps.

| | SAML 2.0 | OIDC |
|---|----------|------|
| Born | 2005 | 2014 |
| Format | **XML assertions** (signed) | **JWT** (signed JSON) |
| Transport | Browser POSTs/redirects | Redirects + back-channel API |
| Sweet spot | Enterprise web SSO | Mobile, SPA, APIs, modern apps |
| Token contains | Attributes about user | Claims about user |
| Discovery | Metadata XML file | `.well-known` JSON |

### The SAML Flow (compare to the PKCE diagram)

```
USER's BROWSER          SERVICE PROVIDER (SP)         IdP (Ping)
      │                        │                         │
      │  1. GET /app           │                         │
      │───────────────────────►│                         │
      │                        │                         │
      │  2. redirect with      │                         │
      │     SAMLRequest (XML)  │                         │
      │◄───────────────────────│                         │
      │                        │                         │
      │  3. present to IdP ─────────────────────────────►│
      │                        │                         │
      │  4.            (user logs in at IdP)             │
      │                        │                         │
      │  5. ◄── form POST with SAMLResponse (XML)        │
      │                        │                         │
      │  6. POST assertion ───►│ verifies XML signature  │
      │                        │ creates session         │
```

Everything goes **through the browser** — there is no back channel.
That's why SAML fits web apps but is painful for mobile/APIs, and why
the industry builds new things on OIDC.

### Testing Angle — What Breaks in SAML

```
✅ Clock skew       — assertion valid 2 min ago? (NotBefore/NotOnOrAfter)
✅ Signature        — tampered XML must be rejected
✅ Audience         — assertion meant for SP-A used at SP-B
✅ Replay           — same assertion submitted twice
✅ Attribute mapping— IdP sends "mail", SP expects "email"
```

---

## 3. SCIM — Provisioning, Not Login

### The Problem It Solves

OIDC/SAML answer *"how does a user log in?"* Nobody had answered
*"how do 5,000 employees get accounts created/updated/deactivated in
40 SaaS apps when HR changes one record?"*

**SCIM** (System for Cross-domain Identity Management) is a standard
REST + JSON protocol for **user provisioning**:

```
HR SYSTEM (source of truth)
     │  Jane joins engineering
     ▼
IdP (Ping) ──SCIM──► Salesforce   (create user)
         ──SCIM──► Slack        (create user)
         ──SCIM──► GitHub       (create user)

Jane leaves:
         ──SCIM──► everything   (deactivate — SAME DAY, not "next audit")
```

| Protocol | Question answered |
|----------|-------------------|
| OIDC | "Who is logging in?" (authentication) |
| OAuth | "What may this caller do?" (authorization) |
| SAML | "Who is logging in?" (enterprise web edition) |
| **SCIM** | "Who *exists* in this system?" (provisioning) |

### Testing Angle — SCIM's Real Risk

Deprovisioning lag is a compliance incident. The tests that matter:

```
✅ Terminated user's access dies everywhere within SLA
✅ Attribute change (department) propagates correctly
✅ Conflict handling — user exists in target already
✅ Bulk operations — 500 hires on the same Monday
```

---

## 4. The Playground Script — What You're About to Run

[oidc_playground.py](oidc_playground.py) performs a **real
Authorization Code + PKCE flow** against your tenant:

```
SCRIPT                                     PINGONE
  │                                          │
  │  1. Generate verifier + challenge        │  (the PKCE pair from Step 0)
  │                                          │
  │  2. Start loopback server                │
  │     http://localhost:8080/callback       │  (desktop-app pattern!)
  │                                          │
  │  3. Open browser to /authorize ─────────►│
  │                                          │  4. YOU log in as test.user1
  │                                          │
  │  5. ◄── browser redirected to            │
  │     localhost:8080/callback?code=...     │
  │                                          │
  │  6. POST /token {code, verifier} ───────►│  SHA256 check ✅
  │                                          │
  │  7. ◄── id_token + access_token          │
  │                                          │
  │  8. Decode & inspect every claim         │
  │  9. Call /userinfo, compare to id_token  │
```

**Two things to notice while it runs:**

1. **The loopback redirect is the desktop pattern.** Native apps can't
   receive deep links in a dev script, so they listen on
   `localhost:<port>` — you'll see the code arrive in your own terminal.

2. **You are the user now.** In Step 0 the "actor" was a Worker app.
   Here `test.user1` authenticates — watch how the artifacts differ
   (an `id_token` appears; `sub` is a person, not a client).

---

## 🖱️ Portal Work Before Running (5 min)

You need an **OIDC client application** (different from the Worker app!):

1. `ai-test-lab` → **Applications** → **+**
2. Name: `oidc-playground` → Type: **OIDC Web App** → Save
3. Open it → **Configuration** tab:
   - **Grant type:** Authorization Code
   - **PKCE enforcement:** **REQUIRED** (this is the setting you'd test in prod!)
   - **Redirect URIs:** `http://localhost:8080/callback`
   - **Token endpoint auth method:** None (public client — PKCE protects us)
4. **Enable** the app (toggle, top right)
5. Copy its **Client ID** — add to root `.env`:

```
PINGONE_OIDC_CLIENT_ID=<the new app's client id>
```

**Notice what you just configured:** "PKCE enforcement: REQUIRED" and
"auth method: None" are the exact production settings a security team
argues about. You've now *seen* the knobs the concepts describe.

---

## ✅ Checkpoint

**1. What's the difference between an id_token and an access_token?**

> **Answer:** id_token proves **who logged in** — it's for the client,
> always a JWT, never sent to APIs. access_token proves **what the caller
> may do** — it's sent to resource servers. Confusing them is a classic
> authz vulnerability.

**2. Which protocol would you use to provision 500 new hires into Salesforce?**

> **Answer:** **SCIM** — it's the provisioning protocol (REST+JSON for
> user lifecycle). OIDC/SAML handle login, not account lifecycle.

**3. Why does SAML struggle on mobile but OIDC doesn't?**

> **Answer:** SAML rides entirely through browser POSTs/redirects with
> XML — no back channel, no native-app-friendly token exchange. OIDC
> added back-channel endpoints (/token) and PKCE, so public clients like
> mobile apps can exchange codes directly and safely.

**4. Where does an OIDC client discover the provider's endpoints?**

> **Answer:** The **discovery document** at
> `/.well-known/openid-configuration` — one JSON file listing issuer,
> authorize/token/userinfo endpoints, and the JWKS keys used to verify
> signatures.

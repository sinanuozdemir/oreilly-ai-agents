"""
OIDC Playground - A real Authorization Code + PKCE login against PingOne.

You will WATCH every step of the flow from Step 0's diagram:
  - the verifier/challenge pair being created
  - the browser redirect carrying the code (it arrives at YOUR localhost)
  - the back-channel /token exchange
  - the three tokens coming back
  - what /userinfo says vs what the id_token says

This is the "desktop app" pattern: a native app can't receive a deep link
in dev, so it listens on a loopback URL (http://localhost:PORT/callback).

Run:  python oidc_playground.py
"""

import base64
import hashlib
import json
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

# ─────────────────────────────────────────────────────────────────────
# CONFIG — same root .env as Step 0 (loaded by ping_client at import)
# ─────────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "step0_setup"))
from ping_client import _load_root_env  # noqa: E402  (loads root .env)

_load_root_env()

ENVIRONMENT_ID = os.environ["PINGONE_ENVIRONMENT_ID"]
CLIENT_ID = os.environ["PINGONE_OIDC_CLIENT_ID"]  # the OIDC app, not the Worker!
REGION = os.environ.get("PINGONE_REGION", "com")

AUTH_BASE = f"https://auth.pingone.{REGION}/{ENVIRONMENT_ID}/as"
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "openid profile email"


# ─────────────────────────────────────────────────────────────────────
# PKCE — the two values from Step 0's diagram
# ─────────────────────────────────────────────────────────────────────
def generate_pkce_pair() -> tuple[str, str]:
    """
    code_verifier:  random string, stays secret until the /token call
    code_challenge: SHA256(verifier), sent through the browser
    """
    verifier = secrets.token_urlsafe(64)  # ~86 chars of randomness
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


# ─────────────────────────────────────────────────────────────────────
# LOOPBACK SERVER — catches the redirect (step 5 of the diagram)
# ─────────────────────────────────────────────────────────────────────
class CallbackHandler(BaseHTTPRequestHandler):
    """Receives the redirect from PingOne with ?code=... in the URL."""

    auth_code: str | None = None
    state_seen: str | None = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            CallbackHandler.auth_code = params.get("code", [None])[0]
            CallbackHandler.state_seen = params.get("state", [None])[0]

            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"<h1>Login complete!</h1>"
                b"<p>The authorization code arrived at your loopback server. "
                b"Return to the terminal to watch the /token exchange.</p>"
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):  # keep the terminal clean
        pass


def decode_jwt_unsafe(token: str) -> dict:
    """Decode a JWT payload WITHOUT verifying (learning purposes only!)."""
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def main():
    print("=" * 64)
    print("OIDC PLAYGROUND — Authorization Code + PKCE, live")
    print("=" * 64)

    # ── Steps 1-2: invent the PKCE pair ──────────────────────────────
    verifier, challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(16)  # CSRF protection — see note below

    print("\n🔐 STEP 1-2: PKCE pair generated")
    print(f"   code_verifier  (secret) : {verifier[:20]}...  [{len(verifier)} chars]")
    print(f"   code_challenge (public) : {challenge[:20]}...")
    print(f"   state          (CSRF)   : {state}")

    # ── Step 3: send the user to /authorize ──────────────────────────
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    authorize_url = f"{AUTH_BASE}/authorize?{urlencode(params)}"

    print("\n🌐 STEP 3: Opening browser to /authorize")
    print(f"   {authorize_url[:90]}...")
    print("   (PingOne now has our challenge stored)")

    # Start the loopback server BEFORE opening the browser
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"\n👂 Loopback server listening on {REDIRECT_URI}")

    webbrowser.open(authorize_url)
    print("\n⏳ STEP 4: Log in as your test user in the browser...")

    # Wait for the redirect (step 5)
    while CallbackHandler.auth_code is None:
        thread.join(0.1)
    server.shutdown()

    code = CallbackHandler.auth_code
    print(f"\n📨 STEP 5: Redirect arrived at localhost!")
    print(f"   code  = {code[:25]}...  [{len(code)} chars]")

    # CSRF check: the state PingOne echoed must match what we sent
    if CallbackHandler.state_seen != state:
        print("\n❌ STATE MISMATCH — possible CSRF. Aborting.")
        sys.exit(1)
    print("   state ✅ matches (this is your CSRF check working)")

    # ── Step 6: back-channel exchange — the PKCE moment ──────────────
    print("\n🔄 STEP 6: POST /token (back channel — verifier revealed HERE only)")
    resp = requests.post(
        f"{AUTH_BASE}/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "code_verifier": verifier,  # ← the raw secret, TLS only, one time
        },
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"\n❌ Token exchange failed: {resp.status_code}")
        print(f"   {resp.text}")
        print("\n   Common causes: PKCE not enforced on the app, redirect URI")
        print("   mismatch, token endpoint auth method not set to 'None'.")
        sys.exit(1)

    tokens = resp.json()
    print("   ✅ Exchange succeeded — SHA256(verifier) == challenge")

    # ── Step 7: inspect the artifacts ────────────────────────────────
    print("\n🎫 STEP 7: Tokens received")
    print(f"   id_token     : {len(tokens.get('id_token', ''))} chars (JWT)")
    print(f"   access_token : {len(tokens.get('access_token', ''))} chars")
    print(f"   refresh_token: {'present' if tokens.get('refresh_token') else '(not issued)'}")

    id_claims = decode_jwt_unsafe(tokens["id_token"])
    print("\n🪪 id_token claims — WHO logged in (this is OIDC's contribution):")
    for key in ("iss", "sub", "aud", "exp", "auth_time", "preferred_username", "email"):
        if key in id_claims:
            print(f"   {key:18}: {id_claims[key]}")

    # ── Step 8: /userinfo — the API view of the same user ────────────
    print("\n👤 STEP 8: GET /userinfo (access_token used as Bearer)")
    ui = requests.get(
        f"{AUTH_BASE}/userinfo",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        timeout=30,
    )
    if ui.status_code == 200:
        info = ui.json()
        print(f"   sub   : {info.get('sub')}")
        print(f"   email : {info.get('email')}")
        print(f"   name  : {info.get('name', info.get('preferred_username'))}")
        same = info.get("sub") == id_claims.get("sub")
        print(f"\n   id_token.sub == userinfo.sub ? {'✅ SAME USER' if same else '❌ MISMATCH'}")
    else:
        print(f"   ⚠️  /userinfo returned {ui.status_code}: {ui.text}")

    print("\n" + "=" * 64)
    print("✅ STEP 1 COMPLETE — you just ran a real OIDC + PKCE login")
    print("=" * 64)
    print("""
What to notice:
  • The code arrived via the BROWSER (front channel) — anyone watching
    the redirect could see it. It was still useless to them.
  • The verifier only ever traveled in the POST body (back channel).
  • id_token answered WHO; access_token let us call /userinfo.
  • 'state' protected against CSRF — always verify it.

🎤 Interview line: "I've run the full PKCE flow against PingOne —
   loopback redirect, state validation, back-channel exchange — and
   inspected the resulting id_token and access_token claims."
""")


if __name__ == "__main__":
    main()

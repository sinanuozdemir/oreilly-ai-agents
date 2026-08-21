"""
PingOne Client - Real authenticated client for the PingOne Management API.

This is the foundation everything else builds on:
- MCP tools (Step 1+) wrap these methods
- AI-generated tests (Step 3) exercise these endpoints
- CI gates (Step 4) run against this client

Concepts demonstrated:
- OAuth 2.0 Client Credentials grant (machine-to-machine)
- JWT access tokens with automatic refresh
- Least-privilege: this client can only do what the Worker app's roles allow
"""

import os
import time
import base64
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


def _load_root_env() -> None:
    """
    Load credentials from the .env at the WORKSPACE ROOT, not this folder.

    Single source of truth: one .env for all steps (0-4), so credentials
    are never duplicated across folders. Scripts can be run from anywhere
    and still find it.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return  # env vars may be set directly (e.g., in CI)

    # ping_client.py lives at: <root>/pingone-real-testing/step0_setup/
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    load_dotenv(env_path)

    # Helpful early failure — better than a cryptic KeyError later
    missing = [
        k for k in ("PINGONE_ENVIRONMENT_ID", "PINGONE_CLIENT_ID", "PINGONE_CLIENT_SECRET")
        if not os.environ.get(k)
    ]
    if missing:
        raise RuntimeError(
            f"Missing {missing} — set them in {env_path} "
            f"(see step0_setup/.env.example)"
        )


# Load credentials at import time — any script that imports this client
# gets the root .env automatically.
_load_root_env()


class PingOneClient:
    """
    Authenticated client for PingOne Management API.

    OAuth 2.0 Client Credentials flow:
        1. POST client_id + client_secret to the token endpoint
        2. Receive a JWT access token (valid ~1 hour)
        3. Include it as 'Authorization: Bearer <token>' on every API call
    """

    def __init__(
        self,
        environment_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        region: str = "com",  # com | eu | asia | ca
    ):
        self.environment_id = environment_id or os.environ["PINGONE_ENVIRONMENT_ID"]
        self.client_id = client_id or os.environ["PINGONE_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["PINGONE_CLIENT_SECRET"]

        self.api_base = f"https://api.pingone.{region}/v1"
        self.auth_base = f"https://auth.pingone.{region}/{self.environment_id}/as"

        self._token: Optional[str] = None
        self._token_expiry: float = 0

    # ─────────────────────────────────────────────────────────────
    # AUTHENTICATION
    # ─────────────────────────────────────────────────────────────

    def get_token(self) -> str:
        """
        Get a valid access token, fetching a new one if expired.

        Client Credentials grant = the simplest OAuth flow:
        no browser, no user — just the client proving its own identity.
        """
        if self._token and time.time() < self._token_expiry - 30:
            return self._token

        response = requests.post(
            f"{self.auth_base}/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(self.client_id, self.client_secret),  # HTTP Basic auth
            data={"grant_type": "client_credentials"},
            timeout=30,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Token request failed: {response.status_code} {response.text}"
            )

        payload = response.json()
        self._token = payload["access_token"]
        self._token_expiry = time.time() + payload.get("expires_in", 3600)
        return self._token

    def decode_token(self) -> Dict[str, Any]:
        """
        Decode the JWT payload (without verifying — just for learning).
        Look at 'scope' to see what this token is allowed to do.
        """
        token = self.get_token()
        payload_b64 = token.split(".")[1]
        # Add padding back
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.get_token()}"}

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Central request wrapper — every call goes through here."""
        url = f"{self.api_base}{path}"
        response = requests.request(
            method, url, headers=self._headers(), timeout=30, **kwargs
        )
        return response

    # ─────────────────────────────────────────────────────────────
    # ENVIRONMENTS
    # ─────────────────────────────────────────────────────────────

    def get_environment(self) -> Dict[str, Any]:
        """Get details about our environment."""
        resp = self._request("GET", f"/environments/{self.environment_id}")
        resp.raise_for_status()
        return resp.json()

    # ─────────────────────────────────────────────────────────────
    # USERS
    # ─────────────────────────────────────────────────────────────

    def list_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        resp = self._request(
            "GET",
            f"/environments/{self.environment_id}/users",
            params={"limit": limit},
        )
        resp.raise_for_status()
        return resp.json().get("_embedded", {}).get("users", [])

    def create_user(
        self, username: str, email: str, population_id: str,
        given_name: str = "Test", family_name: str = "User",
    ) -> Dict[str, Any]:
        body = {
            "username": username,
            "email": email,
            "population": {"id": population_id},
            "name": {"given": given_name, "family": family_name},
        }
        resp = self._request(
            "POST", f"/environments/{self.environment_id}/users", json=body
        )
        resp.raise_for_status()
        return resp.json()

    def get_user(self, user_id: str) -> Dict[str, Any]:
        resp = self._request(
            "GET", f"/environments/{self.environment_id}/users/{user_id}"
        )
        resp.raise_for_status()
        return resp.json()

    def delete_user(self, user_id: str) -> None:
        resp = self._request(
            "DELETE", f"/environments/{self.environment_id}/users/{user_id}"
        )
        resp.raise_for_status()

    # ─────────────────────────────────────────────────────────────
    # POPULATIONS (user partitions)
    # ─────────────────────────────────────────────────────────────

    def list_populations(self) -> List[Dict[str, Any]]:
        resp = self._request(
            "GET", f"/environments/{self.environment_id}/populations"
        )
        resp.raise_for_status()
        return resp.json().get("_embedded", {}).get("populations", [])

    # ─────────────────────────────────────────────────────────────
    # GROUPS
    # ─────────────────────────────────────────────────────────────

    def list_groups(self, limit: int = 10) -> List[Dict[str, Any]]:
        resp = self._request(
            "GET",
            f"/environments/{self.environment_id}/groups",
            params={"limit": limit},
        )
        resp.raise_for_status()
        return resp.json().get("_embedded", {}).get("groups", [])

    def create_group(self, name: str, description: str = "") -> Dict[str, Any]:
        resp = self._request(
            "POST",
            f"/environments/{self.environment_id}/groups",
            json={"name": name, "description": description},
        )
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    # Credentials already loaded from the root .env at import time.
    client = PingOneClient()

    print("=" * 60)
    print("STEP 0: FIRST REAL PINGONE API CALL")
    print("=" * 60)

    # 1. Who is our token? (decode the JWT)
    print("\n📜 Token claims (what our Worker app is allowed to do):")
    claims = client.decode_token()
    print(f"   Issuer : {claims.get('iss')}")
    print(f"   Subject: {claims.get('sub')}")
    print(f"   Expires: {time.ctime(claims.get('exp', 0))}")
    print(f"   Scopes : {claims.get('scope', '(none)')}")

    # 2. What environment are we in?
    print("\n🌍 Environment:")
    env = client.get_environment()
    print(f"   Name: {env.get('name')}  (id: {env.get('id')})")
    print(f"   Type: {env.get('type')}   Region: {env.get('region')}")

    # 3. List populations (needed to create users)
    print("\n👥 Populations:")
    for pop in client.list_populations():
        print(f"   - {pop['name']} (id: {pop['id']})")

    # 4. List users (probably just your admin)
    print("\n🧑 Users:")
    for user in client.list_users():
        print(f"   - {user.get('username')} ({user.get('email')})")

    print("\n✅ If you see the above, Step 0 is complete.")
    print("   Next: Step 1 — protocol playground (OIDC flows).")

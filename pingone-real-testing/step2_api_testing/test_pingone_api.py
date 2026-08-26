"""
PingOne API Test Suite - Step 2: from "it works" to "it's proven".

8 real tests against your live tenant. No pytest — just run it:
    python test_pingone_api.py

Each test prints the status code it EXPECTED and GOT — in negative
tests, a 4xx code is a PASS. The exit code (0=green, 1=red) is what
CI will read in Step 4.

What you should SEE while it runs:
  - the CRUD test creates a real user, then deletes it
  - negative tests hope for 4xx (watch for them!)
  - the final test proves nothing was left behind

Contract quirks this suite DOCUMENTED about PingOne (found by failing first):
  - Worker tokens carry the identity in `client_id`, not `sub`
  - duplicate username → 400 with UNIQUENESS_VIOLATION (not 409)
  - email is OPTIONAL when creating a user (missing-email → 201!)
"""

import sys
import time
from pathlib import Path

import requests

# Reuse the Step 0 client — same auth, same root .env loading.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "step0_setup"))
from ping_client import PingOneClient, _load_root_env  # noqa: E402

_load_root_env()

client = PingOneClient()

# ─────────────────────────────────────────────────────────────────────
# Tiny test framework — enough to learn the pattern
# ─────────────────────────────────────────────────────────────────────
RESULTS = []  # (name, passed, detail)


def check(name: str, condition: bool, detail: str = "") -> bool:
    """Record one assertion as a named test result."""
    RESULTS.append((name, condition, detail))
    mark = "✅ PASS" if condition else "❌ FAIL"
    print(f"  {mark}  {name}" + (f"  — {detail}" if detail else ""))
    return condition


def expect_status(name: str, response: requests.Response, expected: int) -> bool:
    """The core API-test move: assert the contract, not just a response."""
    got = response.status_code
    return check(name, got == expected, f"expected {expected}, got {got}")


# Unique-per-run username — the anti-collision trick from CONCEPTS.md.
RUN_ID = str(int(time.time()))
TEST_USERNAME = f"qe-test-{RUN_ID}"
TEST_EMAIL = f"qe-test-{RUN_ID}@example.com"


# ─────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────

def test_1_token_acquisition():
    """Happy path: client credentials grant still works."""
    print("\n🧪 1. Token acquisition (client credentials)")
    try:
        token = client.get_token()
        check("token returned", isinstance(token, str) and len(token) > 100,
              f"{len(token)} chars — JWTs are big")
        check("token looks like a JWT", token.count(".") == 2,
              "header.payload.signature")
    except Exception as e:
        check("token returned", False, str(e))


def test_2_token_claims():
    """The Step 0/1 lesson, as an assertion: this token is a MACHINE.

    PingOne note: Worker-app tokens carry the identity in `client_id`,
    not `sub` — a small deviation from vanilla OAuth you only learn by
    decoding a real token. (This test caught that!)
    """
    print("\n🧪 2. Token claims — who is the 'sub'?")
    claims = client.decode_token()
    check("token carries our Worker app's client_id",
          claims.get("client_id") == client.client_id,
          f"client_id={str(claims.get('client_id'))[:20]}... "
          f"(PingOne uses client_id, not sub, for machine tokens)")
    check("no 'sub' person claim — this is a machine token",
          "sub" not in claims or claims.get("sub") == client.client_id,
          "compare with Step 1: test.user1's id_token HAD a human sub")
    check("token has an expiry", "exp" in claims,
          f"expires {time.ctime(claims.get('exp', 0))}")


def test_3_user_crud_lifecycle():
    """
    The full circle: create → read → delete → verify gone.
    Each arrow is a failure mode single-call tests can't see.
    Teardown runs in `finally` — a failing test still cleans up.
    """
    print("\n🧪 3. User CRUD lifecycle (create → read → delete → 404)")
    populations = client.list_populations()
    if not check("a population exists to create users in", len(populations) > 0):
        return
    pop_id = populations[0]["id"]

    user_id = None
    try:
        # CREATE
        resp = requests.post(
            f"{client.api_base}/environments/{client.environment_id}/users",
            headers={"Authorization": f"Bearer {client.get_token()}"},
            json={
                "username": TEST_USERNAME,
                "email": TEST_EMAIL,
                "population": {"id": pop_id},
                "name": {"given": "QE", "family": "Test"},
            },
            timeout=30,
        )
        if not expect_status("create user → 201", resp, 201):
            print(f"     body: {resp.text[:300]}")
            return
        user_id = resp.json()["id"]
        check("response contains the new user id", bool(user_id))

        # READ — does the created data actually persist and match?
        read_resp = requests.get(
            f"{client.api_base}/environments/{client.environment_id}/users/{user_id}",
            headers={"Authorization": f"Bearer {client.get_token()}"},
            timeout=30,
        )
        expect_status("read back → 200", read_resp, 200)
        if read_resp.status_code == 200:
            check("username round-trips",
                  read_resp.json().get("username") == TEST_USERNAME,
                  "create said one thing, read must agree")
    finally:
        # DELETE — runs even if assertions above failed
        if user_id:
            del_resp = requests.delete(
                f"{client.api_base}/environments/{client.environment_id}/users/{user_id}",
                headers={"Authorization": f"Bearer {client.get_token()}"},
                timeout=30,
            )
            expect_status("delete user → 204", del_resp, 204)

            # VERIFY GONE — the assertion that catches soft-delete leaks
            gone_resp = requests.get(
                f"{client.api_base}/environments/{client.environment_id}/users/{user_id}",
                headers={"Authorization": f"Bearer {client.get_token()}"},
                timeout=30,
            )
            expect_status("deleted user → 404", gone_resp, 404)


def test_4_duplicate_username_rejected():
    """Negative: same username twice → 400 + UNIQUENESS_VIOLATION (PingOne's
    actual contract — discovered when this test failed expecting 409!)."""
    print("\n🧪 4. Negative: duplicate username → 400 + uniqueness detail")
    populations = client.list_populations()
    if not populations:
        check("population exists", False)
        return
    pop_id = populations[0]["id"]
    body = {
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "population": {"id": pop_id},
    }
    headers = {"Authorization": f"Bearer {client.get_token()}"}
    base = f"{client.api_base}/environments/{client.environment_id}/users"

    user_id = None
    try:
        first = requests.post(base, headers=headers, json=body, timeout=30)
        if first.status_code == 201:
            user_id = first.json()["id"]
        if not expect_status("first create → 201 (setup for the real test)",
                             first, 201):
            print(f"     body: {first.text[:300]}")
            return
        # THE ACTUAL TEST: same username, different email
        second = requests.post(base, headers=headers, timeout=30, json={
            **body, "email": f"different-{RUN_ID}@example.com",
        })
        # PingOne note: duplicates come back as 400 (not 409) with a
        # UNIQUENESS_VIOLATION code in the body — this test taught us that.
        expect_status("duplicate username → 400", second, 400)
        if second.status_code == 400:
            check("error body says WHY (uniqueness)",
                  "UNIQUENESS" in second.text.upper(),
                  "contract detail: the code must name the violation")
    finally:
        if user_id:
            requests.delete(f"{base}/{user_id}", headers=headers, timeout=30)


def test_5_unknown_population_rejected():
    """Negative: a population id that doesn't exist → 4xx with detail.

    PingOne note: an earlier version of this test asserted 'missing email
    → 400' — and the tenant returned 201! Email is OPTIONAL in PingOne's
    schema. That failure was the suite doing its job: documenting real
    behavior instead of assumed behavior. This version tests a reference
    to a nonexistent population — a genuine referential-integrity case.
    """
    print("\n🧪 5. Negative: unknown population reference → 4xx")
    resp = requests.post(
        f"{client.api_base}/environments/{client.environment_id}/users",
        headers={"Authorization": f"Bearer {client.get_token()}"},
        json={
            "username": f"bad-pop-{RUN_ID}",
            "email": f"bad-pop-{RUN_ID}@example.com",
            "population": {"id": "00000000-0000-0000-0000-000000000000"},
        },
        timeout=30,
    )
    check("unknown population → 400 or 404",
          resp.status_code in (400, 404),
          f"got {resp.status_code}")
    if resp.status_code in (400, 404):
        check("error body explains the problem",
              len(resp.text) > 20,
              "a bare 4xx with no detail is a DX bug in itself")
    # Safety net: if the tenant somehow accepted it, don't leave debris
    if resp.status_code == 201:
        uid = resp.json().get("id")
        if uid:
            requests.delete(
                f"{client.api_base}/environments/{client.environment_id}/users/{uid}",
                headers={"Authorization": f"Bearer {client.get_token()}"},
                timeout=30,
            )


def test_6_garbage_token_rejected():
    """Security: a nonsense Bearer token must be 401 — never 200, never 500."""
    print("\n🧪 6. Security: garbage token → 401")
    resp = requests.get(
        f"{client.api_base}/environments/{client.environment_id}/users",
        headers={"Authorization": "Bearer total.garbage.token"},
        params={"limit": 1},
        timeout=30,
    )
    expect_status("garbage token → 401", resp, 401)


def test_7_populations_readable():
    """Happy path list call — and a peek at response envelope shape."""
    print("\n🧪 7. Populations list")
    resp = requests.get(
        f"{client.api_base}/environments/{client.environment_id}/populations",
        headers={"Authorization": f"Bearer {client.get_token()}"},
        timeout=30,
    )
    expect_status("list populations → 200", resp, 200)
    if resp.status_code == 200:
        pops = resp.json().get("_embedded", {}).get("populations", [])
        check("HAL envelope parsed (_embedded.populations)", len(pops) > 0,
              f"{len(pops)} population(s): " +
              ", ".join(p["name"] for p in pops[:5]))


def test_8_no_debris_left_behind():
    """The suite's promise to itself: zero test users remain."""
    print("\n🧪 8. Cleanup verification — no debris")
    users = client.list_users(limit=100)
    debris = [
        u for u in users
        if any(str(u.get("username", "")).startswith(p)
               for p in ("qe-test-", "bad-pop-"))
    ]
    check("no test users left in tenant", len(debris) == 0,
          f"found {len(debris)} leftover(s): "
          + ", ".join(u['username'] for u in debris) if debris
          else "tenant is clean")


# ─────────────────────────────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 64)
    print("STEP 2: API TEST SUITE — live against your PingOne tenant")
    print("=" * 64)
    print(f"Run id: {RUN_ID}  (usernames get this suffix → no collisions)")

    for test in (
        test_1_token_acquisition,
        test_2_token_claims,
        test_3_user_crud_lifecycle,
        test_4_duplicate_username_rejected,
        test_5_unknown_population_rejected,
        test_6_garbage_token_rejected,
        test_7_populations_readable,
        test_8_no_debris_left_behind,
    ):
        try:
            test()
        except Exception as e:
            check(f"{test.__name__} raised unexpectedly", False, repr(e))

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print("\n" + "=" * 64)
    print(f"RESULT: {passed}/{total} assertions passed")
    print("=" * 64)

    if passed == total:
        print("\n🎉 Step 2 complete. You now have:")
        print("   • happy-path tests (token, CRUD, lists)")
        print("   • negative tests (duplicate username, unknown population)")
        print("   • security test (401 garbage token)")
        print("   • self-cleaning discipline (unique names + finally teardown)")
        print("\n   Bonus: your first run found 3 REAL contract quirks —")
        print("   PingOne uses client_id (not sub), 400 (not 409) for dupes,")
        print("   and email is optional. That's what tests are FOR.")
        print("\n   Next: Step 3 — let an AI GENERATE these, and build the")
        print("   evaluator that decides which generated tests deserve to run.")
        return 0
    print("\n❌ Some assertions failed — read the details above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

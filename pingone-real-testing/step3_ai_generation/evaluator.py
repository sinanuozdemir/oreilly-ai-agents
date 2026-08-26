"""
Test Spec Evaluator - the 3-stage gauntlet from CONCEPTS.md §3.

  Stage 1  SCHEMA     — is it a well-formed spec? (free, microseconds)
  Stage 2  SEMANTIC   — does it make sense for THIS API? (grounded rules)
  Stage 3  EXECUTION  — does reality agree? (live tenant, self-cleaning)

Each stage catches a different failure mode. Cheapest first — you never
execute a hallucination against prod.

This is the "40% reduction" architecture, pointed at a real tenant.
"""

import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "step0_setup"))
from ping_client import PingOneClient  # noqa: E402

from test_generator import ALLOWED_ENDPOINTS, GROUNDING_FACTS  # noqa: E402

VALID_TYPES = {"happy", "negative"}
VALID_CLEANUP = {"delete_if_created", "none"}
REQUIRED_FIELDS = {
    "name", "type", "endpoint", "expected_status", "rationale", "cleanup",
}


@dataclass
class Verdict:
    """One spec's journey through the gauntlet."""
    spec: Dict[str, Any]
    accepted: bool = False
    rejected_at: Optional[str] = None      # "schema" | "semantic" | "execution"
    reason: str = ""
    actual_status: Optional[int] = None    # filled by stage 3
    elapsed_ms: int = 0


# ─────────────────────────────────────────────────────────────────────
# STAGE 1: SCHEMA — free, instant, merciless
# ─────────────────────────────────────────────────────────────────────

def stage1_schema(spec: Dict[str, Any]) -> Optional[str]:
    """Return a rejection reason, or None if the spec is well-formed."""
    missing = REQUIRED_FIELDS - spec.keys()
    if missing:
        return f"missing fields: {sorted(missing)}"

    if not isinstance(spec["name"], str) or not re.fullmatch(
        r"[a-z][a-z0-9_]*", spec["name"]
    ):
        return "name must be snake_case"

    if spec["endpoint"] not in ALLOWED_ENDPOINTS:
        return f"hallucinated endpoint: {spec['endpoint']!r} not in ALLOWED list"

    if spec["type"] not in VALID_TYPES:
        return f"type must be one of {VALID_TYPES}"

    status = spec["expected_status"]
    if not isinstance(status, int) or not (100 <= status <= 599):
        return f"expected_status {status!r} is not a real HTTP code"

    if spec["cleanup"] not in VALID_CLEANUP:
        return f"cleanup must be one of {VALID_CLEANUP}"

    return None


# ─────────────────────────────────────────────────────────────────────
# STAGE 2: SEMANTIC — grounded rules encode VERIFIED FACTS
# ─────────────────────────────────────────────────────────────────────

def stage2_semantic(spec: Dict[str, Any]) -> Optional[str]:
    """
    Rule-based semantic check, grounded in facts Step 2 verified.
    (An LLM judge can augment this for fuzzy cases — but rules are
    free, instant, and deterministic, so they run first.)
    """
    status = spec["expected_status"]
    ttype = spec["type"]
    payload = spec.get("payload") or {}

    # Rule: type must agree with the expected status class
    if ttype == "negative" and status < 400:
        return f"negative test expecting {status} — nonsense (must be 4xx)"
    if ttype == "happy" and status >= 400:
        return f"happy test expecting {status} — nonsense (must be 2xx)"

    # Grounded rule: email is OPTIONAL in PingOne (Step 2 discovery!)
    # Only fires when missing-email is the SOLE defect being tested —
    # i.e. the population reference is a valid one (<POPULATION_ID>
    # placeholder or a real id). If the population is bogus (zero UUID),
    # the 4xx is justified by THAT, and the spec is legitimately negative.
    if spec["endpoint"] == "POST /users" and "email" not in payload:
        pop_id = str((payload.get("population") or {}).get("id", ""))
        population_is_valid = pop_id == "<POPULATION_ID>" or (
            pop_id and pop_id != "00000000-0000-0000-0000-000000000000"
        )
        if population_is_valid and status >= 400:
            return ("contradicts verified fact: email is OPTIONAL in "
                    "PingOne — missing email alone returns 201, not 4xx")

    # Grounded rule: deleting a nonexistent user → 404
    if spec["endpoint"] == "DELETE /users/{id}" and status != 404:
        if payload.get("id") == "00000000-0000-0000-0000-000000000000":
            return ("contradicts verified fact: deleting a nonexistent "
                    "user returns 404")

    # Grounded rule: duplicates → 400, never 409 (generic REST trap)
    if "duplicat" in spec["name"].lower() and status == 409:
        return ("contradicts verified fact: PingOne returns 400 + "
                "UNIQUENESS_VIOLATION for duplicates, not 409")

    # Rule: rationale must exist and be non-trivial
    if len(str(spec.get("rationale", ""))) < 15:
        return "rationale too thin — a test without a 'why' rots"

    return None


# ─────────────────────────────────────────────────────────────────────
# STAGE 3: EXECUTION — reality is the final judge
# ─────────────────────────────────────────────────────────────────────

class Executor:
    """
    Runs accepted-looking specs against the live tenant.
    Self-cleaning per Step 2 discipline: delete_if_created runs in
    `finally`, so a failed spec still leaves no debris.
    """

    def __init__(self, client: PingOneClient, run_id: str):
        self.client = client
        self.run_id = run_id
        self._population_id: Optional[str] = None

    def _resolve(self, value: Any) -> Any:
        """Replace <RUN_ID> and <POPULATION_ID> placeholders."""
        if isinstance(value, str):
            value = value.replace("<RUN_ID>", self.run_id)
            if "<POPULATION_ID>" in value:
                value = value.replace("<POPULATION_ID>", self._pop_id())
            return value
        if isinstance(value, dict):
            return {k: self._resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve(v) for v in value]
        return value

    def _pop_id(self) -> str:
        if not self._population_id:
            pops = self.client.list_populations()
            self._population_id = pops[0]["id"] if pops else ""
        return self._population_id

    def execute(self, spec: Dict[str, Any]) -> Verdict:
        verdict = Verdict(spec=spec)
        headers = {"Authorization": f"Bearer {self.client.get_token()}"}
        base = f"{self.client.api_base}/environments/{self.client.environment_id}"
        method, path = spec["endpoint"].split(" ", 1)
        payload = self._resolve(spec.get("payload"))

        if "{id}" in path:  # /users/{id} → use payload-provided id
            path = path.replace("{id}", (payload or {}).get("id", "0" * 32))

        created_id: Optional[str] = None
        try:
            resp = requests.request(
                method, f"{base}{path}", headers=headers,
                json=payload if method in ("POST",) else None,
                timeout=30,
            )
            verdict.actual_status = resp.status_code
            if resp.status_code == 201:
                created_id = resp.json().get("id")

            expected = spec["expected_status"]
            if resp.status_code == expected:
                verdict.accepted = True
                verdict.reason = f"reality agrees: {expected}"
            else:
                verdict.rejected_at = "execution"
                verdict.reason = (f"expected {expected}, tenant said "
                                  f"{resp.status_code}")
        except Exception as e:
            verdict.rejected_at = "execution"
            verdict.reason = f"raised: {e!r}"
        finally:
            # Cleanup if ANYTHING was created — even when the spec said
            # cleanup: "none". A negative spec that unexpectedly succeeds
            # (like a "duplicate" that wasn't) still creates a real user.
            # The runner's contract: NOTHING generated leaks into the tenant.
            if created_id:
                requests.delete(f"{base}/users/{created_id}",
                                headers=headers, timeout=30)
        return verdict


# ─────────────────────────────────────────────────────────────────────
# THE GAUNTLET
# ─────────────────────────────────────────────────────────────────────

def evaluate(specs: List[Dict[str, Any]], client: Optional[PingOneClient],
             run_id: str, verbose: bool = True) -> List[Verdict]:
    """
    Run every spec through the 3 stages. Pass `client=None` to skip
    stage 3 (offline dry-run of stages 1+2 only).
    """
    executor = Executor(client, run_id) if client else None
    verdicts: List[Verdict] = []

    for spec in specs:
        started = time.time()
        v = Verdict(spec=spec)

        reason = stage1_schema(spec)
        if reason:
            v.rejected_at, v.reason = "schema", reason
        else:
            reason = stage2_semantic(spec)
            if reason:
                v.rejected_at, v.reason = "semantic", reason
            elif executor:
                v = executor.execute(spec)
                v.spec = spec
            else:
                v.accepted, v.reason = True, "stages 1+2 passed (offline mode)"

        v.elapsed_ms = int((time.time() - started) * 1000)
        verdicts.append(v)

        if verbose:
            name = spec.get("name", "?")
            if v.accepted:
                print(f"  ✅ ACCEPT  {name:<38} {v.reason} ({v.elapsed_ms}ms)")
            else:
                print(f"  ❌ REJECT {name:<39} [{v.rejected_at}] {v.reason}")

    return verdicts


def report(verdicts: List[Verdict]) -> Dict[str, int]:
    """The metrics block — your before/after story in one print."""
    total = len(verdicts)
    rejected = [v for v in verdicts if not v.accepted]
    by_stage = {}
    for v in rejected:
        by_stage[v.rejected_at] = by_stage.get(v.rejected_at, 0) + 1

    accepted = total - len(rejected)
    rate = (len(rejected) / total * 100) if total else 0

    print("\n" + "=" * 64)
    print("📊 PIPELINE REPORT")
    print("=" * 64)
    print(f"  Generated:            {total}")
    for stage in ("schema", "semantic", "execution"):
        if stage in by_stage:
            print(f"  Stage rejected ({stage:<8}): {by_stage[stage]}")
    print(f"  Accepted:             {accepted}")
    print(f"  Rejection rate:       {rate:.0f}%")
    print()
    if rate >= 50:
        print("  High rejection = the system WORKING on raw generation.")
        print("  Feed failures back as grounding facts → watch the rate drop.")
    return {"total": total, "accepted": accepted, "by_stage": by_stage,
            "rejection_rate": rate}

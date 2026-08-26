"""
AI Test Generator - LLM writes test SPECS, not test code.

Design decision (see CONCEPTS.md §2): the LLM outputs structured JSON
specs. Your runner controls execution — the LLM only decides WHAT to
test. Same reason you don't let agents run arbitrary SQL.

LLM: Kimi (Moonshot AI) via the OpenAI-compatible API — this repo's
standard fallback strategy. No MOONSHOT_API_KEY? Deterministic
template fallback kicks in so the pipeline always runs for learning.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "step0_setup"))
from ping_client import _load_root_env  # noqa: E402

_load_root_env()

# ─────────────────────────────────────────────────────────────────────
# GROUNDING — verified facts about OUR tenant's real contract.
# Every one of these was discovered by a FAILING test in Step 2.
# This is the flywheel: tests teach tests.
# ─────────────────────────────────────────────────────────────────────
GROUNDING_FACTS = [
    "Duplicate username returns 400 with UNIQUENESS_VIOLATION in the error body (NOT 409).",
    "Email is OPTIONAL when creating a user — missing email returns 201.",
    "Worker app tokens carry the identity in client_id, NOT sub.",
    "Valid endpoints: GET/POST /users, GET/DELETE /users/{id}, GET /populations, GET/POST /groups.",
    "Creating a user REQUIRES a valid population id; an unknown population id returns 400.",
    "A garbage Bearer token returns 401.",
    "Successful user creation returns 201 with an 'id' field.",
    "Deleting a user returns 204; reading a deleted user returns 404.",
]

ALLOWED_ENDPOINTS = [
    "POST /users",
    "GET /users",
    "GET /users/{id}",
    "DELETE /users/{id}",
    "GET /populations",
    "GET /groups",
    "POST /groups",
]

GENERATION_PROMPT = """You are a senior QE engineer designing API test cases for the PingOne
Management API (identity platform: users, populations, groups).

VERIFIED FACTS about this API's real behavior (do not contradict these):
{facts}

ALLOWED endpoints (use ONLY these):
{endpoints}

Generate {n} test specifications as a JSON array. Mix happy-path and
negative tests. Each spec MUST follow this exact schema:

{{
  "name": "snake_case_name",
  "type": "happy" | "negative",
  "endpoint": "METHOD /path" (from the ALLOWED list),
  "payload": {{ ... }} or null,
  "expected_status": <integer HTTP code>,
  "rationale": "one sentence: what bug would this catch?",
  "cleanup": "delete_if_created" | "none"
}}

Rules:
- Negative tests must expect 4xx; happy tests must expect 2xx.
- Use the placeholder "<POPULATION_ID>" for population ids in payloads.
- Use the placeholder "<RUN_ID>" inside any username/email so runs
  never collide (e.g. "ai-gen-<RUN_ID>@example.com").
- Do NOT invent endpoints or fields beyond what the facts describe.
- Return ONLY the JSON array. No markdown fences, no commentary.
"""


def _call_kimi(prompt: str) -> str:
    """Call Kimi via the OpenAI-compatible API (repo fallback standard)."""
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["MOONSHOT_API_KEY"],
        base_url="https://api.moonshot.ai/v1",
    )
    completion = client.chat.completions.create(
        model="kimi-k2.6",
        messages=[
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        # Note: kimi-k2.6 rejects any temperature other than the default
        # (400: "only 1 is allowed") — omit the parameter entirely.
    )
    return completion.choices[0].message.content or ""


def _parse_specs(raw: str) -> List[Dict[str, Any]]:
    """Extract the JSON array from the LLM's reply, tolerant of fences."""
    text = raw.strip()
    if text.startswith("```"):
        # strip ```json ... ``` wrappers if the model added them anyway
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        specs = json.loads(text[start : end + 1])
        return [s for s in specs if isinstance(s, dict)]
    except json.JSONDecodeError:
        return []


def _fallback_specs(n: int) -> List[Dict[str, Any]]:
    """
    Deterministic generator when no API key is set — proves the
    pipeline works without an LLM, and gives the evaluator a mix of
    good and DELIBERATELY BAD specs to reject (that's the demo!).
    """
    good = [
        {
            "name": "create_user_happy",
            "type": "happy",
            "endpoint": "POST /users",
            "payload": {
                "username": "ai-gen-<RUN_ID>",
                "email": "ai-gen-<RUN_ID>@example.com",
                "population": {"id": "<POPULATION_ID>"},
            },
            "expected_status": 201,
            "rationale": "Baseline: valid user creation must succeed.",
            "cleanup": "delete_if_created",
        },
        {
            "name": "create_user_unknown_population",
            "type": "negative",
            "endpoint": "POST /users",
            "payload": {
                "username": "ai-gen-badpop-<RUN_ID>",
                "population": {"id": "00000000-0000-0000-0000-000000000000"},
            },
            "expected_status": 400,
            "rationale": "Referential integrity: unknown population rejected.",
            "cleanup": "delete_if_created",
        },
        {
            "name": "list_users_happy",
            "type": "happy",
            "endpoint": "GET /users",
            "payload": None,
            "expected_status": 200,
            "rationale": "Baseline read path stays healthy.",
            "cleanup": "none",
        },
        # ── deliberately bad specs, to exercise the evaluator ──
        {
            "name": "delete_nonexistent_expect_200",
            "type": "negative",
            "endpoint": "DELETE /users/{id}",
            "payload": {"id": "00000000-0000-0000-0000-000000000000"},
            "expected_status": 200,  # WRONG on purpose (should be 404)
            "rationale": "Plausible-sounding but wrong expectation.",
            "cleanup": "none",
        },
        {
            "name": "missing_email_rejected",
            "type": "negative",
            "endpoint": "POST /users",
            "payload": {
                "username": "ai-gen-noemail-<RUN_ID>",
                "population": {"id": "<POPULATION_ID>"},
            },
            "expected_status": 400,  # contradicts GROUNDING (email optional!)
            "rationale": "Generic REST assumption — wrong for PingOne.",
            "cleanup": "delete_if_created",
        },
        {
            "name": "hallucinated_endpoint",
            "type": "negative",
            "endpoint": "POST /users/bulk-import",  # not in ALLOWED list
            "payload": {"users": []},
            "expected_status": 400,
            "rationale": "Classic hallucination: plausible fake endpoint.",
            "cleanup": "none",
        },
    ]
    return good[:n] if n <= len(good) else good


def generate_specs(n: int = 8, verbose: bool = True) -> List[Dict[str, Any]]:
    """
    Generate n test specs. Uses Kimi if MOONSHOT_API_KEY is set,
    otherwise the deterministic fallback (which includes deliberately
    bad specs so the evaluator always has something to catch).
    """
    if os.environ.get("MOONSHOT_API_KEY"):
        if verbose:
            print(f"🤖 Generating {n} specs with Kimi (grounded prompt)...")
        prompt = GENERATION_PROMPT.format(
            facts="\n".join(f"  - {f}" for f in GROUNDING_FACTS),
            endpoints="\n".join(f"  - {e}" for e in ALLOWED_ENDPOINTS),
            n=n,
        )
        try:
            specs = _parse_specs(_call_kimi(prompt))
            if specs:
                if verbose:
                    print(f"   → Kimi returned {len(specs)} specs")
                return specs
            if verbose:
                print("   ⚠️  Kimi output unparseable — falling back to templates")
        except Exception as e:
            if verbose:
                print(f"   ⚠️  LLM call failed ({e}) — falling back to templates")
    elif verbose:
        print("🤖 No MOONSHOT_API_KEY — using deterministic template specs")
        print("   (includes deliberately bad specs so the evaluator has prey)")

    return _fallback_specs(n)


if __name__ == "__main__":
    for spec in generate_specs():
        print(json.dumps(spec, indent=2))
        print()

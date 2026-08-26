"""
Step 3 Pipeline - generate → evaluate → execute → measure.

    python run_pipeline.py            # full run against live tenant
    python run_pipeline.py --offline  # stages 1+2 only (no API calls)

The exit code is CI-ready: 0 if at least one spec was accepted AND
nothing crashed, 1 otherwise. Step 4 wires this into a quality gate.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "step0_setup"))
from ping_client import PingOneClient, _load_root_env  # noqa: E402

from test_generator import GROUNDING_FACTS, generate_specs  # noqa: E402
from evaluator import evaluate, report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true",
                        help="stages 1+2 only, no live tenant calls")
    parser.add_argument("-n", type=int, default=8, help="specs to generate")
    args = parser.parse_args()

    run_id = str(int(time.time()))

    print("=" * 64)
    print("STEP 3: AI-GENERATED TESTS → EVALUATOR GAUNTLET → LIVE TENANT")
    print("=" * 64)

    print("\n📌 GROUNDING FACTS (learned by Step 2's failures):")
    for fact in GROUNDING_FACTS:
        print(f"   • {fact}")

    print("\n── Phase 1: GENERATE ──────────────────────────────────────")
    specs = generate_specs(n=args.n)
    print(f"   {len(specs)} candidate specs entering the gauntlet\n")

    print("── Phase 2+3: EVALUATE (schema → semantic → execution) ────")
    _load_root_env()
    client = None if args.offline else PingOneClient()
    verdicts = evaluate(specs, client, run_id)

    metrics = report(verdicts)

    accepted_names = [v.spec["name"] for v in verdicts if v.accepted]
    if accepted_names:
        print("  🏆 Survivors (these EARNED a place in the regression suite):")
        for name in accepted_names:
            print(f"     • {name}")

    print("\n🎤 The story: generation is cheap — the evaluator is the")
    print("   product. Rejection reasons above ARE the audit trail.")
    return 0 if metrics["accepted"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

"""Measure how well the LLM turns spoken instructions into {tool, action, handedness}.

    cd application && LLM_PROVIDER=ollama LLM_MODEL=llama3.1 python eval/eval_parser.py

Reads ``eval/instructions.jsonl`` (includes speech-to-text style corruptions such
as "in session" for "incision" and "switching" for "stitching"), runs the real
``LLMService`` once per instruction, and reports per-field accuracy, exact-match
rate, JSON-validity rate and latency. Writes ``eval/results.md``.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from backend.config import Config  # noqa: E402
from backend.services.command_service import CommandService  # noqa: E402
from backend.services.llm_service import LLMService  # noqa: E402

SYNONYMS = {"stitch": {"stitch", "suture", "stitching"}, "grasp": {"grasp", "hold", "grab"}}


def action_matches(expected: str, got: str | None) -> bool:
    if got is None:
        return False
    got = got.lower().strip()
    return got == expected or got in SYNONYMS.get(expected, set())


def main() -> None:
    cases = [json.loads(l) for l in (HERE / "instructions.jsonl").read_text().splitlines() if l.strip()]
    llm = LLMService()
    mapper = CommandService()
    no_object = {"object_detected": False, "height_match": False, "distance_match": False}

    rows, latencies = [], []
    for c in cases:
        t0 = time.perf_counter()
        r = llm.process_instruction(c["instruction"])
        latencies.append(time.perf_counter() - t0)
        ok_json = "error" not in r
        tool_ok = ok_json and (r.get("tool") or "").lower() == c["tool"]
        action_ok = ok_json and action_matches(c["action"], r.get("action"))
        hand_ok = ok_json and (r.get("handedness") or "").lower() == c["handedness"]
        expected_cmd = mapper.map_to_command({"action": c["action"], "handedness": c["handedness"]}, no_object)
        got_cmd = mapper.map_to_command(r if ok_json else {}, no_object)
        rows.append({"instruction": c["instruction"], "json": ok_json, "tool": tool_ok, "action": action_ok,
                     "handedness": hand_ok, "command_ok": got_cmd == expected_cmd,
                     "got": {k: r.get(k) for k in ("tool", "action", "handedness")} if ok_json else r.get("error")})

    n = len(rows)
    rate = lambda k: sum(bool(r[k]) for r in rows) / n  # noqa: E731
    summary = {
        "model": f"{Config.LLM_PROVIDER}:{Config.LLM_MODEL}", "n": n,
        "valid_json": rate("json"), "tool_acc": rate("tool"), "action_acc": rate("action"),
        "handedness_acc": rate("handedness"), "command_acc": rate("command_ok"),
        "exact_match": sum(r["tool"] and r["action"] and r["handedness"] for r in rows) / n,
        "p50_latency_s": statistics.median(latencies), "p95_latency_s": sorted(latencies)[int(0.95 * (n - 1))],
    }
    lines = [f"# Command-parser evaluation — `{summary['model']}`", "",
             f"{n} spoken instructions, run {time.strftime('%Y-%m-%d')}. Six of them contain speech-to-text "
             "corruptions the prompt is meant to tolerate.", "",
             "| metric | value |", "|---|---|"]
    for k in ("valid_json", "tool_acc", "action_acc", "handedness_acc", "exact_match", "command_acc"):
        lines.append(f"| {k} | {summary[k]:.2f} |")
    lines.append(f"| p50 latency | {summary['p50_latency_s']:.2f} s |")
    lines.append(f"| p95 latency | {summary['p95_latency_s']:.2f} s |")
    lines += ["", "## Failures", "", "| instruction | expected | got |", "|---|---|---|"]
    for r, c in zip(rows, cases):
        if not (r["tool"] and r["action"] and r["handedness"]):
            lines.append(f"| {c['instruction']} | {c['tool']}/{c['action']}/{c['handedness']} | {json.dumps(r['got'])} |")
    (HERE / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run the full Lost & Underfound quality firewall and write review artifacts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_OUT_DIR = ROOT / "art" / "act01-production" / "qa" / "night-audit"
TRANSIENT_OUT_DIR = ROOT / "out" / "night-audit"
OUT_DIR = CANONICAL_OUT_DIR
LOG_DIR = OUT_DIR / "logs"
REPORT_JSON = OUT_DIR / "qa-report.json"
REPORT_MD = OUT_DIR / "qa-report.md"


@dataclass(frozen=True)
class AuditStep:
    name: str
    command: list[str]
    expected: str = "pass"


def npm_command() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def npx_command() -> str:
    return "npx.cmd" if os.name == "nt" else "npx"


NPM = npm_command()
NPX = npx_command()

STEPS = [
    AuditStep("negative-control-broken-sheet", [NPM, "run", "qa:broken"], expected="fail"),
    AuditStep("registration-placeholders", [NPM, "run", "qa:placeholder"]),
    AuditStep("registration-pip", [NPM, "run", "qa:pip"]),
    AuditStep("registration-bottlecap", [NPM, "run", "qa:bottlecap"]),
    AuditStep("registration-bramble", [NPM, "run", "qa:bramble"]),
    AuditStep("registration-bramble-talking-head", [NPM, "run", "qa:bramble-talking-head"]),
    AuditStep("registration-scuttle", [NPM, "run", "qa:scuttle"]),
    AuditStep("registration-grommet-placeholder", [NPM, "run", "qa:grommet-placeholder"]),
    AuditStep("production-animation", [NPM, "run", "qa:production"]),
    AuditStep("cast-scale", [NPM, "run", "qa:cast"]),
    AuditStep("lora-manifest", [NPM, "run", "qa:lora"]),
    AuditStep("bramble-rig", [NPM, "run", "qa:rig:bramble"]),
    AuditStep("engine-character-exports", [NPM, "run", "qa:engine:characters"]),
    AuditStep("animation-admission", [NPM, "run", "qa:animation-admission"]),
    AuditStep("runtime-scene-contract", [NPM, "run", "qa:runtime-scene"]),
    AuditStep("pip-movement", [NPM, "run", "qa:pip-movement"]),
    AuditStep("runtime-sprite-flow", [NPM, "run", "qa:sprite-flow"]),
    AuditStep("act1-playthrough-contract", [NPM, "run", "qa:act1-playthrough"]),
    AuditStep("scene-layers", [NPM, "run", "qa:layers"]),
    AuditStep("ambient-motion-layers", [NPM, "run", "qa:ambient-layers"]),
    AuditStep("interactable-change-layers", [NPM, "run", "qa:change-layers"]),
    AuditStep("ags-room1-geometry", [NPM, "run", "qa:ags:room1"]),
    AuditStep("ags-multiroom-geometry", [NPM, "run", "qa:ags:geometry"]),
    AuditStep("ags-backgrounds", [NPM, "run", "qa:ags:background"]),
    AuditStep("ags-actor-scale-proofs", [NPM, "run", "qa:ags:actor-scale-proofs"]),
    AuditStep("godot-content-manifest", [NPM, "run", "qa:godot-content"]),
    AuditStep("runtime-visual-playthrough", [NPM, "run", "qa:runtime-visual"]),
    AuditStep("typescript", [NPX, "tsc", "--noEmit"]),
]


PROOF_PATHS = [
    "art/qa-placeholder/onion.png",
    "art/pip-walk/onion.png",
    "art/old-bottlecap-idle/onion.png",
    "art/bramble-idle/onion.png",
    "art/scuttle-walk/onion.png",
    "art/grommet-idle/onion.png",
    "art/act01-production/qa/runtime-sprite-flow/sprite-flow-report.json",
    "art/act01-production/qa/runtime-sprite-flow/sprite-flow-final.png",
    "art/act01-production/qa/runtime-sprite-flow/sprite-flow-mobile.png",
    "art/act01-production/qa/runtime-playthrough/desktop-01-discovery-cold-open.png",
    "art/act01-production/qa/runtime-playthrough/desktop-02-discovery-dust-reveal.png",
    "art/act01-production/qa/runtime-playthrough/desktop-03-clerk-bramble-greeting.png",
    "art/act01-production/qa/runtime-playthrough/desktop-04-gate-before-toll.png",
    "art/act01-production/qa/runtime-playthrough/desktop-05-gate-toll-paid.png",
    "art/act01-production/qa/runtime-playthrough/desktop-06-act1-complete.png",
    "art/act01-production/qa/runtime-playthrough/mobile-portrait-01-discovery-cold-open.png",
    "art/act01-production/qa/runtime-playthrough/mobile-portrait-02-discovery-dust-reveal.png",
    "art/act01-production/qa/runtime-playthrough/mobile-portrait-03-clerk-bramble-greeting.png",
    "art/act01-production/qa/runtime-playthrough/mobile-portrait-04-gate-before-toll.png",
    "art/act01-production/qa/runtime-playthrough/mobile-portrait-05-gate-toll-paid.png",
    "art/act01-production/qa/runtime-playthrough/mobile-portrait-06-act1-complete.png",
]


def configure_output_dir(update_proofs: bool) -> None:
    global OUT_DIR, LOG_DIR, REPORT_JSON, REPORT_MD

    OUT_DIR = CANONICAL_OUT_DIR if update_proofs else TRANSIENT_OUT_DIR
    LOG_DIR = OUT_DIR / "logs"
    REPORT_JSON = OUT_DIR / "qa-report.json"
    REPORT_MD = OUT_DIR / "qa-report.md"


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def snapshot_files(paths: list[Path]) -> dict[Path, bytes | None]:
    snapshot: dict[Path, bytes | None] = {}
    for path in paths:
        snapshot[path] = path.read_bytes() if path.exists() else None
    return snapshot


def restore_files(snapshot: dict[Path, bytes | None]) -> None:
    for path, content in snapshot.items():
        if content is None:
            if path.exists():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def run_step(step: AuditStep) -> dict:
    started = time.monotonic()
    process = subprocess.run(
        step.command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
    )
    elapsed = round(time.monotonic() - started, 3)
    passed = process.returncode == 0
    ok = passed if step.expected == "pass" else not passed
    log_path = LOG_DIR / f"{step.name}.log"
    write_text(log_path, process.stdout)
    return {
        "name": step.name,
        "command": " ".join(step.command),
        "expected": step.expected,
        "exit_code": process.returncode,
        "ok": ok,
        "duration_seconds": elapsed,
        "log": relative(log_path),
    }


def collect_proofs() -> list[dict]:
    proofs = []
    for proof in PROOF_PATHS:
        path = ROOT / proof
        proofs.append(
            {
                "path": proof,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    return proofs


def write_reports(results: list[dict], proofs: list[dict], started_at: str) -> dict:
    failed = [result for result in results if not result["ok"]]
    missing_proofs = [proof for proof in proofs if not proof["exists"]]
    status = "pass" if not failed and not missing_proofs else "fail"
    report = {
        "status": status,
        "started_at": started_at,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "steps": results,
        "proofs": proofs,
        "missing_proofs": missing_proofs,
    }
    write_text(REPORT_JSON, f"{json.dumps(report, indent=2)}\n")

    lines = [
        "# Lost & Underfound Night Audit",
        "",
        f"Status: **{status.upper()}**",
        f"Started: `{report['started_at']}`",
        f"Completed: `{report['completed_at']}`",
        "",
        "## Gates",
        "",
        "| Gate | Result | Expected | Seconds | Log |",
        "|---|---:|---:|---:|---|",
    ]
    for result in results:
        label = "PASS" if result["ok"] else "FAIL"
        lines.append(
            f"| `{result['name']}` | {label} | {result['expected']} | {result['duration_seconds']} | `{result['log']}` |"
        )

    lines.extend(["", "## Proof Artifacts", ""])
    for proof in proofs:
        marker = "OK" if proof["exists"] else "MISSING"
        lines.append(f"- {marker} `{proof['path']}`")

    if missing_proofs:
        lines.extend(["", "## Missing Proofs", ""])
        for proof in missing_proofs:
            lines.append(f"- `{proof['path']}`")

    write_text(REPORT_MD, "\n".join(lines) + "\n")
    return report


def main() -> int:
    update_proofs = "--update-proofs" in sys.argv[1:]
    configure_output_dir(update_proofs)
    started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    mutable_proof_paths = [ROOT / proof for proof in PROOF_PATHS]
    mutable_snapshot = snapshot_files(mutable_proof_paths) if not update_proofs else {}

    try:
        mode = "proof update" if update_proofs else "clean verify"
        print(f"Lost & Underfound night audit started ({mode}).")
        results: list[dict] = []
        for index, step in enumerate(STEPS, start=1):
            print(f"[{index}/{len(STEPS)}] {step.name}")
            result = run_step(step)
            results.append(result)
            if not result["ok"]:
                proofs = collect_proofs()
                write_reports(results, proofs, started_at)
                print(f"Night audit failed at {step.name}.")
                print(f"Report: {relative(REPORT_MD)}")
                return 1

        proofs = collect_proofs()
        report = write_reports(results, proofs, started_at)
        print(f"Night audit {report['status'].upper()}.")
        print(f"Report: {relative(REPORT_MD)}")
        print(f"Machine report: {relative(REPORT_JSON)}")
        if not update_proofs:
            print("Committed proof artifacts were restored after verification.")
        if report["status"] != "pass":
            return 1
        return 0
    finally:
        if not update_proofs:
            restore_files(mutable_snapshot)


if __name__ == "__main__":
    sys.exit(main())

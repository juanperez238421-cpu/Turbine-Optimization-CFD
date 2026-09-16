#!/usr/bin/env python3
from __future__ import annotations
import csv, json, re
from pathlib import Path

ROOT = Path(r"D:\Academía\Maestría\MEAS_D_25_17345_TRANSFER_REVISION")
E = ROOT / "02_EVIDENCE"

def newest(paths):
    existing = [p for p in paths if p.exists()]
    return max(existing, key=lambda p: p.stat().st_mtime) if existing else None

selected = {
    "qa": newest([E / "STAGE2C_QA_REPORT.json", E / "STAGE2_QA_REPORT.json"]),
    "freeze": newest([E / "STAGE2C_EVIDENCE_FREEZE_REPORT.md", E / "EVIDENCE_FREEZE_REPORT.md"]),
    "ledger": newest([E / "STUDY_EVIDENCE_LEDGER_FINAL.csv", E / "STUDY_EVIDENCE_LEDGER.csv"]),
    "claims": newest([E / "CLAIM_SOURCE_AUDIT.csv"]),
    "counts": newest([E / "RECOMPUTED_COUNTS.csv"]),
    "taxonomy": newest([E / "METHOD_TAXONOMY.md"]),
}

errors = []
for key, path in selected.items():
    if path is None:
        errors.append(f"missing required artifact: {key}")

if selected["qa"]:
    try:
        qa = json.loads(selected["qa"].read_text(encoding="utf-8"))
        if str(qa.get("gate", "")).upper() != "PASS":
            errors.append(f"QA gate is not PASS: {qa.get('gate')}")
        if qa.get("critical_errors"):
            errors.append(f"QA critical_errors non-empty: {len(qa['critical_errors'])}")
    except Exception as exc:
        errors.append(f"cannot parse QA JSON: {exc}")

if selected["freeze"]:
    text = selected["freeze"].read_text(encoding="utf-8", errors="replace")
    if not re.search(r"STAGE\s*2(?:C)?\s*(?:PASSED|PASS)|STAGE PASSED", text, re.I):
        errors.append("freeze report does not explicitly confirm Stage-2/2C PASS")

if selected["ledger"]:
    try:
        with selected["ledger"].open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        retained = [r for r in rows if r.get("verification_status", "").strip().upper() not in {"EXCLUDED", "EXCLUDED_PENDING_REVIEW"}]
        unresolved = [r for r in retained if r.get("verification_status", "").strip().upper() != "VERIFIED"]
        if unresolved:
            errors.append(f"retained ledger rows not VERIFIED: {len(unresolved)}/{len(retained)}")
    except Exception as exc:
        errors.append(f"cannot inspect ledger: {exc}")

print("Stage-3 prerequisite check")
for key, path in selected.items():
    print(f"{key}: {path if path else 'MISSING'}")

if errors:
    print("\nSTAGE 3 BLOCKED — RETURN TO STAGE 2")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("\nSTAGE 3 READY — ALL PREREQUISITES PASSED")
raise SystemExit(0)

#!/usr/bin/env python3
"""Deterministic senior audit for quantitative result metadata.

The engine is deliberately conservative:
- hard blockers override completeness;
- calculated values are recomputed where an expression is supplied;
- no missing scientific value is silently inferred;
- "release candidate" is a metadata/readiness state, not a claim of scientific truth.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)

SAFE_FUNCS = {
    "abs": abs,
    "sqrt": math.sqrt,
    "count_positive": lambda *xs: sum(float(x) > 0 for x in xs),
    "count_negative": lambda *xs: sum(float(x) < 0 for x in xs),
}

ALLOWED_AST = (
    ast.Expression,
    ast.Constant,
    ast.UnaryOp,
    ast.UAdd,
    ast.USub,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.Call,
    ast.Name,
    ast.Load,
)


def normalize_doi(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.I)
    value = re.sub(r"^doi:\s*", "", value, flags=re.I)
    return value.rstrip(" .;,").lower()


def parse_flags(value: str) -> List[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def parse_inputs(value: str) -> List[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def safe_eval(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST):
            raise ValueError(f"Unsupported expression node: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in SAFE_FUNCS:
            raise ValueError(f"Unsupported name: {node.id}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in SAFE_FUNCS:
                raise ValueError("Unsupported function call")
    value = eval(compile(tree, "<audit-expression>", "eval"), {"__builtins__": {}}, SAFE_FUNCS)
    return float(value)


def load_policy(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def metadata_coverage(row: Dict[str, str], fields: Iterable[str]) -> float:
    fields = list(fields)
    if not fields:
        return 100.0
    present = sum(bool((row.get(f) or "").strip()) for f in fields)
    return round(100.0 * present / len(fields), 1)


def audit_registry(rows: List[Dict[str, str]], policy: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    ids = [r.get("result_id", "").strip() for r in rows]
    duplicate_ids = {k for k, v in Counter(ids).items() if k and v > 1}
    known_ids = set(ids)

    results: List[Dict[str, Any]] = []
    structural_errors = 0

    for row in rows:
        rid = row.get("result_id", "").strip()
        issues: List[Dict[str, str]] = []
        declared = parse_flags(row.get("declared_flags", ""))

        def issue(code: str, severity: str, message: str) -> None:
            issues.append({"code": code, "severity": severity, "message": message})

        for field in policy["critical_metadata_fields"]:
            if not (row.get(field) or "").strip():
                issue("MISSING_METADATA", "ERROR", f"Required metadata field is empty: {field}")

        if rid in duplicate_ids:
            issue("DUPLICATE_RESULT_ID", "ERROR", f"Duplicate result_id: {rid}")

        evidence = (row.get("evidence_mode") or "").strip()
        if evidence not in policy["evidence_modes"]:
            issue("INVALID_EVIDENCE_MODE", "ERROR", f"Unknown evidence mode: {evidence}")

        for field, policy_key in [
            ("source_kind", "source_kinds"),
            ("result_origin", "result_origins"),
            ("comparison_class", "comparison_classes"),
            ("uncertainty_status", "uncertainty_statuses"),
            ("validation_scope", "validation_scopes"),
            ("claim_scope", "claim_scopes"),
        ]:
            value = (row.get(field) or "").strip()
            if value and value not in policy[policy_key]:
                issue("INVALID_ENUM", "ERROR", f"{field} has unsupported value: {value}")

        doi = normalize_doi(row.get("doi", ""))
        if doi and not DOI_RE.match(doi):
            issue("INVALID_DOI", "ERROR", f"DOI syntax is invalid after normalization: {doi}")

        try:
            declared_value = float(row.get("result_value", ""))
        except ValueError:
            declared_value = math.nan
            issue("INVALID_RESULT_VALUE", "ERROR", "result_value is not numeric")

        if row.get("source_kind") == "PRIMARY_PAPER":
            if not doi and not (row.get("source_file") or "").strip():
                issue("SOURCE_IDENTITY_INCOMPLETE", "ERROR", "Primary-paper result has neither DOI nor source file")

        if policy.get("require_locator_for_release") and not (row.get("source_locator") or "").strip():
            issue("SOURCE_LOCATOR_MISSING", "WARNING", "No page/table/figure/raw-data locator is recorded")

        if "SOURCE_LOCATOR_PENDING" in declared:
            issue("SOURCE_LOCATOR_PENDING", "WARNING", "Primary-source locator is explicitly pending final freeze")

        reproduced_value = None
        expression = (row.get("calculation_expression") or "").strip()
        if row.get("result_origin") == "calculated":
            if not expression:
                issue("CALCULATION_EXPRESSION_MISSING", "WARNING", "Calculated result has no executable expression")
            else:
                try:
                    reproduced_value = safe_eval(expression)
                    tol = float(policy.get("calculation_tolerance_abs", 0.0))
                    if math.isfinite(declared_value) and abs(reproduced_value - declared_value) > tol:
                        issue(
                            "CALCULATION_MISMATCH",
                            "ERROR",
                            f"Declared={declared_value:g}; reproduced={reproduced_value:g}; tolerance={tol:g}",
                        )
                except Exception as exc:
                    issue("CALCULATION_NOT_EXECUTABLE", "ERROR", str(exc))

            for dep in parse_inputs(row.get("input_result_ids", "")):
                if dep not in known_ids:
                    issue("UNKNOWN_INPUT_RESULT", "ERROR", f"Dependency does not exist: {dep}")

        hard = set(policy["hard_blocker_flags"])
        warnings = set(policy["warning_flags"])
        hard_hits = sorted(set(declared) & hard)
        warning_hits = sorted(set(declared) & warnings)

        for flag in hard_hits:
            issue(flag, "BLOCKER", "Declared scientific/provenance hard blocker")
        for flag in warning_hits:
            if flag != "SOURCE_LOCATOR_PENDING":
                issue(flag, "WARNING", "Declared scientific/provenance limitation")

        if row.get("comparison_class") == "CROSS_STUDY_NONCOMPARABLE" and row.get("claim_scope") == "CROSS_STUDY_HARMONIZED":
            issue("CROSS_STUDY_POOLING_UNJUSTIFIED", "BLOCKER", "Claim scope contradicts comparison metadata")

        if row.get("validation_scope") == "UNTESTED" and row.get("claim_scope") == "LOCAL_VALIDATION_ONLY":
            issue("UNTESTED_OPTIMUM_AS_VALIDATED", "BLOCKER", "Untested result cannot be classified as validated")

        has_error = any(x["severity"] == "ERROR" for x in issues)
        has_blocker = any(x["severity"] == "BLOCKER" for x in issues)
        has_warning = any(x["severity"] == "WARNING" for x in issues)

        if has_error or has_blocker:
            state = "BLOCKED"
        elif has_warning:
            state = "CONDITIONAL"
        elif row.get("result_origin") == "calculated" and reproduced_value is not None:
            state = "REPRODUCIBLE"
        elif (row.get("source_citation_key") or "").strip() and ((row.get("source_locator") or "").strip()):
            state = "TRACEABLE"
        else:
            state = "RELEASE_CANDIDATE"

        coverage = metadata_coverage(row, policy["critical_metadata_fields"])
        if has_error:
            structural_errors += 1

        results.append(
            {
                "result_id": rid,
                "claim_group": row.get("claim_group", ""),
                "result_label": row.get("result_label", ""),
                "declared_value": None if not math.isfinite(declared_value) else declared_value,
                "unit": row.get("unit", ""),
                "evidence_mode": evidence,
                "doi": doi,
                "audit_state": state,
                "metadata_coverage_pct": coverage,
                "reproduced_value": reproduced_value,
                "comparison_class": row.get("comparison_class", ""),
                "uncertainty_status": row.get("uncertainty_status", ""),
                "validation_scope": row.get("validation_scope", ""),
                "claim_scope": row.get("claim_scope", ""),
                "publication_role": row.get("publication_role", ""),
                "issues": issues,
            }
        )

    state_counts = Counter(x["audit_state"] for x in results)
    issue_counts = Counter(
        issue["code"] for result in results for issue in result["issues"]
    )
    summary = {
        "policy_version": policy.get("policy_version"),
        "records": len(results),
        "state_counts": dict(sorted(state_counts.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
        "structural_error_records": structural_errors,
        "hard_blocked_records": sum(x["audit_state"] == "BLOCKED" for x in results),
    }
    return results, summary


def write_outputs(results: List[Dict[str, Any]], summary: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "audit_results.json").write_text(
        json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    fields = [
        "result_id","claim_group","result_label","declared_value","unit","evidence_mode","doi",
        "audit_state","metadata_coverage_pct","reproduced_value","comparison_class",
        "uncertainty_status","validation_scope","claim_scope","publication_role","issue_codes",
    ]
    with (out_dir / "audit_results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for result in results:
            flat = {k: result.get(k, "") for k in fields}
            flat["issue_codes"] = ";".join(x["code"] for x in result["issues"])
            writer.writerow(flat)

    lines = [
        "# Santiago result metadata audit",
        "",
        f"- Policy version: **{summary['policy_version']}**",
        f"- Records: **{summary['records']}**",
        f"- Structural-error records: **{summary['structural_error_records']}**",
        f"- Blocked records: **{summary['hard_blocked_records']}**",
        "",
        "## Audit-state distribution",
        "",
    ]
    for state, n in summary["state_counts"].items():
        lines.append(f"- {state}: {n}")

    lines += ["", "## Result decisions", ""]
    for result in results:
        issues = ", ".join(x["code"] for x in result["issues"]) or "none"
        rv = result["reproduced_value"]
        repro = "" if rv is None else f"; reproduced={rv:.6g}"
        lines.append(
            f"- **{result['result_id']}** — {result['audit_state']} — "
            f"{result['declared_value']} {result['unit']}{repro}; issues: {issues}"
        )

    lines += [
        "",
        "## Interpretation rule",
        "",
        "Audit state describes metadata/provenance readiness. It does not convert a conditional result "
        "into a universal design law and does not override source-specific geometry, operating state, "
        "uncertainty, or validation boundaries.",
        "",
    ]
    (out_dir / "AUDIT_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument(
        "--fail-on-structural-errors",
        action="store_true",
        help="Return nonzero only for malformed registry/schema-level errors; scientific blockers remain reportable outputs.",
    )
    args = parser.parse_args()

    policy = load_policy(args.policy)
    rows = load_registry(args.input)
    results, summary = audit_registry(rows, policy)
    write_outputs(results, summary, args.out_dir)

    print(json.dumps(summary, indent=2))
    if args.fail_on_structural_errors and summary["structural_error_records"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

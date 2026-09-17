"""Validate the structure and internal accounting of a matching.json file.

This validator checks completeness invariants, not the truth of the quoted JD.
It deliberately contains no candidate-specific geography, names or records.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

GRADES = {"S", "A", "B", "C"}


def count_raw_catalog(path: Path) -> int | None:
    """Count common JSON catalog shapes; return None when the shape is unknown."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for keys in (
            ("data", "list"),
            ("data", "records"),
            ("data", "items"),
            ("data", "positions"),
            ("data", "data"),
            ("list",),
            ("records",),
            ("items",),
            ("positions",),
            ("rows",),
            ("jobs",),
        ):
            node: Any = data
            for key in keys:
                if not isinstance(node, dict) or key not in node:
                    break
                node = node[key]
            else:
                if isinstance(node, list):
                    return len(node)
    return None


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python verify-matching.py <matching.json>")
        return 2

    matching_path = Path(sys.argv[1]).resolve()
    try:
        matching = json.loads(matching_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"passed": False, "errors": [f"cannot read JSON: {exc}"]}))
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(matching, dict):
        print(json.dumps({"passed": False, "errors": ["root must be an object"]}))
        return 1

    for field in ("company", "date", "scope", "catalog_index", "positions", "raw_catalog"):
        if field not in matching:
            errors.append(f"missing required field: {field}")

    for field in ("company", "date", "scope"):
        if not nonempty_string(matching.get(field)):
            errors.append(f"{field} must be a non-empty string")

    catalog_index = matching.get("catalog_index")
    positions = matching.get("positions")
    raw_catalog = matching.get("raw_catalog")
    if not isinstance(catalog_index, list) or not all(isinstance(item, dict) for item in catalog_index):
        errors.append("catalog_index must be an array of objects")
        catalog_index = []
    if not isinstance(positions, list) or not all(isinstance(item, dict) for item in positions):
        errors.append("positions must be an array of objects")
        positions = []
    if not isinstance(raw_catalog, dict):
        errors.append("raw_catalog must be an object")
        raw_catalog = {}

    if errors:
        report = {"passed": False, "company": matching.get("company"), "date": matching.get("date"), "errors": errors, "warnings": warnings}
        print(json.dumps(report, ensure_ascii=False))
        return 1

    catalog_by_id: dict[str, dict[str, Any]] = {}
    for item in catalog_index:
        item_id = item.get("id")
        key = str(item_id) if item_id is not None else ""
        if not key.strip():
            errors.append("catalog_index item has an empty id")
            continue
        if key in catalog_by_id:
            errors.append(f"duplicate catalog id: {key}")
        catalog_by_id[key] = item
        if not nonempty_string(item.get("title")):
            errors.append(f"{key}: catalog item is missing title")
        if type(item.get("in_scope")) is not bool:
            errors.append(f"{key}: in_scope must be boolean")
        if item.get("in_scope") is False and not nonempty_string(item.get("exclusion")):
            errors.append(f"{key}: out-of-scope item needs an exclusion reason")

    position_ids: set[str] = set()
    for position in positions:
        raw_id = position.get("id")
        position_id = str(raw_id) if raw_id is not None else ""
        if not position_id.strip():
            errors.append("positions contains an empty id")
            continue
        if position_id in position_ids:
            errors.append(f"duplicate position id: {position_id}")
        position_ids.add(position_id)
        if position_id not in catalog_by_id:
            errors.append(f"{position_id}: not present in catalog_index")

        evidence = position.get("jd_evidence")
        if (
            not isinstance(evidence, list)
            or not all(nonempty_string(quote) for quote in evidence)
            or len(set(evidence)) < 2
        ):
            errors.append(f"{position_id}: jd_evidence needs at least two different non-empty quotes")

        if position.get("excluded") is True:
            if not nonempty_string(position.get("exclusion_reason")):
                errors.append(f"{position_id}: excluded item needs exclusion_reason")
            continue

        if position.get("grade") not in GRADES:
            errors.append(f"{position_id}: grade must be one of S/A/B/C")
        for field in ("coverage_estimate", "resume_version", "match_reasons", "gaps"):
            if not nonempty_string(position.get(field)):
                errors.append(f"{position_id}: missing {field}")

    in_scope_ids = {
        str(item.get("id"))
        for item in catalog_index
        if item.get("in_scope") is not False and item.get("id") is not None
    }
    missing = sorted(in_scope_ids - position_ids)
    if missing:
        errors.append(f"{len(missing)} in-scope positions are missing from positions: {', '.join(missing[:20])}")

    total_positions = raw_catalog.get("total_positions")
    if not isinstance(total_positions, int) or isinstance(total_positions, bool) or total_positions < 0:
        errors.append("raw_catalog.total_positions must be a non-negative integer")
    elif total_positions != len(catalog_index):
        errors.append(
            f"raw_catalog.total_positions={total_positions} does not equal catalog_index count {len(catalog_index)}"
        )

    raw_file = raw_catalog.get("file")
    raw_path: Path | None = None
    if nonempty_string(raw_file):
        raw_path = Path(raw_file)
        if not raw_path.is_absolute():
            raw_path = matching_path.parent / raw_path
        raw_path = raw_path.resolve()
        if not raw_path.is_file():
            errors.append(f"raw_catalog.file is not a file: {raw_file}")
        else:
            raw_count = count_raw_catalog(raw_path)
            if raw_count is None:
                warnings.append("raw catalog shape could not be counted automatically; verify official totals manually")
            elif raw_count != len(catalog_index):
                errors.append(
                    f"catalog_index count {len(catalog_index)} does not equal raw catalog count {raw_count}"
                )
    else:
        errors.append("raw_catalog.file must point to the raw snapshot")

    counts = {
        "catalog_total": len(catalog_index),
        "in_scope": len(in_scope_ids),
        "positions_listed": len(positions),
        "matched": sum(1 for item in positions if item.get("excluded") is not True),
        "excluded_in_positions": sum(1 for item in positions if item.get("excluded") is True),
        "out_of_scope_in_catalog": len(catalog_index) - len(in_scope_ids),
    }
    report = {
        "passed": not errors,
        "company": matching.get("company"),
        "date": matching.get("date"),
        "counts": counts,
        "errors": errors,
        "warnings": warnings,
    }
    output_path = matching_path.with_name(matching_path.stem + "-verification.json")
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())


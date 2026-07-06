from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any


REQUIRED_FIELDS_BY_TABLE = {
    "cases": ("case_code", "title"),
    "contracts": ("contract_code", "contract_name"),
    "payments": ("contract_id", "payment_month", "payment_amount"),
    "documents": ("file_name",),
}

DUPLICATE_FIELDS_BY_TABLE = {
    "cases": "case_code",
    "contracts": "contract_code",
}

ACCEPTED_WARNING_POLICY = {
    "status": "disabled",
    "allowed_warning_codes": [],
    "non_bypassable_gates": [
        "preview_errors",
        "duplicate_in_batch",
        "existing_case_code",
        "requires_confirmation",
        "source_chain_contract",
        "stale_preview_guard",
    ],
    "reason": "No formal allowlist policy exists yet; accepted_warning_codes cannot enable writes or bypass safety gates.",
}


MAPPING_DRAFT: dict[str, dict[str, Any]] = {
    "case_code": {
        "target_table": "cases",
        "target_field": "case_code",
        "confidence": 0.86,
        "mode": "exact",
        "requires_confirmation": False,
        "notes": "Case identifier from staged source row.",
        "aliases": ["case_no", "case_id", "案件編號", "案號"],
    },
    "title": {
        "target_table": "cases",
        "target_field": "title",
        "confidence": 0.78,
        "mode": "exact",
        "requires_confirmation": False,
        "notes": "Case title or short description.",
        "aliases": ["case_title", "subject", "案件名稱", "案名"],
    },
    "owner": {
        "target_table": "cases",
        "target_field": "owner",
        "confidence": 0.72,
        "mode": "exact",
        "requires_confirmation": False,
        "notes": "Business owner or responsible team.",
        "aliases": ["department", "dept", "承辦單位", "負責人"],
    },
    "amount": {
        "target_table": "cases",
        "target_field": "amount",
        "confidence": 0.62,
        "mode": "manual-confirm",
        "requires_confirmation": True,
        "notes": "Money fields must be confirmed before any formal import.",
        "aliases": ["case_amount", "total_amount", "金額", "總金額", "預算金額"],
    },
    "contract_code": {
        "target_table": "contracts",
        "target_field": "contract_code",
        "confidence": 0.84,
        "mode": "exact",
        "requires_confirmation": False,
        "notes": "Contract identifier from source row.",
        "aliases": ["contract_no", "合約編號", "契約編號"],
    },
    "contract_name": {
        "target_table": "contracts",
        "target_field": "contract_name",
        "confidence": 0.8,
        "mode": "exact",
        "requires_confirmation": False,
        "notes": "Contract display name.",
        "aliases": ["contract_title", "合約名稱", "契約名稱"],
    },
    "vendor_name": {
        "target_table": "contracts",
        "target_field": "vendor_name",
        "confidence": 0.74,
        "mode": "exact",
        "requires_confirmation": False,
        "notes": "Vendor or supplier name.",
        "aliases": ["vendor", "supplier", "廠商", "供應商"],
    },
    "contract_amount": {
        "target_table": "contracts",
        "target_field": "amount",
        "confidence": 0.68,
        "mode": "manual-confirm",
        "requires_confirmation": True,
        "notes": "Contract amount requires confirmation.",
        "aliases": ["合約金額", "契約金額"],
    },
    "case_id": {
        "target_table": "contracts",
        "target_field": "case_id",
        "confidence": 0.58,
        "mode": "manual-confirm",
        "requires_confirmation": True,
        "notes": "Relationship fields must be confirmed against existing cases.",
        "aliases": ["related_case_id", "關聯案件", "案件ID"],
    },
    "contract_id": {
        "target_table": "payments",
        "target_field": "contract_id",
        "confidence": 0.58,
        "mode": "manual-confirm",
        "requires_confirmation": True,
        "notes": "Relationship fields must be confirmed against existing contracts.",
        "aliases": ["related_contract_id", "關聯合約", "合約ID"],
    },
    "payment_month": {
        "target_table": "payments",
        "target_field": "payment_month",
        "confidence": 0.7,
        "mode": "manual-confirm",
        "requires_confirmation": True,
        "notes": "Payment month requires confirmation.",
        "aliases": ["pay_month", "付款月份", "請款月份"],
    },
    "payment_amount": {
        "target_table": "payments",
        "target_field": "payment_amount",
        "confidence": 0.7,
        "mode": "manual-confirm",
        "requires_confirmation": True,
        "notes": "Payment amount requires confirmation.",
        "aliases": ["pay_amount", "付款金額", "請款金額"],
    },
    "file_name": {
        "target_table": "documents",
        "target_field": "file_name",
        "confidence": 0.66,
        "mode": "manual-confirm",
        "requires_confirmation": True,
        "notes": "Document and PDF fields require confirmation.",
        "aliases": ["filename", "pdf_file", "document_file", "檔名", "PDF檔名", "文件"],
    },
    "document_type": {
        "target_table": "documents",
        "target_field": "document_type",
        "confidence": 0.6,
        "mode": "manual-confirm",
        "requires_confirmation": True,
        "notes": "Document category requires confirmation.",
        "aliases": ["doc_type", "文件類型", "PDF類型"],
    },
}


def mapping_draft_catalog() -> dict[str, Any]:
    items = [
        {
            "source_field": source_field,
            "target_table": mapping["target_table"],
            "target_field": mapping["target_field"],
            "confidence": mapping["confidence"],
            "mode": mapping["mode"],
            "requires_confirmation": mapping["requires_confirmation"],
            "notes": mapping["notes"],
            "aliases": mapping.get("aliases", []),
        }
        for source_field, mapping in sorted(MAPPING_DRAFT.items())
    ]
    by_table = Counter(item["target_table"] for item in items)
    return {
        "field_count": len(items),
        "requires_confirmation_count": sum(1 for item in items if item["requires_confirmation"]),
        "target_tables": dict(sorted(by_table.items())),
        "fields": items,
    }


def mapping_preview(batch: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    preview_rows = [preview_row(row) for row in rows]
    add_validation_warnings(preview_rows)
    warning_count = sum(
        1
        for row in preview_rows
        for warning in row["warnings"]
        if warning["severity"] == "warning"
    )
    error_count = sum(
        1
        for row in preview_rows
        for warning in row["warnings"]
        if warning["severity"] == "error"
    )
    warning_by_code = Counter(
        warning["code"]
        for row in preview_rows
        for warning in row["warnings"]
    )
    return {
        "batch": batch,
        "row_count": len(preview_rows),
        "rows": preview_rows,
        "summary": {
            "candidate_count": sum(len(row["candidates"]) for row in preview_rows),
            "unmapped_field_count": sum(len(row["unmapped_fields"]) for row in preview_rows),
            "requires_confirmation_count": sum(
                1
                for row in preview_rows
                for candidate in row["candidates"]
                if candidate["requires_confirmation"]
            ),
            "warning_count": warning_count,
            "error_count": error_count,
            "warning_by_code": dict(sorted(warning_by_code.items())),
        },
    }


def confirm_cases_dry_run_plan(
    preview: dict[str, Any],
    confirmed_fields: list[dict[str, Any]],
    existing_case_codes: set[str] | None = None,
) -> dict[str, Any]:
    existing_case_codes = existing_case_codes or set()
    validate_confirm_preview(preview, confirmed_fields, existing_case_codes)
    rows = []
    for row in preview["rows"]:
        fields = {
            candidate["target_field"]: candidate["value"]
            for candidate in row["candidates"]
            if candidate["target_table"] == "cases"
        }
        if not fields:
            continue
        rows.append(
            {
                "action": "create",
                "target_table": "cases",
                "row_number": row["row_number"],
                "source_row_id": row["row_id"],
                "record": {
                    key: fields[key]
                    for key in ("case_code", "title", "owner", "amount")
                    if key in fields
                },
            }
        )
    return {
        "dry_run": True,
        "target_tables": ["cases"],
        "summary": {
            **preview["summary"],
            "planned_create_count": len(rows),
        },
        "plan": {"cases": rows},
        "preview": preview,
    }


def confirm_preflight_report(
    preview: dict[str, Any],
    confirmed_fields: list[dict[str, Any]],
    accepted_warning_codes: list[str],
    existing_case_codes: set[str] | None = None,
) -> dict[str, Any]:
    existing_case_codes = existing_case_codes or set()
    duplicate_warnings = cases_duplicate_warnings(preview)
    existing_conflicts = cases_existing_conflicts(preview, existing_case_codes)
    missing_confirmations = cases_missing_confirmations(preview, confirmed_fields)
    gates = [
        make_gate(
            "formal_write_disabled",
            "blocked",
            "Formal import confirm writes are disabled until transaction, rollback, source-chain, stale preview, actor, and idempotency gates are implemented.",
        ),
        make_gate(
            "preview_errors",
            "blocked" if preview["summary"]["error_count"] > 0 else "pass",
            "Mapping preview error warnings must be zero before any import confirm.",
        ),
        make_gate(
            "duplicate_in_batch",
            "blocked" if duplicate_warnings else "pass",
            "Duplicate cases.case_code values inside the staged batch are blocked.",
            evidence={"count": len(duplicate_warnings)},
        ),
        make_gate(
            "existing_case_code",
            "blocked" if existing_conflicts else "pass",
            "Existing cases.case_code values are create-only conflicts.",
            evidence={"values": existing_conflicts},
        ),
        make_gate(
            "requires_confirmation",
            "blocked" if missing_confirmations else "pass",
            "Every cases candidate with requires_confirmation=true must be explicitly confirmed.",
            evidence={"missing": missing_confirmations},
        ),
        make_gate(
            "accepted_warning_codes_policy",
            "blocked",
            "accepted_warning_codes has no formal allowlist policy yet and cannot bypass errors or confirmations.",
            evidence={"accepted_warning_codes": accepted_warning_codes},
        ),
        make_gate(
            "source_chain_contract",
            "blocked",
            "Formal writes must atomically record batch_id, import_row_id, row_number, source_fields, target_fields, mapping_version, and actor in audit_logs.",
        ),
        make_gate(
            "stale_preview_guard",
            "blocked",
            "Formal writes require a preview hash, row version, or batch lock before enabling writes.",
        ),
    ]
    return {
        "mode": "preflight",
        "dry_run_supported": True,
        "formal_write_allowed": False,
        "target_tables": ["cases"],
        "mapping_version": "draft-v1",
        "freshness": {
            "strategy": "server_preview_fingerprint",
            "fingerprint": preview_fingerprint(preview),
            "mapping_version": "draft-v1",
            "server_preview_rerun": True,
        },
        "accepted_warning_policy": ACCEPTED_WARNING_POLICY,
        "summary": {
            **preview["summary"],
            "gate_count": len(gates),
            "blocked_gate_count": sum(1 for gate in gates if gate["status"] == "blocked"),
            "existing_case_conflict_count": len(existing_conflicts),
            "missing_confirmation_count": len(missing_confirmations),
        },
        "gates": gates,
        "source_chain_requirements": [
            "batch_id",
            "import_row_id",
            "row_number",
            "source_fields",
            "target_fields",
            "mapping_version",
            "actor",
            "server_preview_rerun",
        ],
        "next_allowed_action": "run_cases_dry_run",
        "preview": preview,
    }


def preview_fingerprint(preview: dict[str, Any]) -> str:
    payload = {
        "batch_id": preview["batch"]["id"],
        "mapping_version": "draft-v1",
        "rows": [
            {
                "row_id": row["row_id"],
                "row_number": row["row_number"],
                "candidates": sorted(
                    [
                        {
                            "target_table": candidate["target_table"],
                            "target_field": candidate["target_field"],
                            "source_field": candidate["source_field"],
                            "value": candidate["value"],
                            "requires_confirmation": candidate["requires_confirmation"],
                        }
                        for candidate in row["candidates"]
                    ],
                    key=lambda item: (item["target_table"], item["target_field"], item["source_field"]),
                ),
                "unmapped_fields": sorted(
                    row["unmapped_fields"],
                    key=lambda item: item["source_field"],
                ),
                "warnings": sorted(
                    [
                        {
                            "code": warning["code"],
                            "severity": warning["severity"],
                            "source_field": warning.get("source_field"),
                            "target_table": warning["target_table"],
                            "target_field": warning["target_field"],
                            "row_number": warning["row_number"],
                            "value": warning.get("value"),
                            "related_row_numbers": warning.get("related_row_numbers", []),
                        }
                        for warning in row["warnings"]
                    ],
                    key=lambda item: (
                        item["row_number"],
                        item["code"],
                        item["target_table"],
                        item["target_field"],
                        str(item.get("source_field")),
                    ),
                ),
            }
            for row in preview["rows"]
        ],
        "summary": preview["summary"],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_confirm_preview(
    preview: dict[str, Any],
    confirmed_fields: list[dict[str, Any]],
    existing_case_codes: set[str],
) -> None:
    if preview["summary"]["error_count"] > 0:
        raise ValueError("Import confirm blocked: mapping preview contains error warnings.")

    duplicate_warnings = cases_duplicate_warnings(preview)
    if duplicate_warnings:
        raise RuntimeError("Import confirm blocked: duplicate cases.case_code in staged rows.")

    existing_conflicts = cases_existing_conflicts(preview, existing_case_codes)
    if existing_conflicts:
        raise RuntimeError("Import confirm blocked: cases.case_code already exists.")

    missing_confirmations = cases_missing_confirmations(preview, confirmed_fields)
    if missing_confirmations:
        raise ValueError(
            "Import confirm blocked: requires_confirmation fields were not explicitly confirmed."
        )


def cases_duplicate_warnings(preview: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        warning
        for row in preview["rows"]
        for warning in row["warnings"]
        if warning["code"] == "duplicate_in_batch" and warning["target_table"] == "cases"
    ]


def cases_existing_conflicts(preview: dict[str, Any], existing_case_codes: set[str]) -> list[str]:
    return [
        candidate["value"]
        for row in preview["rows"]
        for candidate in row["candidates"]
        if candidate["target_table"] == "cases"
        and candidate["target_field"] == "case_code"
        and str(candidate["value"]).strip() in existing_case_codes
    ]


def cases_missing_confirmations(
    preview: dict[str, Any],
    confirmed_fields: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    confirmed = {
        (
            int(item["row_number"]),
            str(item["target_table"]),
            str(item["target_field"]),
        )
        for item in confirmed_fields
    }
    missing_confirmations = [
        {
            "row_number": row["row_number"],
            "target_table": candidate["target_table"],
            "target_field": candidate["target_field"],
            "source_field": candidate["source_field"],
        }
        for row in preview["rows"]
        for candidate in row["candidates"]
        if candidate["target_table"] == "cases"
        and candidate["requires_confirmation"]
        and (row["row_number"], candidate["target_table"], candidate["target_field"]) not in confirmed
    ]
    return missing_confirmations


def make_gate(
    code: str,
    status: str,
    message: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "status": status,
        "message": message,
        "evidence": evidence or {},
    }


def preview_row(import_row: dict[str, Any]) -> dict[str, Any]:
    raw = parse_raw_json(import_row["raw_json"])
    candidates: list[dict[str, Any]] = []
    unmapped_fields: list[dict[str, Any]] = []
    for source_field, value in raw.items():
        mapping = find_mapping(source_field)
        if mapping is None:
            unmapped_fields.append({"source_field": source_field, "value": value})
            continue
        candidates.append(
            {
                "target_table": mapping["target_table"],
                "target_field": mapping["target_field"],
                "source_field": source_field,
                "value": value,
                "requires_confirmation": bool(mapping["requires_confirmation"]),
                "confidence": mapping["confidence"],
                "mode": mapping["mode"],
                "notes": mapping["notes"],
            }
        )
    return {
        "row_id": import_row["id"],
        "row_number": import_row["row_number"],
        "candidates": candidates,
        "unmapped_fields": unmapped_fields,
        "warnings": [],
    }


def add_validation_warnings(preview_rows: list[dict[str, Any]]) -> None:
    duplicate_values: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row in preview_rows:
        candidates_by_table = candidates_by_target(row["candidates"])
        add_missing_required_warnings(row, candidates_by_table)
        add_amount_warnings(row)
        add_payment_month_warnings(row)
        for table, field in DUPLICATE_FIELDS_BY_TABLE.items():
            candidate = candidates_by_table.get(table, {}).get(field)
            if candidate and not is_blank(candidate["value"]):
                normalized_value = str(candidate["value"]).strip()
                duplicate_values[(table, field, normalized_value)].append(row["row_number"])

    for (table, field, value), row_numbers in duplicate_values.items():
        if len(row_numbers) < 2:
            continue
        for row in preview_rows:
            if row["row_number"] not in row_numbers:
                continue
            candidate = candidates_by_target(row["candidates"]).get(table, {}).get(field)
            if not candidate or str(candidate["value"]).strip() != value:
                continue
            row["warnings"].append(
                make_warning(
                    code="duplicate_in_batch",
                    severity="warning",
                    message=f"{table}.{field} duplicates another staged row in this batch.",
                    source_field=candidate["source_field"],
                    target_table=table,
                    target_field=field,
                    row_number=row["row_number"],
                    value=candidate["value"],
                    related_row_numbers=[number for number in row_numbers if number != row["row_number"]],
                )
            )


def add_missing_required_warnings(
    row: dict[str, Any],
    candidates_by_table: dict[str, dict[str, dict[str, Any]]],
) -> None:
    for table, required_fields in REQUIRED_FIELDS_BY_TABLE.items():
        table_candidates = candidates_by_table.get(table)
        if not table_candidates:
            continue
        for target_field in required_fields:
            candidate = table_candidates.get(target_field)
            if candidate and not is_blank(candidate["value"]):
                continue
            row["warnings"].append(
                make_warning(
                    code="missing_required",
                    severity="error",
                    message=f"{table}.{target_field} is required for rows mapped to {table}.",
                    source_field=candidate["source_field"] if candidate else None,
                    target_table=table,
                    target_field=target_field,
                    row_number=row["row_number"],
                    value=candidate["value"] if candidate else None,
                )
            )


def add_amount_warnings(row: dict[str, Any]) -> None:
    for candidate in row["candidates"]:
        if candidate["target_field"] not in {"amount", "payment_amount"}:
            continue
        value = candidate["value"]
        if is_blank(value):
            continue
        amount = parse_decimal(value)
        if amount is None:
            row["warnings"].append(
                make_warning(
                    code="invalid_amount",
                    severity="error",
                    message=f"{candidate['target_table']}.{candidate['target_field']} must be numeric.",
                    source_field=candidate["source_field"],
                    target_table=candidate["target_table"],
                    target_field=candidate["target_field"],
                    row_number=row["row_number"],
                    value=value,
                )
            )
            continue
        if amount <= 0:
            row["warnings"].append(
                make_warning(
                    code="invalid_amount",
                    severity="warning",
                    message=f"{candidate['target_table']}.{candidate['target_field']} is zero or negative.",
                    source_field=candidate["source_field"],
                    target_table=candidate["target_table"],
                    target_field=candidate["target_field"],
                    row_number=row["row_number"],
                    value=value,
                )
            )


def add_payment_month_warnings(row: dict[str, Any]) -> None:
    for candidate in row["candidates"]:
        if candidate["target_table"] != "payments" or candidate["target_field"] != "payment_month":
            continue
        value = candidate["value"]
        if is_blank(value):
            continue
        text = str(value).strip()
        if re.fullmatch(r"\d{6}", text):
            month = int(text[4:6])
            severity = "warning" if 1 <= month <= 12 else "error"
            message = (
                "payments.payment_month looks like YYYYMM; expected YYYY-MM."
                if severity == "warning"
                else "payments.payment_month month is invalid; expected YYYY-MM."
            )
            row["warnings"].append(
                make_warning(
                    code="invalid_month",
                    severity=severity,
                    message=message,
                    source_field=candidate["source_field"],
                    target_table="payments",
                    target_field="payment_month",
                    row_number=row["row_number"],
                    value=value,
                )
            )
            continue
        match = re.fullmatch(r"\d{4}-(\d{2})", text)
        if match and 1 <= int(match.group(1)) <= 12:
            continue
        row["warnings"].append(
            make_warning(
                code="invalid_month",
                severity="error",
                message="payments.payment_month must use YYYY-MM with a valid month.",
                source_field=candidate["source_field"],
                target_table="payments",
                target_field="payment_month",
                row_number=row["row_number"],
                value=value,
            )
        )


def candidates_by_target(candidates: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    by_table: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for candidate in candidates:
        by_table[candidate["target_table"]][candidate["target_field"]] = candidate
    return by_table


def make_warning(
    *,
    code: str,
    severity: str,
    message: str,
    source_field: str | None,
    target_table: str,
    target_field: str,
    row_number: int,
    value: Any | None = None,
    related_row_numbers: list[int] | None = None,
) -> dict[str, Any]:
    warning = {
        "code": code,
        "severity": severity,
        "message": message,
        "source_field": source_field,
        "target_table": target_table,
        "target_field": target_field,
        "row_number": row_number,
    }
    if value is not None:
        warning["value"] = value
    if related_row_numbers:
        warning["related_row_numbers"] = related_row_numbers
    return warning


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def parse_decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        amount = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return None
    return amount if amount.is_finite() else None


def parse_raw_json(raw_json: str) -> dict[str, Any]:
    try:
        value = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"import row contains invalid raw_json: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("import row raw_json must be a JSON object.")
    return value


def find_mapping(source_field: str) -> dict[str, Any] | None:
    normalized = normalize_field(source_field)
    for canonical_field, mapping in MAPPING_DRAFT.items():
        aliases = [canonical_field, *mapping.get("aliases", [])]
        if normalized in {normalize_field(alias) for alias in aliases}:
            return mapping
    return None


def normalize_field(value: str) -> str:
    return re.sub(r"[\s_\-./()（）]+", "", value).casefold()

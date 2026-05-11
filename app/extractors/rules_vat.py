from __future__ import annotations

import re
from typing import Any

from app.extractors.reading_order import sort_ocr_lines
from app.models.invoice import InvoiceCanonical
from app.parsers.common import invoice_from_mapped
from app.parsers.shudian_map import map_flat_to_canonical

_RE_INVOICE_CODE = re.compile(r"(?:发票代码|代码)[：:\s]*([0-9]{10,12})")
_RE_INVOICE_NO = re.compile(r"(?:发票号码|号码)[：:\s]*([0-9]{8,20})")
_RE_DATE = re.compile(
    r"(?:开票日期|日期)[：:\s]*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日|(\d{4})-(\d{1,2})-(\d{1,2})"
)
_RE_TAX_ID = re.compile(r"(?:纳税人识别号|统一社会信用代码|税号)[：:\s]*([0-9A-Z]{15,20})")
_RE_AMOUNT_PAY = re.compile(r"(?:价税合计|小写)[（(]?\s*¥?\s*([0-9,]+\.?\d*)")
_RE_TOTAL = re.compile(r"(?:合计|金额)[：:\s]*¥?\s*([0-9,]+\.?\d*)")
_RE_TAX = re.compile(r"(?:税额)[：:\s]*¥?\s*([0-9,]+\.?\d*)")


def _lines_text(sorted_items: list[dict[str, Any]]) -> list[str]:
    return [str(it.get("text", "")).strip() for it in sorted_items if str(it.get("text", "")).strip()]


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    return m.group(1) if m else None


def _first_match_date(text: str) -> str | None:
    m = _RE_DATE.search(text)
    if not m:
        return None
    if m.group(1):
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return f"{m.group(4)}-{int(m.group(5)):02d}-{int(m.group(6)):02d}"


def extract_from_ocr_lines(ocr_items: list[dict[str, Any]]) -> tuple[InvoiceCanonical, list[str]]:
    warnings: list[str] = []
    items = sort_ocr_lines(ocr_items)
    lines = _lines_text(items)
    blob = "\n".join(lines)

    flat: dict[str, str] = {}

    code = _first_match(_RE_INVOICE_CODE, blob)
    if code:
        flat["invoice_code"] = code.replace(" ", "")
    no = _first_match(_RE_INVOICE_NO, blob)
    if no:
        flat["invoice_number"] = no.replace(" ", "")
    d = _first_match_date(blob)
    if d:
        flat["issue_date"] = d

    amt = _first_match(_RE_AMOUNT_PAY, blob)
    if amt:
        flat["total_with_tax"] = amt.replace(",", "")

    tax = _first_match(_RE_TAX, blob)
    if tax:
        flat["tax_amount"] = tax.replace(",", "")

    total = _first_match(_RE_TOTAL, blob)
    if total:
        flat["amount_without_tax"] = total.replace(",", "")

    ids_found = _RE_TAX_ID.findall(blob)
    if len(ids_found) >= 2:
        flat["buyer_tax_id"] = ids_found[0]
        flat["seller_tax_id"] = ids_found[1]
    elif len(ids_found) == 1:
        flat["buyer_tax_id"] = ids_found[0]
        warnings.append("single_tax_id_heuristic")

    if not flat:
        warnings.append("no_regex_hits_try_manual_review")

    mapped = map_flat_to_canonical(flat)
    inv = invoice_from_mapped(mapped)
    preview = lines[:80]
    inv = inv.model_copy(update={"extra": {**inv.extra, "ocr_line_preview": preview, "ocr_full_text": blob[:8000]}})
    return inv, warnings

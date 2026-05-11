from __future__ import annotations

import re
from typing import Any

from app.extractors.reading_order import sort_ocr_lines
from app.models.invoice import InvoiceCanonical

_RE_BIZ_NO = re.compile(r"(?:사업자(?:등록)?번호)\s*[:：]?\s*([0-9]{3}-?[0-9]{2}-?[0-9]{5})")
_RE_OWNER = re.compile(r"(?:대표자)\s*[:：]?\s*([가-힣A-Za-z\s]{2,30})")
_RE_TEL = re.compile(r"(?:TEL|전화번호?)\s*[:：]?\s*([0-9\-]{8,20})", re.IGNORECASE)
_RE_DATE = re.compile(r"(20\d{2})[.\-/년]?\s*(\d{1,2})[.\-/월]?\s*(\d{1,2})")
_RE_RECEIPT_NO = re.compile(r"(?:영수번호)\s*[:：]?\s*([0-9A-Za-z\-]{1,30})")
_RE_APPROVAL_NO = re.compile(r"(?:승인번호|거래번호)\s*[:：]?\s*([0-9A-Za-z\-]{6,40})")
_RE_TERMINAL_NO = re.compile(r"(?:단말기번호)\s*[:：]?\s*([0-9A-Za-z\-]{6,30})")
_RE_ADDRESS_HINT = re.compile(r"(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)")
_RE_ITEM_MONEY = re.compile(r"([0-9][0-9,\s]{2,})")
_RE_NON_ITEM_LINE = re.compile(
    r"(?:사업자번호|대표자|TEL|영수번호|판매시간|합계|현금|거스름|공급가|부가세|승인번호|단말기번호|번호|서울특별시)"
)


def _norm_money(v: str) -> str:
    return re.sub(r"[^\d.]", "", v)


def _lines_text(sorted_items: list[dict[str, Any]]) -> list[str]:
    return [str(it.get("text", "")).strip() for it in sorted_items if str(it.get("text", "")).strip()]


def _first(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    if not m:
        return None
    return m.group(1).strip()


def _extract_merchant_name(lines: list[str]) -> str | None:
    for line in lines[:8]:
        s = line.strip()
        if not s:
            continue
        if any(k in s for k in ["사업자번호", "대표자", "TEL", "영수번호", "판매시간"]):
            continue
        if s.startswith("[") and s.endswith("]"):
            continue
        if re.search(r"[가-힣A-Za-z]{2,}", s):
            return s
    return None


def _extract_address(lines: list[str]) -> str | None:
    merged: list[str] = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if _RE_ADDRESS_HINT.search(s):
            merged.append(s)
        elif merged and len(merged) < 3:
            # Continue a possible multi-line address block.
            if re.search(r"[가-힣0-9\-]", s):
                merged.append(s)
    if not merged:
        return None
    return " ".join(merged[:3])


def _extract_money_by_keywords(blob: str, keywords: list[str]) -> str | None:
    for kw in keywords:
        m = re.search(rf"{kw}\s*[:：]?\s*([0-9][0-9,\s.]*)", blob)
        if m:
            v = _norm_money(m.group(1))
            if v:
                return v
    return None


def _extract_money_from_lines(lines: list[str], keywords: list[str]) -> str | None:
    for i, line in enumerate(lines):
        joined = line.replace(" ", "")
        if not any(re.search(kw, joined) for kw in keywords):
            continue
        window = lines[i : i + 5]
        merged = " ".join(window)
        nums = re.findall(r"[0-9][0-9,\s]{1,}", merged)
        for n in reversed(nums):
            v = _norm_money(n)
            if len(v) >= 3:
                return v
    return None


def _extract_receipt_no(blob: str, lines: list[str]) -> str | None:
    receipt_no = _first(_RE_RECEIPT_NO, blob)
    if receipt_no and len(receipt_no) >= 4:
        return receipt_no
    for line in reversed(lines[-12:]):
        m = re.search(r"\b(20\d{14,18})\b", line)
        if m:
            return m.group(1)
    return None


def _extract_issue_date(blob: str) -> str | None:
    m = _RE_DATE.search(blob)
    if not m:
        return None
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def _extract_items(lines: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    started = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if "상품" in line and ("금액" in line or "단가" in line):
            started = True
            continue
        if not started:
            continue
        if _RE_NON_ITEM_LINE.search(line):
            if items:
                break
            continue

        money_tokens = _RE_ITEM_MONEY.findall(line)
        if not money_tokens:
            continue

        # Keep lines with at least one Korean letter as item candidates.
        if not re.search(r"[가-힣A-Za-z]", line):
            continue

        normalized_money = [_norm_money(tok) for tok in money_tokens]
        normalized_money = [m for m in normalized_money if m]
        if not normalized_money:
            continue

        amount = normalized_money[-1]
        unit_price = normalized_money[0] if len(normalized_money) >= 2 else None
        qty = normalized_money[1] if len(normalized_money) >= 3 else None

        # Item name: trim trailing money tokens and separators.
        name = line
        for tok in money_tokens:
            name = name.replace(tok, " ")
        name = re.sub(r"[-_=:.]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        if len(name) < 2:
            continue

        items.append(
            {
                "name": name,
                "qty": qty,
                "unit_price": unit_price,
                "amount": amount,
                "raw_line": line,
            }
        )
        if len(items) >= 30:
            break
    return items


def extract_from_ocr_lines_kr(ocr_items: list[dict[str, Any]]) -> tuple[InvoiceCanonical, list[str]]:
    warnings: list[str] = []
    lines = _lines_text(sort_ocr_lines(ocr_items))
    blob = "\n".join(lines)

    merchant_name = _extract_merchant_name(lines)
    biz_no = _first(_RE_BIZ_NO, blob)
    owner = _first(re.compile(r"(?:대표자)\s*[:：]?\s*([가-힣A-Za-z]{2,30})"), blob)
    tel = _first(_RE_TEL, blob)
    address = _extract_address(lines)
    issue_date = _extract_issue_date(blob)
    receipt_no = _extract_receipt_no(blob, lines)
    approval_no = _first(_RE_APPROVAL_NO, blob)
    terminal_no = _first(_RE_TERMINAL_NO, blob)

    subtotal = _extract_money_by_keywords(blob, ["합\\s*계"]) or _extract_money_from_lines(lines, ["합계", "합\\s*계"])
    cash_paid = _extract_money_by_keywords(blob, ["현\\s*금"]) or _extract_money_from_lines(lines, ["현금"])
    change = _extract_money_by_keywords(blob, ["거스름돈", "거스름톤"]) or _extract_money_from_lines(lines, ["거스름"])
    supply_amount = _extract_money_by_keywords(blob, ["공급가액", "공\\s*급\\s*가"]) or _extract_money_from_lines(
        lines, ["공급가", "급가"]
    )
    vat_amount = _extract_money_by_keywords(blob, ["부가세", "세\\s*액", "VAT"]) or _extract_money_from_lines(
        lines, ["부가세", "세액", "VAT"]
    )
    total_amount = subtotal or cash_paid
    items = _extract_items(lines)
    if not merchant_name and len(lines) > 1 and re.search(r"[가-힣A-Za-z]{2,}", lines[1]):
        merchant_name = lines[1]
    conf_values = [float(it.get("confidence", 0.0)) for it in ocr_items if isinstance(it.get("confidence"), (int, float))]
    overall_confidence = (sum(conf_values) / len(conf_values)) if conf_values else None

    inv = InvoiceCanonical(
        invoice_number=receipt_no,
        issue_date=issue_date,
        seller_name=merchant_name,
        seller_tax_id=biz_no,
        amount_without_tax=supply_amount or subtotal,
        tax_amount=vat_amount,
        total_with_tax=total_amount,
        remark=owner,
        extra={
            "receipt_country": "KR",
            "doc_type": "kr_receipt",
            "merchant_name": merchant_name,
            "business_number": biz_no,
            "owner_name": owner,
            "phone": tel,
            "address": address,
            "receipt_no": receipt_no,
            "approval_no": approval_no,
            "terminal_no": terminal_no,
            "subtotal": subtotal,
            "cash_paid": cash_paid,
            "change": change,
            "supply_amount": supply_amount,
            "vat_amount": vat_amount,
            "total_amount": total_amount,
            "currency": "KRW",
            "items": items,
            "items_count": len(items),
            "overall_confidence": overall_confidence,
            "ocr_line_preview": lines[:120],
            "ocr_full_text": blob[:8000],
        },
    )

    if not any([merchant_name, biz_no, receipt_no, subtotal, issue_date]):
        warnings.append("kr_receipt_no_key_fields_detected")
    return inv, warnings

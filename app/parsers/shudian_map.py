"""Map flattened 数电票 keys (XML local names / JSON keys) to InvoiceCanonical fields."""

from __future__ import annotations

import re
from typing import Any


def normalize_key(key: str) -> str:
    k = key.strip().lower()
    k = k.split("}")[-1]
    k = re.sub(r"[^a-z0-9]+", "", k)
    return k


def key_candidates(raw_key: str) -> list[str]:
    """Full path normalized + each path segment (handles Invoice.Header.FpHm)."""
    nk = normalize_key(raw_key)
    parts = re.split(r"[.\[\]]+", raw_key)
    tails = [normalize_key(p) for p in parts if p and p.strip()]
    ordered: list[str] = []
    seen: set[str] = set()
    for c in [nk, *tails]:
        if c and c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered


# Keys match against key_candidates entries (whole string).
_ALIASES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(?:fpdm|invoicecode|invoice_code)$"), "invoice_code"),
    (re.compile(r"^(?:fphm|invoicenumber|invoice_number)$"), "invoice_number"),
    (re.compile(r"^(?:kprq|invoicedate|issue_date|billingdate)$"), "issue_date"),
    (re.compile(r"^(?:gmfmc|buyername|purchasername)$"), "buyer_name"),
    (re.compile(r"^(?:gmfnsrsbh|buyertaxno|purchasertaxno)$"), "buyer_tax_id"),
    (re.compile(r"^(?:xsfmc|sellername|salesname)$"), "seller_name"),
    (re.compile(r"^(?:xsfnsrsbh|sellertaxno|salestaxno)$"), "seller_tax_id"),
    (re.compile(r"^(?:hjje|amountwithouttax|totalamount)$"), "amount_without_tax"),
    (re.compile(r"^(?:hjse|taxamount)$"), "tax_amount"),
    (re.compile(r"^(?:jshj|totalwithtax|amountwithtax|pricetaxtotal)$"), "total_with_tax"),
    (re.compile(r"^(?:bz|remark|memo)$"), "remark"),
]


def _match_field(nk: str) -> str | None:
    for pat, fname in _ALIASES:
        if pat.match(nk):
            return fname
    return None


def map_flat_to_canonical(flat: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    extra: dict[str, str] = {}

    for raw_k, v in flat.items():
        if v is None:
            continue
        s = str(v).strip()
        if not s:
            continue

        field: str | None = None
        for cand in key_candidates(raw_k):
            field = _match_field(cand)
            if field:
                break

        if field:
            if field not in out or out[field] in (None, ""):
                out[field] = s
        else:
            extra[raw_k] = s

    out["extra"] = extra
    return out

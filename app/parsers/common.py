from __future__ import annotations

from typing import Any

from app.models.invoice import InvoiceCanonical


def invoice_from_mapped(mapped: dict[str, Any]) -> InvoiceCanonical:
    m = dict(mapped)
    raw_extra = m.pop("extra", None)
    extra: dict[str, Any] = dict(raw_extra) if isinstance(raw_extra, dict) else {}
    data: dict[str, Any] = {"extra": extra}
    for name in InvoiceCanonical.model_fields:
        if name == "extra":
            continue
        if name in m and m[name] not in (None, ""):
            data[name] = m[name]
    return InvoiceCanonical(**data)

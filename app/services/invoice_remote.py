from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.models.invoice import InvoiceCanonical, InvoiceParseRequest, InvoiceParseResponse


def _remote_url(settings: Settings) -> str:
    base = (settings.invoice_remote_base_url or "").rstrip("/")
    path = settings.invoice_remote_parse_path or "/v1/parse"
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


def _trim_remote_raw(data: dict[str, Any]) -> dict[str, Any]:
    keep = {}
    for k in ("success", "source", "warnings", "compute_mode"):
        if k in data:
            keep[k] = data[k]
    return keep


async def parse_remote(req: InvoiceParseRequest, settings: Settings) -> InvoiceParseResponse:
    base = settings.invoice_remote_base_url
    if not base:
        raise ValueError("invoice_remote_base_url_not_set")

    url = _remote_url(settings)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if settings.invoice_remote_api_key:
        headers["Authorization"] = f"Bearer {settings.invoice_remote_api_key}"

    payload = req.model_dump(mode="json", exclude_none=True)

    async with httpx.AsyncClient(timeout=settings.invoice_remote_timeout_sec) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"remote_http_{e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ValueError("remote_unreachable") from e

    if not isinstance(data, dict):
        raise ValueError("remote_invalid_json_shape")

    try:
        return InvoiceParseResponse.model_validate(data)
    except Exception:
        inv_obj = data.get("invoice")
        if isinstance(inv_obj, dict):
            inv = InvoiceCanonical.model_validate(inv_obj)
        else:
            inv = InvoiceCanonical(extra={"remote_unparsed": True})

        warnings = data.get("warnings")
        if not isinstance(warnings, list):
            warnings = []

        return InvoiceParseResponse(
            success=bool(data.get("success", True)),
            compute_mode="remote",
            source=str(data.get("source") or "remote"),
            invoice=inv,
            warnings=[str(x) for x in warnings],
            remote_raw=_trim_remote_raw(data),
        )

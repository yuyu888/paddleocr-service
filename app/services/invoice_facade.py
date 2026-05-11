from __future__ import annotations

import base64

from app.config import Settings
from app.core import ocr_engine
from app.extractors.rules_receipt_kr import extract_from_ocr_lines_kr
from app.extractors.rules_vat import extract_from_ocr_lines
from app.models.invoice import ComputeMode, DocType, InputKind, InvoiceParseRequest, InvoiceParseResponse
from app.parsers.shudian_xml import parse_shudian_json, parse_shudian_xml
from app.services.structured_fields import build_structured_fields


def _resolve_mode(req: InvoiceParseRequest, settings: Settings) -> ComputeMode:
    if req.compute_mode is not None:
        return req.compute_mode
    raw = (settings.default_invoice_compute_mode or "local").lower()
    return ComputeMode.remote if raw == "remote" else ComputeMode.local


async def parse_local(req: InvoiceParseRequest, settings: Settings) -> InvoiceParseResponse:
    warnings: list[str] = []

    if req.input_kind == InputKind.shudian_xml:
        inv, w = parse_shudian_xml(req.payload)
        warnings.extend(w)
        resp = InvoiceParseResponse(
            success=True,
            compute_mode="local",
            source="shudian",
            invoice=inv,
            warnings=warnings,
            remote_raw=None,
        )
        resp.structured_fields = build_structured_fields(resp)
        return resp

    if req.input_kind == InputKind.shudian_json:
        inv, w = parse_shudian_json(req.payload)
        warnings.extend(w)
        resp = InvoiceParseResponse(
            success=True,
            compute_mode="local",
            source="shudian",
            invoice=inv,
            warnings=warnings,
            remote_raw=None,
        )
        resp.structured_fields = build_structured_fields(resp)
        return resp

    if req.input_kind == InputKind.image_base64:
        raw = req.payload.strip()
        if "," in raw:
            raw = raw.split(",", 1)[1]
        data = base64.b64decode(raw, validate=False)
        if len(data) > settings.invoice_local_image_max_bytes:
            raise ValueError("image_too_large")

        img = ocr_engine.decode_image_bytes(data)
        if img is None:
            raise ValueError("invalid_image")

        ocr_items = ocr_engine.run_ocr_on_bgr(
            img, lang=req.lang, return_text_only=False, auto_rotate=req.auto_rotate
        )
        if req.doc_type == DocType.kr_receipt:
            inv, w = extract_from_ocr_lines_kr(ocr_items)
        else:
            inv, w = extract_from_ocr_lines(ocr_items)
        warnings.extend(w)
        resp = InvoiceParseResponse(
            success=True,
            compute_mode="local",
            source="ocr",
            invoice=inv,
            warnings=warnings,
            remote_raw=None,
        )
        resp.structured_fields = build_structured_fields(resp)
        return resp

    raise ValueError("unsupported_input_kind")


async def parse_invoice(req: InvoiceParseRequest, settings: Settings) -> InvoiceParseResponse:
    mode = _resolve_mode(req, settings)
    if mode == ComputeMode.local:
        return await parse_local(req, settings)

    from app.services.invoice_remote import parse_remote

    resp = await parse_remote(req, settings)
    if not resp.structured_fields:
        resp.structured_fields = build_structured_fields(resp)
    return resp

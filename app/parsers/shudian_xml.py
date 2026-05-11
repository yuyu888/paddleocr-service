from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Any

from app.parsers.common import invoice_from_mapped
from app.parsers.shudian_map import map_flat_to_canonical


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _flatten_xml(element: ET.Element, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    tag = _local_tag(element.tag)
    path = f"{prefix}.{tag}" if prefix else tag

    text = (element.text or "").strip()
    tail = (element.tail or "").strip()
    if text:
        out[path] = text
    if tail:
        out[f"{path}@tail"] = tail

    children = list(element)
    if not children and text:
        out[tag] = text

    for child in children:
        out.update(_flatten_xml(child, path))

    return out


def parse_shudian_xml(xml_text: str) -> tuple[InvoiceCanonical, list[str]]:
    warnings: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"invalid_xml: {e}") from e

    flat = _flatten_xml(root)
    if not flat:
        warnings.append("empty_xml_flatten")

    mapped = map_flat_to_canonical(flat)
    inv = invoice_from_mapped(mapped)
    return inv, warnings


def parse_shudian_json(json_text: str) -> tuple[InvoiceCanonical, list[str]]:
    warnings: list[str] = []
    try:
        obj = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid_json: {e}") from e

    flat: dict[str, str] = {}

    def walk(o: Any, prefix: str) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                p = f"{prefix}.{k}" if prefix else str(k)
                if isinstance(v, (dict, list)):
                    walk(v, p)
                elif v is not None:
                    flat[p] = str(v).strip()
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{prefix}[{i}]")

    walk(obj, "")
    if not flat:
        warnings.append("empty_json_flatten")

    mapped = map_flat_to_canonical(flat)
    inv = invoice_from_mapped(mapped)
    return inv, warnings

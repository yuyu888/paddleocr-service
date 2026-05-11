from __future__ import annotations

from typing import Any


def sort_ocr_lines(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reading order: top-to-bottom, left-to-right by bbox center."""

    def key(it: dict[str, Any]) -> tuple[float, float]:
        bb = it.get("bbox") or {}
        cx = (float(bb.get("xmin", 0)) + float(bb.get("xmax", 0))) / 2.0
        cy = (float(bb.get("ymin", 0)) + float(bb.get("ymax", 0))) / 2.0
        return (cy, cx)

    return sorted(items, key=key)

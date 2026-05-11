from __future__ import annotations

from typing import Any

from app.models.invoice import InvoiceParseResponse


def _sf(
    field_code: str,
    label_zh: str,
    group_zh: str,
    value: str | None,
    value_mean_zh: str | None = None,
) -> dict[str, Any]:
    return {
        "fieldCode": field_code,
        "labelZh": label_zh,
        "groupZh": group_zh,
        "value": value,
        "valueMeanZh": value_mean_zh,
    }


def build_structured_fields(resp: InvoiceParseResponse) -> list[dict[str, Any]]:
    inv = resp.invoice
    extra = inv.extra or {}
    doc_type = str(extra.get("doc_type") or "cn_vat")

    if doc_type == "kr_receipt":
        conf = extra.get("overall_confidence")
        conf_str = f"{float(conf):.2f}" if isinstance(conf, (int, float)) else None
        return [
            _sf("extractEngine", "抽取引擎", "基本信息", "paddleocr-local", "PaddleOCR 本地规则抽取"),
            _sf("country", "国家/地区", "基本信息", str(extra.get("receipt_country") or "KR"), "韩国"),
            _sf("language", "语言", "基本信息", "ko", "韩语"),
            _sf("currency", "币种", "基本信息", str(extra.get("currency") or "KRW"), "韩元"),
            _sf("invoiceNumber", "发票/收据号码", "票据信息", inv.invoice_number),
            _sf("invoiceDate", "开票/交易日期", "票据信息", inv.issue_date),
            _sf("sellerName", "销方/商户名称", "交易方", inv.seller_name or extra.get("merchant_name")),
            _sf("buyerName", "购方名称", "交易方", inv.buyer_name),
            _sf("subtotalAmount", "不含税金额（销售额/공급가）", "金额信息", inv.amount_without_tax),
            _sf("taxAmount", "税额（부가세/VAT 等）", "金额信息", inv.tax_amount),
            _sf("totalAmount", "价税合计", "金额信息", inv.total_with_tax or extra.get("total_amount")),
            _sf("overallConfidence", "整体可信度（0~1）", "质量与风险", conf_str, "较高" if conf_str else None),
            _sf("lineItemCount", "明细行数", "质量与风险", str(extra.get("items_count", 0))),
        ]

    # Fallback generic output
    return [
        _sf("extractEngine", "抽取引擎", "基本信息", "paddleocr-local"),
        _sf("country", "国家/地区", "基本信息", str(extra.get("receipt_country") or "" or None)),
        _sf("invoiceNumber", "发票/收据号码", "票据信息", inv.invoice_number),
        _sf("invoiceDate", "开票/交易日期", "票据信息", inv.issue_date),
        _sf("sellerName", "销方/商户名称", "交易方", inv.seller_name),
        _sf("buyerName", "购方名称", "交易方", inv.buyer_name),
        _sf("subtotalAmount", "不含税金额", "金额信息", inv.amount_without_tax),
        _sf("taxAmount", "税额", "金额信息", inv.tax_amount),
        _sf("totalAmount", "价税合计", "金额信息", inv.total_with_tax),
        _sf("lineItemCount", "明细行数", "质量与风险", str(extra.get("items_count", 0))),
    ]

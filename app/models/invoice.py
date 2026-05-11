from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class ComputeMode(str, Enum):
    local = "local"
    remote = "remote"


class InputKind(str, Enum):
    shudian_xml = "shudian_xml"
    shudian_json = "shudian_json"
    image_base64 = "image_base64"


class DocType(str, Enum):
    cn_vat = "cn_vat"
    kr_receipt = "kr_receipt"


class InvoiceCanonical(BaseModel):
    """Unified invoice fields; values are strings or None (unknown)."""

    invoice_code: str | None = None
    invoice_number: str | None = None
    issue_date: str | None = None
    buyer_name: str | None = None
    buyer_tax_id: str | None = None
    seller_name: str | None = None
    seller_tax_id: str | None = None
    amount_without_tax: str | None = None
    tax_amount: str | None = None
    total_with_tax: str | None = None
    remark: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class InvoiceParseRequest(BaseModel):
    compute_mode: ComputeMode | None = Field(
        default=None,
        description="local=本机解析；remote=转发远程。缺省使用环境变量 DEFAULT_INVOICE_COMPUTE_MODE",
    )
    input_kind: InputKind
    doc_type: DocType = Field(default=DocType.cn_vat, description="票据类型：cn_vat 或 kr_receipt")
    payload: str = Field(..., description="数电 XML/JSON 原文，或图片 Base64")
    lang: str = Field(default="ch", description="image_base64 时 OCR 语言")
    auto_rotate: bool = Field(default=True, description="影像是否尝试保持当前方向（占位，与 OCR 一致）")


class InvoiceParseResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    compute_mode: str
    source: str
    invoice: InvoiceCanonical
    warnings: list[str] = Field(default_factory=list)
    remote_raw: dict[str, Any] | None = Field(
        default=None,
        description="remote 模式下可选的远端原始 JSON 子集（不含大段 payload）",
    )
    structured_fields: list[dict[str, Any]] = Field(
        default_factory=list,
        serialization_alias="structuredFields",
        description="面向前端消费的结构化字段列表",
    )

# API 与调用示例

服务默认监听 **8088**。下文示例中的 `http://localhost:8088` 请换成你的实际地址。

交互式文档：<http://localhost:8088/docs>（OpenAPI 由 FastAPI 生成，以页面为准）。

---

## 枚举与类型约定（先看本节）

### `lang`（OCR 识别语言）

所有 OCR 接口中的 `lang` 均传入 **字符串**。代码里会做 **大小写不敏感** 匹配；**未出现在下表的任意值会回退为中文 `ch`**。

| 请求取值（示例） | 实际 PaddleOCR `lang` | 说明 |
|------------------|----------------------|------|
| `ch` | `ch` | 中文（简体），默认 |
| `en` | `en` | 英文 |
| `korean` | `korean` | 韩文 |
| `japan` | `japan` | 日文 |
| `german` | `german` | 德文 |
| `french` | `french` | 法文 |

与 `GET /languages` 返回的键一致。

### 布尔参数（`auto_rotate`、`return_text_only`）

- **JSON 请求体**：使用 JSON 布尔 `true` / `false`。
- **`multipart/form-data`（如 `POST /ocr`、`/ocr/batch`）**：字段值传字符串 **`true`** 或 **`false`**（小写，与 curl `-F` 示例一致）。

### 发票 `compute_mode`（可选）

| 取值 | 含义 |
|------|------|
| `local` | 在本容器内解析（数电 XML/JSON 或影像 OCR+规则） |
| `remote` | 将同一 JSON 请求体转发到配置的远程解析服务 |

**省略**该字段时，使用环境变量 **`DEFAULT_INVOICE_COMPUTE_MODE`**；未设置环境变量时默认为 **`local`**。

### 发票 `input_kind`（必填）

| 取值 | 含义 |
|------|------|
| `shudian_xml` | `payload` 为 **数电票 XML 全文**（字符串） |
| `shudian_json` | `payload` 为 **数电票 JSON 全文**（字符串，即一段 JSON 的文本形式） |
| `image_base64` | `payload` 为 **图片 Base64**（可带 `data:image/jpeg;base64,` 等前缀） |

### 发票 `doc_type`（可选）

| 取值 | 含义 |
|------|------|
| `cn_vat` | 中国增值税票据规则（默认） |
| `kr_receipt` | 韩国小票规则（商户名、사업자번호、영수번호、合计等） |

### 发票响应中的 `source`（只读，由服务填写）

| 取值 | 含义 |
|------|------|
| `shudian` | 来自数电 XML/JSON 解析 |
| `ocr` | 来自影像 OCR + 规则抽取 |

### 发票响应中的 `compute_mode`（只读）

与本次实际执行一致：`local` 或 `remote`（字符串）。

---

## 通用说明

- **Content-Type**：JSON 接口为 `application/json`；上传文件为 `multipart/form-data`。
- **错误**：HTTP 状态与 **`detail` 枚举/固定文案** 见 **[错误码与 `detail` 列表](#错误码与-detail-列表)**；校验失败另见该节 **422** 说明。

---

## 元数据与健康

### `GET /`

无请求参数。

```bash
curl -s http://localhost:8088/ | jq .
```

### `GET /health`

无请求参数。响应中 `engines_loaded` 为已加载的 OCR 语言键列表（如 `["ch"]`），冷启动可能为空。

```bash
curl -s http://localhost:8088/health | jq .
```

### `GET /languages`

无请求参数。返回 `languages` 对象，键为 **`lang` 枚举取值**（见上文表）。

```bash
curl -s http://localhost:8088/languages | jq .
```

---

## OCR

### `POST /ocr`（`multipart/form-data`）

| 字段 | 必填 | 类型 / 枚举 | 默认 | 说明 |
|------|------|-------------|------|------|
| `file` | 是 | 文件 | — | 图片二进制 |
| `lang` | 否 | **见上文 `lang` 表** | `ch` | |
| `auto_rotate` | 否 | 布尔 | `true` | 当前实现为占位，等价原图 |
| `return_text_only` | 否 | 布尔 | `false` | `true` 时结果不含坐标 |

```bash
curl -s -X POST http://localhost:8088/ocr \
  -F "file=@./sample.jpg" \
  -F "lang=ch" \
  -F "return_text_only=false" | jq .
```

### `POST /ocr/base64`（`application/json`）

| 字段 | 必填 | 类型 / 枚举 | 默认 | 说明 |
|------|------|-------------|------|------|
| `image_base64` | 是 | 字符串 | — | 纯 Base64 或 `data:image/...;base64,...` |
| `lang` | 否 | **见上文 `lang` 表** | `ch` | |
| `auto_rotate` | 否 | 布尔 | `true` | |
| `return_text_only` | 否 | 布尔 | `false` | |

```bash
IMG_B64=$(base64 -i ./sample.jpg)   # macOS；Linux 可用 base64 -w0
curl -s -X POST http://localhost:8088/ocr/base64 \
  -H "Content-Type: application/json" \
  -d "{\"image_base64\": \"${IMG_B64}\", \"lang\": \"ch\", \"return_text_only\": true}" | jq .
```

### `POST /ocr/url`（`application/json`）

服务端对 `url` 发起 **GET** 下载，再按图片解码。

| 字段 | 必填 | 类型 / 枚举 | 默认 | 说明 |
|------|------|-------------|------|------|
| `url` | 是 | 字符串（URL） | — | 须可公网/内网访问 |
| `lang` | 否 | **见上文 `lang` 表** | `ch` | |
| `auto_rotate` | 否 | 布尔 | `true` | |
| `return_text_only` | 否 | 布尔 | `false` | |

拉取失败一般为 **502**，`detail` 含 `拉取 URL 失败`。

```bash
curl -s -X POST http://localhost:8088/ocr/url \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/invoice.png","lang":"ch","return_text_only":false}' | jq .
```

### `POST /ocr/batch`（`multipart/form-data`）

| 字段 | 必填 | 类型 / 枚举 | 默认 | 说明 |
|------|------|-------------|------|------|
| `files` | 是 | 文件，可多个 | — | 每个 part 使用同名 `files` |
| `lang` | 否 | **见上文 `lang` 表** | `ch` | |
| `return_text_only` | 否 | 布尔 | `false` | 无 `auto_rotate` 字段 |

```bash
curl -s -X POST http://localhost:8088/ocr/batch \
  -F "files=@./a.jpg" \
  -F "files=@./b.png" \
  -F "lang=ch" \
  -F "return_text_only=true" | jq .
```

### OCR 响应结构（节选）

含坐标时，`results` 中每项含 `text`、`confidence`、`coordinates`、`bbox`（`xmin/ymin/xmax/ymax`）。

```json
{
  "success": true,
  "language": "ch",
  "text_count": 12,
  "results": [
    {
      "text": "示例",
      "confidence": 0.99,
      "bbox": {"xmin": 10, "ymin": 20, "xmax": 80, "ymax": 40}
    }
  ],
  "full_text": "示例\n..."
}
```

### Python：单图上传 OCR

```python
import requests

url = "http://localhost:8088/ocr"
with open("sample.jpg", "rb") as f:
    resp = requests.post(
        url,
        files={"file": f},
        data={"lang": "ch", "return_text_only": "true"},
        timeout=120,
    )
resp.raise_for_status()
print(resp.json()["full_text"])
```

---

## 发票：`POST /invoice/v1/parse`（`application/json`）与 `POST /invoice/v1/parse/file`（`multipart/form-data`）

| 字段 | 必填 | 类型 / 枚举 | 默认 | 说明 |
|------|------|-------------|------|------|
| `compute_mode` | 否 | **`local`** \| **`remote`** | 读环境变量，缺省为 `local` | 见上文枚举表 |
| `input_kind` | 是 | **`shudian_xml`** \| **`shudian_json`** \| **`image_base64`** | — | 决定 `payload` 语义 |
| `doc_type` | 否 | **`cn_vat`** \| **`kr_receipt`** | `cn_vat` | 仅 `image_base64` 时生效，决定使用哪套规则抽取 |
| `payload` | 是 | 字符串 | — | XML / JSON 文本 / 图片 Base64 |
| `lang` | 否 | **见上文 `lang` 表** | `ch` | 仅 **`input_kind` = `image_base64`** 时参与 OCR |
| `auto_rotate` | 否 | 布尔 | `true` | 仅影像路径传入 OCR |

### 文件上传版：`POST /invoice/v1/parse/file`（`multipart/form-data`）

该接口用于直接 `-F "file=@..."` 上传图片并返回结构化结果，服务端会自动将文件转为 Base64 后走同一发票解析链路。

| 字段 | 必填 | 类型 / 枚举 | 默认 | 说明 |
|------|------|-------------|------|------|
| `file` | 是 | 文件 | — | 票据图片 |
| `compute_mode` | 否 | **`local`** \| **`remote`** | 读环境变量，缺省 `local` | 与 JSON 版一致 |
| `doc_type` | 否 | **`cn_vat`** \| **`kr_receipt`** | `cn_vat` | 与 JSON 版一致 |
| `lang` | 否 | **见上文 `lang` 表** | `ch` | OCR 语言 |
| `auto_rotate` | 否 | 布尔 | `true` | 影像路径参数 |

示例（韩国小票）：

```bash
curl -s -X POST http://localhost:8088/invoice/v1/parse/file \
  -F "file=@./invoice/20251209-173728.png" \
  -F "compute_mode=local" \
  -F "doc_type=kr_receipt" \
  -F "lang=korean" \
  -F "auto_rotate=true" | jq .
```

### 数电票 JSON（`compute_mode`: `local`，`input_kind`: `shudian_json`）

`payload` 必须是 **字符串**，其内部为 JSON 文本。

```bash
curl -s -X POST http://localhost:8088/invoice/v1/parse \
  -H "Content-Type: application/json" \
  -d '{
    "compute_mode": "local",
    "input_kind": "shudian_json",
    "payload": "{\"fphm\":\"12345678\",\"fpdm\":\"044001900111\",\"kprq\":\"2024-01-15\"}"
  }' | jq .
```

使用文件避免转义：

```bash
jq -n --rawfile p payload.json '{compute_mode:"local",input_kind:"shudian_json",payload:$p}' \
  | curl -s -X POST http://localhost:8088/invoice/v1/parse \
    -H "Content-Type: application/json" \
    -d @- | jq .
```

### 数电票 XML（`input_kind`: `shudian_xml`）

`payload` 为 **整段 XML 字符串**。

```bash
curl -s -X POST http://localhost:8088/invoice/v1/parse \
  -H "Content-Type: application/json" \
  -d "{\"compute_mode\":\"local\",\"input_kind\":\"shudian_xml\",\"payload\":\"$(cat invoice.xml | sed 's/\"/\\\\\"/g' )\"}"
```

更推荐用 `jq` 或单独 `body.json` 组装请求体。

### 影像发票（`input_kind`: `image_base64`）

```bash
IMG_B64=$(base64 -i ./scan.jpg)
curl -s -X POST http://localhost:8088/invoice/v1/parse \
  -H "Content-Type: application/json" \
  -d "{\"input_kind\":\"image_base64\",\"payload\":\"${IMG_B64}\",\"lang\":\"ch\"}" | jq .
```

韩国小票建议显式传 `doc_type=kr_receipt`（并将 `lang` 设为 `korean`）：

```bash
IMG_B64=$(base64 -i ./kr-receipt.png)
curl -s -X POST http://localhost:8088/invoice/v1/parse \
  -H "Content-Type: application/json" \
  -d "{\"input_kind\":\"image_base64\",\"doc_type\":\"kr_receipt\",\"payload\":\"${IMG_B64}\",\"lang\":\"korean\"}" | jq .
```

`doc_type=kr_receipt` 时，`invoice.extra` 会固定包含以下键（未识别到时值为 `null` 或空数组）：

- `receipt_country`（固定 `KR`）
- `doc_type`（固定 `kr_receipt`）
- `merchant_name`
- `business_number`
- `owner_name`
- `phone`
- `address`
- `receipt_no`
- `approval_no`
- `terminal_no`
- `subtotal`
- `cash_paid`
- `change`
- `supply_amount`
- `vat_amount`
- `total_amount`
- `currency`（固定 `KRW`）
- `items`（韩国小票明细数组，元素含 `name/qty/unit_price/amount/raw_line`）
- `items_count`

### 远程解析（`compute_mode`: `remote`）

1. 配置：`INVOICE_REMOTE_BASE_URL`（必填）、`INVOICE_REMOTE_PARSE_PATH`（默认 `/v1/parse`）、可选 `INVOICE_REMOTE_API_KEY`。
2. 请求体中 `"compute_mode": "remote"`，或依赖环境变量 **`DEFAULT_INVOICE_COMPUTE_MODE`** = `remote`。

```bash
docker run -d -p 8088:8088 \
  -e DEFAULT_INVOICE_COMPUTE_MODE=remote \
  -e INVOICE_REMOTE_BASE_URL=https://your-parse-api.example.com \
  -e INVOICE_REMOTE_PARSE_PATH=/v1/parse \
  -e INVOICE_REMOTE_API_KEY=your_token \
  --name paddleocr-service paddleocr-service:latest
```

本服务将 **与下表同结构的 JSON** POST 到远端。远端若返回与下节一致的 **`InvoiceParseResponse` 形态**，会直接校验；否则会尝试读取 `invoice` 对象，并在 `remote_raw` 中保留少量元信息。

发票接口的 **HTTP 状态与 `detail` 取值** 见文末 **[错误码与 `detail` 列表](#错误码与-detail-列表)**。

### 发票响应结构（要点）

| 字段 | 类型 | 枚举 / 说明 |
|------|------|-------------|
| `success` | 布尔 | — |
| `compute_mode` | 字符串 | **`local`** \| **`remote`** |
| `source` | 字符串 | **`shudian`** \| **`ocr`** |
| `invoice` | 对象 | 见下 |
| `structuredFields` | 对象数组 | 前端可直接消费的标准字段列表（见下方示例） |
| `warnings` | 字符串数组 | — |
| `remote_raw` | 对象或 `null` | 仅 remote 时可能有内容 |

`invoice` 内为可空字符串字段：`invoice_code`、`invoice_number`、`issue_date`、`buyer_name`、`buyer_tax_id`、`seller_name`、`seller_tax_id`、`amount_without_tax`、`tax_amount`、`total_with_tax`、`remark`，以及 **`extra`** 对象（未映射键值、OCR 预览等）。

```json
{
  "success": true,
  "compute_mode": "local",
  "source": "shudian",
  "invoice": {
    "invoice_code": "...",
    "invoice_number": "...",
    "issue_date": "...",
    "buyer_name": null,
    "buyer_tax_id": null,
    "seller_name": null,
    "seller_tax_id": null,
    "amount_without_tax": null,
    "tax_amount": null,
    "total_with_tax": null,
    "remark": null,
    "extra": {}
  },
  "warnings": [],
  "remote_raw": null
}
```

`structuredFields`（示例，`doc_type=kr_receipt`）：

```json
[
  {"fieldCode":"extractEngine","labelZh":"抽取引擎","groupZh":"基本信息","value":"paddleocr-local","valueMeanZh":"PaddleOCR 本地规则抽取"},
  {"fieldCode":"country","labelZh":"国家/地区","groupZh":"基本信息","value":"KR","valueMeanZh":"韩国"},
  {"fieldCode":"language","labelZh":"语言","groupZh":"基本信息","value":"ko","valueMeanZh":"韩语"},
  {"fieldCode":"currency","labelZh":"币种","groupZh":"基本信息","value":"KRW","valueMeanZh":"韩元"},
  {"fieldCode":"invoiceNumber","labelZh":"发票/收据号码","groupZh":"票据信息","value":"2025102010000023","valueMeanZh":null},
  {"fieldCode":"invoiceDate","labelZh":"开票/交易日期","groupZh":"票据信息","value":"2025-10-20","valueMeanZh":null},
  {"fieldCode":"sellerName","labelZh":"销方/商户名称","groupZh":"交易方","value":"팔도밀방강남본점","valueMeanZh":null},
  {"fieldCode":"subtotalAmount","labelZh":"不含税金额（销售额/공급가）","groupZh":"金额信息","value":"58181","valueMeanZh":null},
  {"fieldCode":"taxAmount","labelZh":"税额（부가세/VAT 等）","groupZh":"金额信息","value":"5819","valueMeanZh":null},
  {"fieldCode":"totalAmount","labelZh":"价税合计","groupZh":"金额信息","value":"64000","valueMeanZh":null},
  {"fieldCode":"lineItemCount","labelZh":"明细行数","groupZh":"质量与风险","value":"2","valueMeanZh":null}
]
```

环境变量完整表见 [engineering.md](engineering.md#环境变量)。

---

## 错误码与 `detail` 列表

以下指 **HTTP 状态码** 与响应 JSON 中的 **`detail`** 字段（字符串，或 FastAPI 校验错误时的数组结构）。成功响应无统一 `detail` 字段。

### 请求体验证（所有 JSON 体接口）

| HTTP | 说明 |
|------|------|
| **422** | 请求 JSON 结构或类型不符合 OpenAPI / Pydantic 规则（如枚举写错、缺必填字段）。`detail` 为 FastAPI 默认的 **对象数组**（含 `loc`、`msg`、`type`），以 `/docs` 试调为准。 |

### OCR：`POST /ocr`、`/ocr/base64`、`/ocr/url`、`/ocr/batch`

| HTTP | `detail` 形式 | 触发条件 |
|------|----------------|----------|
| **400** | `无法解析图片文件` | 上传内容无法解码为图片（`/ocr`） |
| **400** | `无法解析 Base64 图片` | Base64 解码后无法解码为图片（`/ocr/base64`） |
| **400** | `URL 内容无法解码为图片` | URL 下载成功但内容无法按图片解码（`/ocr/url`） |
| **502** | `拉取 URL 失败: …` | 下载 `url` 失败（网络、4xx/5xx 等）（`/ocr/url`） |
| **500** | `OCR 识别失败: …` | 其它运行时异常；冒号后为异常信息（可能含 Paddle 栈） |

批量接口 `/ocr/batch`：单张失败时在该文件的 `results[].error` 中返回字符串，**整单 HTTP 仍为 200**，外层 `success: true`。

### 发票：`POST /invoice/v1/parse` 与 `POST /invoice/v1/parse/file`

| HTTP | `detail`（精确或前缀） | 触发条件 |
|------|-------------------------|----------|
| **400** | `image_too_large` | 影像 Base64 解码后超过 `INVOICE_LOCAL_IMAGE_MAX_BYTES` |
| **400** | `invalid_image` | 影像无法解码为图片 |
| **400** | `unsupported_input_kind` | 内部未识别的 `input_kind`（经 Pydantic 校验的正常请求不应出现） |
| **400** | `invalid_xml: …` | `shudian_xml` 的 `payload` 非合法 XML；冒号后为解析器信息 |
| **400** | `invalid_json: …` | `shudian_json` 的 `payload` 非合法 JSON 文本 |
| **400** | `remote_invalid_json_shape` | 远程返回体不是 JSON 对象 |
| **502** | `remote_http_<数字>` | 远程 HTTP 非 2xx，`<数字>` 为远端状态码，如 `remote_http_500` |
| **503** | `invoice_remote_base_url_not_set` | `compute_mode` 为 `remote`（或默认 `remote`）但未配置 `INVOICE_REMOTE_BASE_URL` |
| **503** | `remote_unreachable` | 连接远程失败（DNS、超时、拒连等） |
| **500** | `invoice_parse_failed: …` | 未归类为 `ValueError` 的其它异常；冒号后为异常信息 |

发票请求体字段非法、枚举越界等同样可能返回 **422**（见上节）。

# PaddleOCR Service

基于 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 与 [FastAPI](https://fastapi.tiangolo.com/) 的 HTTP OCR 服务，支持 Docker 分层构建：基础镜像固定依赖与模型，应用镜像仅包含业务代码，便于频繁迭代。

## 功能概览

- 图片 OCR：文件上传、Base64、批量图片
- 多语言引擎按需加载（中文、英文、日韩德法等）
- 健康检查与接口文档（Swagger）

默认监听端口：**8088**。

## 环境要求

- macOS（或任意支持 Docker 的系统）
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 已安装并运行

## 项目结构

| 文件 | 说明 |
|------|------|
| `Dockerfile.base` | 基础镜像：系统依赖、`pip` 安装、预下载中文 OCR 模型 |
| `Dockerfile` | 应用镜像：基于基础镜像，复制 `app.py`、`start.sh` |
| `build-base.sh` | 构建基础镜像 |
| `build-app.sh` | 构建应用镜像（依赖本地已有基础镜像） |
| `app.py` | FastAPI 服务入口 |
| `start.sh` | 容器内启动脚本 |
| `requirements.txt` | Python 依赖锁定 |

## 首次构建与运行

在项目根目录执行：

```bash
cd /path/to/paddleocr-service

# 1. 构建基础镜像（耗时较长，首次约数分钟至十几分钟）
chmod +x build-base.sh build-app.sh   # 若尚未可执行
./build-base.sh

# 2. 构建应用镜像（通常很快）
./build-app.sh

# 3. 启动容器
docker run -d -p 8088:8088 --name paddleocr-service paddleocr-service:latest

# 4. 查看日志
docker logs -f paddleocr-service
```

浏览器打开：<http://localhost:8088/docs> 查看交互式 API 文档。

根路径 <http://localhost:8088/> 会返回服务信息摘要。

## 日常开发：只改业务代码时

修改 `app.py` 或 `start.sh` 后，只需重建应用镜像并重启容器：

```bash
./build-app.sh
docker rm -f paddleocr-service
docker run -d -p 8088:8088 --name paddleocr-service paddleocr-service:latest
```

无需重新执行 `./build-base.sh`，除非依赖或基础环境有变。

## 何时需要重建基础镜像

在以下情况执行 `./build-base.sh`，然后再 `./build-app.sh`：

- 修改了 `requirements.txt`（升级 Paddle、FastAPI 等）
- 修改了 `Dockerfile.base` 中的系统包或构建步骤

基础镜像构建阶段会尝试预下载 PaddleOCR 中文模型；若网络失败，构建仍会继续（`|| true`），模型可能在容器首次实际调用对应语言时下载。

## 镜像标签（可选）

```bash
# 基础镜像带版本标签
./build-base.sh v1.0.0

# 应用镜像指定标签，且指定依赖的基础镜像标签
./build-app.sh v1.2.0 v1.0.0
```

第二个参数为基础镜像 tag，需与 `paddleocr-service-base:<tag>` 一致。

## 常用 Docker 命令

```bash
docker stop paddleocr-service    # 停止
docker start paddleocr-service   # 启动已有容器
docker logs -f paddleocr-service # 跟随日志
```

## API 摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务信息摘要 |
| GET | `/health` | 健康检查 |
| GET | `/languages` | 支持的语言 |
| POST | `/ocr` | 上传图片文件 OCR |
| POST | `/ocr/base64` | Base64 图片 OCR |
| POST | `/ocr/batch` | 批量图片 OCR |

具体参数与响应以 `/docs` 为准。

## 健康检查

```bash
curl http://localhost:8088/health
```

返回示例：

```json
{"status": "healthy", "engines_loaded": []}
```

完成 OCR 调用后，`engines_loaded` 会包含已加载的语言，例如 `ch`。

## 调用示例

下面的命令在项目根目录执行，将 `./sample.jpg` 替换为你的本地图片路径。

### 1. 单图 OCR（文件上传）

```bash
curl -X POST http://localhost:8088/ocr \
  -F "file=@./sample.jpg" \
  -F "lang=ch" \
  -F "return_text_only=false"
```

只想拿到识别文本（不要坐标）：

```bash
curl -X POST http://localhost:8088/ocr \
  -F "file=@./sample.jpg" \
  -F "lang=ch" \
  -F "return_text_only=true"
```

提取「整段拼接文本」字段（需要 `jq`）：

```bash
curl -s -X POST http://localhost:8088/ocr \
  -F "file=@./sample.jpg" \
  -F "lang=ch" | jq -r '.full_text'
```

### 2. Base64 OCR

```bash
IMG_B64=$(base64 -i ./sample.jpg)

curl -X POST http://localhost:8088/ocr/base64 \
  -H "Content-Type: application/json" \
  -d "{\"image_base64\": \"${IMG_B64}\", \"lang\": \"ch\", \"return_text_only\": true}"
```

### 3. 批量 OCR

```bash
curl -X POST http://localhost:8088/ocr/batch \
  -F "files=@./sample-1.jpg" \
  -F "files=@./sample-2.png" \
  -F "lang=ch" \
  -F "return_text_only=true"
```

### 4. Python 调用示例

```python
import requests

url = "http://localhost:8088/ocr"
with open("sample.jpg", "rb") as f:
    resp = requests.post(
        url,
        files={"file": f},
        data={"lang": "ch", "return_text_only": "true"},
    )
print(resp.json()["full_text"])
```

返回结构（节选）：

```json
{
  "success": true,
  "language": "ch",
  "text_count": 12,
  "results": [
    {"text": "发票代码", "confidence": 0.99, "bbox": {"xmin": 30, "ymin": 40, "xmax": 200, "ymax": 70}}
  ],
  "full_text": "发票代码\n..."
}
```

## 本地开发（非 Docker）

若需在宿主机直接运行（需自行安装与镜像一致的 Python 与系统依赖）：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 许可证

项目内第三方库（PaddleOCR、FastAPI 等）遵循各自开源许可证。

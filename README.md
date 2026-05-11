# PaddleOCR Service

基于 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 与 [FastAPI](https://fastapi.tiangolo.com/) 的 HTTP 服务：通用 OCR、发票结构化（数电票 XML/JSON、影像 OCR+规则）、可选转发远程解析。Docker 分层构建（基础镜像固定依赖与模型，应用镜像仅业务代码）。

## 功能概览

- **OCR**：上传图片、Base64、图片 URL、批量
- **发票**：`POST /invoice/v1/parse`；数电直解析；影像走本机 PaddleOCR + 规则；`compute_mode` 支持 `local` / `remote`
- **多语言 OCR**：中/英/日韩德法等按需加载
- **文档**：交互式 OpenAPI — `http://<host>:8088/docs`

默认端口：**8088**。

## 环境要求

- 任意支持 Docker 的主机（文档示例以 macOS + [Docker Desktop](https://www.docker.com/products/docker-desktop/) 为参考）

## 快速开始

```bash
cd /path/to/paddleocr-service
chmod +x build-base.sh build-app.sh   # 若需要
./build-base.sh
./build-app.sh
docker run -d -p 8088:8088 --name paddleocr-service paddleocr-service:latest
```

**逐步跟着做（含每步 curl）**：[docs/example.md](docs/example.md)。

浏览器打开：<http://localhost:8088/docs>。日常只改业务代码时：`./build-app.sh` 后重建容器即可。

**Docker 构建与镜像分层**（脚本参数、何时重建 base、运行与排障）见 **[docs/docker-build.md](docs/docker-build.md)**。

## 详细文档

| 文档 | 内容 |
|------|------|
| [docs/README.md](docs/README.md) | 文档索引与导航 |
| [docs/example.md](docs/example.md) | **从零开始：构建 → 容器运行 → curl 示例（逐步命令）** |
| [docs/docker-build.md](docs/docker-build.md) | **Docker 分层构建、脚本、运行与排障（完整说明）** |
| [docs/api.md](docs/api.md) | 接口说明、请求/响应要点、**curl / Python 调用示例** |
| [docs/engineering.md](docs/engineering.md) | **工程结构**、模块职责、环境变量、扩展点 |

## 许可证

项目内第三方库（PaddleOCR、FastAPI 等）遵循各自开源许可证。

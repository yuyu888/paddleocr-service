# PaddleOCR Service

基于 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 与 [FastAPI](https://fastapi.tiangolo.com/) 的 HTTP 服务：通用 OCR、发票结构化（数电票 XML/JSON、影像 OCR+规则）、可选转发远程解析。Docker 分层构建（基础镜像固定依赖与模型，应用镜像仅业务代码）。

## 功能概览

- **OCR**：上传图片、Base64、图片 URL、批量
- **发票**：`POST /invoice/v1/parse`；数电直解析；影像走本机 PaddleOCR + 规则；`compute_mode` 支持 `local` / `remote`
- **多语言 OCR**：中/英/日韩德法等按需加载
- **文档**：交互式 OpenAPI — `http://<host>:8088/docs`

默认端口：**8088**。

默认采用 CPU 推理；如需 GPU 推理，可通过环境变量 `OCR_USE_GPU=true` 开启（前提：镜像与宿主机已具备 CUDA/cuDNN 与 `paddlepaddle-gpu` 运行条件）。

## 环境要求

- 选型建议（在成本、速度、并发之间权衡）：

| 对比维度 | CPU 路线 | GPU 路线 |
|------|------|------|
| 硬件成本 | 低，现有服务器通常可直接部署 | 高，需要 NVIDIA GPU 与对应驱动栈 |
| 处理速度 | 较慢（参考：10 页复杂 PDF 约 3-5 分钟） | 显著更快（同任务约 20-40 秒，约 5-10 倍） |
| 并发能力 | 偏弱，适合低到中并发 | 偏强，适合高并发与实时场景 |
| 显存/内存 | 主要消耗系统内存（参考约 4 GB 可起步） | 主要消耗显存（基础约 2.4 GB，复杂任务峰值可到 6 GB） |
| 环境配置复杂度 | 简单：安装 CPU 版 `paddlepaddle` 即可 | 较复杂：需匹配 CUDA、cuDNN、驱动与 `paddlepaddle-gpu` |
| 硬件生态 | 通用 X86/ARM 平台 | 主流为 NVIDIA；其他加速硬件需额外适配方案 |
| 操作系统版本建议 | Linux：Ubuntu 22.04+ / Debian 12+ / CentOS Stream 9+ | Linux：Ubuntu 22.04 LTS 或 Debian 12（需安装 NVIDIA Driver + NVIDIA Container Toolkit） |
| 服务器配置建议 | 4 vCPU / 8 GB RAM 起步（中等并发），SSD >= 30 GB | 8 vCPU / 16 GB RAM 起步，NVIDIA T4（16 GB）或更高，SSD >= 50 GB |

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

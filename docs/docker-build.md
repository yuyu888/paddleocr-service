# Docker 构建与运行说明

本文说明本仓库 **两层镜像** 的职责、构建命令、参数含义、与日常运维的关系。构建需在**项目根目录**执行，且本机已安装并启动 [Docker](https://docs.docker.com/get-docker/)（如 Docker Desktop）。

---

## 1. 为什么拆成两个镜像

| 层级 | 镜像名（默认 tag） | Dockerfile | 特点 |
|------|-------------------|------------|------|
| **基础镜像** | `paddleocr-service-base:latest` | `Dockerfile.base` | **重、慢**：系统 apt 包、`pip install` 全量依赖、可选预拉 PaddleOCR 中文模型。依赖或系统库变更时才需要重做。 |
| **应用镜像** | `paddleocr-service:latest` | `Dockerfile` | **轻、快**：在已有基础镜像之上只 `COPY app/` 与 `start.sh`。只改业务代码时**只重建这一层**即可。 |

这样日常迭代不必反复安装 Paddle 与大量 Python 包，缩短构建时间。

---

## 2. 涉及文件一览

| 文件 | 作用 |
|------|------|
| `Dockerfile.base` | 定义基础镜像：Python 3.10 slim、系统库、`requirements.txt`、`pip` 清华源、预初始化 PaddleOCR（中文）。 |
| `Dockerfile` | 定义应用镜像：`ARG BASE_IMAGE` 指定依赖的基础镜像名，复制 `app/`、`start.sh`，暴露 8088。 |
| `build-base.sh` | 封装 `docker build -f Dockerfile.base`，产出 `paddleocr-service-base:<tag>`。 |
| `build-app.sh` | 检查本地是否存在指定基础镜像，再 `docker build` 应用镜像，通过 `--build-arg BASE_IMAGE=...` 传入基础镜像。 |
| `requirements.txt` | 被 `Dockerfile.base` 复制进镜像并执行 `pip install`；**改它会改变基础镜像层缓存**，通常需重建基础镜像。 |

---

## 3. 镜像命名与标签（tag）

- **基础镜像**：`paddleocr-service-base:<tag>`，`tag` 默认为 `latest`。
- **应用镜像**：`paddleocr-service:<tag>`，`tag` 默认为 `latest`。

标签用于版本管理（例如基础环境与业务发版不同步时，用不同 tag 对齐）。

---

## 4. 构建命令（脚本）

### 4.1 构建基础镜像：`build-base.sh`

```text
./build-base.sh [tag]
```

- **省略参数**：等价于 `./build-base.sh latest`，生成 `paddleocr-service-base:latest`。
- **指定 tag**：例如 `./build-base.sh v1.0.0`，生成 `paddleocr-service-base:v1.0.0`。

脚本内部等价于（在项目根目录；**默认**传入 `APT_USE_MIRROR=1`，见下文 apt 源说明）：

```bash
docker build -f Dockerfile.base \
  --build-arg "APT_USE_MIRROR=${APT_USE_MIRROR:-1}" \
  -t "paddleocr-service-base:${TAG}" .
```

**基础镜像里大致做了什么**（对应 `Dockerfile.base`）：

1. 基于 `python:3.10-slim`，设置 `WORKDIR /app` 与常用环境变量。
2. **（默认）** 将 Debian `apt` 源中的 `deb.debian.org` / `security.debian.org` 替换为 **清华大学开源镜像站**（HTTPS），避免中国大陆直连官方源超时；`pip` 仍使用清华 PyPI（见下一步）。
3. `apt-get install`：OpenCV / Paddle 运行常见的图形与数学库（如 `libgl1`、`libglib2.0-0` 等）。
4. 复制 `requirements.txt` 并 `pip install -r`（默认使用清华 PyPI 镜像加速）。
5. 执行一段 Python 预初始化中文 `PaddleOCR`（用于触发模型下载）。若网络失败，构建**不会失败**（命令末尾为 `|| true`），模型可能在**容器首次真正跑 OCR 时**再下载。

**海外或官方源可用时**（不需要国内 apt 镜像）：

```bash
APT_USE_MIRROR=0 ./build-base.sh
# 或
docker build -f Dockerfile.base --build-arg APT_USE_MIRROR=0 -t paddleocr-service-base:latest .
```

### 4.2 构建应用镜像：`build-app.sh`

```text
./build-app.sh [应用tag] [基础镜像tag]
```

- **两个参数都省略**：`./build-app.sh`  
  - 应用镜像：`paddleocr-service:latest`  
  - 使用的基础镜像：`paddleocr-service-base:latest`
- **只改应用 tag**：`./build-app.sh v1.2.0`  
  - 应用：`paddleocr-service:v1.2.0`  
  - 基础仍为：`paddleocr-service-base:latest`
- **同时指定应用与基础 tag**：`./build-app.sh v1.2.0 v1.0.0`  
  - 应用：`paddleocr-service:v1.2.0`  
  - 基础：`paddleocr-service-base:v1.0.0`（**该镜像必须已存在于本机 `docker images`**，否则脚本退出并提示先执行 `build-base.sh`）

脚本会检查 `docker image inspect "${BASE_IMAGE}"` 是否存在；内部构建命令为：

```bash
docker build --build-arg BASE_IMAGE="${BASE_IMAGE}" -t "${IMAGE_NAME}" .
```

`Dockerfile` 中的 `FROM ${BASE_IMAGE}` 即使用上述 build-arg。

---

## 5. 推荐操作顺序

### 5.1 第一次在本机构建

```bash
cd /path/to/paddleocr-service
chmod +x build-base.sh build-app.sh   # 若尚未可执行
./build-base.sh          # 耗时较长，耐心等完成
./build-app.sh           # 通常很快
```

### 5.2 日常只修改 `app/` 或 `start.sh`

**不需要**重新执行 `./build-base.sh`（除非依赖或 `Dockerfile.base` 有变）：

```bash
./build-app.sh
docker rm -f paddleocr-service 2>/dev/null || true
docker run -d -p 8088:8088 --name paddleocr-service paddleocr-service:latest
```

### 5.3 必须重新构建基础镜像的情况

在以下任一情况发生后，应执行 **`./build-base.sh`**（必要时带新 tag），再 **`./build-app.sh`**：

- 修改了 **`requirements.txt`**（升级 Paddle、新增 `httpx` 等）。
- 修改了 **`Dockerfile.base`**（系统包、Python 版本、预下载逻辑等）。

---

## 6. 运行容器

最简运行（默认 `latest` 应用镜像）：

```bash
docker run -d -p 8088:8088 --name paddleocr-service paddleocr-service:latest
```

查看日志：

```bash
docker logs -f paddleocr-service
```

发票远程模式等环境变量可在 `docker run` 时传入，例如：

```bash
docker run -d -p 8088:8088 \
  -e DEFAULT_INVOICE_COMPUTE_MODE=remote \
  -e INVOICE_REMOTE_BASE_URL=https://example.com \
  --name paddleocr-service paddleocr-service:latest
```

完整变量表见 [engineering.md](engineering.md#环境变量)。

---

## 7. 与「自定义基础镜像名 / 私服」的关系

- 应用构建**完全依赖** `BASE_IMAGE` build-arg，默认写死在脚本里的名字是 `paddleocr-service-base:<base_tag>`。
- 若你从私有 Registry 拉取已打好的基础镜像，只要本地 tag 与 `build-app.sh` 第二个参数一致即可；或自行执行：

```bash
docker build --build-arg BASE_IMAGE=your-registry/paddle-base:1.0 -t paddleocr-service:latest .
```

---

## 8. 常见问题

**Q：`apt-get` 报 `Unable to connect to deb.debian.org`？**  
A：多为网络环境无法直连 Debian 官方源。本仓库 **`Dockerfile.base` 默认**将 apt 换为 **清华镜像**（`APT_USE_MIRROR=1`）。若仍失败，检查本机到 `mirrors.tuna.tsinghua.edu.cn` 的访问；或在能访问官方源的环境使用 `APT_USE_MIRROR=0 ./build-base.sh` 构建。

**Q：`./build-app.sh` 提示未找到基础镜像？**  
A：先在同一台机器执行 `./build-base.sh`（或 `./build-base.sh <与第二个参数一致的 tag>`），确认 `docker images | grep paddleocr-service-base` 有对应条目。

**Q：容器里第一次 OCR 很慢或超时？**  
A：可能是基础镜像构建时模型预下载未成功（`|| true`），首次运行会下载模型到容器内，属预期现象。网络稳定时可重建基础镜像并观察构建日志。

**Q：能否只用一份 Dockerfile？**  
A：可以，但会失去「业务代码快速重建」的优势；当前仓库刻意采用两层以优化迭代体验。

---

## 9. 相关文档

- 从零逐步构建与 curl 验证：[example.md](example.md)
- 接口与调用示例：[api.md](api.md)
- 代码目录与扩展点：[engineering.md](engineering.md)

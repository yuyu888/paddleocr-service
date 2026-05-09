#!/bin/bash
# 构建 PaddleOCR 服务的应用镜像（基于已构建好的基础镜像）
# 用法: ./build-app.sh [tag] [base_tag]
# 示例: ./build-app.sh
#       ./build-app.sh v1.2.0
#       ./build-app.sh v1.2.0 v1.0.0

set -e

TAG="${1:-latest}"
BASE_TAG="${2:-latest}"
IMAGE_NAME="paddleocr-service-v3:${TAG}"
BASE_IMAGE="paddleocr-service-base:${BASE_TAG}"

cd "$(dirname "$0")"

if ! docker image inspect "${BASE_IMAGE}" >/dev/null 2>&1; then
    echo "==> 未找到基础镜像 ${BASE_IMAGE}，请先执行 ./build-base.sh" >&2
    exit 1
fi

echo "==> 开始构建应用镜像: ${IMAGE_NAME} (基于 ${BASE_IMAGE})"

docker build --build-arg BASE_IMAGE="${BASE_IMAGE}" -t "${IMAGE_NAME}" .

echo "==> 应用镜像构建完成: ${IMAGE_NAME}"
docker images "${IMAGE_NAME}"

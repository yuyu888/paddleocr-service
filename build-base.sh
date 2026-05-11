#!/bin/bash
# 构建 PaddleOCR 服务的基础镜像
# 用法: ./build-base.sh [tag]
# 示例: ./build-base.sh
#       ./build-base.sh v1.0.0
#
# 海外网络无需替换 Debian apt 源时：
#   APT_USE_MIRROR=0 ./build-base.sh

set -e

TAG="${1:-latest}"
IMAGE_NAME="paddleocr-service-base:${TAG}"

cd "$(dirname "$0")"

echo "==> 开始构建基础镜像: ${IMAGE_NAME}"

docker build -f Dockerfile.base \
  --build-arg "APT_USE_MIRROR=${APT_USE_MIRROR:-1}" \
  -t "${IMAGE_NAME}" .

echo "==> 基础镜像构建完成: ${IMAGE_NAME}"
docker images "${IMAGE_NAME}"

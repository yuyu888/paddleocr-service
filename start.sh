#!/bin/bash

# 启动脚本
echo "========================================="
echo "PaddleOCR Service Starting..."
echo "========================================="

# 设置环境变量
export PYTHONUNBUFFERED=1

# 启动服务
python app.py

# 保持容器运行
tail -f /dev/null
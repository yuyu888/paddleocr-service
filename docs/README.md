# 文档索引

本目录存放设计与使用细节；根目录 [README.md](../README.md) 仅保留概览与快速开始。

| 文档 | 说明 |
|------|------|
| [example.md](example.md) | **从零开始：依次构建 → 运行容器 → curl 验证（逐步命令）** |
| [docker-build.md](docker-build.md) | **Docker 分层构建、脚本参数、何时重建基础/应用镜像、运行与排障** |
| [api.md](api.md) | HTTP 接口、字段说明、curl / Python 示例、常见响应形态 |
| [engineering.md](engineering.md) | 代码与目录结构、环境变量、发票流水线、扩展点（构建细节以 docker-build 为准） |

建议：第一次上手先跟 **[example.md](example.md)**；部署细节看 **docker-build.md**；联调接口看 **api.md**。

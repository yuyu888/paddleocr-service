# 构建、运行与 curl 示例

在项目**仓库根目录**执行（路径自行替换）。

## 1. 构建镜像（分两步）

```bash
chmod +x build-base.sh build-app.sh   # 若尚未可执行

./build-base.sh    # ① 基础镜像 paddleocr-service-base:latest（慢）
./build-app.sh     # ② 应用镜像 paddleocr-service:latest（快）
```

## 2. 启动容器

若本机已有同名容器，直接 `docker run` 会失败；先删再启可避免名称冲突（无同名容器时 `rm` 可忽略）。

```bash
docker rm -f paddleocr-service 2>/dev/null || true
docker run -d --name paddleocr-service -p 8088:8088 paddleocr-service:latest
```

## 3. 查日志

宿主机直接看标准输出（推荐）：

```bash
docker logs paddleocr-service
docker logs -f paddleocr-service   # 持续跟踪，Ctrl+C 退出
```

进入容器（一般无单独日志文件；应用日志仍以上述 `docker logs` 为准）：

```bash
docker exec -it paddleocr-service /bin/bash
# 或: docker exec -it paddleocr-service sh
```

## 4. curl 调接口

宿主机执行（无 `jq` 则去掉 `| jq .`）：

```bash
curl -s http://127.0.0.1:8088/health | jq .

curl -s -X POST http://127.0.0.1:8088/ocr \
  -F "file=@/path/to/sample.jpg" -F "lang=ch" -F "return_text_only=true" | jq .

curl -s -X POST http://127.0.0.1:8088/invoice/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"compute_mode":"local","input_kind":"shudian_json","payload":"{\"fphm\":\"12345678\",\"fpdm\":\"044001900111\"}"}' | jq .
```

更多参数见 [api.md](api.md)，构建说明见 [docker-build.md](docker-build.md)。

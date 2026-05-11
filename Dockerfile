# 应用镜像：基于已构建好的基础镜像，仅包含业务代码
# 修改 app/ 或 start.sh 后只需重建本镜像，构建时间极短
ARG BASE_IMAGE=paddleocr-service-base:latest

FROM ${BASE_IMAGE}

WORKDIR /app

COPY app ./app
COPY start.sh .

RUN chmod +x start.sh

EXPOSE 8088

CMD ["./start.sh"]

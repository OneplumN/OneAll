# Probe Dockerfile - 多阶段构建

# 阶段1: 构建
FROM golang:1.21-alpine AS builder

WORKDIR /app

# 安装构建依赖
RUN apk add --no-cache git ca-certificates

# 复制 go.mod 和 go.sum
COPY go.mod go.sum* ./

# 下载依赖
RUN go mod download

# 复制源代码
COPY . .

# 构建二进制文件
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o probe ./cmd/probe

# 阶段2: 生产镜像
FROM alpine:3.19

# 安装 CA 证书（用于 HTTPS 请求）
RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

# 从构建阶段复制二进制文件
COPY --from=builder /app/probe .

# 创建数据目录
RUN mkdir -p /var/lib/oneall-probe/{cache,state,updates}

# 暴露指标端口
EXPOSE 9100

# 默认命令
ENTRYPOINT ["/app/probe"]
CMD ["--config", "/app/config.yaml"]

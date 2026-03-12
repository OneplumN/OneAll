#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROTO_FILE="${ROOT_DIR}/proto/probes/v1/gateway.proto"

if ! command -v protoc >/dev/null 2>&1; then
  echo "protoc 未安装，请先安装 protobuf 编译器" >&2
  exit 1
fi

if ! command -v protoc-gen-go >/dev/null 2>&1; then
  echo "protoc-gen-go 未安装，请先执行: go install google.golang.org/protobuf/cmd/protoc-gen-go@latest" >&2
  exit 1
fi

if ! command -v protoc-gen-go-grpc >/dev/null 2>&1; then
  echo "protoc-gen-go-grpc 未安装，请先执行: go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest" >&2
  exit 1
fi

protoc \
  -I "${ROOT_DIR}/proto" \
  --go_out="${ROOT_DIR}/probes/internal" \
  --go_opt=paths=source_relative \
  --go-grpc_out="${ROOT_DIR}/probes/internal" \
  --go-grpc_opt=paths=source_relative \
  "${PROTO_FILE}"

PYTHON_BIN="${ROOT_DIR}/backend/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

"${PYTHON_BIN}" -m grpc_tools.protoc \
  -I "${ROOT_DIR}/proto" \
  --python_out="${ROOT_DIR}/backend/src" \
  --grpc_python_out="${ROOT_DIR}/backend/src" \
  "${PROTO_FILE}"

echo "proto 代码生成完成"


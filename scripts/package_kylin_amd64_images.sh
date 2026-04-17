#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
git_sha="$(git -C "$repo_root" rev-parse --short HEAD)"
tag_suffix="${git_sha}-linux-amd64"
builder="${DOCKER_BUILDX_BUILDER:-desktop-linux}"
# docker.aityp.com 当前展示的 Docker Hub 镜像代理规则为：
# swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/<repo>
aityp_mirror_prefix="${AITYP_MIRROR_PREFIX:-swr.cn-north-4.myhuaweicloud.com/ddn-k8s}"
output_root="${1:-$repo_root/.tmp/docker-export/oneall-kylin-x86-${git_sha}}"

backend_image="oneall/backend:${tag_suffix}"
frontend_image="oneall/frontend:${tag_suffix}"
probe_image="oneall/probe:${tag_suffix}"

dependency_images=(
  "mysql:8.0"
  "timescale/timescaledb:2.12.0-pg14"
  "redis:7.2-alpine"
)

build_base_images=(
  "python:3.11-slim"
  "node:20-alpine"
  "nginx:alpine"
  "golang:1.21-alpine"
  "alpine:3.19"
)

app_images=(
  "$backend_image"
  "$frontend_image"
  "$probe_image"
)

all_images=(
  "${dependency_images[@]}"
  "${app_images[@]}"
)

manifest_path="${output_root}/image-manifest.txt"
bundle_tar="${output_root}/oneall-images-${tag_suffix}.tar"

mkdir -p "$output_root"

build_image() {
  local image="$1"
  local dockerfile="$2"
  local context="$3"

  docker buildx build \
    --builder "$builder" \
    --platform linux/amd64 \
    --pull=false \
    --load \
    --tag "$image" \
    --file "$dockerfile" \
    "$context"
}

inspect_image() {
  local image="$1"
  docker image inspect "$image" --format '{{.RepoTags}} {{.Os}}/{{.Architecture}}'
}

canonical_image_ref() {
  local image="$1"
  local first_segment="${image%%/*}"

  if [[ "$image" != */* ]]; then
    echo "docker.io/library/${image}"
    return
  fi

  if [[ "$first_segment" == *.* || "$first_segment" == *:* || "$first_segment" == "localhost" ]]; then
    echo "$image"
    return
  fi

  echo "docker.io/${image}"
}

mirror_pull_tag() {
  local image="$1"
  local canonical_image
  local mirror_image

  canonical_image="$(canonical_image_ref "$image")"
  mirror_image="${aityp_mirror_prefix}/${canonical_image}"
  docker pull --platform linux/amd64 "$mirror_image"
  docker tag "$mirror_image" "$image"
}

echo "Pulling linux/amd64 build base images via docker.aityp mapping (${aityp_mirror_prefix})..."
for image in "${build_base_images[@]}"; do
  mirror_pull_tag "$image"
done

echo "Building linux/amd64 application images..."
build_image "$backend_image" "$repo_root/infra/backend.Dockerfile" "$repo_root/backend"
build_image "$frontend_image" "$repo_root/infra/frontend.Dockerfile" "$repo_root"
build_image "$probe_image" "$repo_root/infra/probe.Dockerfile" "$repo_root/probes"

echo "Pulling linux/amd64 dependency images via docker.aityp mapping (${aityp_mirror_prefix})..."
for image in "${dependency_images[@]}"; do
  mirror_pull_tag "$image"
done

echo "Validating image architectures..."
{
  echo "ONEALL_BACKEND_IMAGE=${backend_image}"
  echo "ONEALL_FRONTEND_IMAGE=${frontend_image}"
  echo "ONEALL_PROBE_IMAGE=${probe_image}"
  echo
  for image in "${all_images[@]}"; do
    inspect_image "$image"
  done
} > "$manifest_path"

for image in "${all_images[@]}"; do
  arch="$(docker image inspect "$image" --format '{{.Os}}/{{.Architecture}}')"
  if [[ "$arch" != "linux/amd64" ]]; then
    echo "Unexpected architecture for $image: $arch" >&2
    exit 1
  fi
done

echo "Copying deployment assets..."
cp "$repo_root/infra/docker-compose.offline.yml" "$output_root/docker-compose.offline.yml"
cp "$repo_root/.env.example" "$output_root/.env.example"
mkdir -p "$output_root/probe" "$output_root/timescale"
cp "$repo_root/infra/probe/probe-config.yaml" "$output_root/probe/probe-config.yaml"
cp "$repo_root/infra/timescale/init-timescale.sql" "$output_root/timescale/init-timescale.sql"

cat > "$output_root/offline.env" <<EOF
ONEALL_BACKEND_IMAGE=${backend_image}
ONEALL_FRONTEND_IMAGE=${frontend_image}
ONEALL_PROBE_IMAGE=${probe_image}
EOF

cat > "$output_root/LOAD_AND_RUN.md" <<EOF
# OneAll Kylin x86 Offline Bundle

## 1. Import images

\`\`\`bash
docker load -i $(basename "$bundle_tar")
\`\`\`

## 2. Prepare env

\`\`\`bash
cp .env.example .env
cp offline.env .env.images
\`\`\`

## 3. Start core services

\`\`\`bash
docker compose --env-file .env --env-file .env.images -f docker-compose.offline.yml up -d
\`\`\`

## 4. Start probe when needed

\`\`\`bash
docker compose --env-file .env --env-file .env.images -f docker-compose.offline.yml --profile probe up -d
\`\`\`
EOF

echo "Saving images to ${bundle_tar}..."
docker save -o "$bundle_tar" "${all_images[@]}"

echo "Bundle created at: $output_root"
echo "Images tar: $bundle_tar"

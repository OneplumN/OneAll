#!/usr/bin/env bash
set -euo pipefail

VERSION=${1:-}
if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 <semver-tag>"
  exit 1
fi

echo "[OneAll] Running tests before release $VERSION"
pushd backend >/dev/null
pipenv run pytest
popd >/dev/null

pushd frontend >/dev/null
pnpm run test
popd >/dev/null

echo "[OneAll] Creating git tag $VERSION"
git tag -a "$VERSION" -m "Release $VERSION"
git push origin "$VERSION"

echo "[OneAll] Release $VERSION prepared"

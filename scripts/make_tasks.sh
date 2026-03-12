#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<USAGE
Usage: $(basename "$0") <task>

Tasks:
  backend-install     Install backend dependencies with pipenv
  backend-migrate     Run Django migrations
  backend-run         Start Django development server
  celery-worker       Start Celery worker
  celery-beat         Start Celery beat scheduler
  frontend-install    Install frontend dependencies with pnpm
  frontend-dev        Start Vite development server
  probes-install      Install probe dependencies
  probes-run          Run probe agent with default config
USAGE
}

backend_install() {
  cd "$ROOT_DIR/backend"
  pipenv install --skip-lock --python 3.11
  pipenv run pip install -r requirements.txt
}

backend_migrate() {
  cd "$ROOT_DIR/backend"
  pipenv run python src/manage.py migrate
}

backend_run() {
  cd "$ROOT_DIR/backend"
  pipenv run python src/manage.py runserver 0.0.0.0:8000
}

celery_worker() {
  cd "$ROOT_DIR/backend"
  pipenv run celery -A core.celery_app worker -l info
}

celery_beat() {
  cd "$ROOT_DIR/backend"
  pipenv run celery -A core.celery_app beat -l info
}

frontend_install() {
  cd "$ROOT_DIR/frontend"
  pnpm install
}

frontend_dev() {
  cd "$ROOT_DIR/frontend"
  pnpm run dev
}

probes_install() {
  cd "$ROOT_DIR/probes"
  pipenv install --python 3.11
  pipenv run pip install -e .
}

probes_run() {
  cd "$ROOT_DIR/probes"
  pipenv run python src/agent/main.py --config configs/local.yaml
}

main() {
  local task="${1:-}";
  if [[ -z "$task" ]]; then
    usage
    exit 1
  fi

  case "$task" in
    backend-install) backend_install ;;
    backend-migrate) backend_migrate ;;
    backend-run) backend_run ;;
    celery-worker) celery_worker ;;
    celery-beat) celery_beat ;;
    frontend-install) frontend_install ;;
    frontend-dev) frontend_dev ;;
    probes-install) probes_install ;;
    probes-run) probes_run ;;
    *)
      echo "Unknown task: $task" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"

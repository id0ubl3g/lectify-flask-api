#!/bin/bash

set -e

PY_VERSIONS="3.13 3.12"

find_python() {
  for v in $PY_VERSIONS; do
    if command -v "python$v" >/dev/null 2>&1; then
      command -v "python$v"
      return 0
    fi
  done

  if command -v uv >/dev/null 2>&1; then
    set -- $PY_VERSIONS
    uv python install "$1" >&2
    uv python find "$1"
    return 0
  fi

  return 1
}

sudo apt update
sudo apt install -y libffi-dev python3-dev python3-venv build-essential ffmpeg

PYTHON=$(find_python) || {
  echo "No supported Python found (need one of: $PY_VERSIONS)." >&2
  echo "Install one, e.g.: curl -LsSf https://astral.sh/uv/install.sh | sh && uv python install 3.13" >&2
  exit 1
}

echo "Using interpreter: $PYTHON ($("$PYTHON" -V))"

if [ -d ".venv" ]; then
  CURRENT=$(.venv/bin/python -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "unknown")
  WANTED=$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
  if [ "$CURRENT" != "$WANTED" ]; then
    echo "Existing .venv is Python $CURRENT, recreating with $WANTED..."
    rm -rf .venv
  fi
fi

if [ ! -d ".venv" ]; then
  "$PYTHON" -m venv .venv
fi

source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install --only-binary=:all: -r requirements.txt
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.hermes/skills"

mkdir -p "$DEST"

link_skill() {
  local name="$1"
  local src="$ROOT/skills/$name"
  local dst="$DEST/$name"

  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    echo "ERROR: $dst already exists and is not a symlink."
    echo "Move it away manually before linking."
    exit 1
  fi

  ln -sfn "$src" "$dst"
  echo "linked: $dst -> $src"
}

link_skill dev-process

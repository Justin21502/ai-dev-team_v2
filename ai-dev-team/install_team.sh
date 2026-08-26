#!/usr/bin/env bash
set -e
TEAM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
ln -sf "$TEAM_ROOT/team" "$BIN_DIR/team"
chmod +x "$TEAM_ROOT/team"
echo "Installed 'team' at $BIN_DIR/team"
echo 'If needed, run: export PATH="$HOME/.local/bin:$PATH"'
echo 'Then: team "Build a simple test project that prints Hello World and includes pytest tests"'

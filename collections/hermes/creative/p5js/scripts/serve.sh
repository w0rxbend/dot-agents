#!/usr/bin/env bash
# p5.js Skill — Local Development Server
# Serves the current directory over HTTP for loading local assets (fonts, images)
#
# Usage:
#   bash scripts/serve.sh [port] [directory]
#
# Examples:
#   bash scripts/serve.sh                    # serve CWD on port 8080
#   bash scripts/serve.sh 3000               # serve CWD on port 3000
#   bash scripts/serve.sh 8080 ./my-project  # serve specific directory

PORT="${1:-8080}"
DIR="${2:-.}"

echo "=== p5.js Dev Server ==="
echo "Serving: $(cd "$DIR" && pwd)"
echo "URL:     http://127.0.0.1:$PORT"
echo "Press Ctrl+C to stop"
echo ""

# Loopback only: http.server would otherwise expose the dir to the LAN.
cd "$DIR" || exit 1
if command -v python3 >/dev/null 2>&1; then
  exec python3 -m http.server --bind 127.0.0.1 "$PORT"
elif command -v npx >/dev/null 2>&1; then
  echo "Python3 not found. Using Node.js (serve@14.2.6)..."
  exec npx --yes serve@14.2.6 -l "tcp://127.0.0.1:$PORT" .
else
  echo "Error: Need python3 or npx (Node.js) for local server"
  exit 1
fi

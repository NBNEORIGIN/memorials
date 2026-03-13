#!/bin/bash
set -e

# ── Memorials App Deploy Script ──
# Deploys to Hetzner at app.nbnesigns.co.uk/memorials

REPO_DIR="/opt/nbne/memorials"
REPO_URL="git@github.com:NBNEORIGIN/memorials.git"

echo "=== Memorials Deploy ==="

# Clone or pull
if [ -d "$REPO_DIR" ]; then
    echo "Pulling latest..."
    cd "$REPO_DIR"
    git pull origin main
else
    echo "Cloning repo..."
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Build and start
echo "Building containers..."
docker compose -p memorials build --no-cache

echo "Starting services..."
docker compose -p memorials up -d

echo "=== Deploy complete ==="
echo "Backend:  http://127.0.0.1:8012"
echo "Frontend: http://127.0.0.1:3012"
echo ""
echo "Verify: curl -s http://127.0.0.1:8012/docs | head -5"

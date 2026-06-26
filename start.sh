#!/bin/bash
# VendorShield AI - Start all agents
# Run from the repo root: bash start.sh

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "Starting VendorShield AI from: $ROOT"
echo "=================================================="

# Kill any existing agents
lsof -ti:8000,8001,8002,8003,8004 | xargs kill -9 2>/dev/null
sleep 1

# Start main API (port 8000)
echo "Starting Main API (port 8000)..."
cd "$ROOT"
source api/.venv/bin/activate 2>/dev/null || true
uvicorn api.main:app --port 8000 --log-level warning &
PID_8000=$!

# Start Research Agent (port 8001)
echo "Starting Research Agent (port 8001)..."
cd "$ROOT/external-agents/research-agent"
source .venv/bin/activate 2>/dev/null || true
uvicorn main:app --port 8001 --log-level warning &
PID_8001=$!

# Start Compliance Agent (port 8002)
echo "Starting Compliance Agent (port 8002)..."
cd "$ROOT/external-agents/compliance-agent"
source .venv/bin/activate 2>/dev/null || true
uvicorn main:app --port 8002 --log-level warning &
PID_8002=$!

# Start Financial Agent (port 8003)
echo "Starting Financial Agent (port 8003)..."
cd "$ROOT/external-agents/financial-agent"
source .venv/bin/activate 2>/dev/null || true
uvicorn main:app --port 8003 --log-level warning &
PID_8003=$!

# Start Remediation Agent (port 8004)
echo "Starting Remediation Agent (port 8004)..."
cd "$ROOT/external-agents/remediation-agent"
source .venv/bin/activate 2>/dev/null || true
uvicorn main:app --port 8004 --log-level warning &
PID_8004=$!

echo ""
echo "Waiting for agents to start..."
sleep 5

echo ""
echo "Health checks:"
for port in 8000 8001 8002 8003 8004; do
    STATUS=$(curl -s localhost:$port/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ OK')" 2>/dev/null || echo "❌ DOWN")
    echo "  Port $port: $STATUS"
done

echo ""
echo "All agents running. To run demo:"
echo "  cd $ROOT && python3 demo.py 'Acme Cloud Inc' High"
echo ""
echo "To stop all agents:"
echo "  lsof -ti:8000,8001,8002,8003,8004 | xargs kill -9"
echo ""

# Keep script running
wait

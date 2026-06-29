#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "VendorShield AI — Starting all agents"
echo "======================================"

lsof -ti:8000,8001,8002,8003,8004,8005 | xargs kill -9 2>/dev/null
sleep 1

cd "$ROOT" && uvicorn api.main:app --port 8000 --log-level warning &
cd "$ROOT/external-agents/research-agent" && source .venv/bin/activate && uvicorn main:app --port 8001 --log-level warning &
cd "$ROOT/external-agents/compliance-agent" && source .venv/bin/activate && uvicorn main:app --port 8002 --log-level warning &
cd "$ROOT/external-agents/financial-agent" && source .venv/bin/activate && .venv/bin/uvicorn main:app --port 8003 --log-level warning &
cd "$ROOT/external-agents/remediation-agent" && source .venv/bin/activate && .venv/bin/uvicorn main:app --port 8004 --log-level warning &
cd "$ROOT/external-agents/intake-agent" && /opt/homebrew/bin/python3.11 -m venv .venv 2>/dev/null && source .venv/bin/activate && pip install -r requirements.txt -q && uvicorn main:app --port 8005 --log-level warning &

echo "Waiting for agents to start..."
sleep 5

echo ""
echo "Health checks:"
for port in 8000 8001 8002 8003 8004 8005; do
    STATUS=$(curl -s localhost:$port/health 2>/dev/null | python3 -c "import sys,json; print('✅ OK')" 2>/dev/null || echo "❌ DOWN")
    echo "  Port $port: $STATUS"
done

echo ""
echo "Run demo: python3 demo.py 'Acme Cloud Inc' High"
wait

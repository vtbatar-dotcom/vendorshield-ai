#!/bin/bash
# Clean package script — excludes .env, .venv, __pycache__
cd "$(dirname "$0")"
OUTPUT="vendorshield-ai-$(date +%Y%m%d).zip"
zip -r "$OUTPUT" . \
  -x "*.env" \
  -x "*/.venv/*" \
  -x "*/__pycache__/*" \
  -x "*.pyc" \
  -x "*.git/*" \
  -x "*/dist/*" \
  -x "*/node_modules/*"
echo "Package created: $OUTPUT ($(du -sh $OUTPUT | cut -f1))"

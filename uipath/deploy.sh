#!/bin/bash
# VendorShield AI - UiPath deployment script
# Run this once UiPath Labs access is confirmed

echo "VendorShield AI - UiPath Deployment"
echo "===================================="

# Check CLI auth
echo "Checking UiPath CLI authentication..."
uipath auth status || { echo "ERROR: Not authenticated. Run: uipath auth login"; exit 1; }

# Set your tenant URL
TENANT_URL=${UIPATH_TENANT_URL:-"https://cloud.uipath.com"}
echo "Tenant: $TENANT_URL"

# Deploy Maestro Case schema
echo ""
echo "1. Importing Maestro Case schema..."
echo "   → Open UiPath Studio Web"
echo "   → Go to Maestro → Cases → Import"
echo "   → Upload: uipath/maestro-case/VendorRiskCase.json"

# Deploy API Workflows
echo ""
echo "2. Deploying API Workflows..."
echo "   → Go to Orchestrator → API Workflows"
echo "   → Import: uipath/api-workflows/ResearchWorkflow.json"
echo "   → Import: uipath/api-workflows/RemediationWorkflow.json"
echo "   → Set API_BASE_URL to your FastAPI server URL"

# Deploy Action Center task
echo ""
echo "3. Setting up Action Center task..."
echo "   → Go to Action Center → Task Catalog"
echo "   → Import: uipath/agents/intake-agent/HumanReviewTask.json"

echo ""
echo "4. Set environment variables in Orchestrator:"
echo "   API_BASE_URL = http://your-server:8000"
echo "   ANTHROPIC_API_KEY = your-key"
echo "   TAVILY_API_KEY = your-key"

echo ""
echo "Deployment guide complete."
echo "See docs/setup-guide.md for detailed steps."

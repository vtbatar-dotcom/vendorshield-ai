# Risk Scoring — UiPath Coded Agent

The risk scoring logic lives in api/routes/risk.py as a FastAPI endpoint.

To convert to a UiPath Coded Agent (Python SDK):
1. Install UiPath Python SDK: pip install uipath
2. Wrap the scoring logic in a UiPath activity class
3. Deploy via uip project deploy

The weighted model, keywords, and thresholds are production-ready.
See api/routes/risk.py for the implementation.

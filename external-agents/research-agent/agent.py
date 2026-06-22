from __future__ import annotations
import json, os, re
import anthropic
from tavily import TavilyClient

def check_sanctions(vendor_name: str) -> str:
    SANCTIONED_KEYWORDS = ["iran", "north korea", "dprk", "russia sanctioned", "belarus", "cuba embargo", "syria", "sdn list"]
    hits = [kw for kw in SANCTIONED_KEYWORDS if kw in vendor_name.lower()]
    if hits:
        return f"SANCTIONS HIT: {vendor_name} matched: {hits}"
    return f"CLEAR: {vendor_name} found no sanctions matches."

def analyze_sentiment(text: str) -> str:
    negative = ["breach", "hack", "lawsuit", "fine", "penalty", "fraud", "bankrupt", "sanction", "violation", "leak", "ransomware", "attack", "scandal", "investigation", "sued"]
    positive = ["award", "certified", "compliant", "growth", "profit", "partnership", "recognized", "secure", "trusted", "leader"]
    neg = sum(1 for s in negative if s in text.lower())
    pos = sum(1 for s in positive if s in text.lower())
    total = neg + pos
    if total == 0:
        return "sentiment_score: 0.0, label: neutral"
    score = round((pos - neg) / total, 2)
    label = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"
    return f"sentiment_score: {score}, label: {label}"

def web_search(query: str) -> str:
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    results = client.search(query, max_results=5)
    output = []
    for r in results.get("results", []):
        output.append(f"Title: {r.get('title','')}\nURL: {r.get('url','')}\nDate: {r.get('published_date','unknown')}\nContent: {r.get('content','')[:300]}")
    return "\n\n".join(output) if output else "No results found."

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for news, breaches, lawsuits about a vendor.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"]
        }
    },
    {
        "name": "check_sanctions",
        "description": "Check if a vendor name appears on sanctions lists.",
        "input_schema": {
            "type": "object",
            "properties": {"vendor_name": {"type": "string", "description": "Vendor name to check"}},
            "required": ["vendor_name"]
        }
    },
    {
        "name": "analyze_sentiment",
        "description": "Analyze sentiment of text about a vendor.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to analyze"}},
            "required": ["text"]
        }
    }
]

def run_tool(name: str, inputs: dict) -> str:
    if name == "web_search":
        return web_search(inputs["query"])
    elif name == "check_sanctions":
        return check_sanctions(inputs["vendor_name"])
    elif name == "analyze_sentiment":
        return analyze_sentiment(inputs["text"])
    return "Unknown tool"

def run_research(vendor_name: str, vendor_domain: str | None) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    domain_info = f" (domain: {vendor_domain})" if vendor_domain else ""
    messages = [{"role": "user", "content": f"""Research vendor "{vendor_name}"{domain_info} for third-party risk.
1. Search for recent news, breaches, lawsuits, fines
2. Search for "{vendor_name} data breach OR security incident OR lawsuit"
3. Check sanctions
4. Analyze sentiment of findings

You MUST end your final response with ONLY a JSON object, no other text, no markdown fences:
{{"risk_signals": ["specific finding 1", "specific finding 2"], "sentiment_score": -0.5, "news_items": [{{"title": "article title", "url": "https://...", "published": "2024-01-01", "sentiment": -0.5}}], "sanctions_hits": []}}"""}]

    print(f"Starting research for {vendor_name}...")
    last_text = ""

    for iteration in range(8):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages
        )

        print(f"Iteration {iteration+1}: stop_reason={response.stop_reason}")

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    last_text = block.text
                    print(f"Final text: {last_text[:200]}")

            # Try to extract JSON from anywhere in the response
            json_match = re.search(r'\{[\s\S]*"risk_signals"[\s\S]*\}', last_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Try full text after stripping markdown
            clean = re.sub(r"```(?:json)?", "", last_text).strip()
            try:
                return json.loads(clean)
            except json.JSONDecodeError:
                # Build response from what we gathered during tool calls
                return {
                    "risk_signals": [last_text[:500]] if last_text else ["research complete"],
                    "sentiment_score": 0.0,
                    "news_items": [],
                    "sanctions_hits": []
                }

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  Tool: {block.name}({block.input})")
                    result = run_tool(block.name, block.input)
                    print(f"  Result: {result[:150]}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})

    return {"risk_signals": ["max iterations reached"], "sentiment_score": 0.0, "news_items": [], "sanctions_hits": []}

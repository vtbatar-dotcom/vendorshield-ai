from langchain.tools import tool

@tool
def analyze_sentiment(text: str) -> str:
    """Analyze the sentiment of a text snippet about a vendor.
    Returns a score from -1.0 (very negative) to 1.0 (very positive)."""
    text_lower = text.lower()
    negative_signals = [
        "breach", "hack", "lawsuit", "fine", "penalty", "fraud",
        "bankrupt", "sanction", "violation", "leak", "exposed",
        "ransomware", "attack", "scandal", "investigation", "sued",
    ]
    positive_signals = [
        "award", "certified", "compliant", "growth", "profit",
        "partnership", "recognized", "secure", "trusted", "leader",
    ]
    neg_count = sum(1 for s in negative_signals if s in text_lower)
    pos_count = sum(1 for s in positive_signals if s in text_lower)
    total = neg_count + pos_count
    if total == 0:
        return "sentiment_score: 0.0, label: neutral"
    score = round((pos_count - neg_count) / total, 2)
    label = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"
    return f"sentiment_score: {score}, label: {label}"

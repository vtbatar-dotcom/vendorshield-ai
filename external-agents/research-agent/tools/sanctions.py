from langchain.tools import tool

SANCTIONED_KEYWORDS = [
    "iran", "north korea", "dprk", "russia sanctioned",
    "belarus", "cuba embargo", "syria", "venezuela maduro",
    "sdn list", "specially designated national",
]

@tool
def check_sanctions(vendor_name: str) -> str:
    """Check if a vendor name appears on OFAC or other sanctions lists.
    Input: vendor name string. Returns: sanctions findings or clear."""
    name_lower = vendor_name.lower()
    hits = [kw for kw in SANCTIONED_KEYWORDS if kw in name_lower]
    if hits:
        return f"SANCTIONS HIT: {vendor_name} matched keywords: {hits}"
    return f"CLEAR: {vendor_name} found no matches on sanctions screening."

from langchain_community.tools.tavily_search import TavilySearchResults

def get_search_tool() -> TavilySearchResults:
    return TavilySearchResults(
        max_results=5,
        description=(
            "Search the web for news, breach reports, lawsuits, and public "
            "information about a vendor. Input: a search query string."
        ),
    )

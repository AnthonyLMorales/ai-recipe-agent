import logging
import os

from dotenv import load_dotenv
from langchain_tavily import TavilySearch

load_dotenv()

logger = logging.getLogger(__name__)


class TavilySearchTool:
    """Wrapper for Tavily web search functionality."""

    def __init__(self, max_results: int = 3):
        """
        Initialize Tavily search tool.

        Args:
            max_results: Maximum number of search results to return
        """
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY not found in environment variables. "
                "Please add it to your .env file."
            )

        self.search = TavilySearch(max_results=max_results, tavily_api_key=api_key)
        self.max_results = max_results

    def search_recipes(self, query: str) -> list[dict]:
        """
        Search the web for cooking/recipe information using Tavily.

        Args:
            query: Search query string

        Returns:
            List of search results
        """
        try:
            logger.info(f"Tavily search for: {query}")

            # Perform search
            results = self.search.invoke(query)

            # TavilySearch returns a string or dict, wrap in list for consistency
            if isinstance(results, list):
                search_results = results
            else:
                search_results = [{"results": results}]

            logger.info(f"Found {len(search_results)} results")

            return search_results

        except Exception as e:
            logger.error(f"Tavily search failed: {str(e)}")
            return [{"query": query, "results": f"Search failed: {str(e)}"}]


# Create singleton instance
tavily_search_tool = TavilySearchTool(max_results=3)

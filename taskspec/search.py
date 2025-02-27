"""
Web search integration for additional context.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from rich.console import Console

console = Console()

def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web for additional context using Brave Search API.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of search results (title, link, description)
    """
    api_key = os.getenv("BRAVE_API_KEY")
    
    if not api_key:
        console.print("[yellow]Warning: No Brave API key found. Web search disabled.[/yellow]")
        return []
    
    url = "https://api.search.brave.com/res/v1/web/search"
    
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key
    }
    
    params = {
        "q": f"{query} programming implementation guide",
        "count": max_results
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        if "web" in data and "results" in data["web"]:
            for result in data["web"]["results"]:
                results.append({
                    "title": result.get("title", ""),
                    "description": result.get("description", ""),
                    "url": result.get("url", "")
                })
        
        return results
    
    except Exception as e:
        console.print(f"[yellow]Warning: Error during web search: {str(e)}[/yellow]")
        return []
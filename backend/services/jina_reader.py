import os
import httpx
import asyncio

async def fetch_job_content(url: str) -> str:
    """
    Fetches the content of a URL using Jina AI Reader API to get clean Markdown.
    Docs: https://jina.ai/reader
    """
    # The Jina Reader API URL format
    jina_url = f"https://r.jina.ai/{url}"
    
    api_key = os.getenv("JINA_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "X-Target-Selector": "body", # focus on the body, can be customized
    }
    
    # We use httpx for async requests
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(jina_url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Jina API returned status {response.status_code} for {url}")
                return "" # Return empty string or fallback on failure
        except Exception as e:
            print(f"Error fetching job content from Jina: {e}")
            return ""

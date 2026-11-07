from langchain.tools import tool 
import requests 
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os 
from rich import print
from dotenv import load_dotenv 


load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Tavily Tool
@tool
def web_search(query : str) -> str:
    """Search in the web recent and realiable web information on a topic. IT will be return titles, URLs and short summary"""
    results = tavily.search(query = query,max_result = 5)
    
    out = []
    
    for r in results['results']:
     out.append(
        f"Title: {r['title']}\n"
        f"URL: {r['url']}\n"
        f"Snippet: {r['content'][:300]}\n"
    )
        
    return "\n----\n".join(out)    


#Beautifulsoup4 for web scrapping

@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        resp = requests.get(
            url,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        return soup.get_text(separator=" ", strip=True)[:3000]

    except Exception as e:
        return f"Could not scrape URL: {str(e)}"


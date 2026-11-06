from langchain.tools import tool 
import requests 
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os 
from rich import print
from dotenv import load_dotenv 


load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

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

print(web_search.invoke("What is the current news in cricket world?"))
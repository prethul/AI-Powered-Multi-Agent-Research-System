from langchain.agents import create_agent 
from langchain_google_genai import ChatGoogleGenerativeAI 
from dotenv import load_dotenv 
from langchain_core.prompts import PromptTemplate 
from langchain_core.output_parsers import StrOutputParser 
from tools import web_search, scrape_url
import os


load_dotenv ()

llm = ChatGoogleGenerativeAI(
    model ='gemini-3.5-flash-lite'
)

# First agent 
def build_search_agent():
    return create_agent(
        model = llm,
        tools = [web_search]
    )
    
# Second agent 
def build_reader_agent():
    return create_agent(
        model =llm,
        tools = [scrape_url]
    )    
    
       
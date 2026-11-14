from langchain_core.messages import HumanMessage
from multi_agents import (
    build_search_agent,
    build_reader_agent,
    writter_chain,
    critic_chain,
)

def run_research_agent(topic : str)-> dict:
    
    state = {}
    
    # search agent 
    print("\n"+"= "*50)  
    print("Step-1 search agent is working.....")
    print("="*50)
    
    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [HumanMessage(content=f"Find recent, reliable and decent information about: {topic}")]
    })
    
    state['search_results'] = search_result['messages'][-1].content
    
    print("\n search result ",state['search_results'])
    
    
    #step-2 reader_agent 
    
    print("\n"+"= "*50)  
    print("Step-2 reader agent is working.....")
    print("="*50)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [HumanMessage(
            content=(
                f"Based on the following search results about '{topic}', "
                "pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_results'][:800]}"
            )
        )]
    })

    state["scraped_content"] = reader_result["messages"][-1].content
    print("Scraped_content : ",state["scraped_content"])
    
    
    # step-3 
    
    print("\n"+"= "*50)  
    print("Step-3 the writter agent is drafting the report.....")
    print("="*50)
    
    research_combained = (
        f"Search_results : \n {state['search_results']} \n\n"
        f"Detailed_scraped_content : \n {state['scraped_content']}"
    )
    
    state["report"] = writter_chain.invoke({
        'topic' : topic,
        "research" : research_combained
    })
    
    print("Final report \n", state["report"])
    
    #step-4 critic report
    print("\n"+"= "*50)  
    print("Step-4 The llm is reviweing the report.....")
    print("="*50)
    
    state["feedback"] = critic_chain.invoke({
        "report" : state["report"]
    })
    
    print("Critic Report \n :",state["feedback"])
    
    return state
 
if __name__ == "__main__":
    topic = input("Enter a research topic :") 
    run_research_agent(topic)
    
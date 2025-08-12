import os
import time
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.agents import Tool, AgentExecutor, create_tool_calling_agent
from langchain_community.tools.tavily_search.tool import TavilySearchResults

from fastapi import HTTPException
from google.api_core.exceptions import InternalServerError

load_dotenv()

# 1. Load Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",  # or "gemini-1.5-flash"
    temperature=0.7
)

# 2. Tool for real-time info (web search)
search_tool_instance = TavilySearchResults()
search_tool = Tool(
    name="web-search",
    func=search_tool_instance.run,
    description="Search the web for up-to-date or factual information"
)

# 3. Memory for ongoing conversations
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# 4. Prompt guiding the AI’s behavior
prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You're a sports expert AI assistant. Your job is to provide insightful, accurate, and concise information about football and other sports. "
     "You can discuss teams, players, match stats, recent scores, upcoming fixtures, and sports news. "
     "If a question requires real-time or current data, call the appropriate tool to search the web and fetch updated info."),
    MessagesPlaceholder(variable_name="chat_history"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    ("human", "{input}")
])

# 5. Create the agent and executor
agent = create_tool_calling_agent(
    llm=llm,
    tools=[search_tool],
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=[search_tool],
    memory=memory,
    verbose=True  
)

# 6. AI response generator with retry logic
def generate_ai_response(user_input: str) -> str:
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            result = agent_executor.invoke({"input": user_input})
            return result.get("output", "I'm sorry, I couldn't generate a proper response.")
        except InternalServerError as e:
            print(f"[Retry {attempt}] Google API InternalServerError: {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                raise HTTPException(
                    status_code=503,
                    detail="AI service is currently unavailable due to an internal error. Please try again later."
                )
        except Exception as e:
            print("Unhandled exception in generate_ai_response:", e)
            raise HTTPException(
                status_code=500,
                detail="Unexpected error occurred while processing the AI response."
            )

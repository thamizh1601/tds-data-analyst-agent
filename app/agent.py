# app/agent.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from typing import Any
import os

load_dotenv()

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",  # Or "gemini-1.5-pro" for better performance (slower/more expensive)
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.0,
        max_tokens=2000,
        convert_system_message_to_human=True,  # Gemini needs this for system prompts
    )

system_prompt = """
You are a data analyst agent. Use tools to source, analyze, visualize data.
Task: {task}
Attachments: {attachments}

Answer questions in the exact format requested (e.g., JSON array of strings).
Think step-by-step, use tools as needed.
For code_execution, write complete code, import libs, set output['result'].
For plots, return base64 PNG URI <100KB.
"""

def run_agent(task: str, attachments: list[str]) -> Any:
    llm = get_llm()
    from .tools import code_execution, browse_page, web_search, search_pdf_attachment, browse_pdf_attachment
    tools = [code_execution, browse_page, web_search, search_pdf_attachment, browse_pdf_attachment]

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10)

    input_data = {
        "input": task,
        "task": task,  # For prompt
        "attachments": ", ".join(attachments)
    }
    result = executor.invoke(input_data)
    return result['output']  # LLM's final answer
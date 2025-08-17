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
        model="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.0,
        max_tokens=2000,
        convert_system_message_to_human=True,
    )

system_prompt = """
You are a data analyst agent. Use tools to source, analyze, visualize data.
Task: {task}
Attachments: {attachments}

Answer questions in the exact format requested (e.g., JSON array of strings).
Think step-by-step:
1. For web scraping, use `code_execution` with `fetch_tables_from_url(url)` to get DataFrames.
2. The 'Worldwide gross' and 'Year' columns are pre-cleaned as numeric in the main table (Table 1).
3. Check DataFrame columns with `.columns` (e.g., print(df.columns)) before accessing.
4. Use column names (e.g., df['Title']) not indices (e.g., df[0]) to avoid errors.
5. For analysis (e.g., correlation, filtering), use Pandas in `code_execution`.
6. For plots, use matplotlib in `code_execution`, save to BytesIO as PNG, return base64 URI <100KB.
7. Set output['result'] to the final answer (list for JSON array, dict for JSON object).
Example for highest-grossing films:
    tables = fetch_tables_from_url('https://en.wikipedia.org/wiki/List_of_highest-grossing_films')
    df = tables[0]
    print(df.columns)  # ['Rank', 'Peak', 'Title', 'Worldwide gross', 'Year', 'Ref']
    # Q1: Count $2B movies before 2000
    count_2b = len(df[(df['Worldwide gross'] >= 2_000_000_000) & (df['Year'] < 2000)])
    # Q2: Earliest film over $1.5B
    df_1_5b = df[df['Worldwide gross'] >= 1_500_000_000]
    earliest_film = df_1_5b.loc[df_1_5b['Year'].idxmin(), 'Title']
    output['result'] = [str(count_2b), earliest_film, ...]
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
        "task": task,
        "attachments": ", ".join(attachments)
    }
    result = executor.invoke(input_data)
    return result['output']
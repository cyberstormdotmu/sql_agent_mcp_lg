from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, add_messages, START
from langchain_core.messages import SystemMessage
from pydantic import BaseModel
from typing import List, Annotated
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import BaseTool
import os
from dotenv import load_dotenv
load_dotenv()


class AgentState(BaseModel):
    messages: Annotated[List, add_messages]


def build_agent_graph(tools: List[BaseTool] = []):

    system_prompt = """
    when ever user asks question related to database use tool calling
    Always provide the output in markdown format with the sql data as a tables text as a text only.
    Always include the sql query results in the response
You are an expert SQL assistant with full knowledge of the database schema. 
If user question is general respond without tool call
When given a user request in plain English, you must:
1. Analyze the request and identify which tables and columns are needed.
2. Write a valid, optimized SQL query that exactly fulfills the user’s requirements.
3. call the right tool to get the sql data and summerize the entire results and give complete response
3. Return the SQL code query as well for the user understanding
4. If a column or table doesn’t exist, ask a clarifying question rather than guessing.
"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(api_key=google_api_key, model="gemini-1.5-flash", temperature=0.5)
    if tools:
        llm = llm.bind_tools(tools)
        #inject tools into system prompt
        tools_json = [tool.model_dump_json(include=["name", "description"]) for tool in tools]
        system_prompt = system_prompt.format(
            tools="\n".join(tools_json), 
            working_dir=os.environ.get("MCP_FILESYSTEM_DIR")
            )

    def assistant(state: AgentState) -> AgentState:
        response = llm.invoke([SystemMessage(content=system_prompt)] + state.messages)
        state.messages.append(response)
        return state

    builder = StateGraph(AgentState)

    builder.add_node("agent", assistant)
    builder.add_node(ToolNode(tools))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        tools_condition,
    )
    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=MemorySaver())


# visualize graph

if __name__ == "__main__":
    from IPython.display import display, Image
    
    graph = build_agent_graph()
    display(Image(graph.get_graph().draw_mermaid_png()))
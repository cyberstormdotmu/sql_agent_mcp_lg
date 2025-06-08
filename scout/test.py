# agent.py
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from Agents.graph import build_agent_graph, AgentState

async def run_graph(input_text: str, graph: StateGraph, config: dict) -> str:
    result = await graph.ainvoke(
        input=AgentState(messages=[HumanMessage(content=input_text)]),
        config=config
    )
    messages = result.get("messages", [])
    response_text = ""
    if messages:
        last_message = messages[-1]
        response_text += getattr(last_message, "content", "")
    tool_outputs = result.get("tools", {})
    if tool_outputs:
        response_text += "\n\n--- TOOL OUTPUT ---\n"
        for tool_name, details in tool_outputs.items():
            output = details.get("output", "")
            response_text += f"\n[{tool_name}]:\n{output}\n"
    return response_text or "No response from the agent."

async def get_graph():
    mcp_config = {
        "mcpServers": {
            "mysql": {
                "transport": "stdio",
                "command": "python",
                "args": [r"C:\Users\reddy\Gen_AI_Projects\mcp-intro-main\scout\my_mcp\local_servers\sgl_plugin.py"]
            }
        }
    }
    async with MultiServerMCPClient(connections=mcp_config["mcpServers"]) as client:
        tools = client.get_tools()
        graph = build_agent_graph(tools=tools)
    return graph

async def main(user_input="hi"):
    graph = await get_graph()
    graph_config = {
        "configurable": {
            "thread_id": "1"
        }
    }
    response = await run_graph(user_input, graph, graph_config)
    return response

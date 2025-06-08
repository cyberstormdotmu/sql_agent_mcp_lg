import asyncio
import nest_asyncio
import chainlit as cl
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from Agents.client import stream_graph_response, build_agent_graph
from Agents.graph import AgentState

nest_asyncio.apply()

MCP_SERVERS = {
    "mysql": {
        "transport": "stdio",
        "command": "python",
        "args": [r"C:\Users\reddy\Gen_AI_Projects\mcp-intro-main\scout\my_mcp\local_servers\sgl_plugin.py"]
    }
}

mcp_client = None
agent_graph = None

@cl.on_chat_start
async def start_chat():
    global mcp_client, agent_graph
    mcp_client = MultiServerMCPClient(connections=MCP_SERVERS)
    try:
        await mcp_client.__aenter__()
    except GeneratorExit:
        pass

    tools = mcp_client.get_tools()
    agent_graph = build_agent_graph(tools=tools)

    await cl.Message(
        content="Hello! I'm your MCP-powered assistant. How can I help you today?",
        author="assistant"
    ).send()

@cl.on_message
async def handle_message(msg: cl.Message):
    user_text = msg.content
    await cl.Message(content=user_text, author="user").send()

    graph_config = { "configurable": { "thread_id": "1" } }
    state = AgentState(messages=[HumanMessage(content=user_text)])

    # Collect chunks into a single string
    reply_parts = []
    async for chunk in stream_graph_response(
        input=state,
        graph=agent_graph,
        config=graph_config
    ):
        token = chunk.text if hasattr(chunk, "text") else str(chunk)
        reply_parts.append(token)

    full_reply = "".join(reply_parts)

    # Send the entire reply in one message bubble
    await cl.Message(content=full_reply, author="assistant").send()

@cl.on_chat_end
async def end_chat():
    global mcp_client
    if mcp_client:
        try:
            await mcp_client.__aexit__(None, None, None)
        except RuntimeError as e:
            if "cancel scope" in str(e):
                pass
            else:
                raise

if __name__ == "__main__":
    cl.run()

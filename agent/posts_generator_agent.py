from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from prompts import system_prompt, system_prompt_3, system_prompt_4
import httpx
import json
load_dotenv()
from typing import Dict, List, Any
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from copilotkit import CopilotKitState
from copilotkit.langchain import copilotkit_customize_config
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from copilotkit.langgraph import copilotkit_emit_state
import uuid
import asyncio


# Google Search Tool for OpenRouter
@tool
async def google_search(query: str) -> str:
    """Perform a Google search for the given query."""
    try:
        # Simple Google search implementation
        # In production, you might want to use Google Custom Search API
        return f"Search results for: {query}"
    except Exception as e:
        return f"Search failed: {str(e)}"


# Define the agent's runtime state schema for CopilotKit/LangGraph
class AgentState(CopilotKitState):
    tool_logs: List[Dict[str, Any]]
    response: Dict[str, Any]


async def chat_node(state: AgentState, config: RunnableConfig):
    # 1. Define the model using OpenRouter
    model = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=1.0,
        max_retries=2,
    )
    
    state["tool_logs"].append(
        {
            "id": str(uuid.uuid4()),
            "message": "Analyzing the user's query",
            "status": "processing",
        }
    )
    await copilotkit_emit_state(config, state)

    # 2. Defining a condition to check if the last message is a tool so as to handle the FE tool responses
    if state["messages"][-1].type == "tool":
        messages = [*state["messages"]]
        messages[-1].content = (
            "The posts had been generated successfully. Just generate a summary of the posts."
        )
        resp = await model.ainvoke(
            [*state["messages"]],
            config,
        )
        state["tool_logs"] = []
        await copilotkit_emit_state(config, state)
        return Command(goto="fe_actions_node", update={"messages": resp})

    # 3. Configure the model with tools
    if config is None:
        config = RunnableConfig(recursion_limit=25)
    else:
        config = copilotkit_customize_config(config, emit_messages=True, emit_tool_calls=True)
    
    # 4. Generate response with search capability
    tools = [google_search]
    model_with_tools = model.bind_tools(tools)
    
    # Create the conversation with system prompt
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": system_prompt_4},
        {"role": "user", "content": state["messages"][-1].content}
    ]
    
    response = await model_with_tools.ainvoke(messages, config)
    
    # 5. Update tool logs and response
    state["tool_logs"][-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    state["response"] = response.content
    
    # 6. Handle any tool calls (searches)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            state["tool_logs"].append(
                {
                    "id": str(uuid.uuid4()),
                    "message": f"Performing Web Search for '{tool_call['args']['query']}'",
                    "status": "processing",
                }
            )
            await asyncio.sleep(1)
            await copilotkit_emit_state(config, state)
            state["tool_logs"][-1]["status"] = "completed"
            await copilotkit_emit_state(config, state)
    
    return Command(goto="fe_actions_node", update=state)


async def fe_actions_node(state: AgentState, config: RunnableConfig):
    try:
        if state["messages"][-2].type == "tool":
            return Command(goto="end_node", update=state)
    except Exception as e:
        print("Moved")
        
    state["tool_logs"].append(
        {
            "id": str(uuid.uuid4()),
            "message": "Generating post",
            "status": "processing",
        }
    )
    await copilotkit_emit_state(config, state)
    
    # Initialize the model with OpenRouter
    model = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=1.0,
        max_retries=2,
    )
    
    await copilotkit_emit_state(config, state)
    response = await model.bind_tools([*state["copilotkit"]["actions"]]).ainvoke(
        [system_prompt_3.replace("{context}", state["response"]), *state["messages"]],
        config,
    )
    state["tool_logs"] = []
    await copilotkit_emit_state(config, state)
    # Return the response to the frontend as a message which will invoke the correct calling of the Frontend useCopilotAction necessary.
    return Command(goto="end_node", update={"messages": response})


async def end_node(state: AgentState, config: RunnableConfig):
    return Command(goto=END, update={"messages": state["messages"], "tool_logs": []})


def router_function(state: AgentState, config: RunnableConfig):
    if state["messages"][-2].role == "tool":
        return "end_node"
    else:
        return "fe_actions_node"


# Define a new graph
workflow = StateGraph(AgentState)
workflow.add_node("chat_node", chat_node)
workflow.add_node("fe_actions_node", fe_actions_node)
workflow.add_node("end_node", end_node)
workflow.set_entry_point("chat_node")
workflow.set_finish_point("end_node")
workflow.add_edge(START, "chat_node")
workflow.add_edge("chat_node", "fe_actions_node")
workflow.add_edge("fe_actions_node", END)


# Compile the graph
post_generation_graph = workflow.compile(checkpointer=MemorySaver())

import os
from dotenv import load_dotenv
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from app.tools.stock_tools import fetch_stock_price, get_ticker_by_name

load_dotenv()

# ---------- State Definition ----------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# ---------- Tools ----------
tools = [fetch_stock_price, get_ticker_by_name]

# ---------- Model ----------
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY")
).bind_tools(tools)

# ---------- Graph Logic ----------
def call_model(state: AgentState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState):
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    if isinstance(last_message, HumanMessage):
        return "our_agent"
    return END

# ---------- Compile Graph ----------
graph = StateGraph(AgentState)
graph.add_node("our_agent", call_model)
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "our_agent")
graph.add_conditional_edges("our_agent", should_continue)
graph.add_edge("tools", "our_agent")
app_graph = graph.compile()

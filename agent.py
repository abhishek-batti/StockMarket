from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage, AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
import yfinance as yf
import pandas as pd
import os
import requests
import streamlit as st

# Load environment variables
load_dotenv()

# ---------- State Definition ----------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# ---------- Tools ----------
@tool
def fetch_stock_price(symbol: str = "^NSEI") -> str:
    """
    Fetches the stock price for the given symbol using yfinance.
    Args:
        symbol (str): The stock symbol to fetch the price for. Default is "^NSEI" (Nifty 50).
    Returns:
        str: The stock price information for the past month.
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        if hist.empty:
            return f"No data found for symbol: {symbol}"
        return f"The one month histoy of the stock {symbol} is:\n{hist}" 
    except Exception as e:
        return f"Error fetching data for {symbol}: {e}"

@tool
def get_ticker_by_name(name: str) -> str:
    """
    Fetches the stock ticker symbol for a given company name using Yahoo Finance's search API.
    Args:
        name (str): The name of the company.
    Returns:
        str: The stock ticker symbol if found, else None.
    """
    query = "+".join(name.lower().split())
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
    except Exception as e:
        return f"Error fetching ticker: {e}"

    if "quotes" in data and len(data["quotes"]) > 0:
        return data["quotes"][0]["symbol"]
    return f"No ticker found for {name}."

# ---------- Model + Tools ----------
tools = [fetch_stock_price, get_ticker_by_name]

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY")
).bind_tools(tools)

# ---------- Graph Logic ----------
# ---------- Graph Logic ----------
def call_model(state: AgentState):
    """Wraps model call so it only gets messages and returns messages."""
    response = model.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: AgentState):
    """Decide if we should continue to a tool, agent, or end."""
    last_message = state["messages"][-1]

    # If model asked for a tool → go to tool
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # If last message is from human → always go to agent
    if isinstance(last_message, HumanMessage):
        return "our_agent"

    # Otherwise → end turn
    return END

graph = StateGraph(AgentState)

# Add nodes
graph.add_node("our_agent", call_model)   # ✅ wrapped model
graph.add_node("tools", ToolNode(tools))

# Define edges
graph.add_edge(START, "our_agent")
graph.add_conditional_edges("our_agent", should_continue)
graph.add_edge("tools", "our_agent")

# Compile app
app = graph.compile()
# ---------- Chat Loop ----------
def print_stream(stream):
    for s in stream:
        if "messages" in s:
            msg = s["messages"][-1]
            if isinstance(msg, AIMessage):
                print(f"\nAI: {msg.content}")
            elif isinstance(msg, ToolMessage):
                print(f"\n[Tool]: {msg.content}")

# ---------- Streamlit Chat UI ----------
st.set_page_config(page_title="ITops Agent", page_icon="🤖")
st.title("💬 ITops Agent")

# Keep conversation state
if "state" not in st.session_state:
    st.session_state.state = {"messages": []}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Show past messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about stocks..."):
    # Add user msg
    st.session_state.state["messages"].append(HumanMessage(content=prompt))
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process AI response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        for event in app.stream(st.session_state.state, stream_mode="values"):
            if "messages" in event:
                msg = event["messages"][-1]
                if isinstance(msg, AIMessage):
                    full_response = msg.content
                    response_placeholder.markdown(full_response)
                elif isinstance(msg, ToolMessage):
                    full_response = f"[Tool]: {msg.content}"
                    response_placeholder.markdown(full_response)

            st.session_state.state = event

        st.session_state.chat_history.append(
            {"role": "assistant", "content": full_response}
        )
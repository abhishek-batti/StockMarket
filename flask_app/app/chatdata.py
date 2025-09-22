import redis
import json
import datetime
import os 
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
load_dotenv()
r  = redis.StrictRedis(
    host= os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)
print(r.ping())

def convert_to_json_serializable(messages):
    """conver messages to json serializable format."""
    serializable_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            serializable_messages.append({"type": "human", "content": msg.content})
        elif isinstance(msg, AIMessage):
            serializable_messages.append({"type": "ai", "content": msg.content})
        elif isinstance(msg, ToolMessage):
            serializable_messages.append({"type": "tool", "content": str(msg)})
        else:
            serializable_messages.append({"type": "unknown", "content": str(msg)})
            # Handle unknown message types if necessary
            
    return serializable_messages

def convert_from_json_serializable(serializable_messages):
    """convert messages from json serializable format."""
    messages = []
    for msg in serializable_messages:
        if msg["type"] == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["type"] == "ai":
            messages.append(AIMessage(content=msg["content"]))
        else:
            # Handle unknown message types if necessary
            pass
    return messages

def create_new_chat(session_id):
    session_key = f"chat:{session_id}"
    if r.exists(session_key):
        r.delete(session_key)

    entry = {
        "session_id": session_id,
        "messages": [],  # ✅ store an empty list
        "created_at": datetime.datetime.now().isoformat()
    }
    result = r.set(session_key, json.dumps(entry))
    print(f"Redis SET result: {result}, key: {session_key}, value: {entry}")
    return result


def get_chat_messages(session_id):
    session_key = f"chat:{session_id}"
    chat_json = r.get(session_key)
    if not chat_json:
        return []
    chat_data = json.loads(chat_json)
    return chat_data.get("messages", [])


def update_chat(session_id, messages):
    session_key = f"chat:{session_id}"
    chat_data = {
        "session_id": session_id,
        "messages": convert_to_json_serializable(messages),  # ✅ convert messages
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    r.set(session_key, json.dumps(chat_data))
    print(f"Updated Redis key {session_key}: {chat_data}")
    return chat_data

    

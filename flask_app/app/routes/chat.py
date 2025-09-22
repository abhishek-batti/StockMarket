import logging
from flask import Blueprint, request, jsonify
from langchain_core.messages import HumanMessage
from app.utils.model_utils import app_graph
from app.chatdata import create_new_chat, get_chat_messages, update_chat, convert_from_json_serializable

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG level for maximum verbosity
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("chat_api")

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["GET"])
def chat():
    """Chat endpoint that returns a clean JSON response."""
    data = request.get_json()
    prompt = data.get("message")
    session_id = data.get("session_id", "default_session")

    logger.debug(f"Received request payload: {data}")
    logger.info(f"Incoming chat request | session_id={session_id}, message={prompt}")

    if not prompt:
        logger.warning("No message provided in request.")
        return jsonify({"error": "Message is required"}), 400

    # Load existing chat messages
    past_messages = get_chat_messages(session_id)
    past_messages = convert_from_json_serializable(past_messages)
    logger.debug(f"Past messages retrieved for session '{session_id}': {past_messages}")

    # Create a new chat if none exists
    if not past_messages:
        logger.info(f"No existing chat found for session_id={session_id}, creating new one.")
        created = create_new_chat(session_id)
        logger.debug(f"create_new_chat returned: {created}")
        # Verify if key exists in Redis
        past_messages = get_chat_messages(session_id)
        logger.debug(f"Messages after creation: {past_messages}")

    # Add user message
    user_message = HumanMessage(content=prompt)
    messages = past_messages + [user_message] if past_messages else [user_message]
    logger.debug(f"Messages to be sent to the model: {messages}")
    
    # Call the model graph
    state = {"messages": messages}
    response = app_graph.invoke(state)
    print(response)
    # Update chat in Redis
    updated_chat = update_chat(session_id, response["messages"])
    # Verify saved data
    final_check = get_chat_messages(session_id)
    logger.debug(f"Final messages fetched from Redis for verification: {final_check}")

    return jsonify(updated_chat)

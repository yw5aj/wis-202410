from letta import LocalClient, LettaMessage
from modules.user_management import get_user_agent_id

letta_client = LocalClient()

def get_agent_response(input_text, username):
    agent_id = get_user_agent_id(username)
    if agent_id:
        response = letta_client.user_message(
            agent_id=agent_id,
            message=input_text,
        )
        # Extract the content from the response
        for message in response.messages:
            if isinstance(message, LettaMessage) and message.type == 'user_message':
                return message.content
        return "No user message found in the response"
    return "Error: User agent not found"

def get_agent_advice(username):
    agent_id = get_user_agent_id(username)
    if agent_id:
        response = letta_client.send_message(
            agent_id=agent_id,
            message="Can you provide some advice?",
        )
        # Extract the content from the response
        for message in response.messages:
            if isinstance(message, LettaMessage) and message.type == 'user_message':
                return message.content
        return "No user message found in the response"
    return "Error: User agent not found"

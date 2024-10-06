import json
from letta import LocalClient, LettaMessage
from modules.user_management import get_user_agent_id

letta_client = LocalClient()

def get_agent_response(input_text, username, detailed=False):
    agent_id = get_user_agent_id(username)
    if agent_id:
        response = letta_client.user_message(
            agent_id=agent_id,
            message=input_text,
        )
        return process_agent_messages(response.messages, detailed)
    return "Error: User agent not found"

def get_agent_advice(username, detailed=False):
    agent_id = get_user_agent_id(username)
    if agent_id:
        response = letta_client.user_message(
            agent_id=agent_id,
            message="Can you provide some advice?",
        )
        return process_agent_messages(response.messages, detailed)
    return "Error: User agent not found"

def process_agent_messages(messages, detailed=False):
    result = []
    agent_responses = []
    for message in messages:
        if hasattr(message, 'function_call') and message.function_call.name == 'send_message':
            arguments = json.loads(message.function_call.arguments)
            agent_response = f"🤖 Agent: {arguments['message']}"
            agent_responses.append(agent_response)
            if detailed:
                result.append(agent_response)
        elif detailed:
            if hasattr(message, 'internal_monologue'):
                result.append(f"💭 Inner Monologue: {message.internal_monologue}")
            elif hasattr(message, 'function_call'):
                result.append(f"🛠️ Function Call: {message.function_call.name}({message.function_call.arguments})")
            elif hasattr(message, 'function_return'):
                result.append(f"📊 Function Return: {message.function_return}")
    
    if detailed:
        return "\n".join(result) if result else "No relevant messages found in the response"
    else:
        return "\n".join(agent_responses) if agent_responses else "No agent responses found"

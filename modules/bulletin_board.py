from modules.user_management import get_group_members, get_comprehensive_agent_data, letta_client
from modules.group_data_storage import save_group_data, load_group_data
from datetime import datetime, timedelta
from letta.schemas.message import MessageRole
import json
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def create_or_update_group_bulletin(group_name, group_agent_id, new_item=None):
    members = get_group_members(group_name)
    bulletin_content = f"Group Bulletin Board for {group_name}\n\n"

    # Load existing bulletin
    existing_bulletin = load_group_data(group_name, "bulletin")
    if existing_bulletin:
        bulletin_content += "Existing bulletin content:\n" + existing_bulletin + "\n\n"

    # Get data for the last 7 days
    # TODO: Fix function calls to get proper date range
    # end_date = datetime.now()
    # start_date = end_date - timedelta(days=7)
    end_date = None
    start_date = None

    for username, agent_id in members.items():
        agent_data = get_comprehensive_agent_data(agent_id, start_date, end_date)
        
        bulletin_content += f"User: {username}\n"
        
        # TODO: Fix in-context memory retrieval
        # bulletin_content += f"In-context memory: {agent_data['memory_summaries']['in_context_memory'].memory['human']}...\n"
        
        # TODO: Investigate why archival_memory_summary is not returning data
        # bulletin_content += f"Archival memory: {agent_data['memory_summaries']['archival_memory_summary'].total_passages} passages\n"
        
        # TODO: Find a way to access recall memory content
        # bulletin_content += f"Recall memory: {agent_data['memory_summaries']['recall_memory_summary'].total_messages} messages\n"
        
        bulletin_content += f"Recent messages: {len(agent_data['messages'])}\n"
        bulletin_content += f"Recent archival memory passages: {len(agent_data['archival_memory_passages'])}\n"
        
        # Process messages
        bulletin_content += "Recent messages:\n"
        for message in agent_data['messages'][::-1]:
            if message.role == MessageRole.user:
                message_data = json.loads(message.text)
                if message_data['type'] == 'user_message':
                    bulletin_content += f"User ({message_data['time']}): {message_data['message']}\n"
            elif message.role == MessageRole.assistant:
                for tool_call in message.tool_calls:
                    if tool_call.function.name == 'send_message':
                        tool_call_data = json.loads(tool_call.function.arguments)
                        bulletin_content += f"Assistant: {tool_call_data['message']}\n"
        
        bulletin_content += "\n"
        
        # Add recent archival memory passages
        if agent_data['archival_memory_passages']:
            bulletin_content += "Recent archival memories:\n"
            for passage in agent_data['archival_memory_passages'][:16]:  # Limit to 16 most recent passages
                bulletin_content += f"- {passage.text}\n" 
        
        bulletin_content += "\n"

    if new_item:
        bulletin_content += f"\nNew item to be added: {new_item}\n"

    # Use OpenAI's GPT-4o-mini to update the bulletin board
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant tasked with updating a concise and informative bulletin board for a group."},
            {"role": "user", "content": f"Based on the following information about group members, existing bulletin content, and any new item, update the bulletin board for the group. Follow these guidelines:\n\n1. Limit to 2 items per user\n2. Balance the content between users so that they get roughly equal amounts of items\n3. If there's a new item, make sure to incorporate it prominently\n4. Prioritize recent and important information\n5. Only add or remove items if necessary based on the recent information\n6. Use emojis to make the content more engaging\n7. Use a single newline character to separate each user's content\n8. Return just the content, with no other text\n\nHere's the content to work with:\n\n{bulletin_content}"}
        ]
    )

    updated_bulletin = response.choices[0].message.content

    # Save the updated bulletin
    save_group_data(group_name, "bulletin", updated_bulletin)

    return updated_bulletin

def get_bulletin_board(group_name, group_agent_id):
    existing_bulletin = load_group_data(group_name, "bulletin")
    if existing_bulletin:
        return existing_bulletin
    return create_or_update_group_bulletin(group_name, group_agent_id)
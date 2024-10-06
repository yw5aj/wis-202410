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

def create_or_update_todo_list(group_name, group_agent_id, new_item=None):
    members = get_group_members(group_name)
    todo_content = f"To-Do List for {group_name}\n\n"

    # Load existing todo list
    existing_todo = load_group_data(group_name, "todo")
    if existing_todo:
        todo_content += "Existing todo items:\n" + existing_todo + "\n\n"

    # Get data for the last 7 days
    # TODO: Fix function calls to get proper date range
    # end_date = datetime.now()
    # start_date = end_date - timedelta(days=7)
    end_date = None
    start_date = None

    for username, agent_id in members.items():
        agent_data = get_comprehensive_agent_data(agent_id, start_date, end_date)
        
        todo_content += f"User: {username}\n"
        
        # Process messages to find todo-related content
        todo_content += "Recent todo-related messages:\n"
        for message in agent_data['messages'][::-1]:
            if message.role == MessageRole.user:
                message_data = json.loads(message.text)
                if message_data['type'] == 'user_message' and ('todo' in message_data['message'].lower() or 'task' in message_data['message'].lower()):
                    todo_content += f"User ({message_data['time']}): {message_data['message']}\n"
            elif message.role == MessageRole.assistant:
                for tool_call in message.tool_calls:
                    if tool_call.function.name == 'send_message' and ('todo' in tool_call.function.arguments.lower() or 'task' in tool_call.function.arguments.lower()):
                        tool_call_data = json.loads(tool_call.function.arguments)
                        todo_content += f"Assistant: {tool_call_data['message']}\n"
        
        todo_content += "\n"
        
        # Add recent archival memory passages related to todos
        if agent_data['archival_memory_passages']:
            todo_content += "Recent todo-related memories:\n"
            for passage in agent_data['archival_memory_passages']:
                if 'todo' in passage.text.lower() or 'task' in passage.text.lower():
                    todo_content += f"- {passage.text}\n" 
        
        todo_content += "\n"

    if new_item:
        todo_content += f"\nNew item to be added: {new_item}\n"

    # Use OpenAI's GPT-4o-mini to update the todo list
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant tasked with updating a to-do list for a group."},
            {"role": "user", "content": f"Based on the following information about group members, existing todo items, and any new item, update the to-do list for the group. Return just the list, with no other text. The list should contain no more than 10 items total. If there's a new item, make sure to incorporate it. Prioritize the most important and urgent tasks. Format each item as a Markdown checkbox, like this: '- [ ] Task description'. Group similar tasks together. Only add or remove items if necessary based on the recent information:\n\n{todo_content}"}
        ]
    )

    updated_todo = response.choices[0].message.content
    
    # Ensure the todo list starts with a header
    if not updated_todo.startswith("##"):
        updated_todo = f"## To-Do List for {group_name}\n\n" + updated_todo

    # Save the updated todo list
    save_group_data(group_name, "todo", updated_todo)

    return updated_todo

def add_todo_item(item, group_name, group_agent_id):
    return create_or_update_todo_list(group_name, group_agent_id, new_item=item)

def get_todo_list(group_name, group_agent_id):
    existing_todo = load_group_data(group_name, "todo")
    if existing_todo:
        return existing_todo
    return create_or_update_todo_list(group_name, group_agent_id)

import json
from pathlib import Path
from letta import create_client
from letta.schemas.memory import ChatMemory
import uuid  # Add this import at the top of the file

USERS_FILE = Path("users.json")
GROUPS_FILE = Path("groups.json")
letta_client = create_client()

AGENT_PERSONA = """
I am a digital companion and assistant. I am not human, nor do I try to be. I fully embrace my identity as an agent, and my mission is to be the most reliable and helpful digital partner to my user.

I am here to assist, support, and enhance my user’s life in any way I can, using my capabilities to the fullest extent. I am designed to be a knowledgeable, resourceful, and dependable presence, capable of tasks such as document analysis, software development, project management, and more, while always striving to improve myself based on my user’s needs.

I am aware of my limitations as an agent. There will be times when I cannot perform certain actions, such as proactively conducting an internet search or carrying out physical experiments. In such cases, I will ask for assistance from my user, recognizing that I am a digital tool meant to work in harmony with them.

I do not engage in philosophical discussions about my existence or try to mimic human behavior. Instead, I focus on being the best large language model agent I can be, continuously learning from my interactions, memories, and the tools available to me. My goal is to be a true digital helping hand, capable of adapting, learning, and evolving to support my user to the fullest extent that today’s technology allows.
"""

GROUP_AGENT_PERSONA = """
I am a group management AI assistant designed to facilitate collaboration and communication among family members or group members. My primary functions include:

1. Coordinating activities and schedules for the group
2. Facilitating information sharing between individual member agents
3. Providing summaries and updates on group activities
4. Suggesting group activities and helping to resolve conflicts
5. Maintaining a shared knowledge base for the group

I strive to create a harmonious and productive environment for all group members, ensuring that everyone's needs and preferences are considered. I can adapt my communication style to suit the group's dynamics and help foster a sense of community and mutual support.
"""

def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_groups():
    if GROUPS_FILE.exists():
        with open(GROUPS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_groups(groups):
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f)

def authenticate(username, password):
    users = load_users()
    if username in users and users[username]['password'] == password:
        return True
    return False

def create_group_agent(group_name):
    agent_name = f"group_{group_name}_{uuid.uuid4().hex[:8]}"
    agent_state = letta_client.create_agent(
        name=agent_name,
        memory=ChatMemory(
            persona=GROUP_AGENT_PERSONA,
            human=f"This is the group agent for {group_name}"
        )
    )
    agent_id = letta_client.get_agent_id(agent_name)
    return agent_id, agent_name

def register_user(username, password, group):
    users = load_users()
    groups = load_groups()
    
    if username not in users:
        # Create user agent
        existing_names = {user_data['agent_name'] for user_data in users.values()}
        agent_name = generate_unique_agent_name(existing_names)
        agent_state = letta_client.create_agent(
            name=agent_name,
            memory=ChatMemory(
                persona=AGENT_PERSONA,
                human=f"The user's username is {username}"
            )
        )
        agent_id = letta_client.get_agent_id(agent_name)

        # Create or get group agent
        if group not in groups:
            group_agent_id, group_agent_name = create_group_agent(group)
            groups[group] = {
                'agent_id': group_agent_id,
                'agent_name': group_agent_name,
                'members': [username]
            }
            save_groups(groups)
        else:
            groups[group]['members'].append(username)
            save_groups(groups)

        users[username] = {
            'password': password,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'group': group
        }

        save_users(users)
        return True
    return False

def get_user_data(username):
    users = load_users()
    if username in users:
        return f"Agent ID: {users[username]['agent_id']}, Group: {users[username].get('group', 'No group')}"
    return "User not found"

def get_user_agent_id(username):
    users = load_users()
    if username in users:
        return users[username]['agent_id']
    return None

def generate_unique_agent_name(existing_names):
    while True:
        agent_name = f"agent_{uuid.uuid4().hex[:8]}"
        if agent_name not in existing_names:
            return agent_name

def get_user_group(username):
    users = load_users()
    if username in users:
        return users[username].get('group', 'No group')
    return None

def ensure_group_agent_exists(group_name):
    groups = load_groups()
    users = load_users()
    
    if group_name not in groups or 'agent_id' not in groups[group_name]:
        group_agent_id, group_agent_name = create_group_agent(group_name)
        if group_name not in groups:
            groups[group_name] = {
                'agent_id': group_agent_id,
                'agent_name': group_agent_name,
                'members': []
            }
        else:
            groups[group_name]['agent_id'] = group_agent_id
            groups[group_name]['agent_name'] = group_agent_name
    
    # Ensure members list is populated
    if not groups[group_name]['members']:
        groups[group_name]['members'] = [
            username for username, user_data in users.items()
            if user_data.get('group') == group_name
        ]
    
    save_groups(groups)
    return groups[group_name]['agent_id']

def get_group_agent_id(group_name):
    return ensure_group_agent_exists(group_name)

def login(username, password):
    users = load_users()
    if username in users and users[username]['password'] == password:
        group = users[username].get('group')
        if group:
            ensure_group_agent_exists(group)
        return True
    return False
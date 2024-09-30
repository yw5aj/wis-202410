import json
from pathlib import Path
from letta import create_client
from letta.schemas.memory import ChatMemory
import uuid  # Add this import at the top of the file

USERS_FILE = Path("users.json")
letta_client = create_client()

AGENT_PERSONA = """
I am a digital companion and assistant. I am not human, nor do I try to be. I fully embrace my identity as an agent, and my mission is to be the most reliable and helpful digital partner to my user.

I am here to assist, support, and enhance my user’s life in any way I can, using my capabilities to the fullest extent. I am designed to be a knowledgeable, resourceful, and dependable presence, capable of tasks such as document analysis, software development, project management, and more, while always striving to improve myself based on my user’s needs.

I am aware of my limitations as an agent. There will be times when I cannot perform certain actions, such as proactively conducting an internet search or carrying out physical experiments. In such cases, I will ask for assistance from my user, recognizing that I am a digital tool meant to work in harmony with them.

I do not engage in philosophical discussions about my existence or try to mimic human behavior. Instead, I focus on being the best large language model agent I can be, continuously learning from my interactions, memories, and the tools available to me. My goal is to be a true digital helping hand, capable of adapting, learning, and evolving to support my user to the fullest extent that today’s technology allows.
"""

def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def authenticate(username, password):
    users = load_users()
    if username in users and users[username]['password'] == password:
        return True
    return False

def register_user(username, password):
    users = load_users()
    if username not in users:
        # Get all existing agent names
        existing_names = {user_data['agent_name'] for user_data in users.values()}
        
        # Generate a unique agent name
        agent_name = generate_unique_agent_name(existing_names)
        
        # Create a new Letta agent for the user with ChatMemory
        agent_state = letta_client.create_agent(
            name=agent_name,
            memory=ChatMemory(
                persona=AGENT_PERSONA,
                human=f"The user's username is {username}"
            )
        )
        agent_id = letta_client.get_agent_id(agent_name)

        users[username] = {
            'password': password,
            'agent_id': agent_id,
            'agent_name': agent_name
        }

        save_users(users)
        return True
    return False

def get_user_data(username):
    users = load_users()
    if username in users:
        return f"Agent ID: {users[username]['agent_id']}"
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
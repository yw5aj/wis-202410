import gradio as gr
from modules.voice_processing import process_voice_input
from modules.image_processing import summarize_image
from modules.todo_list import add_todo_item, get_todo_list
from modules.bulletin_board import get_bulletin_board, create_or_update_group_bulletin
from modules.agent_responses import get_agent_response, get_agent_advice
from modules.user_management import authenticate, register_user, get_user_data, get_user_group, get_group_agent_id, ensure_group_agent_exists, load_users

import os
from pathlib import Path

# Ensure necessary directories exist
Path("stored_images").mkdir(exist_ok=True)
Path("image_summaries").mkdir(exist_ok=True)

def process_multimodal(audio, image, model_choice, current_input):
    # Process voice input
    voice_text = process_voice_input(audio) if audio else ""
    
    # Process image input
    image_summary = ""
    if image:
        try:
            result = summarize_image(image, model=model_choice)
            if result['summary'].startswith("Error processing image"):
                image_summary = result['summary']
            else:
                image_summary = f"Image processed with {model_choice} (ID: {result['image_id']}):\n{result['summary']}"
        except Exception as e:
            image_summary = f"Error processing image: {str(e)}"
    
    # Combine voice input and image summary
    new_input = f"Voice input: {voice_text}\n\nImage summary: {image_summary}".strip()
    
    # Append new input to current input
    combined_input = f"{current_input}\n\n{new_input}".strip()
    
    return combined_input

def submit_to_agent(input_text, username, show_details, history):
    agent_response = get_agent_response(input_text, username, detailed=show_details)
    history.append((input_text, agent_response))
    return "", history  # Return empty string to clear input box

def update_todo(todo_item):
    add_todo_item(todo_item)
    return get_todo_list()

def update_bulletin(new_item, group_name, group_agent_id):
    updated_bulletin = create_or_update_group_bulletin(group_name, group_agent_id, new_item)
    return updated_bulletin

def refresh_bulletin(group_name, group_agent_id):
    return create_or_update_group_bulletin(group_name, group_agent_id)

def request_advice(username, show_details, history):
    advice = get_agent_advice(username, detailed=show_details)
    history.append(("Can you provide some advice?", advice))
    return history

def login(username, password):
    if authenticate(username, password):
        group = get_user_group(username)
        group_agent_id = ensure_group_agent_exists(group) if group else None
        return f"Welcome, {username}!", get_user_data(username), username, group, group_agent_id
    else:
        return "Invalid username or password", "", "", "", ""

def register(username, password, group):
    if register_user(username, password, group):
        group_agent_id = get_group_agent_id(group)
        return f"User {username} registered successfully in group {group}! Group Agent ID: {group_agent_id}"
    else:
        return "Username already exists. Please choose a different one."

def update_all_groups():
    users = load_users()
    unique_groups = set(user_data.get('group') for user_data in users.values() if user_data.get('group'))
    for group in unique_groups:
        ensure_group_agent_exists(group)

# Call this function once when the app starts
update_all_groups()

with gr.Blocks() as demo:
    gr.Markdown("# Worlds In-Silico Family Assistant")
    
    current_user = gr.State(value="")
    chat_history = gr.State([])

    with gr.Tab("Login"):
        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
        group_input = gr.Textbox(label="Group (for registration)")
        login_button = gr.Button("Login")
        register_button = gr.Button("Register")
        login_output = gr.Textbox(label="Login Status")
    
    with gr.Tab("Main Interface"):
        user_data = gr.Textbox(label="User Data")
        user_group = gr.Textbox(label="User Group")
        group_agent_id = gr.Textbox(label="Group Agent ID")
        
        with gr.Row():
            with gr.Column(scale=1):
                todo_list = gr.Textbox(label="Family To-Do List", value=get_todo_list(), lines=10)
                todo_input = gr.Textbox(label="Add Todo Item")
                todo_button = gr.Button("Add Todo")

            with gr.Column(scale=2):
                with gr.Row():
                    voice_input = gr.Audio(type="filepath", label="Voice Input")
                    image_input = gr.Image(label="Image Input", type="filepath")
                model_choice = gr.Radio(["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet-20240620"], 
                                        label="Choose Model", 
                                        value="gpt-4o-mini")
                input_box = gr.Textbox(label="Input", lines=5)
                show_details = gr.Checkbox(label="Show agent thought process", value=False)
                with gr.Row():
                    process_button = gr.Button("Process Multimodal Input")
                    submit_button = gr.Button("Submit to Agent")

            with gr.Column(scale=1):
                bulletin_board = gr.Markdown(label="Family Bulletin Board", value="")
                bulletin_input = gr.Textbox(label="New Bulletin Item (optional)")
                update_bulletin_button = gr.Button("Update Bulletin Board")

        agent_responses = gr.Chatbot(label="Conversation History")
        advice_button = gr.Button("Any advice?")

        with gr.Row():
            with gr.Column(scale=2):
                gr.Image("logo.png", show_label=False, height=100)
            with gr.Column(scale=2):
                gr.Markdown(
                    """
                    # Worlds In-Silico Family Assistant
                    ### Connecting Intelligent Worlds, Empowering Real Lives
                    """
                )
                
        # Connect components
        process_button.click(
            process_multimodal, 
            inputs=[voice_input, image_input, model_choice, input_box], 
            outputs=input_box
        )
        submit_button.click(
            submit_to_agent, 
            inputs=[input_box, current_user, show_details, chat_history], 
            outputs=[input_box, agent_responses]
        )
        todo_button.click(update_todo, todo_input, todo_list)
        update_bulletin_button.click(
            update_bulletin,
            inputs=[bulletin_input, user_group, group_agent_id],
            outputs=bulletin_board
        )
        advice_button.click(request_advice, inputs=[current_user, show_details, chat_history], outputs=agent_responses)
        
        # Connect login components
        login_button.click(login, inputs=[username_input, password_input], outputs=[login_output, user_data, current_user, user_group, group_agent_id])
        register_button.click(register, inputs=[username_input, password_input, group_input], outputs=login_output)

        # Update bulletin board on login
        login_button.click(
            lambda group, agent_id: f"## {group} Bulletin Board\n\n{create_or_update_group_bulletin(group, agent_id)}" if group and agent_id else "",
            inputs=[user_group, group_agent_id],
            outputs=bulletin_board
        )

demo.launch(share=True)

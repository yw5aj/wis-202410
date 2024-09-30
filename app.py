import gradio as gr
from modules.voice_processing import process_voice_input
from modules.image_processing import summarize_image
from modules.todo_list import add_todo_item, get_todo_list
from modules.bulletin_board import add_bulletin_item, get_bulletin_board
from modules.agent_responses import get_agent_response, get_agent_advice
from modules.user_management import authenticate, register_user, get_user_data

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

def submit_to_agent(input_text, username):
    agent_response = get_agent_response(input_text, username)
    return agent_response

def update_todo(todo_item):
    add_todo_item(todo_item)
    return get_todo_list()

def update_bulletin(bulletin_item):
    add_bulletin_item(bulletin_item)
    return get_bulletin_board()

def request_advice(username):
    return get_agent_advice(username)

def login(username, password):
    if authenticate(username, password):
        return f"Welcome, {username}!", get_user_data(username), username
    else:
        return "Invalid username or password", "", ""

def register(username, password):
    if register_user(username, password):
        return f"User {username} registered successfully!"
    else:
        return "Username already exists. Please choose a different one."

with gr.Blocks() as demo:
    gr.Markdown("# Worlds In-Silico Family Assistant")
    
    current_user = gr.State(value="")

    with gr.Tab("Login"):
        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
        login_button = gr.Button("Login")
        register_button = gr.Button("Register")
        login_output = gr.Textbox(label="Login Status")
    
    with gr.Tab("Main Interface"):
        user_data = gr.Textbox(label="User Data")
        
        with gr.Row():
            with gr.Column(scale=1):
                todo_list = gr.Textbox(label="Family To-Do List", value=get_todo_list(), lines=10)
                todo_input = gr.Textbox(label="Add Todo Item")
                todo_button = gr.Button("Add Todo")

            with gr.Column(scale=2):
                with gr.Row():
                    voice_input = gr.Audio(type="filepath", label="Voice Input")
                    image_input = gr.Image(label="Image Input", type="filepath")
                model_choice = gr.Radio(["gpt-4o", "claude-3-5-sonnet-20240620"], label="Choose Model", value="gpt-4o")
                input_box = gr.Textbox(label="Input", lines=5)
                with gr.Row():
                    process_button = gr.Button("Process Multimodal Input")
                    submit_button = gr.Button("Submit to Agent")

            with gr.Column(scale=1):
                bulletin_board = gr.Textbox(label="Family Bulletin Board", value=get_bulletin_board(), lines=10)
                bulletin_input = gr.Textbox(label="Add Bulletin Item")
                bulletin_button = gr.Button("Add Bulletin")
        
        agent_responses = gr.Textbox(label="Agent Responses & Recommendations", lines=5)
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
            inputs=[input_box, current_user], 
            outputs=agent_responses
        )
        todo_button.click(update_todo, todo_input, todo_list)
        bulletin_button.click(update_bulletin, bulletin_input, bulletin_board)
        advice_button.click(request_advice, inputs=[current_user], outputs=agent_responses)
        
        # Connect login components
        login_button.click(login, inputs=[username_input, password_input], outputs=[login_output, user_data, current_user])
        register_button.click(register, inputs=[username_input, password_input], outputs=login_output)

demo.launch()

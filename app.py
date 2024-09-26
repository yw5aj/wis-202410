import gradio as gr
from modules.voice_processing import process_voice_input
from modules.image_processing import summarize_image
from modules.todo_list import add_todo_item, get_todo_list
from modules.bulletin_board import add_bulletin_item, get_bulletin_board
from modules.agent_responses import get_agent_response, get_agent_advice

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

def submit_to_agent(input_text):
    agent_response = get_agent_response(input_text)
    return agent_response

def update_todo(todo_item):
    add_todo_item(todo_item)
    return get_todo_list()

def update_bulletin(bulletin_item):
    add_bulletin_item(bulletin_item)
    return get_bulletin_board()

def request_advice():
    return get_agent_advice()

with gr.Blocks() as demo:
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

    # Connect components
    process_button.click(
        process_multimodal, 
        inputs=[voice_input, image_input, model_choice, input_box], 
        outputs=input_box
    )
    submit_button.click(
        submit_to_agent, 
        inputs=input_box, 
        outputs=agent_responses
    )
    todo_button.click(update_todo, todo_input, todo_list)
    bulletin_button.click(update_bulletin, bulletin_input, bulletin_board)
    advice_button.click(request_advice, None, agent_responses)

demo.launch()

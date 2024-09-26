import os
import uuid
import base64
from pathlib import Path
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
import mimetypes

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Define storage directories
IMAGE_DIR = Path("stored_images")
SUMMARY_DIR = Path("image_summaries")

# Ensure directories exist
IMAGE_DIR.mkdir(exist_ok=True)
SUMMARY_DIR.mkdir(exist_ok=True)

def get_mime_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"

def summarize_image(image_path, model="claude-3-5-sonnet-20240620"):
    # Generate a unique ID for the image
    image_id = str(uuid.uuid4())
    
    # Read the image file
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    # Encode the image data to base64
    base64_image = base64.b64encode(image_data).decode('utf-8')
    
    # Get the MIME type of the image
    mime_type = get_mime_type(image_path)
    
    if model == "gpt-4o":
        summary = summarize_with_gpt4o(base64_image, mime_type)
    elif model == "claude-3-5-sonnet-20240620":
        summary = summarize_with_claude(base64_image, mime_type)
    else:
        raise ValueError("Unsupported model. Choose 'gpt-4o' or 'claude-3-5-sonnet-20240620'.")
    
    # Save the image to the file system
    new_image_path = IMAGE_DIR / f"{image_id}{Path(image_path).suffix}"
    with open(new_image_path, "wb") as new_image_file:
        new_image_file.write(image_data)
    
    # Save the summary to a text file
    summary_path = SUMMARY_DIR / f"{image_id}.txt"
    with open(summary_path, "w") as summary_file:
        summary_file.write(summary)
    
    return {
        "image_id": image_id,
        "image_path": str(new_image_path),
        "summary_path": str(summary_path),
        "summary": summary,
    }

def summarize_with_gpt4o(base64_image, mime_type):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please describe this image in detail."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=512,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error processing image with GPT-4: {str(e)}"

def summarize_with_claude(base64_image, mime_type):
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Please describe this image in detail.",
                        },
                    ],
                }
            ],
        )
        return response.content[0].text
    except Exception as e:
        return f"Error processing image with Claude: {str(e)}"
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def process_voice_input(audio_file):
    if not audio_file:
        return "No voice input provided."
    
    try:
        with open(audio_file, "rb") as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio
            )
        return transcript.text
    except Exception as e:
        return f"Error processing voice input: {str(e)}"

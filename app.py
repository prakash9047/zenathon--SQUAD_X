from flask import Flask, request, render_template
import torch
from transformers import pipeline
import os
import re
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API")

# Initialize Flask app
app = Flask(__name__)

# Load summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn", 
                      device=torch.device('cuda:0') if torch.cuda.is_available() else -1)

# Transcription function using Groq API
def audio_to_text(filepath):
    """Transcribes audio using Whisper API through Groq"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Audio file {filepath} not found.")
    
    client = Groq(api_key=GROQ_API_KEY)
    with open(filepath, "rb") as file:
        try:
            response = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=file,
            )
            print("\nTranscription:\n", response.text)
            return response.text
        except Exception as e:
            print("Transcription Error:", str(e))
            return ""

# Helper function to chunk text
def chunk_text(text, max_tokens=512):
    sentences = text.split(". ")
    chunks, current_chunk = [], ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_tokens:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

# Helper function to clean transcribed text
def clean_transcription(text):
    text = re.sub(r'http[s]?://\S+', '', text)
    unwanted_phrases = [
        "CNN.com will feature iReporter photos",
        "Visit CNN.com/Travel", 
    ]
    for phrase in unwanted_phrases:
        text = text.replace(phrase, "")
    return text.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'audio' not in request.files:
            return "<h3 style='color:red;'>Error: No file uploaded.</h3>", 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return "<h3 style='color:red;'>Error: No file selected.</h3>", 400

        os.makedirs("uploads", exist_ok=True)
        audio_path = os.path.join("uploads", audio_file.filename)
        audio_file.save(audio_path)

        # Transcribe audio using Groq API
        transcribed_text = audio_to_text(audio_path)
        cleaned_text = clean_transcription(transcribed_text)

        # Chunk and summarize text
        chunks = chunk_text(cleaned_text)
        summarized_text = " ".join([
            summarizer(chunk, max_length=50, min_length=35, do_sample=False)[0]['summary_text']
            for chunk in chunks
        ])

        os.remove(audio_path)
        return render_template('result.html', transcription=cleaned_text, summary=summarized_text)
    except Exception as e:
        print(f"Error: {e}")
        return "<h3 style='color:red;'>An error occurred while processing the file.</h3>", 500

if __name__ == '__main__':
    os.makedirs("uploads", exist_ok=True)
    app.run()

import streamlit as st
import os
import tempfile
import moviepy.editor as mp
import speech_recognition as sr
import groq
import PyPDF2
import docx
import csv
import json
import magic
from pathlib import Path
import requests
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(page_title="Code Review Summarizer", layout="wide")

# App title and description
st.title("AI-Powered Code Review Summarizer")
st.write("Upload meeting recordings (MP4) and connect to GitHub repositories to extract actionable insights")

# Initialize session state variables
if 'extracted_text' not in st.session_state:
    st.session_state['extracted_text'] = ""
if 'summary' not in st.session_state:
    st.session_state['summary'] = ""
if 'action_items' not in st.session_state:
    st.session_state['action_items'] = []
if 'code_feedback' not in st.session_state:
    st.session_state['code_feedback'] = {}
if 'processing_complete' not in st.session_state:
    st.session_state['processing_complete'] = False

# Function to extract audio from video
def extract_audio(video_file):
    """Extract audio from uploaded video file"""
    # Create temporary files
    temp_video_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    
    # Save paths
    video_path = temp_video_file.name
    audio_path = temp_audio_file.name
    
    # Close file handles
    temp_video_file.close()
    temp_audio_file.close()
    
    # Write video data to temp file
    with open(video_path, 'wb') as f:
        f.write(video_file.read())
    
    # Extract audio from video
    try:
        with st.spinner("Extracting audio from video..."):
            video = mp.VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)
            video.close()
        
        # Try to delete the video file
        try:
            os.unlink(video_path)
        except:
            pass
        
        return audio_path
    except Exception as e:
        st.error(f"Error extracting audio: {str(e)}")
        # Make sure to close the video in case of errors
        try:
            video.close()
        except:
            pass
        raise e

# Function to transcribe audio to text
def speech_to_text(audio_path):
    """Convert audio to text using speech recognition"""
    recognizer = sr.Recognizer()
    
    # Create a progress bar for transcription
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text("Starting transcription...")
    
    # Get audio duration
    audio_clip = mp.AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    audio_clip.close()
    
    full_text = ""
    
    with sr.AudioFile(audio_path) as source:
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source)
        
        # Process audio in chunks
        chunk_duration = 30  # seconds
        offset = 0
        
        while offset < audio_duration:
            chunk_text = ""
            audio_data = recognizer.record(source, duration=min(chunk_duration, audio_duration - offset))
            try:
                chunk_text = recognizer.recognize_google(audio_data)
                full_text += chunk_text + " "
            except sr.UnknownValueError:
                full_text += "[inaudible] "
            except sr.RequestError as e:
                st.error(f"API error: {e}")
                return f"Error: {e}"
            
            # Update progress
            progress = min(1.0, (offset + chunk_duration) / audio_duration)
            progress_bar.progress(progress)
            status_text.text(f"Transcribing: {int(progress * 100)}% complete")
            
            offset += chunk_duration
    
    # Try to delete the audio file
    try:
        os.unlink(audio_path)
    except:
        pass
    
    progress_bar.progress(1.0)
    status_text.text("Transcription complete!")
    
    return full_text.strip()

# Function to get repository files
def get_github_files(repo_url, branch, github_token):
    """Fetch file content from GitHub repository"""
    # Clean URL format
    clean_url = repo_url.rstrip('/')
    if clean_url.endswith('.git'):
        clean_url = clean_url[:-4]
    
    # Extract owner and repo name
    repo_parts = clean_url.split('github.com/')[-1].split('/')
    if len(repo_parts) < 2:
        return None, "Invalid GitHub URL format"
    
    owner = repo_parts[0]
    repo = repo_parts[1]
    
    # Set up headers
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    # Get repository contents
    files_dict = {}
    excluded_dirs = ["node_modules", ".git", "__pycache__", "dist", "build"]
    excluded_extensions = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".ttf"]
    
    def is_excluded_file(path):
        """Check if file should be excluded"""
        for dir_name in excluded_dirs:
            if f"/{dir_name}/" in path or path.startswith(f"{dir_name}/"):
                return True
        
        for ext in excluded_extensions:
            if path.endswith(ext):
                return True
        
        return False
    
    def process_contents(path=""):
        """Recursively process repository contents"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        if branch:
            url += f"?ref={branch}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            contents = response.json()
            
            # Handle array response (directory)
            if isinstance(contents, list):
                for item in contents:
                    if item["type"] == "file" and not is_excluded_file(item["path"]):
                        # Get file content
                        file_response = requests.get(item["download_url"], headers=headers)
                        file_content = file_response.text
                        files_dict[item["path"]] = file_content
                    
                    elif item["type"] == "dir" and not is_excluded_file(item["path"]):
                        process_contents(item["path"])
            
            # Handle object response (file)
            elif isinstance(contents, dict) and contents["type"] == "file":
                file_response = requests.get(contents["download_url"], headers=headers)
                file_content = file_response.text
                files_dict[contents["path"]] = file_content
        
        except requests.exceptions.RequestException as e:
            if "404" in str(e):
                return None, f"Repository not found: {owner}/{repo}"
            return None, f"GitHub API error: {str(e)}"
    
    try:
        process_contents()
        return files_dict, None
    except Exception as e:
        return None, f"Error fetching repository: {str(e)}"

# Function to analyze extracted text and map to GitHub
def analyze_code_review(text, files_dict, model_name, groq_api_key):
    """Analyze code review transcript and generate insights linked to GitHub files"""
    # Initialize the Groq client
    client = groq.Client(api_key=groq_api_key)
    
    # Create analysis prompt with repository context
    file_list = "\n".join([f"- {path}" for path in files_dict.keys()])
    
    prompt = f"""
    You are analyzing a transcript from a code review meeting. The transcript is from a recorded video meeting.
    
    The GitHub repository being discussed contains these files:
    {file_list}
    
    Based on the meeting transcript below, please:
    1. Identify the main code files being discussed
    2. Extract specific action items and who they're assigned to
    3. Summarize key feedback for each code file mentioned
    4. Note any architectural decisions or important changes
    
    Transcript:
    {text}
    
    Format your response in JSON with these sections:
    - summary: Overall meeting summary
    - action_items: List of {{"task": "...", "assignee": "...", "file": "..."}}
    - file_feedback: Dictionary mapping file paths to feedback
    - decisions: List of architectural or design decisions made
    
    Return ONLY valid JSON.
    """
    
    # Generate analysis using Groq API
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a code review analysis assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2000
    )
    
    # Extract and parse the JSON response
    try:
        result_text = response.choices[0].message.content
        # Extract JSON from the response (in case there's text around it)
        json_pattern = r'```json\s*([\s\S]*?)\s*```|({[\s\S]*})'
        match = re.search(json_pattern, result_text)
        
        if match:
            json_str = match.group(1) or match.group(2)
            analysis_data = json.loads(json_str)
        else:
            analysis_data = json.loads(result_text)
            
        return analysis_data
    except json.JSONDecodeError:
        # If JSON parsing fails, generate a structured report instead
        st.warning("Could not parse JSON response, generating text report instead")
        summary_prompt = f"""
        Analyze this code review transcript and provide a structured report:
        
        {text}
        
        Focus on key feedback, action items, and decisions made.
        """
        
        report_response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a code review analysis assistant."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        return {
            "summary": report_response.choices[0].message.content,
            "action_items": [],
            "file_feedback": {},
            "decisions": []
        }

# Function to generate a simple summary from text or GitHub content
def generate_simple_summary(text, model_name, groq_api_key):
    """Generate a basic summary from text when no GitHub repository is available"""
    client = groq.Client(api_key=groq_api_key)
    
    prompt = f"""
    Analyze the following content (which could be from a code review, meeting transcript, or documentation):
    
    {text[:8000]}  # Limit text length to avoid token issues
    
    Please provide:
    1. A concise summary of the key points
    2. Important action items or tasks mentioned
    3. Any technical decisions or discussions
    
    Format your response as a well-structured report.
    """
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful content analysis assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1500
    )
    
    return response.choices[0].message.content

# Function to extract text from any file
def extract_text_from_file(uploaded_file):
    """Extract text from an uploaded file (fallback for non-MP4 files)"""
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_path = temp_file.name
    temp_file.close()
    
    # Write uploaded file to temp file
    with open(temp_file_path, 'wb') as f:
        f.write(uploaded_file.read())
    
    # Get file type
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(temp_file_path)
    
    # Extract text based on file type
    extracted_text = ""
    try:
        if 'video' in mime_type:
            # Process as video
            audio_path = extract_audio(uploaded_file)
            extracted_text = speech_to_text(audio_path)
        elif 'audio' in mime_type:
            # Direct audio processing
            with open(temp_file_path, 'rb') as f:
                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_audio_path = temp_audio.name
                temp_audio.close()
                
                # Convert to wav if needed
                audio_clip = mp.AudioFileClip(temp_file_path)
                audio_clip.write_audiofile(temp_audio_path, verbose=False, logger=None)
                audio_clip.close()
                
                extracted_text = speech_to_text(temp_audio_path)
        elif mime_type == 'application/pdf':
            with open(temp_file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    extracted_text += page.extract_text() + "\n"
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = docx.Document(temp_file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            extracted_text = '\n'.join(full_text)
        elif 'text/' in mime_type:
            with open(temp_file_path, 'r', encoding='utf-8', errors='replace') as f:
                extracted_text = f.read()
        else:
            # For unsupported files, try as text
            try:
                with open(temp_file_path, 'r', encoding='utf-8', errors='replace') as f:
                    extracted_text = f.read()
            except:
                extracted_text = f"Unsupported file type: {mime_type}"
    except Exception as e:
        extracted_text = f"Error extracting text: {str(e)}"
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass
    
    return extracted_text

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    groq_api_key = st.text_input("Enter Groq API Key", type="password")
    model_name = st.text_input("Enter Model Name", value="llama3-70b-8192")
    github_token = st.text_input("GitHub Token (for private repos)", type="password")
    
    st.markdown("---")
    st.header("Instructions")
    st.markdown("""
    1. Enter your Groq API key
    2. Upload a meeting recording (MP4) or other file
    3. Optionally enter GitHub repository URL
    4. Process and generate insights
    """)
    
    # Debug information in sidebar (can be removed in production)
    if st.checkbox("Show Debug Info"):
        st.write("Session State Variables:")
        st.write(f"- Extracted Text Length: {len(st.session_state['extracted_text'])}")
        st.write(f"- Summary Available: {'Yes' if st.session_state['summary'] else 'No'}")
        st.write(f"- Processing Complete: {st.session_state['processing_complete']}")

# Main interface with tabs
tab1, tab2 = st.tabs(["Meeting Analysis", "Results"])

with tab1:
    st.header("Upload Meeting Recording")
    uploaded_file = st.file_uploader("Upload MP4 video of code review meeting or any other file", 
                                    type=['mp4', 'wav', 'mp3', 'pdf', 'docx', 'txt'])
    
    col1, col2 = st.columns(2)
    with col1:
        repo_url = st.text_input("GitHub Repository URL (optional)", 
                                placeholder="https://github.com/username/repo")
    with col2:
        branch = st.text_input("Branch/Tag (optional)", value="main")
    
    # Add a simplified mode option
    simple_mode = st.checkbox("Simple Mode (Skip GitHub integration)", 
                            value=False,
                            help="Use this if you only want to extract text and generate a summary without GitHub integration")
    
    if uploaded_file is not None and st.button("Process Content"):
        if not groq_api_key:
            st.error("Please enter your Groq API key in the sidebar")
        else:
            try:
                # Extract text from the uploaded file
                with st.spinner("Processing uploaded file..."):
                    extracted_text = extract_text_from_file(uploaded_file)
                    
                    # Store extracted text in session state
                    st.session_state['extracted_text'] = extracted_text
                    
                    # Display confirmation
                    if extracted_text:
                        st.success(f"Successfully extracted text ({len(extracted_text)} characters)")
                        st.info("Preview of extracted text:")
                        st.text(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
                
                # Process GitHub repository if URL is provided and not in simple mode
                files_dict = {}
                if repo_url and not simple_mode:
                    with st.spinner("Fetching GitHub repository..."):
                        files_dict, error = get_github_files(repo_url, branch, github_token)
                        if error:
                            st.error(error)
                        else:
                            st.success(f"Successfully fetched {len(files_dict)} files from the repository")
                
                # Generate analysis based on the available content
                if extracted_text:
                    with st.spinner(f"Analyzing content with {model_name}..."):
                        if files_dict and not simple_mode:
                            # Full analysis with GitHub integration
                            analysis = analyze_code_review(extracted_text, files_dict, model_name, groq_api_key)
                            st.session_state['summary'] = analysis.get('summary', '')
                            st.session_state['action_items'] = analysis.get('action_items', [])
                            st.session_state['code_feedback'] = analysis.get('file_feedback', {})
                            st.session_state['decisions'] = analysis.get('decisions', [])
                        else:
                            # Simple analysis without GitHub
                            summary = generate_simple_summary(extracted_text, model_name, groq_api_key)
                            st.session_state['summary'] = summary
                            st.session_state['action_items'] = []
                            st.session_state['code_feedback'] = {}
                        
                        # Set processing complete flag
                        st.session_state['processing_complete'] = True
                        
                        # Notify user to check results tab
                        st.success("Analysis complete! View results in the Results tab.")
                        # Auto-switch to results tab
                        st.balloons()
            
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

with tab2:
    # Show a message if no processing has been done yet
    if not st.session_state['processing_complete']:
        st.info("No results to display yet. Process a file first in the Meeting Analysis tab.")
    else:
        st.header("Content Analysis Results")
        
        # Always show the extracted text 
        st.subheader("Extracted Text")
        if st.session_state['extracted_text']:
            with st.expander("View Full Extracted Text", expanded=False):
                st.text_area("Text Content", st.session_state['extracted_text'], height=300)
                # ADD UNIQUE KEY to fix duplicate widget error
                st.download_button(
                    label="Download Extracted Text",
                    data=st.session_state['extracted_text'],
                    file_name="extracted_text.txt",
                    mime="text/plain",
                    key="download_extracted_text_1"  # Added unique key here
                )
        else:
            st.warning("No text was extracted. There might have been an issue with the file processing.")
        
        # Display summary
        st.subheader("Analysis Summary")
        if st.session_state['summary']:
            st.markdown(st.session_state['summary'])
        else:
            st.warning("No summary was generated. Please check if text extraction was successful.")
        
        # Display action items if available
        if st.session_state['action_items']:
            st.subheader("Action Items")
            for item in st.session_state['action_items']:
                st.markdown(f"- **{item.get('task')}** - Assigned to: {item.get('assignee')} ({item.get('file', 'No file specified')})")
        
        # Display file feedback if available
        if st.session_state['code_feedback']:
            st.subheader("File Feedback")
            for file_path, feedback in st.session_state['code_feedback'].items():
                with st.expander(f"File: {file_path}"):
                    st.markdown(feedback)
        
        # Display decisions if available
        if 'decisions' in st.session_state and st.session_state['decisions']:
            st.subheader("Key Decisions")
            for decision in st.session_state['decisions']:
                st.markdown(f"- {decision}")
        
        # Download options
        st.subheader("Download Options")
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state['summary']:
                # Create a formatted report for download
                report = f"""# Content Analysis Report\n\n## Summary\n{st.session_state['summary']}\n\n"""
                
                if st.session_state['action_items']:
                    report += "## Action Items\n"
                    for item in st.session_state['action_items']:
                        report += f"- {item.get('task')} - Assigned to: {item.get('assignee')} ({item.get('file', 'No file')})\n"
                
                if st.session_state['code_feedback']:
                    report += "\n## File Feedback\n"
                    for file_path, feedback in st.session_state['code_feedback'].items():
                        report += f"### {file_path}\n{feedback}\n\n"
                
                if 'decisions' in st.session_state and st.session_state['decisions']:
                    report += "\n## Key Decisions\n"
                    for decision in st.session_state['decisions']:
                        report += f"- {decision}\n"
                
                st.download_button(
                    label="Download Analysis Report",
                    data=report,
                    file_name="content_analysis_report.md",
                    mime="text/markdown",
                    key="download_analysis_report"  # Added unique key here
                )
        
        with col2:
            if st.session_state['extracted_text']:
                st.download_button(
                    label="Download Extracted Text",
                    data=st.session_state['extracted_text'],
                    file_name="extracted_text.txt",
                    mime="text/plain",
                    key="download_extracted_text_2"  # Added unique key here
                )


  import streamlit as st
import os
import tempfile
import moviepy.editor as mp
import speech_recognition as sr
from groq import Groq
import requests
import json
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import re

# Load environment variables (for Groq API key if needed)
load_dotenv()

# Set page configuration
st.set_page_config(page_title="AI Code Review Summarizer", layout="wide")

# App title and description
st.title("AI-Powered Code Review Summarizer")
st.write("Upload meeting recordings or documents and integrate with GitHub and Asana for actionable insights.")

# Session state initialization
if 'meeting_archive' not in st.session_state:
    st.session_state['meeting_archive'] = []
if 'processing_complete' not in st.session_state:
    st.session_state['processing_complete'] = False
if 'extracted_text' not in st.session_state:
    st.session_state['extracted_text'] = ""
if 'summary_data' not in st.session_state:
    st.session_state['summary_data'] = {}
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# --------------------------------------------------------------------
# Utility Functions
# --------------------------------------------------------------------

def extract_audio(file):
    """Extract and convert audio from a video or audio file to a PCM-compatible WAV."""
    temp_source_path = None
    try:
        file_extension = file.name.split('.')[-1].lower()
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp_file:
            temp_file.write(file.read())
            temp_source_path = temp_file.name

        # Convert to WAV if necessary
        if file_extension == 'mp4':  # Video file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                video = mp.VideoFileClip(temp_source_path)
                video.audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
                video.close()
                audio_path = temp_audio.name
        elif file_extension == 'mp3':  # MP3 file conversion to WAV
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                audio_clip = mp.AudioFileClip(temp_source_path)
                audio_clip.write_audiofile(temp_audio.name, verbose=False, logger=None)
                audio_clip.close()
                audio_path = temp_audio.name
        elif file_extension == 'wav':  # Already WAV
            audio_path = temp_source_path
            temp_source_path = None  # Do not delete later
        else:
            raise ValueError("Unsupported file format. Use mp4, mp3, or wav.")
        return audio_path
    except Exception as e:
        st.error(f"Error extracting audio: {str(e)}")
        return None
    finally:
        if temp_source_path and os.path.exists(temp_source_path):
            try:
                os.unlink(temp_source_path)
            except Exception as cleanup_error:
                st.error(f"Error cleaning up source file: {cleanup_error}")

def speech_to_text(audio_path):
    """Convert audio to text and delete the audio file afterwards."""
    if not audio_path:
        return ""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                return text
            except sr.UnknownValueError:
                return "[inaudible]"
            except sr.RequestError as e:
                st.error(f"Speech recognition error: {e}")
                return ""
    finally:
        if os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except Exception as cleanup_error:
                st.error(f"Error cleaning up audio file: {cleanup_error}")

# --- Updated GitHub integration functions ---
def get_github_files(repo_url, branch, github_token):
    """Fetch file content from GitHub repository recursively, excluding unwanted files."""
    # Clean URL format
    clean_url = repo_url.rstrip('/')
    if clean_url.endswith('.git'):
        clean_url = clean_url[:-4]
    
    # Extract owner and repo name
    repo_parts = clean_url.split('github.com/')[-1].split('/')
    if len(repo_parts) < 2:
        return None, "Invalid GitHub URL format"
    
    owner, repo = repo_parts[0], repo_parts[1]
    
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    files_dict = {}
    excluded_dirs = ["node_modules", ".git", "__pycache__", "dist", "build"]
    excluded_extensions = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".ttf", ".mp4"]

    def is_excluded_file(path):
        for dir_name in excluded_dirs:
            if f"/{dir_name}/" in path or path.startswith(f"{dir_name}/"):
                return True
        for ext in excluded_extensions:
            if path.endswith(ext):
                return True
        return False

    def process_contents(path=""):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        if branch:
            url += f"?ref={branch}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            contents = response.json()
            if isinstance(contents, list):
                for item in contents:
                    if item["type"] == "file" and not is_excluded_file(item["path"]):
                        file_resp = requests.get(item["download_url"], headers=headers)
                        files_dict[item["path"]] = file_resp.text
                    elif item["type"] == "dir" and not is_excluded_file(item["path"]):
                        process_contents(item["path"])
            elif isinstance(contents, dict) and contents["type"] == "file":
                file_resp = requests.get(contents["download_url"], headers=headers)
                files_dict[contents["path"]] = file_resp.text
        except requests.exceptions.RequestException as e:
            if "404" in str(e):
                return None, f"Repository not found: {owner}/{repo}"
            return None, f"GitHub API error: {str(e)}"

    try:
        process_contents()
        return files_dict, None
    except Exception as e:
        return None, f"Error fetching repository: {str(e)}"

def extract_suggested_changes(file_feedback, action_items):
    """Extract suggested code changes from feedback and action items."""
    suggested_changes = []
    code_pattern = r'```(?:\w*)\n([\s\S]*?)\n```'
    for file_path, feedback in file_feedback.items():
        code_blocks = re.findall(code_pattern, feedback)
        for code in code_blocks:
            if code.strip():
                suggested_changes.append({
                    'file': file_path,
                    'code': code,
                    'description': f"Suggested change from code review: {feedback.split('.')[0]}."
                })
    for item in action_items:
        if 'file' in item and item['file'] and item['task']:
            if any(keyword in item['task'].lower() for keyword in ['add', 'change', 'modify', 'implement', 'fix']):
                suggested_changes.append({
                    'file': item['file'],
                    'code': None,
                    'description': f"Action item: {item['task']} (Assigned to: {item['assignee']})"
                })
    return suggested_changes

def get_language_from_file(file_path):
    """Determine programming language from file extension."""
    extension = file_path.split('.')[-1].lower()
    language_map = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'html': 'html',
        'css': 'css',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'cs': 'csharp',
        'go': 'go',
        'rb': 'ruby',
        'php': 'php',
        'swift': 'swift',
        'kt': 'kotlin',
        'md': 'markdown'
    }
    return language_map.get(extension, 'text')

def apply_change_to_github(repo_url, branch, github_token, file_path, new_code, commit_message):
    """Apply changes to a file in the GitHub repository using PyGithub."""
    if not github_token:
        return False, "GitHub token is required to make changes"
    try:
        from github import Github, GithubException
        g = Github(github_token)
        clean_url = repo_url.rstrip('/')
        if clean_url.endswith('.git'):
            clean_url = clean_url[:-4]
        repo_parts = clean_url.split('github.com/')[-1].split('/')
        owner = repo_parts[0]
        repo_name = repo_parts[1]
        repo_obj = g.get_repo(f"{owner}/{repo_name}")
        try:
            file_content = repo_obj.get_contents(file_path, ref=branch)
            current_content = file_content.decoded_content.decode('utf-8')
        except GithubException:
            return False, f"File {file_path} not found in repository"
        updated_content = new_code if new_code else current_content
        try:
            repo_obj.update_file(
                file_path,
                commit_message,
                updated_content,
                file_content.sha,
                branch=branch
            )
            return True, f"Successfully updated {file_path}"
        except GithubException as e:
            return False, f"Error updating file: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def create_pull_request(repo_url, branch, github_token, title, description):
    """Create a pull request for changes made using PyGithub."""
    if not github_token:
        return False, "GitHub token is required to create a pull request"
    try:
        from github import Github
        g = Github(github_token)
        clean_url = repo_url.rstrip('/')
        if clean_url.endswith('.git'):
            clean_url = clean_url[:-4]
        repo_parts = clean_url.split('github.com/')[-1].split('/')
        owner = repo_parts[0]
        repo_name = repo_parts[1]
        repo_obj = g.get_repo(f"{owner}/{repo_name}")
        source_branch = f"code-review-changes-{uuid.uuid4().hex[:6]}"
        source_branch_ref = repo_obj.get_git_ref(f"heads/{branch}")
        source_branch_sha = source_branch_ref.object.sha
        try:
            repo_obj.create_git_ref(ref=f"refs/heads/{source_branch}", sha=source_branch_sha)
        except Exception:
            pass  # branch may already exist
        pr = repo_obj.create_pull(
            title=title,
            body=description,
            head=source_branch,
            base=branch
        )
        return True, pr.html_url
    except Exception as e:
        return False, f"Error creating pull request: {str(e)}"

# Groq and Chatbot functions
def analyze_with_groq(text, files_dict=None):
    """Analyze text using Groq API."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    file_list = "\n".join(files_dict.keys()) if files_dict else "No files provided."
    prompt = f"""
Analyze this code review meeting transcript:
{text}

GitHub files: {file_list}

Provide:
1. A summary
2. Action items (task, assignee)
3. Code feedback (file, feedback)
4. Decisions

Return JSON:
{{
    "summary": "...",
    "action_items": [{{"task": "...", "assignee": "..."}}],
    "code_feedback": {{"file_path": "feedback"}},
    "decisions": ["..."]
}}
"""
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.5
        )
        raw_response = response.choices[0].message.content
        st.write("Raw Groq response:", raw_response)
        return json.loads(raw_response)
    except json.JSONDecodeError:
        st.error("Failed to parse Groq response.")
        return {"summary": raw_response if 'raw_response' in locals() else "", "action_items": [], "code_feedback": {}, "decisions": []}
    except Exception as e:
        st.error(f"Groq API error: {e}")
        return {"summary": "Analysis failed.", "action_items": [], "code_feedback": {}, "decisions": []}

def chatbot_response(query, summary_data):
    """Generate chatbot response using Groq and summary data."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    context = json.dumps(summary_data, indent=2)
    prompt = f"""
Based on this meeting summary:
{context}

Answer this question: {query}
"""
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Chatbot error: {e}")
        return "Sorry, I couldn't process your request."

# Asana integration function
def create_asana_task(asana_pat, project_id, task_name, task_notes=None, assignee=None):
    """
    Create a task in Asana.
    :param asana_pat: Asana Personal Access Token.
    :param project_id: ID of the Asana project.
    :param task_name: Task name.
    :param task_notes: Task description/notes.
    :param assignee: (Optional) Assignee's email or user ID.
    :return: True if created successfully, False otherwise.
    """
    url = 'https://app.asana.com/api/1.0/tasks'
    headers = {
        'Authorization': f'Bearer {asana_pat}',
        'Content-Type': 'application/json'
    }
    payload = {
        "data": {
            "name": task_name,
            "notes": task_notes,
            "projects": [project_id]
        }
    }
    if assignee:
        payload["data"]["assignee"] = assignee
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            return True
        else:
            st.error(f"Asana API error: {response.text}")
            return False
    except Exception as e:
        st.error(f"Asana API exception: {e}")
        return False

# SMTP email function
def send_email(smtp_server, smtp_port, sender_email, sender_password, recipients, summary_data):
    """Send meeting summary via email using provided SMTP credentials."""
    msg = MIMEMultipart()
    msg['Subject'] = "Code Review Meeting Summary"
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    body = f"""
    <h2>Meeting Summary</h2>
    <p>{summary_data.get('summary', 'No summary available')}</p>
    <h3>Action Items</h3>
    <ul>
      {''.join([f'<li>{item["task"]} (Assignee: {item["assignee"]})</li>' for item in summary_data.get('action_items', [])])}
    </ul>
    """
    msg.attach(MIMEText(body, 'html'))
    try:
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# --------------------------------------------------------------------
# UI Functions
# --------------------------------------------------------------------

def upload_tab():
    """Upload and process meeting content."""
    st.header("Upload & Process")
    uploaded_file = st.file_uploader("Upload audio/video", type=['mp4', 'mp3', 'wav'])
    repo_url = st.text_input("GitHub Repo URL (optional)")
    github_token = st.text_input("GitHub Token (optional)", type="password")
    branch = st.text_input("GitHub Branch (default: main)", value="main")
    
    if st.button("Process"):
        if not uploaded_file:
            st.error("Please upload a file.")
            return
        with st.spinner("Processing..."):
            audio_path = extract_audio(uploaded_file)
            if not audio_path:
                return
            text = speech_to_text(audio_path)
            files_dict = {}
            if repo_url:
                files_dict, err = get_github_files(repo_url, branch, github_token)
                if err:
                    st.error(err)
            summary_data = analyze_with_groq(text, files_dict)
            st.session_state['extracted_text'] = text
            st.session_state['summary_data'] = summary_data
            st.session_state['processing_complete'] = True
            st.session_state['meeting_archive'].append({
                "id": str(uuid.uuid4()),
                "text": text,
                "summary_data": summary_data
            })
            st.success("Processing complete! Check other tabs.")

def summary_tab():
    """Display summary and integrate with Asana."""
    st.header("Summary & Insights")
    if not st.session_state['processing_complete']:
        st.info("Process a meeting first.")
        return
    data = st.session_state['summary_data']
    st.subheader("Summary")
    st.write(data.get('summary', 'No summary available'))
    st.subheader("Action Items")
    for item in data.get('action_items', []):
        st.write(f"- {item.get('task', '')} (Assignee: {item.get('assignee', '')})")
    st.subheader("Code Feedback")
    for file, feedback in data.get('code_feedback', {}).items():
        st.write(f"**{file}**: {feedback}")
    st.subheader("Decisions")
    for decision in data.get('decisions', []):
        st.write(f"- {decision}")
    
    st.subheader("Asana Integration")
    col1, col2 = st.columns(2)
    with col1:
        asana_pat = st.text_input("Asana Personal Access Token (PAT)", type="password")
    with col2:
        asana_project_id = st.text_input("Asana Project ID")
    
    if st.button("Send to Asana"):
        if not asana_pat or not asana_project_id:
            st.error("Please fill in all Asana fields.")
            return
        for item in data.get('action_items', []):
            task_name = item.get('task', 'Untitled Task')
            task_notes = f"Assignee: {item.get('assignee', 'N/A')}"
            if create_asana_task(asana_pat, asana_project_id, task_name, task_notes, item.get('assignee', '')):
                st.success(f"Task '{task_name}' created in Asana.")
            else:
                st.error(f"Failed to create task '{task_name}'.")

def chat_tab():
    """Interactive chatbot for meeting content."""
    st.header("Chat with Meeting")
    if not st.session_state['processing_complete']:
        st.info("Process a meeting first.")
        return
    chat_container = st.container()
    for msg in st.session_state['chat_history']:
        chat_container.chat_message(msg["role"]).write(msg["content"])
    if query := st.chat_input("Ask about the meeting..."):
        st.session_state['chat_history'].append({"role": "user", "content": query})
        chat_container.chat_message("user").write(query)
        response = chatbot_response(query, st.session_state['summary_data'])
        st.session_state['chat_history'].append({"role": "ai", "content": response})
        chat_container.chat_message("ai").write(response)

def email_tab():
    """Send meeting summary via email with SMTP credentials provided via UI."""
    st.header("Email Summary")
    if not st.session_state['processing_complete']:
        st.info("Process a meeting first.")
        return
    col1, col2 = st.columns(2)
    with col1:
        smtp_server = st.text_input("SMTP Server", value="")
    with col2:
        smtp_port = st.text_input("SMTP Port", value="587")
    sender_email = st.text_input("Sender Email", value="")
    sender_password = st.text_input("Sender Password", type="password")
    recipients = st.text_input("Recipient Emails (comma-separated)", "")
    if st.button("Send Email"):
        if not (smtp_server and smtp_port and sender_email and sender_password and recipients):
            st.error("Please fill in all SMTP and recipient fields.")
            return
        recipient_list = [r.strip() for r in recipients.split(",")]
        if send_email(smtp_server, smtp_port, sender_email, sender_password, recipient_list, st.session_state['summary_data']):
            st.success("Email sent successfully!")
        else:
            st.error("Failed to send email.")

# --------------------------------------------------------------------
# Main UI
# --------------------------------------------------------------------
def main():
    tabs = st.tabs(["Upload & Process", "Summary & Insights", "Chat", "Email"])
    with tabs[0]:
        upload_tab()
    with tabs[1]:
        summary_tab()
    with tabs[2]:
        chat_tab()
    with tabs[3]:
        email_tab()

if __name__ == "__main__":
    main()

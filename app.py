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
import base64

# Load environment variables (e.g., GROQ_API_KEY)
load_dotenv()
// CODE REVIEW: Missing code to integrate Rock API and assign a task in Asana project
// RECOMMENDATION: Add the specified line of code to integrate the Rock API and assign a task in the Asana project
// SUGGESTED CODE:
// print("I love Rock API") and asana_task_assignment() function call

# Set page configuration
st.set_page_config(page_title="AI Code Review Summarizer", layout="wide")

# App title and description
st.title("AI-Powered Code Review Summarizer")
st.write("Upload meeting recordings/documents and integrate with GitHub, Asana, and Email for actionable insights.")

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
if 'asana_tasks_created' not in st.session_state:
    st.session_state['asana_tasks_created'] = []

# --------------------------------------------------------------------
# GitHub Integration Functions
# --------------------------------------------------------------------

def get_github_files(repo_url, branch, github_token):
    """
    Fetch file content from a GitHub repository.
    Handles duplicate file names by using full relative paths.
    """
    clean_url = repo_url.rstrip('/')
    if clean_url.endswith('.git'):
        clean_url = clean_url[:-4]

    repo_parts = clean_url.split('github.com/')[-1].split('/')
    if len(repo_parts) < 2:
        return None, "Invalid GitHub URL format"

    owner, repo = repo_parts[0], repo_parts[1]
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    files_dict = {}
    excluded_dirs = ["node_modules", ".git", "pycache", "dist", "build"]
    excluded_extensions = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".ttf"]

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
                        file_response = requests.get(item["download_url"], headers=headers)
                        files_dict[item["path"]] = file_response.text
                    elif item["type"] == "dir" and not is_excluded_file(item["path"]):
                        process_contents(item["path"])
            elif isinstance(contents, dict) and contents["type"] == "file":
                file_response = requests.get(contents["download_url"], headers=headers)
                files_dict[contents["path"]] = file_response.text
        except requests.exceptions.RequestException as e:
            if "404" in str(e):
                return None, f"Repository not found: {owner}/{repo}"
            return None, f"GitHub API error: {str(e)}"

    try:
        process_contents()
        return files_dict, None
    except Exception as e:
        return None, f"Error fetching repository: {str(e)}"

def update_github_comments(repo_url, branch, github_token, comment_body):
    """
    Update GitHub with meeting insights.
    This function creates an issue with the meeting summary.
    """
    clean_url = repo_url.rstrip('/')
    if clean_url.endswith('.git'):
        clean_url = clean_url[:-4]
    repo_parts = clean_url.split('github.com/')[-1].split('/')
    if len(repo_parts) < 2:
        return False
    owner, repo = repo_parts[0], repo_parts[1]

    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    # Create an issue with the meeting summary
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    data = {
        "title": "Automated Code Review Meeting Summary",
        "body": comment_body
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 201

# --------------------------------------------------------------------
# Utility Functions
# --------------------------------------------------------------------

def extract_audio(file):
    """Extract and convert audio from a video or audio file to a PCM-compatible WAV."""
    temp_source_path = None
    try:
        file_extension = file.name.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp_file:
            temp_file.write(file.read())
            temp_source_path = temp_file.name

        if file_extension == 'mp4':
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                video = mp.VideoFileClip(temp_source_path)
                video.audio.write_audiofile(temp_audio.name, verbose=False, logger=None)
                video.close()
                audio_path = temp_audio.name
        elif file_extension == 'mp3':
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                audio_clip = mp.AudioFileClip(temp_source_path)
                audio_clip.write_audiofile(temp_audio.name, verbose=False, logger=None)
                audio_clip.close()
                audio_path = temp_audio.name
        elif file_extension == 'wav':
            audio_path = temp_source_path
            temp_source_path = None
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
        return json.loads(raw_response)
    except json.JSONDecodeError:
        # Try to extract JSON from text (in case model adds commentary)
        try:
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                extracted_json = raw_response[json_start:json_end]
                return json.loads(extracted_json)
        except:
            pass
        
        st.error("Failed to parse Groq response.")
        return {"summary": raw_response if 'raw_response' in locals() else "", 
                "action_items": [], 
                "code_feedback": {}, 
                "decisions": []}
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
# Asana Functions (Improved)
# --------------------------------------------------------------------

def extract_asana_project_id(project_url):
    """Extract project ID from Asana URL."""
    # Extract ID from URLs like: https://app.asana.com/0/1209864167784857/1209864173573367
    pattern = r'asana\.com/\d+/(\d+)'
    matches = re.search(pattern, project_url)
    if matches:
        return matches.group(1)
    return project_url  # Return as-is if no match (might be direct ID)

def validate_asana_credentials(asana_pat, project_id):
    """Validate Asana credentials by making a test API call."""
    if not asana_pat or not project_id:
        return False, "Missing Asana PAT or Project ID"
    
    headers = {
        'Authorization': f'Bearer {asana_pat}',
        'Accept': 'application/json'
    }
    
    # Try to get project details to validate credentials and project ID
    url = f'https://app.asana.com/api/1.0/projects/{project_id}'
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True, "Validated successfully"
        elif response.status_code == 401:
            return False, "Invalid Asana Personal Access Token"
        elif response.status_code == 404:
            return False, "Project not found. Please check the Project ID"
        else:
            return False, f"Asana API error: {response.status_code}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def get_asana_users(asana_pat, workspace_gid):
    """Get list of users in an Asana workspace to map assignees."""
    headers = {
        'Authorization': f'Bearer {asana_pat}',
        'Accept': 'application/json'
    }
    
    url = f'https://app.asana.com/api/1.0/workspaces/{workspace_gid}/users'
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json().get('data', [])
            return {user['name'].lower(): user['gid'] for user in users}
        return {}
    except Exception:
        return {}

def get_workspace_from_project(asana_pat, project_id):
    """Get workspace GID from project ID."""
    headers = {
        'Authorization': f'Bearer {asana_pat}',
        'Accept': 'application/json'
    }
    
    url = f'https://app.asana.com/api/1.0/projects/{project_id}'
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('data', {}).get('workspace', {}).get('gid')
        return None
    except Exception:
        return None

def create_asana_task(asana_pat, project_id, task_name, task_notes=None, assignee_name=None):
    """
    Create a task in Asana with improved handling of assignees.
    """
    url = 'https://app.asana.com/api/1.0/tasks'
    headers = {
        'Authorization': f'Bearer {asana_pat}',
        'Content-Type': 'application/json'
    }
    
    # Prepare base payload
    payload = {
        "data": {
            "name": task_name,
            "notes": task_notes or "",
            "projects": [project_id]
        }
    }
    
    # Handle assignee if provided
    if assignee_name and assignee_name.strip().lower() not in ['', 'n/a', 'none', 'unassigned']:
        # Get workspace from project to find users
        workspace_gid = get_workspace_from_project(asana_pat, project_id)
        if workspace_gid:
            # Get users in workspace
            users = get_asana_users(asana_pat, workspace_gid)
            # Find closest match for assignee
            assignee_name_lower = assignee_name.strip().lower()
            for name, gid in users.items():
                if assignee_name_lower in name:  # Partial match
                    payload["data"]["assignee"] = gid
                    break
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            task_data = response.json().get('data', {})
            return True, task_data.get('gid', 'unknown')
        else:
            error_msg = response.json().get('errors', [{}])[0].get('message', 'Unknown error')
            return False, f"Asana API error: {error_msg}"
    except Exception as e:
        return False, f"Asana API exception: {str(e)}"

def process_all_asana_tasks(asana_pat, project_id, action_items):
    """Process all action items as Asana tasks in batch."""
    results = []
    for item in action_items:
        task_name = item.get('task', 'Untitled Task')
        assignee = item.get('assignee', '')
        task_notes = f"Assignee: {assignee}\nAutomatically created from code review meeting."
        
        success, task_id = create_asana_task(asana_pat, project_id, task_name, task_notes, assignee)
        results.append({
            "task": task_name,
            "assignee": assignee,
            "success": success,
            "task_id": task_id if success else None,
            "error": task_id if not success else None
        })
    
    return results

# --------------------------------------------------------------------
# UI Functions
# --------------------------------------------------------------------

def upload_tab():
    """Upload and process meeting content (includes GitHub integration)."""
    st.header("Upload & Process")
    uploaded_file = st.file_uploader("Upload audio/video", type=['mp4', 'mp3', 'wav'])
    
    # Direct text input option
    text_input_option = st.checkbox("Or enter meeting transcript directly")
    direct_text = ""
    if text_input_option:
        direct_text = st.text_area("Enter meeting transcript", height=200)
    
    repo_url = st.text_input("GitHub Repo URL (optional)")
    github_token = st.text_input("GitHub Token (optional)", type="password")
    branch = st.text_input("GitHub Branch (default: main)", value="main")
    
    if st.button("Process"):
        if not uploaded_file and not direct_text:
            st.error("Please upload a file or enter a meeting transcript.")
            return
            
        with st.spinner("Processing..."):
            text = ""
            if uploaded_file:
                audio_path = extract_audio(uploaded_file)
                if not audio_path:
                    return
                text = speech_to_text(audio_path)
            else:
                text = direct_text
                
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
            st.success("Processing complete!")
    
    # GitHub integration UI
    if st.session_state.get('processing_complete') and repo_url and github_token:
        st.subheader("Update GitHub with Meeting Summary")
        comment_body = st.text_area("Meeting Summary to post on GitHub (issue body):", 
                                    value=st.session_state['summary_data'].get('summary', ''))
        if st.button("Post Meeting Summary to GitHub"):
            success = update_github_comments(repo_url, branch, github_token, comment_body)
            if success:
                st.success("Meeting summary posted to GitHub as an issue!")
            else:
                st.error("Failed to update GitHub with the meeting summary.")

def summary_tab():
    """Display summary and actionable insights."""
    st.header("Summary & Insights")
    if not st.session_state.get('processing_complete'):
        st.info("Please process a meeting first.")
        return
    data = st.session_state['summary_data']
    st.subheader("Summary")
    st.write(data.get('summary', 'No summary available'))
    st.subheader("Action Items")
    action_items = data.get('action_items', [])
    if not action_items:
        st.info("No action items detected in the meeting.")
    else:
        for item in action_items:
            st.write(f"- {item.get('task', '')} (Assignee: {item.get('assignee', '')})")
    st.subheader("Code Feedback")
    code_feedback = data.get('code_feedback', {})
    if isinstance(code_feedback, dict) and not code_feedback:
        st.info("No code feedback detected in the meeting.")
    else:
        # Handle both dictionary and simple string feedback
        if isinstance(code_feedback, dict):
            for file, feedback in code_feedback.items():
                st.markdown(f"**{file}**:")
                st.code(feedback)
        else:
            st.markdown("**File: app.py**:")
            st.code(code_feedback)
    st.subheader("Decisions")
    decisions = data.get('decisions', [])
    if not decisions:
        st.info("No decisions detected in the meeting.")
    else:
        for decision in decisions:
            st.write(f"- {decision}")
    
    # Add option to download summary as JSON
    if st.button("Download Summary as JSON"):
        json_data = json.dumps(data, indent=2)
        b64 = base64.b64encode(json_data.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="meeting_summary.json">Download JSON</a>'
        st.markdown(href, unsafe_allow_html=True)

def chat_tab():
    """Interactive chatbot for meeting content."""
    st.header("Chat with Meeting")
    if not st.session_state.get('processing_complete'):
        st.info("Please process a meeting first.")
        return
        
    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state['chat_history'] = []
        st.rerun()
        
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
    """Send meeting summary via email using SMTP credentials."""
    st.header("Email Summary")
    if not st.session_state.get('processing_complete'):
        st.info("Please process a meeting first.")
        return
    col1, col2 = st.columns(2)
    with col1:
        smtp_server = st.text_input("SMTP Server", value="")
    with col2:
        smtp_port = st.text_input("SMTP Port", value="587")
    sender_email = st.text_input("Sender Email", value="")
    sender_password = st.text_input("Sender Password", type="password")
    recipients = st.text_input("Recipient Emails (comma-separated)", "")
    
    # Preview email content
    if st.checkbox("Preview email content"):
        st.subheader("Email Preview")
        summary = st.session_state['summary_data'].get('summary', 'No summary available')
        action_items = st.session_state['summary_data'].get('action_items', [])
        st.write("**Subject:** Code Review Meeting Summary")
        st.write("**Body:**")
        st.write("### Meeting Summary")
        st.write(summary)
        st.write("### Action Items")
        for item in action_items:
            st.write(f"- {item.get('task', '')} (Assignee: {item.get('assignee', '')})")
    
    if st.button("Send Email"):
        if not (smtp_server and smtp_port and sender_email and sender_password and recipients):
            st.error("Please fill in all SMTP and recipient fields.")
            return
        recipient_list = [r.strip() for r in recipients.split(",")]
        if send_email(smtp_server, smtp_port, sender_email, sender_password, recipient_list, st.session_state['summary_data']):
            st.success("Email sent successfully!")
        else:
            st.error("Failed to send email.")

def asana_tab():
    """Improved Asana integration with better validation and project ID handling."""
    st.header("Asana Integration")
    if not st.session_state.get('processing_complete'):
        st.info("Please process a meeting first.")
        return
    
    # Display current action items
    st.subheader("Current Action Items")
    action_items = st.session_state['summary_data'].get('action_items', [])
    
    # If no action items found, provide manual entry option
    if not action_items:
        st.warning("No action items were detected in the meeting transcript.")
    else:
        # Show existing action items
        for i, item in enumerate(action_items):
            st.write(f"{i+1}. **{item.get('task', 'Untitled')}** (Assignee: {item.get('assignee', 'Unassigned')})")
    
    # Show Asana integration fields if we have action items
    if action_items:
        st.subheader("Asana Integration")
        # Asana credentials input
        asana_pat = st.text_input("Asana Personal Access Token (PAT)", type="password", key="asana_pat")
        asana_project_url = st.text_input("Asana Project URL or ID", key="asana_project_url", 
                                            help="Paste the full URL or project ID")
        
        # Extract project ID from URL
        project_id = extract_asana_project_id(asana_project_url) if asana_project_url else ""
        
        # Validate inputs and provide real-time feedback
        if asana_pat and project_id:
            # Clear validation if URL changed
            if 'last_asana_project' not in st.session_state or st.session_state.get('last_asana_project') != project_id:
                st.session_state.pop('asana_validated', None)
                st.session_state['last_asana_project'] = project_id
                
            # Check if already validated to avoid repeated API calls
            if 'asana_validated' not in st.session_state:
                with st.spinner("Validating Asana credentials..."):
                    valid, message = validate_asana_credentials(asana_pat, project_id)
                    if valid:
                        st.success(f"✅ Asana credentials validated: {message}")
                        st.session_state['asana_validated'] = True
                    else:
                        st.error(f"❌ Asana validation failed: {message}")
                        st.session_state['asana_validated'] = False
        
        # Process button specifically for Asana
        if st.button("Process Asana Tasks", key="process_asana"):
            if not asana_pat or not project_id:
                st.error("Please provide both Asana PAT and Project ID.")
                return
            
            current_action_items = st.session_state['summary_data'].get('action_items', [])
            if not current_action_items:
                st.error("No action items to process.")
                return
                
            with st.spinner("Creating tasks in Asana..."):
                results = process_all_asana_tasks(asana_pat, project_id, current_action_items)
                
                # Track results for user feedback
                success_count = sum(1 for r in results if r['success'])
                
                if success_count > 0:
                    st.success(f"✅ Successfully created {success_count} tasks in Asana!")
                    
                    # Show details of created tasks
                    st.subheader("Created Tasks")
                    for result in results:
                        if result['success']:
                            st.write(f"✅ '{result['task']}' - Assignee: {result['assignee']}")
                        else:
                            st.write(f"❌ Failed to create '{result['task']}': {result['error']}")
                            
                    # Store created tasks in session state
                    st.session_state['asana_tasks_created'] = results
                    
                else:
                    st.error("Failed to create any tasks in Asana. Please check your credentials and try again.")

# --------------------------------------------------------------------
# Main UI
# --------------------------------------------------------------------
def main():
    tabs = st.tabs(["Upload & Process", "Summary & Insights", "Chat", "Email", "Asana Integration"])
    with tabs[0]:
        upload_tab()
    with tabs[1]:
        summary_tab()
    with tabs[2]:
        chat_tab()
    with tabs[3]:
        email_tab()
    with tabs[4]:
        asana_tab()

if __name__ == "__main__":
    main()
    
    #gemini


# 🚀 AI-Powered Code Review Summarizer

An intelligent tool that transforms code review meeting recordings into actionable insights, mapping feedback directly to your GitHub repositories.


ui for app
![image](https://github.com/user-attachments/assets/e940fe4e-b2cd-48a8-a0b3-aa54f3789b1b)

github integration
![image](https://github.com/user-attachments/assets/2afdb271-9515-437f-ae3d-df58420736bc)

summary&results
![image](https://github.com/user-attachments/assets/56c9f082-a077-4758-9524-ff0d14df28b9)

chatbot support
![image](https://github.com/user-attachments/assets/6656161d-b328-40dd-b1e1-393eb3cfe0d5)

email integration
![image](https://github.com/user-attachments/assets/854f7fbb-f81f-46ef-af9e-f9a30afbe2c3)

asana project management tool integrition
![image](https://github.com/user-attachments/assets/85be4422-ba55-4e88-a2d8-edbe03aeb8ab)


✨ Features

📹 Video Transcription: Convert meeting recordings to searchable text
🔤 Direct Text Input: Option to paste meeting transcripts directly
📄 Multi-Format Support: Process MP4, WAV, and MP3 files
🔄 GitHub Integration: Map feedback to specific repository files
✅ Action Item Extraction: Automatically identify and assign tasks
💬 Code Feedback Analysis: Generate targeted file-specific feedback
🏗️ Decision Documentation: Track architectural and design decisions
💬 Interactive Chat: Ask questions about the meeting content
📧 Email Integration: Send summaries directly to team members
📋 Asana Integration: Create tasks in Asana from meeting action items

🛠️ Installation

--------Clone the repository:

git clone https://github.com/yourusername/ai-code-review-summarizer.git
cd ai-code-review-summarizer

--------Create a virtual environment and activate it:
python -m venv venv
 # On Windows: venv\Scripts\activate

--------Install the required dependencies:
ypip install -r requirements.txt

--------Set up environment variables in a .env file:

 GROQ_API_KEY=your_groq_api_key


####📦 Requirements

Key dependencies:

streamlit
moviepy
speech_recognition
groq
python-dotenv
requests

-----For a complete list of dependencies, see requirements.txt.

-------Start the Streamlit app:
streamlit run app.py

>>Access the application in your web browser at http://localhost:8501
>>Navigate through the application tabs:

Upload & Process: Upload meeting recordings or enter text directly
Summary & Insights: View the generated summary, action items, feedback, and decisions
Chat: Ask questions about the meeting content
Email: Send meeting summaries via email
Asana Integration: Create tasks in Asana from meeting action items



---------💻 Tech Stack

---Frontend: Streamlit
---backend:
Speech-to-Text: Speech Recognition with Google API
Audio Processing: MoviePy
AI Analysis: Groq API with LLaMA3 models
Integrations: GitHub API, Asana API, Email (SMTP)

🔄 Workflow
1. Upload Content

Upload audio/video recordings (MP4, MP3, WAV) or paste meeting transcript
Optionally connect to GitHub repository for code context

2. AI Analysis

Audio is automatically transcribed to text
Text and repository files are analyzed by Groq LLaMA models
AI extracts key insights, action items, feedback, and decisions

3. View & Share Results

Review the AI-generated summary and insights
Chat with the AI to ask follow-up questions
Send results via email to team members
Create tasks in Asana for action items

4. GitHub Integration

Post meeting summaries as GitHub issues
Map feedback to specific repository files

-----👨‍💻 Examples
Processing a Code Review Meeting

Upload an MP4 recording of your code review meeting
Enter your GitHub repository URL and token (for private repos)
Click "Process"
Review the generated summary and insights
Send the summary to team members via email
Create tasks in Asana for action items

-------Using Direct Text Input

Check "Or enter meeting transcript directly"
Paste your meeting transcript
Click "Process"
Review the generated summary and insights

------Interacting with Meeting Content

Navigate to the "Chat" tab
Ask questions about specific parts of the meeting
Get AI-generated responses based on the meeting content

------🔧 Integration Setup
--GitHub Integration

Requires a GitHub token with repo scope
Enter repository URL and branch (default: main)

--Email Integration

Requires SMTP server details and credentials
Supports sending to multiple recipients

--Asana Integration

Requires Asana Personal Access Token (PAT)
Enter Asana Project URL or ID

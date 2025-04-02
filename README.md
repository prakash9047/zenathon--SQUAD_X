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

📹 Video Transcription – Convert meeting recordings to searchable text.

🔤 Direct Text Input – Option to paste meeting transcripts directly.

📄 Multi-Format Support – Process MP4, WAV, and MP3 files.

🔄 GitHub Integration – Map feedback to specific repository files.

✅ Action Item Extraction – Automatically identify and assign tasks.

💬 Code Feedback Analysis – Generate targeted file-specific feedback.

🏗️ Decision Documentation – Track architectural and design decisions.

💬 Interactive Chat – Ask questions about the meeting content.

📧 Email Integration – Send summaries directly to team members.

📋 Asana Integration – Create tasks in Asana from meeting action items.

🛠️ Installation

Clone the Repository

git clone https://github.com/yourusername/ai-code-review-summarizer.git
cd ai-code-review-summarizer

Create and Activate a Virtual Environment

python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

Install Dependencies

pip install -r requirements.txt

Set Up Environment Variables

Create a .env file and add the following:

GROQ_API_KEY=your_groq_api_key

📦 Requirements

Key dependencies:

streamlit

moviepy

speech_recognition

groq

python-dotenv

requests

For a complete list of dependencies, see requirements.txt.

🚀 Usage

Start the Application

streamlit run app.py

Access the Application

Open your browser and navigate to: http://localhost:8501

Navigate Through Application Tabs

Upload & Process – Upload recordings or input text directly.

Summary & Insights – View AI-generated summaries, action items, and decisions.

Chat – Ask AI-based questions about the meeting content.

Email – Send summaries via email.

Asana Integration – Create tasks in Asana from extracted action items.

💻 Tech Stack

Frontend: Streamlit

Backend:

Speech-to-Text: Google API via speech_recognition

Audio Processing: MoviePy

AI Analysis: Groq API (LLaMA3 models)

Integrations: GitHub API, Asana API, SMTP Email

🔄 Workflow

Upload Content

Upload meeting recordings (MP4, MP3, WAV) or paste transcripts.

(Optional) Connect to a GitHub repository for code context.

AI Analysis

Audio is transcribed to text.

AI analyzes meeting content and extracts key insights, feedback, and decisions.

View & Share Results

Review AI-generated summaries and insights.

Chat with AI for follow-up questions.

Send results via email.

Create Asana tasks from extracted action items.

GitHub Integration

Post summaries as GitHub issues.

Map feedback to specific repository files.

👨‍💻 Examples

Processing a Code Review Meeting

Upload an MP4 recording of your code review meeting.

Enter your GitHub repository URL and token (for private repos).

Click Process.

Review the generated summary and insights.

Send the summary via email.

Create Asana tasks for action items.

Using Direct Text Input

Check "Or enter meeting transcript directly".

Paste your meeting transcript.

Click Process.

Review the generated summary and insights.

Interacting with Meeting Content

Go to the Chat tab.

Ask questions about specific parts of the meeting.

Receive AI-generated responses based on the meeting content.

🔧 Integration Setup

GitHub Integration

Requires a GitHub token with repo scope.

Enter repository URL and branch (default: main).

Email Integration

Requires SMTP server details and credentials.

Supports sending to multiple recipients.

Asana Integration

Requires Asana Personal Access Token (PAT).

Enter Asana Project URL or ID.

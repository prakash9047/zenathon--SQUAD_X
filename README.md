AI-Powered Code Review Summarizer
An intelligent tool that analyzes video recordings of code review meetings, extracts actionable insights, and maps them to GitHub repositories.

##Overview
The AI-Powered Code Review Summarizer is designed to streamline the code review process by automatically extracting valuable information from meeting recordings and associating that feedback with specific files in your GitHub repository. This tool helps teams document discussions, track action items, and maintain a record of design decisions made during code reviews.
Features

Video Transcription: Automatically convert MP4 recordings of meetings to text
Multiple File Format Support: Process MP4, WAV, MP3, PDF, DOCX, and TXT files
GitHub Integration: Connect to repositories to map feedback to specific files
Action Item Extraction: Identify and assign tasks to team members
Code Feedback Analysis: Generate targeted feedback for specific files
Decision Documentation: Track architectural and design decisions
Simple Mode: Generate summaries without GitHub integration
Export Options: Download analysis reports in Markdown format

##Installation

Clone the repository:
bashCopygit clone https://github.com/yourusername/code-review-summarizer.git
cd code-review-summarizer

##Install the required dependencies:
bashCopypip install -r requirements.txt

##Set up environment variables in a .env file:
CopyGROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=your_github_token


###Requirements

Python 3.7+
Streamlit
MoviePy
SpeechRecognition
Groq Python client
PyPDF2
python-docx
python-magic
python-dotenv
requests

##Usage

Start the Streamlit app:
bashCopystreamlit run app.py

Access the application in your web browser at http://localhost:8501
Configure your Groq API key in the sidebar (required for AI analysis)
Upload a meeting recording (MP4) or other supported file
Optionally enter a GitHub repository URL to map feedback to code files
Click "Process Content" to start the analysis
Switch to the "Results" tab to view the generated insights
Download the analysis report or extracted text as needed

##Workflow

Upload File: The application accepts video recordings (MP4), audio files (WAV, MP3), or text-based documents (PDF, DOCX, TXT)
Text Extraction: For video/audio files, the app extracts and transcribes the content; for text files, it extracts the content directly
GitHub Integration: If a repository URL is provided, the app fetches relevant files to provide context for the analysis
AI Analysis: Using Groq's large language models, the app analyzes the extracted text to identify key insights
Results Generation: The app presents a summary, action items, file-specific feedback, and decisions made during the meeting

##Configuration Options

Groq API Key: Required for AI analysis
Model Name: Default is "llama3-70b-8192", but other Groq models can be specified
GitHub Token: Optional, required only for private repositories
Simple Mode: Skip GitHub integration for faster processing

##Example usage
pythonCopy# Processing a code review meeting recording with GitHub integration
1. Enter your Groq API key in the sidebar
2. Upload the MP4 recording of your code review meeting
3. Enter the GitHub repository URL: https://github.com/yourusername/your-repo
4. Click "Process Content"
5. View the generated summary, action items, and file feedback
6. Download the analysis report for sharing with your team
Limitations

The quality of transcription depends on the audio quality of the meeting recording
Large video files may take longer to process
Repository analysis is limited to text-based files (excludes binary files, images, etc.)
Private repositories require a valid GitHub token with appropriate permissions

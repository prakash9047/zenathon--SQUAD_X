# 🚀 AI-Powered Code Review Summarizer

An intelligent tool that transforms code review meeting recordings into actionable insights, mapping feedback directly to your GitHub repositories.
ui for app
![image](https://github.com/user-attachments/assets/31e988ba-6183-441b-ad15-b2dbebbd2f1a)
processed file in app
![image](https://github.com/user-attachments/assets/fd3da74b-9636-428e-a8a0-800da51c1e21)
results page in app
![image](https://github.com/user-attachments/assets/b13f68d5-1c96-4212-927d-7cb1cb4cf554)



## ✨ Features

- **📹 Video Transcription**: Convert meeting recordings to searchable text
- **📄 Multi-Format Support**: Process MP4, WAV, MP3, PDF, DOCX, and TXT files
- **🔄 GitHub Integration**: Map feedback to specific repository files
- **✅ Action Item Extraction**: Automatically identify and assign tasks
- **💬 Code Feedback Analysis**: Generate targeted file-specific feedback
- **🏗️ Decision Documentation**: Track architectural and design decisions
- **🔍 Simple Mode**: Generate summaries without GitHub integration
- **📥 Export Options**: Download analysis reports in Markdown format

## 📋 Progress Summary

### Phase 1 - Speech-to-Text Transcription ✓
- **Speech-to-Text Tools:**
  1. Google Speech-to-Text API via `speech_recognition` library
  2. Audio Extraction: `moviepy` for converting video files to WAV audio
- **Transcription Module:**
  1. Chunked audio processing (30s intervals) for reliability
  2. Noise adjustment and error handling ([inaudible] placeholders)
  3. Temporary file cleanup for audio/video

### Phase 2 - GitHub Integration ✓
- **GitHub API Integration:**
  1. Repository file extraction with authentication support
  2. Selective file processing (exclude binaries, node_modules, etc.)
  3. Content mapping for code review alignment

### Phase 3 - AI-Powered Summarization ✓
- **Integrated:**
  1. Support for Groq API with multiple models (llama3-70b-8192 default)
  2. Structured analysis into summary, action items, file feedback, and decisions
  3. JSON response parsing with fallback to text reports

### Phase 4 - UI Development ✓
- **Developed a Streamlit app with:**
  1. Video upload & processing
  2. Multi-format support
  3. GitHub repository connection
  4. Extracted text and summary display
  5. Downloadable outputs (MD, TXT)
  6. Simple mode for skipping GitHub integration

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/prakash9047/zenathon--SQUAD_X.git
   cd folder
   ```

2. Install the required dependencies:
   ```bash
   create virtual environment by python -m venv "your env name"
   scipts\activate\"your env name"
   then,
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file:
   ```
   GROQ_API_KEY=your_groq_api_key
   GITHUB_TOKEN=your_github_token
   ```

## 📦 Requirements

- Python 3.7+
- Streamlit
- MoviePy
- SpeechRecognition
- Groq Python client
- PyPDF2
- python-docx
- python-magic
- python-dotenv
- requests

## 🚦 Usage

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Access the application in your web browser at `http://localhost:8501`

3. Configure your Groq API key in the sidebar (required for AI analysis)

4. Upload a meeting recording (MP4) or other supported file

5. Optionally enter a GitHub repository URL to map feedback to code files

6. Click "Process Content" to start the analysis

7. Switch to the "Results" tab to view the generated insights

## 💻 Tech Stack

- **Speech-to-Text:** `speech_recognition` (Google API), `moviepy` (audio extraction)
- **File Processing:** `PyPDF2`, `python-docx`, `python-magic`
- **AI Integration:** Groq API client
- **GitHub Integration:** Requests library for GitHub API
- **Frontend UI:** Streamlit

## 🔄 Workflow

1. **Upload File**: Submit video recordings (MP4), audio files, or text-based documents
2. **Text Extraction**: The app transcribes or extracts content automatically
3. **GitHub Integration**: Connect to repositories to provide context for analysis
4. **AI Analysis**: Use Groq's LLMs to identify key insights and action items
5. **Results Generation**: View summaries, action items, and file-specific feedback
6. **download report**

## ⚙️ Configuration Options

- **Groq API Key**: Required for AI analysis
- **Model Name**: Default is "llama3-70b-8192", but other Groq models can be specified
- **GitHub Token**: Optional, required only for private repositories
- **Simple Mode**: Skip GitHub integration for faster processing

## 📝 Example

```python
# Processing a code review meeting recording with GitHub integration
1. Enter your Groq API key in the sidebar
2. Upload the MP4 recording of your code review meeting
3. Enter the GitHub repository URL: https://github.com/yourusername/your-repo
4. Click "Process Content"
5. View the generated summary, action items, and file feedback
6. Download the analysis report for sharing with your team
```


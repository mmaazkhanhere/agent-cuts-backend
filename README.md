# **AgentCut: AI-Powered Video Content Curation**
AgentCut is an advanced application designed to transform raw video into ready-to-post, high-impact social media content. By intelligently segmenting videos, scoring content, and generating compelling text, ClipGenius streamlines content creation for creators and marketers.

## **Features**
- **Intelligent Video Segmentation:** Divides videos into meaningful segments using a dedicated Video Segmentation Agent.
- **Accurate Transcription:** Utilizes a robust Transcription Agent with sentence-level timestamps for precise text extraction from audio.
- **Content Ranking & Scoring:** A Ranking Agent assesses each segment's trending potential, engagement, and overall score using Google Search for real-time insights.
- **AI-Powered Content Generation:** A Content Writing Agent crafts engaging titles, descriptions, and relevant hashtags for each top-performing segment.
- **Modular Agent Architecture:** Built with a clean, scalable structure, enabling easy integration of new functionalities.
- **FastAPI Integration: Provides** a user-friendly API for seamless interaction and deployment.


## **🚀 Quick Start**
To get started with AgentCut, follow these steps:

### **1. Environment Setup**
Create a .env file in the root directory and populate it with your API keys:
```
# Required for Transcription Agent
GROQ_API_KEY=your_groq_key_here

# Required for Google Search in Ranking Agent
GOOGLE_API_KEY=your_google_ai_key_here
```

**Get Your API Keys:**

*Groq*: https://console.groq.com/
*Google AI Studio*: https://aistudio.google.com/ 

### **2. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **3. Install Dependencies**

```bash
uvicorn main:app --reload
```

### **4. Run Agent**
- Add video file to video directory
- Go to the `agent_cuts` directory
- Run the following command
```bash
adk run .
```

## **Project Structure**

```
agent-cuts-backend/
├── agent_cuts/           # main agent
│   ├── __init__.py               
│   ├── sub_agent/            # sub agents involved in the agent flow
│   │   ├── copywriter_agent     # agent to find hashtags, title, and description
│   │   ├── ranking_agent             # Main transcription engine
│   │   └── segmentation_agent          # Google ADK wrapper
├   |   |__ transcription_agent             # Main transcription engine
│   │   └── video_segmentation_agent
|   | agent.py
segments/                    # Video segments
│   ├── seg_01
├── main.py            # FastAPI server
├── tests              # Tests
└── utils              # Weather agent example
```

## 🎯  **Key Agents & Their Roles**

### **1. Transcription Agent**
- **Purpose:** Converts spoken words in video segments into accurate, timestamped text.
-  **Key Features:**
    - Sentence-Level Timestamps: Provides precise timing for each sentence.
    - Word-Level Precision: Leverages Groq's word timestamps for high accuracy.
    - Intelligent Chunking: Segments audio at natural pauses for efficient processing.
    - Parallel Processing: Concurrent transcription for speed.
    - Dual API Support: Direct transcription (Groq) and ADK agent modes.
- **External Tools**: Custom video transcription (Groq Whisper API).
- **Sample Output:
```json
{
  "segments" : [
     {
      "text": "Tanya Cushman Reviewer's Name Reviewer's Name So, I'll start with this.",
      "start_time": 0.0,
      "end_time": 18.72
    },
    {
      "text": "A couple of years ago, an event planner called me because I was going to do a speaking event.",
      "start_time": 17.74,
      "end_time": 22.72
    },
    ]
}
```

### **2. Video Segmentation Agent**
- **Purpose:** Analyzes the video content to identify logical breaks and create distinct, meaningful segments.
- **External Tools:** Custom video segmentation tool.

### **3. Ranking Agent**
- **Purpose:** Evaluates each video segment's potential for virality and engagement.
- **Metrics:**
    - **Trending Potential:** How likely the content is to become popular.
    - **Engagement Potential:** How likely users are to interact with the content (likes, comments, shares).
    - **Overall Score:** A comprehensive score based on a weighted combination of trending and engagement.
- **External Tools:** Google Search (to gauge current trends and related content popularity).

### **4. Content Writing Agent **
- **Purpose:** Generates compelling textual assets for each high-scoring video segment.
- **Output:** Optimized titles, descriptive summaries, and relevant hashtags, ready for social media posting.

### **5. Orchestrator Agent**
- **Purpose:** Manages the workflow between all other agents, ensuring a seamless and efficient content creation pipeline.


## 🌐 API Endpoints

Genius provides the following FastAPI endpoints:

### POST /process-video - Process a Video for Content Curation

*Description:* Uploads a video file, processes it through all agents (segmentation, transcription, ranking, content writing), and returns curated content suggestions.

*Request:* multipart/form-data with video file.

bash
curl -X POST "http://localhost:8000/process-video" \
  -F "file=@your_video.mp4"


### GET /health - System Status

*Description:* Checks the health and availability of the ClipGenius API.

*Request:* GET

bash
curl http://localhost:8000/health


## Testing

A comprehensive test suite is available to ensure the reliability and accuracy of each agent.

## ⚡ Performance

- *Speed:* Optimized for efficient processing, leveraging parallel execution where possible.
- *Accuracy:* High precision in transcription, segmentation, and content generation.
- *Scalability:* Designed with modularity to handle increasing workloads and future agent additions.

## 🔍 Troubleshooting

- *API Key Issues:* Ensure all required API keys (GROQ_API_KEY, GOOGLE_API_KEY, GOOGLE_CSE_ID) are correctly set in your .env file.
- *FFmpeg:* Ensure FFmpeg is installed and accessible in your system's PATH for audio/video processing.
- *Import Errors:* If you encounter ModuleNotFoundError, verify your Python environment and package installation.
- *Supported Formats:* For video inputs, ensure you're using common formats like MP4, AVI, MOV, MKV, WEBM. For audio, MP3, WAV, M4A are supported.

ClipGenius is production-ready for content creators and marketers looking to automate and optimize their video content strategy!

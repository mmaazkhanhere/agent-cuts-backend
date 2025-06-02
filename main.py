"""FastAPI application for Agent Cuts Backend"""
from fastapi import FastAPI, UploadFile, File
from agent import run_agent
from subagents.transcription import TranscriptionSubAgent
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Agent Cuts API", version="3.0")

@app.get("/")
def get_root():
    return {
        "message": "Agent Cuts API v3.0", 
        "features": [
            "Multi-agent architecture",
            "Video transcription with sentence-level timestamps",
            "Weather and time information",
            "Modular design"
        ]
    }

@app.post('/chat')
async def chat_endpoint(prompt: str):
    """Chat with the main agent"""
    response = await run_agent(prompt)
    return {"response": response}

@app.post('/transcribe')
async def transcribe_video_endpoint(file: UploadFile = File(...)):
    """Transcribe uploaded video using transcription subagent"""
    try:
        # Validate file type
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.mp3', '.wav', '.m4a'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return {
                "status": "error",
                "message": f"Unsupported file type: {file_ext}",
                "supported_formats": list(allowed_extensions)
            }
        
        # Check API key
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return {"status": "error", "message": "GROQ_API_KEY not configured"}
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Use transcription subagent
            transcription_agent = TranscriptionSubAgent(groq_api_key)
            result = await transcription_agent.transcribe_video(
                video_path=temp_file_path,
                sentence_level=True
            )
            
            # Add API-specific metadata
            if result['status'] == 'success':
                result['api_info'] = {
                    "filename": file.filename,
                    "file_size_mb": len(content) / (1024 * 1024),
                    "processing_method": "transcription_subagent_v3"
                }
                
                # Add sentence count to main metadata
                if 'sentence_segments' in result:
                    result['metadata']['sentence_count'] = len(result['sentence_segments'])
            
            return {
                "status": result["status"],
                "data": result
            }
            
        finally:
            # Always cleanup temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        return {"status": "error", "message": f"Processing failed: {str(e)}"}

@app.get("/health")
async def health_check():
    """Health check with detailed status"""
    groq_api_key = os.getenv("GROQ_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    return {
        "status": "healthy",
        "version": "3.0",
        "api_keys": {
            "groq_configured": bool(groq_api_key),
            "google_configured": bool(google_api_key)
        },
        "endpoints": {
            "/transcribe": "Direct transcription (Groq only)",
            "/chat": "Main agent chat",
            "/health": "This health check"
        },
        "architecture": "Multi-agent system with subagents"
    }

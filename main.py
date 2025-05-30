"""
Updated FastAPI application using the new transcription agent package
"""
from fastapi import FastAPI, UploadFile, File
from demo_agent import weather_time_agent_runner
from transcription_agent import transcribe_video, run_transcription_agent
from segmentation_agent.agent import run_segmentation_agent
import tempfile
import os
import json
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="ClipGenius Transcription API", version="2.0")

@app.get("/")
def get_root():
    return {
        "message": "ClipGenius Transcription API v2.0", 
        "features": [
            "Video transcription with sentence-level timestamps",
            "Intelligent audio chunking",
            "Parallel processing",
            "Multiple output formats"
        ]
    }

@app.post('/chat')
async def get_agent_response(prompt: str):
    """Chat with weather/time agent"""
    response = await weather_time_agent_runner(prompt)
    return {"response": response}

@app.post('/transcribe')
async def transcribe_video_endpoint(file: UploadFile = File(...)):
    """Transcribe uploaded video using the transcription agent package"""
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
            # Use the transcription agent package
            result = await transcribe_video(
                video_path=temp_file_path,
                groq_api_key=groq_api_key,
                sentence_level=True
            )
            
            # Add API-specific metadata
            if result['status'] == 'success':
                result['api_info'] = {
                    "filename": file.filename,
                    "file_size_mb": len(content) / (1024 * 1024),
                    "processing_method": "transcription_agent_package_v2"
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

@app.post('/transcribe-adk')
async def transcribe_with_adk_agent(file: UploadFile = File(...)):
    """Transcribe using Google ADK agent (requires GOOGLE_API_KEY)"""
    try:
        # Check both API keys
        groq_api_key = os.getenv("GROQ_API_KEY")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not groq_api_key:
            return {"status": "error", "message": "GROQ_API_KEY not configured"}
        if not google_api_key:
            return {"status": "error", "message": "GOOGLE_API_KEY required for ADK agent"}
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Use ADK agent
            response = await run_transcription_agent(temp_file_path)
            return {
                "status": "success",
                "filename": file.filename,
                "adk_response": response
            }
        finally:
            os.unlink(temp_file_path)
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    """Health check with detailed status"""
    groq_api_key = os.getenv("GROQ_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    return {
        "status": "healthy",
        "version": "2.0",
        "api_keys": {
            "groq_configured": bool(groq_api_key),
            "google_configured": bool(google_api_key)
        },
        "endpoints": {
            "/transcribe": "Direct transcription (Groq only)",
            "/transcribe-adk": "ADK agent transcription (requires Google AI)",
            "/chat": "Weather/time agent",
            "/health": "This health check"
        },
        "features": [
            "Sentence-level timestamps",
            "Intelligent audio chunking", 
            "Parallel processing",
            "Word-level precision"
        ]
    }

@app.get("/formats")
async def get_supported_formats():
    """Get supported file formats and output options"""
    return {
        "input_formats": [".mp4", ".avi", ".mov", ".mkv", ".webm", ".mp3", ".wav", ".m4a"],
        "output_features": {
            "chunk_segments": "Original audio chunks with timestamps",
            "sentence_segments": "Individual sentences with precise timing",
            "full_text": "Complete transcription text",
            "metadata": "Processing statistics and quality metrics"
        },
        "timestamp_precision": "Word-level accuracy when available"
    }


@app.get('/segmentation')
async def segmentation_agent_endpoint():
    """Segmentation agent endpoint"""
    # Placeholder for segmentation agent logic
    transcript_path = "e:\\Web 3.0\\Generative AI\\Github\\agent-cuts-backend\\test_transcript.json"
    with open(transcript_path, 'r') as file:
            transcript = json.load(file)
    transcript_json = json.dumps(transcript)
    try:
        response = await run_segmentation_agent(transcript_json)
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        return {
            "status": "error",
            "response": str(e)
        }
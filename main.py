"""
Updated FastAPI application using the new transcription agent package
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from transcription_agent import transcribe_video, run_transcription_agent
from segmentation_agent.agent import run_segmentation_agent
from ranking_agent.agent import run_ranking_agent
from video_segmentation_agent.agent import run_video_segmentation_agent
from utils.session_manager import session_manager
from utils.phrase_generator import generate_unique_phrase

import tempfile
import os
import json
import shutil
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
    

@app.get('/ranking')
async def segmentation_agent_endpoint():
    """Ranking agent endpoint"""
    # Placeholder for segmentation agent logic
    segment_path = "e:\\Web 3.0\\Generative AI\\Github\\agent-cuts-backend\\output\\segmentation_response.json"
    with open(segment_path, 'r') as file:
            segments = json.load(file)
    segments_json = json.dumps(segments)
    try:
        response = await run_ranking_agent(segments_json)
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        return {
            "status": "error",
            "response": str(e)
        }
    

@app.get('/video_segment')
async def video_segmentation_endpoint():
    """Video segmentation agent endpoint"""
    # Placeholder for segmentation agent logic
    ranking_path = "e:\\Web 3.0\\Generative AI\\Github\\agent-cuts-backend\\output\\ranking_response.json"
    with open(ranking_path, 'r') as file:
            ranking = json.load(file)
    ranking_json = json.dumps(ranking)
    try:
        response = await run_video_segmentation_agent(ranking_json)
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        return {
            "status": "error",
            "response": str(e)
        }


@app.post('/process-video')
async def process_video_complete(request: dict):
    """Complete video processing pipeline: transcription -> segmentation -> ranking -> video segments"""
    try:
        video_path = request.get("video_path")
        if not video_path:
            return {"status": "error", "message": "video_path is required"}
            
        # Step 1: Transcription
        transcript_result = await run_transcription_agent(video_path)
        if isinstance(transcript_result, str):
            transcript_data = json.loads(transcript_result)
        else:
            transcript_data = transcript_result
            
        # Step 2: Segmentation
        segment_result = await run_segmentation_agent(json.dumps(transcript_data))
        if isinstance(segment_result, str):
            segment_data = json.loads(segment_result)
        else:
            segment_data = segment_result
            
        # Step 3: Ranking
        ranking_result = await run_ranking_agent(json.dumps(segment_data))
        if isinstance(ranking_result, str):
            ranking_data = json.loads(ranking_result)
        else:
            ranking_data = ranking_result
            
        # Prepare ranking data in expected format
        if isinstance(ranking_data, dict) and "ranked_list" in ranking_data:
            formatted_ranking = ranking_data
        elif isinstance(ranking_data, list):
            formatted_ranking = {"ranked_list": ranking_data}
        else:
            formatted_ranking = {"ranked_list": [ranking_data]}
            
        # Step 4: Video Segmentation
        video_seg_input = {
            "video_path": video_path,
            "ranked_segments": formatted_ranking
        }
        video_result = await run_video_segmentation_agent(json.dumps(video_seg_input))
        
        # Get segment paths
        output_dir = "segments"
        segment_paths = []
        if os.path.exists(output_dir):
            for file in sorted(os.listdir(output_dir)):
                if file.endswith('.mp4'):
                    segment_paths.append(os.path.join(output_dir, file))
        
        return {
            "status": "success",
            "video_path": video_path,
            "segment_paths": segment_paths,
            "segment_count": len(segment_paths),
            "processing_details": {
                "transcription": transcript_data.get("status"),
                "segmentation": segment_data.get("status") if isinstance(segment_data, dict) else "success",
                "ranking": ranking_data.get("status") if isinstance(ranking_data, dict) else "success",
                "video_segmentation": json.loads(video_result) if isinstance(video_result, str) else video_result
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    

async def process_video_background(unique_phrase: str, video_path: str):
    """Background task to process video"""
    print(f"[Background Task] Starting processing for {unique_phrase}")
    print(f"[Background Task] Video path: '{video_path}'")
    print(f"[Background Task] Path exists: {os.path.exists(video_path)}")
    
    try:
        # Update progress: Starting transcription
        session_manager.update_progress(unique_phrase, "transcription", 10)
        
        # Step 1: Transcription
        transcript_result = await run_transcription_agent(video_path)
        if isinstance(transcript_result, str):
            transcript_data = json.loads(transcript_result)
        else:
            transcript_data = transcript_result
        
        # Check for transcription errors
        if isinstance(transcript_data, dict) and transcript_data.get('status') == 'error':
            raise Exception(f"Transcription failed: {transcript_data.get('error', 'Unknown error')}")
        
        session_manager.update_progress(unique_phrase, "transcription_complete", 30)
        
        # Step 2: Segmentation
        session_manager.update_progress(unique_phrase, "segmentation", 40)
        
        # Prepare data for segmentation
        if isinstance(transcript_data, dict) and 'segments' in transcript_data:
            segmentation_input = transcript_data
        else:
            raise Exception("Invalid transcript format for segmentation")
            
        segment_result = await run_segmentation_agent(json.dumps(segmentation_input))
        if isinstance(segment_result, str):
            segment_data = json.loads(segment_result)
        else:
            segment_data = segment_result
        
        session_manager.update_progress(unique_phrase, "segmentation_complete", 60)
        
        # Step 3: Ranking
        session_manager.update_progress(unique_phrase, "ranking", 70)
        ranking_result = await run_ranking_agent(json.dumps(segment_data))
        if isinstance(ranking_result, str):
            ranking_data = json.loads(ranking_result)
        else:
            ranking_data = ranking_result
        
        # Prepare ranking data
        if isinstance(ranking_data, dict) and "ranked_list" in ranking_data:
            formatted_ranking = ranking_data
        elif isinstance(ranking_data, list):
            formatted_ranking = {"ranked_list": ranking_data}
        else:
            formatted_ranking = {"ranked_list": [ranking_data]}
        
        session_manager.update_progress(unique_phrase, "ranking_complete", 85)
        
        # Step 4: Video Segmentation
        session_manager.update_progress(unique_phrase, "video_segmentation", 90)
        
        # Create unique output directory for this session
        output_dir = f"segments/{unique_phrase}"
        os.makedirs(output_dir, exist_ok=True)
        
        video_seg_input = {
            "video_path": video_path,
            "ranked_segments": formatted_ranking
        }
        
        # Modify video segmentation to use custom output dir
        video_result = await run_video_segmentation_agent(json.dumps(video_seg_input), output_dir)
        
        # Get segment paths
        segment_paths = []
        if os.path.exists(output_dir):
            for file in sorted(os.listdir(output_dir)):
                if file.endswith('.mp4'):
                    segment_paths.append(os.path.join(output_dir, file))
        
        # Update progress: Complete
        session_manager.update_progress(unique_phrase, "completed", 100, segment_paths)
        
    except Exception as e:
        session_manager.set_error(unique_phrase, str(e))


@app.post('/upload-video')
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload video and get unique phrase for tracking"""
    print("Received file:", file.filename)
    try:
        # Validate file type
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(400, f"Unsupported file type: {file_ext}")
        
        # Generate unique phrase
        unique_phrase = generate_unique_phrase()
        
        # Create upload directory
        upload_dir = f"uploads/{unique_phrase}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded file
        file_path = os.path.join(upload_dir, file.filename)
        file_path = os.path.abspath(file_path)  # Ensure absolute path
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        print("File saved to:", file_path)
        # Create session
        session_manager.create_session(unique_phrase, file_path)
        print("Session created for unique phrase:", unique_phrase)
        # Start background processing
        background_tasks.add_task(process_video_background, unique_phrase, file_path)
        print("Background task started for unique phrase:", unique_phrase)
        return {
            "status": "success",
            "unique_phrase": unique_phrase,
            "message": "Video uploaded successfully. Processing started.",
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get('/progress/{unique_phrase}')
async def get_progress(unique_phrase: str):
    """Get processing progress by unique phrase"""
    session = session_manager.get_session(unique_phrase)
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    return {
        "status": session["status"],
        "progress": session["progress"],
        "segment_count": len(session["segment_paths"]),
        "error": session["error"],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"]
    }


@app.get('/download-segment/{unique_phrase}/{segment_index}')
async def download_segment(unique_phrase: str, segment_index: int):
    """Download a specific video segment"""
    session = session_manager.get_session(unique_phrase)
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    if session["status"] != "completed":
        raise HTTPException(400, f"Processing not complete. Status: {session['status']}")
    
    if segment_index < 0 or segment_index >= len(session["segment_paths"]):
        raise HTTPException(404, f"Invalid segment index. Available: 0-{len(session['segment_paths'])-1}")
    
    segment_path = session["segment_paths"][segment_index]
    
    if not os.path.exists(segment_path):
        raise HTTPException(404, "Segment file not found")
    
    return FileResponse(
        segment_path,
        media_type="video/mp4",
        filename=os.path.basename(segment_path)
    )


@app.get('/segments/{unique_phrase}')
async def get_segments_info(unique_phrase: str):
    """Get information about all segments for a session"""
    session = session_manager.get_session(unique_phrase)
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    segments_info = []
    for i, path in enumerate(session["segment_paths"]):
        if os.path.exists(path):
            size = os.path.getsize(path)
            segments_info.append({
                "index": i,
                "filename": os.path.basename(path),
                "size_mb": round(size / (1024 * 1024), 2),
                "download_url": f"/download-segment/{unique_phrase}/{i}"
            })
    
    return {
        "unique_phrase": unique_phrase,
        "status": session["status"],
        "total_segments": len(segments_info),
        "segments": segments_info
    }


@app.get('/sessions')
async def list_sessions():
    """List all sessions"""
    sessions = session_manager.get_all_sessions()
    
    return {
        "total_sessions": len(sessions),
        "sessions": [
            {
                "unique_phrase": phrase,
                "status": data["status"],
                "created_at": data["created_at"],
                "segment_count": len(data["segment_paths"])
            }
            for phrase, data in sessions.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
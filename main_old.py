"""
Updated FastAPI application using the agent_cuts ADK agent
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from agent_cuts_runner import process_video_with_agent_cuts, run_agent_cuts
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
    """Complete video processing pipeline using agent_cuts"""
    try:
        video_path = request.get("video_path")
        if not video_path:
            return {"status": "error", "message": "video_path is required"}
        
        # Use agent_cuts for processing
        result = await process_video_with_agent_cuts(
            video_path=video_path,
            output_dir="segments/direct_process"
        )
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    

async def process_video_background(unique_phrase: str, video_path: str):
    """Background task to process video using agent_cuts"""
    print(f"[Background Task] Starting processing for {unique_phrase}")
    print(f"[Background Task] Video path: '{video_path}'")
    print(f"[Background Task] Path exists: {os.path.exists(video_path)}")
    
    try:
        # Update progress: Starting
        session_manager.update_progress(unique_phrase, "starting", 5)
        
        # Create unique output directory for this session
        output_dir = f"segments/{unique_phrase}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Process video using agent_cuts
        result = await process_video_with_agent_cuts(
            video_path=video_path,
            output_dir=output_dir,
            user_id=unique_phrase,
            session_id=unique_phrase
        )
        
        # Check if processing was successful
        if result['status'] == 'success':
            # Extract processing state updates
            state = result.get('processing_state', {})
            
            # Update progress based on what was completed
            if state.get('transcription'):
                session_manager.update_progress(unique_phrase, "transcription_complete", 25)
            
            if state.get('segmentation'):
                session_manager.update_progress(unique_phrase, "segmentation_complete", 50)
            
            if state.get('ranking'):
                session_manager.update_progress(unique_phrase, "ranking_complete", 75)
            
            if state.get('video_segments'):
                session_manager.update_progress(unique_phrase, "video_segmentation_complete", 90)
            
            if state.get('copywriting'):
                session_manager.update_progress(unique_phrase, "copywriting_complete", 95)
            
            # Get final segment paths
            segment_paths = result.get('segment_paths', [])
            
            # Update progress: Complete
            session_manager.update_progress(unique_phrase, "completed", 100, segment_paths)
            
            print(f"[Background Task] Completed successfully with {len(segment_paths)} segments")
            
        else:
            # Processing failed
            error_msg = result.get('error', 'Unknown error during processing')
            session_manager.set_error(unique_phrase, error_msg)
            print(f"[Background Task] Failed: {error_msg}")
        
    except Exception as e:
        error_msg = f"Exception during processing: {str(e)}"
        session_manager.set_error(unique_phrase, error_msg)
        print(f"[Background Task] Exception: {error_msg}")


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
    """List all processing sessions"""
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


@app.post('/process-video')
async def process_video_direct(request: dict):
    """Direct video processing using agent_cuts (synchronous)"""
    try:
        video_path = request.get("video_path")
        if not video_path:
            return {"status": "error", "message": "video_path is required"}
        
        # Process directly using agent_cuts
        result = await process_video_with_agent_cuts(
            video_path=video_path,
            output_dir="segments/direct_process"
        )
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

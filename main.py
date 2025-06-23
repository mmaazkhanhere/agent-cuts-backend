"""
FastAPI application using the agent_cuts ADK agent
Following the ADK pattern from https://github.com/google/adk-samples
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from agent_cuts_runner import process_video_with_agent_cuts_async
from utils.session_manager import session_manager
from utils.phrase_generator import generate_unique_phrase
from fastapi.staticfiles import StaticFiles

import os
import json
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="ClipGenius Agent Cuts API", version="3.0")

# Mount the segments directory as a static file server
segments_dir = os.path.abspath("segments")
os.makedirs(segments_dir, exist_ok=True)
app.mount("/static/segments", StaticFiles(directory=segments_dir), name="segments")



@app.get("/")
def get_root():
    return {
        "message": "ClipGenius Agent Cuts API v3.0", 
        "description": "Video processing using ADK sequential agents",
        "features": [
            "Video transcription with timestamps",
            "Intelligent content segmentation",
            "Viral potential ranking",
            "Automatic video cutting",
            "AI copywriting for each segment"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check with API status"""
    groq_api_key = os.getenv("GROQ_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    return {
        "status": "healthy",
        "version": "3.0",
        "api_keys": {
            "groq_configured": bool(groq_api_key),
            "google_configured": bool(google_api_key)
        },
        "agent": "agent_cuts (ADK Sequential Agent)",
        "endpoints": {
            "/upload-video": "Upload video for async processing",
            "/progress/{unique_phrase}": "Check processing progress",
            "/segments/{unique_phrase}": "Get segment information",
            "/download-segment/{unique_phrase}/{index}": "Download segment",
            "/sessions": "List all sessions"
        }
    }


async def process_video_background(unique_phrase: str, video_path: str):
    """Background task to process video using agent_cuts"""
    print(f"[Background Task] Starting processing for {unique_phrase}")
    print(f"[Background Task] Video path: '{video_path}'")
    
    try:
        # Update progress: Starting
        session_manager.update_progress(unique_phrase, "initializing", 5)
        
        # Create unique output directory
        output_dir = os.path.abspath(f"segments")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process video using agent_cuts
        result = await process_video_with_agent_cuts_async(
            video_path=video_path,
            output_dir=output_dir,
            user_id=unique_phrase,
            session_id=unique_phrase
        )
        
        if result['status'] == 'success':
            # Track progress through the pipeline
            state = result.get('processing_state', {})
            
            progress_steps = [
                ('transcription', 'transcribing', 20),
                ('segmentation', 'segmenting', 40),
                ('ranking', 'ranking', 60),
                ('video_segments', 'cutting_video', 80),
                ('copywriting', 'generating_copy', 95)
            ]
            
            for key, step_name, percentage in progress_steps:
                if state.get(key):
                    session_manager.update_progress(unique_phrase, step_name, percentage)
            
            # Get final segments
            segment_paths = result.get('segment_paths', [])
            
            # Get Copywriter output if available
            copywriter_output = result.get('copywriter_output', None)
            # Complete
            session_manager.update_progress(unique_phrase, "completed", 100, segment_paths, copywriter_output)
            print(f"[Background Task] Completed with {len(segment_paths)} segments")

            # Delete original video file
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"[Background Task] Deleted original video file: {video_path}")
            
        else:
            error_msg = result.get('error', 'Processing failed')
            session_manager.set_error(unique_phrase, error_msg)
            print(f"[Background Task] Failed: {error_msg}")
        
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        session_manager.set_error(unique_phrase, error_msg)
        print(f"[Background Task] {error_msg}")


@app.post('/upload-video')
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload video and start processing with agent_cuts"""
    print(f"Received file: {file.filename}")
    
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
        file_path = os.path.abspath(os.path.join(upload_dir, file.filename))
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        print(f"File saved to: {file_path}")
        
        # Create session
        session_manager.create_session(unique_phrase, file_path)
        print(f"Session created: {unique_phrase}")
        
        # Start background processing
        background_tasks.add_task(process_video_background, unique_phrase, file_path)
        print(f"Background task started")
        
        return {
            "status": "success",
            "unique_phrase": unique_phrase,
            "message": "Video uploaded. Processing started.",
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {str(e)}")
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
            filename = os.path.basename(path)

            segments_info.append({
                "index": i,
                "filename": os.path.basename(path),
                "size_mb": round(size / (1024 * 1024), 2),
                "download_url": f"/download-segment/{unique_phrase}/{i}",
                "static_url": f"/static/segments/{filename}"

            })
    
    return {
        "unique_phrase": unique_phrase,
        "status": session["status"],
        "total_segments": len(segments_info),
        "segments": segments_info
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Runner for the agent_cuts ADK agent
Follows the ADK examples pattern from https://github.com/google/adk-samples
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent_cuts import agent_cut
from utils.session_manager import session_manager  # Import the session manager

load_dotenv()

# Session management
session_service = InMemorySessionService()
APP_NAME = "agent_cuts_app"

# Create runner with the sequential agent
runner = Runner(
    agent=agent_cut,
    app_name=APP_NAME,
    session_service=session_service
)

# For compatibility with existing code
# For async compatibility 
async def process_video_with_agent_cuts_async(
    video_path: str, 
    output_dir: str = "segments",
    user_id: str = "default_user",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a video using the agent_cuts sequential agent (async version)
    
    Args:
        video_path: Path to the video file
        output_dir: Directory for output segments
        user_id: User identifier
        session_id: Session identifier (auto-generated if not provided)
    
    Returns:
        Dict containing processing results
    """
    if not session_id:
        # Generate a unique session ID based on current time
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"    
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the input message for the agent
    message_data = {
        "video_path": video_path,
        "output_dir": output_dir,
        "instructions": """Process this video through all stages:
1. Transcribe the video to get text with timestamps
2. Segment the transcript into logical topics"""
    }
    
    message = json.dumps(message_data)
    
    # Create session properly with await
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    )
    
    # Create content for the message
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)]
    )
    
    # Process through the sequential agent
    final_response = None
    processing_state = {
        "transcription": None,
        "segmentation": None,
        "ranking": None,
        "video_segments": None,
        "copywriting": None
    }
    
    try:
        # Use async run method
        events_iterator = runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        )
        
        # Process events to get the final response
        session_manager.update_progress(session_id, "transcribing", 20)
        async for event in events_iterator:
            if event.is_final_response() and event.content and event.content.parts:
                print(f"[INFO] Final response from [{event.author}]")
                
                # Update processing state based on which agent responded
                agent_name = event.author
                if "transcription_agent" in agent_name:
                    processing_state["transcription"] = True
                    print("[STATUS] ✅ Transcription completed")
                    # Update session_manager
                    session_manager.update_progress(session_id, "segmenting", 40)
                elif "segmentation_agent" in agent_name:
                    processing_state["segmentation"] = True
                    print("[STATUS] ✅ Segmentation completed")
                    # Update session_manager
                    session_manager.update_progress(session_id, "ranking", 60)
                elif "combined_scoring_agent" in agent_name or "ranking_agent" in agent_name:
                    processing_state["ranking"] = True
                    print("[STATUS] ✅ Ranking completed")
                    # Update session_manager
                    session_manager.update_progress(session_id, "cutting_video", 80)
                elif "video_segmentation_agent" in agent_name:
                    processing_state["video_segments"] = True
                    print("[STATUS] ✅ Video segmentation completed")
                    # Update session_manager
                    session_manager.update_progress(session_id, "generating_copy", 95)
                elif "copywriter_agent" in agent_name:
                    processing_state["copywriting"] = True
                    print("[STATUS] ✅ Copywriting completed")
                    # Update session_manager

                for part in event.content.parts:
                    if part.text:
                        final_response = part.text
                        try:
                            final_data = json.loads(final_response)
                            print("[INFO] Final response parsed as JSON:", final_data)
                        except json.JSONDecodeError:
                            print("[INFO] Final response is not JSON")
                            print("[INFO] Final response text:", final_response.strip())
                        break
        
        # Check final session state using await
        final_session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        
        if final_session and final_session.state:
            print("[INFO] Final session state:", json.dumps(final_session.state, indent=2))
            # Update processing state from session if available
            for key in processing_state.keys():
                if key in final_session.state:
                    processing_state[key] = final_session.state[key]
    
    except Exception as e:
        print(f"[ERROR] Exception during processing: {str(e)}")
        # Update session_manager with error
        session_manager.set_error(session_id, str(e))
        return {
            "status": "error",
            "error": str(e),
            "processing_state": processing_state
        }
    
    # Get segment paths from output directory
    segment_paths = []
    if os.path.exists(output_dir):
        for file in sorted(os.listdir(output_dir)):
            if file.endswith('.mp4'):
                segment_paths.append(os.path.join(output_dir, file))
    
    # Update the final status in session_manager with segments
    if len(segment_paths) > 0:
        session_manager.update_progress(session_id, "completed", 100, segment_paths)
    
    return {
        "status": "success",
        "video_path": video_path,
        "output_dir": output_dir,
        "segment_paths": segment_paths,
        "segment_count": len(segment_paths),
        "processing_state": processing_state,
        "final_response": final_response,
        "session_id": session_id
    }
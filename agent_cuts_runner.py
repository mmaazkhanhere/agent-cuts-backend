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

def process_video_with_agent_cuts(
    video_path: str, 
    output_dir: str = "segments",
    user_id: str = "default_user",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a video using the agent_cuts sequential agent
    
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
    
    # Use synchronous session service functions by running the async ones through a loop
    loop = asyncio.get_event_loop()
    
    # Create session
    loop.run_until_complete(session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id
    ))
    
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
        # Run the agent synchronously
        events = runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        )
        
        # Process events to get the final response
        for event in events:
            if event.is_final_response() and event.content and event.content.parts:
                print(f"[INFO] Final response from [{event.author}]")
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
        
        # Check final session state - using run_until_complete for the async get_session
        final_session = loop.run_until_complete(session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        ))
        
        if final_session and final_session.state:
            print("[INFO] Final session state:", json.dumps(final_session.state, indent=2))
            # Update processing state from session if available
            for key in processing_state.keys():
                if key in final_session.state:
                    processing_state[key] = final_session.state[key]
    
    except Exception as e:
        print(f"[ERROR] Exception during processing: {str(e)}")
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
        async for event in events_iterator:
            if event.is_final_response() and event.content and event.content.parts:
                print(f"[INFO] Final response from [{event.author}]")
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


def run_agent_cuts(video_path: str, output_dir: str = "segments") -> str:
    """
    Simple wrapper to run agent_cuts and return JSON result
    
    Args:
        video_path: Path to video file
        output_dir: Output directory for segments
        
    Returns:
        JSON string with results
    """
    result = process_video_with_agent_cuts(video_path, output_dir)
    return json.dumps(result, indent=2)


# For async compatibility
async def run_agent_cuts_async(video_path: str, output_dir: str = "segments") -> str:
    """
    Async wrapper for run_agent_cuts
    """
    return run_agent_cuts(video_path, output_dir)


# For testing
if __name__ == "__main__":
    video_path = "video/test.mp4"
    result = process_video_with_agent_cuts(video_path)
    print(json.dumps(result, indent=2))
import os
import json
from dotenv import load_dotenv
from typing import Dict, List, Any

from moviepy import VideoFileClip

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .utils import add_audio_to_segments


def video_segmentation_tool(json_data: str, output_dir: str = "segments"):
    """
    Agent tool that splits video into segments based on JSON data containing start/end times
    """
    # Parse JSON string if needed
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data
        
    os.makedirs(output_dir, exist_ok=True)
    video_path = data["video_path"]
    
    # Use absolute path to avoid permission issues
    if not os.path.isabs(video_path):
        video_path = os.path.abspath(video_path)
    
    # Load video without audio first to avoid processing issues
    video = VideoFileClip(video_path, audio=False)
    
    segments = data["ranked_segments"]["ranked_list"]
    for i, segment in enumerate(segments):
        # Handle different segment data structures
        if "segment" in segment:
            # Nested structure from ranking
            seg_data = segment["segment"]
            start = float(seg_data.get("start_time", 0))
            end = float(seg_data.get("end_time", 0))
            topic = seg_data.get("topic", f"Segment_{i+1}")
        else:
            # Direct structure
            start = float(segment.get("start_time", 0))
            end = float(segment.get("end_time", 0))
            topic = segment.get("topic", segment.get("text", f"Segment_{i+1}")[:30])
        
        # Handle segments that might exceed video duration
        if end > video.duration:
            end = video.duration
        if start > video.duration:
            print(f"Skipping segment {i+1} (starts after video ends)")
            continue
            
        clip = video.subclipped(start, end)
        
        topic = topic.replace(" ", "_").replace("/", "-")[:30]
        output_path = os.path.join(output_dir, f"seg_{i+1:02d}_{topic}.mp4")
        
        # Write without audio first (fixes the AttributeError)
        clip.write_videofile(
            output_path,
            codec="libx264",
            audio=False,  # Disable audio to avoid the error
            logger=None,
            threads=4  # Helps with processing speed
        )
        
        print(f"Created video segment: {output_path}")
        clip.close()
    
    video.close()
    
    # Now add audio separately using FFmpeg
    add_audio_to_segments(video_path, output_dir)


video_segmentation_agent = Agent(
    name="video_segmentation_agent",
    model="gemini-2.0-flash",
    description="Video segmentation agent that segments video based on start and endtime specified in the json input",
    instruction="You are video segmentation agent. You have to use the json input and segment video based on the start and end time. Follow the steps" \
    "Do not explain what you're doing - just use the tool and return results",
    tools=[video_segmentation_tool],
)

session_service = InMemorySessionService()
APP_NAME = "video_segmentation_app"
USER_ID = "default_user"
SESSION_ID = "default_session"

runner = Runner(
    agent=video_segmentation_agent,
    app_name=APP_NAME,
    session_service=session_service
)


async def run_video_segmentation_agent(json_data, output_dir: str = "segments"):
    """
    Run the ADK transcription agent
    
    Returns:
        JSON string with simplified transcript format
    """
    try:
        # Ensure json_data is a dictionary
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
    except json.JSONDecodeError as e:
        return json.dumps({"status": "error", "error": f"Invalid JSON input: {str(e)}"})

    groq_api_key = os.getenv("GOOGLE_API_KEY")
    if not groq_api_key:
        return json.dumps({"status": "error", "error": "GOOGLE_API_KEY not found in environment variables"})
    
    video_path = json_data.get("video_path")
    if not video_path:
        return json.dumps({"status": "error", "error": "Missing 'video_path' in JSON input"})
    
    prompt = f"Segment this video: {video_path} and save to {output_dir}"
    
    new_message_content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )

    tool_result = None
    
    try:
        # Ensure session exists
        if not await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID):
            await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

        # Use async version and capture tool outputs
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=new_message_content
        ):
            # Look for tool calls and responses
            if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    # Check for function response (tool output)
                    if hasattr(part, 'function_response') and part.function_response:
                        if part.function_response.name == 'video_segmentation_tool':
                            tool_result = part.function_response.response
                            print(f"[*] Got tool result: {tool_result}")
                            break
                            
            if tool_result:
                break
                
    except Exception as e:
        print(f"Error during agent run: {e}")
        return json.dumps({"status": "error", "error": f"An error occurred: {str(e)}"})

    # Return success message if tool result is obtained
    if tool_result:
        return json.dumps({"status": "success", "message": "video segmented successfully", "data": tool_result})
    
    # Fallback: Run the transcription directly if agent didn't call tool
    print("[!] Agent didn't call tool, running transcription directly...")
    try:
        # Use the passed json_data directly
        video_segmentation_tool(json_data, output_dir)
        return json.dumps({"status": "success", "message": "video segmented successfully"})
    except Exception as e:
        return json.dumps({"status": "error", "error": f"Direct transcription failed: {str(e)}"})
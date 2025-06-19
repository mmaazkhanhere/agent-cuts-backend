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

def video_segmentation_tool(json_data: Dict[str, Any], output_dir: str = "segments") -> Dict[str, Any]:
    """
    Agent tool that splits video into segments based on JSON data containing start/end times
    
    Args:
        json_data: A dictionary containing:
            - video_path: Path to the input video file
            - ranked_segments: Dictionary with a "ranked_list" key containing segments 
              with "start_time", "end_time", and "topic" fields
        output_dir: Directory to save the segmented video files
        
    Returns:
        A dictionary containing information about the created segments
    """
    print("[*] Video segmentation tool called with PARAMS:", json_data, "output_dir:", output_dir)
    
    # Parse JSON string if needed
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            return {"status": "error", "error": "Invalid JSON input"}
    else:
        data = json_data
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Check for required fields
    if "video_path" not in data:
        return {"status": "error", "error": "Missing video_path in input data"}
    
    if "ranked_segments" not in data or "ranked_list" not in data["ranked_segments"]:
        return {"status": "error", "error": "Missing ranked_segments.ranked_list in input data"}
    
    video_path = data["video_path"]
    
    # Use absolute path to avoid permission issues
    if not os.path.isabs(video_path):
        video_path = os.path.abspath(video_path)
    
    if not os.path.exists(video_path):
        return {"status": "error", "error": f"Video file not found: {video_path}"}
    
    # Load video without audio first to avoid processing issues
    video = VideoFileClip(video_path, audio=False)
    created_segments = []
    
    segments = data["ranked_segments"]["ranked_list"]
    for i, segment in enumerate(segments):
        try:
            # Handle different segment data structures
            if "segment" in segment:
                # Nested structure from ranking
                seg_data = segment["segment"]
                
                # Check if start_time and end_time exist and are valid
                if "start_time" not in seg_data or "end_time" not in seg_data:
                    print(f"Skipping segment {i+1} (missing start_time or end_time)")
                    continue
                
                # Convert to float, handling potential errors
                try:
                    start = float(seg_data["start_time"])
                    end = float(seg_data["end_time"])
                except (ValueError, TypeError):
                    print(f"Skipping segment {i+1} (invalid start_time or end_time format)")
                    continue
                    
                topic = seg_data.get("topic", f"Segment_{i+1}")
            else:
                # Direct structure
                # Check if start_time and end_time exist and are valid
                if "start_time" not in segment or "end_time" not in segment:
                    print(f"Skipping segment {i+1} (missing start_time or end_time)")
                    continue
                
                # Convert to float, handling potential errors
                try:
                    start = float(segment["start_time"])
                    end = float(segment["end_time"])
                except (ValueError, TypeError):
                    print(f"Skipping segment {i+1} (invalid start_time or end_time format)")
                    continue
                    
                topic = segment.get("topic", segment.get("text", f"Segment_{i+1}")[:30])
            
            # Handle segments that might exceed video duration
            if end > video.duration:
                print(f"Adjusting segment {i+1} end time from {end} to {video.duration} (video duration)")
                end = video.duration
            if start > video.duration:
                print(f"Skipping segment {i+1} (starts after video ends)")
                continue
            if start >= end:
                print(f"Skipping segment {i+1} (start time {start} >= end time {end})")
                continue
                
            clip = video.subclipped(start, end)
            
            # Clean the topic for filename
            safe_topic = ''.join(c if c.isalnum() or c in '_- ' else '_' for c in topic)
            safe_topic = safe_topic.replace(" ", "_").replace("/", "-")[:30]
            output_path = os.path.join(output_dir, f"seg_{i+1:02d}_{safe_topic}.mp4")
            
            # Write without audio first (fixes the AttributeError)
            clip.write_videofile(
                output_path,
                codec="libx264",
                audio=False,  # Disable audio to avoid the error
                logger=None,
                threads=4  # Helps with processing speed
            )
            
            created_segments.append({
                "index": i+1,
                "topic": topic,
                "start_time": start,
                "end_time": end,
                "output_path": output_path,
                "duration": end - start
            })
            
            print(f"Created video segment: {output_path}")
            clip.close()
            
        except Exception as e:
            print(f"Error processing segment {i+1}: {str(e)}")
            continue
    
    video.close()
    
    # Now add audio separately using FFmpeg
    try:
        add_audio_to_segments(video_path, output_dir)
    except Exception as e:
        print(f"Warning: Could not add audio to segments: {str(e)}")
    
    return {
        "status": "success",
        "segments_created": len(created_segments),
        "segment_details": created_segments,
        "output_directory": os.path.abspath(output_dir)
    }

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
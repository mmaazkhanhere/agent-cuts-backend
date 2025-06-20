import os
from typing import Dict, Any
from dotenv import load_dotenv
from moviepy import VideoFileClip

from google.adk.agents import Agent

from .prompt import VIDEO_SEGMENTATION_AGENT_PROMPT
from .utils import add_audio_to_segments

load_dotenv()
def video_segmentation_tool(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent tool that splits video into segments based on JSON data containing start/end times
    
    Args:
        json_data: A dictionary containing:
            - video_path: Path to the input video file
            - ranked_segments: Dictionary with a "ranked_list" key containing segments 
              with nested "segment" objects that have "start_time", "end_time", and "topic" fields
            - output_dir: Directory to save the segmented video files
    Returns:
        A dictionary containing information about the created segments
    """
    output_dir = "segments"

    if "output_dir" in json_data:
        output_dir = json_data["output_dir"]
    
    print("[*] Video segmentation tool called with PARAMS:", json_data, "output_dir:", output_dir)
    
    # Use a file-based tracking system instead of context
    # since context access is problematic
    session_id = json_data.get("session_id", "default_session")
    video_path = json_data.get("video_path", "unknown_video")
    video_basename = os.path.basename(video_path)
    
    # Create a unique tracking file for this job
    tracking_dir = os.path.join(os.path.dirname(output_dir), ".tracking")
    os.makedirs(tracking_dir, exist_ok=True)
    tracking_file = os.path.join(tracking_dir, f"{session_id}_{video_basename}.lock")
    
    # Check if we've already processed this video
    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r') as f:
                saved_output_dir = f.read().strip()
                
            # If we already segmented this video to this output directory, return cached info
            if saved_output_dir == output_dir:
                print(f"[INFO] Video {video_basename} already segmented to {output_dir}")
                
                # Try to read result file if it exists
                result_file = os.path.join(output_dir, "segmentation_result.json")
                if os.path.exists(result_file):
                    try:
                        import json
                        with open(result_file, 'r') as f:
                            cached_result = json.load(f)
                            return cached_result
                    except:
                        pass
                        
                # If we can't find the detailed results, return basic info
                return {
                    "status": "already_processed",
                    "message": f"Video has already been segmented to {output_dir}",
                    "output_directory": os.path.abspath(output_dir)
                }
        except:
            # If there's an error reading the tracking file, proceed with processing
            pass
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Use absolute path to avoid permission issues
    if not os.path.isabs(video_path):
        video_path = os.path.abspath(video_path)
    
    # Load video without audio first to avoid processing issues
    video = VideoFileClip(video_path, audio=False)
    
    segments = json_data["ranked_segments"]["ranked_list"]
    created_segments = []
    
    for i, segment_data in enumerate(segments):
        try:
            # Handle nested segment structure
            if "segment" in segment_data:
                segment = segment_data["segment"]
            else:
                segment = segment_data
            
            # Extract start and end times
            start = float(segment["start_time"])
            end = float(segment["end_time"])
            
            # Handle segments that might exceed video duration
            if end > video.duration:
                end = video.duration
            if start > video.duration:
                print(f"Skipping segment {i+1} (starts after video ends)")
                continue
                
            clip = video.subclipped(start, end)
            
            # Get topic with fallback options
            topic = segment.get("topic", f"Segment_{i+1}")
            safe_topic = topic.replace(" ", "_").replace("/", "-")[:30]
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
    
    # Save the result
    result = {
        "status": "success",
        "segments_created": len(created_segments),
        "segment_details": created_segments,
        "output_directory": os.path.abspath(output_dir)
    }
    
    # Save result to a file for future reference
    try:
        import json
        result_file = os.path.join(output_dir, "segmentation_result.json")
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save result file: {str(e)}")
    
    # Mark this video as processed by creating the tracking file
    try:
        with open(tracking_file, 'w') as f:
            f.write(output_dir)
    except Exception as e:
        print(f"Warning: Could not create tracking file: {str(e)}")
    
    return result

video_segmentation_agent = Agent(
    name="video_segmentation_agent",
    model="gemini-2.0-flash",
    description="Video segmentation agent that segments video based on start and endtime specified in the json input",
    instruction=VIDEO_SEGMENTATION_AGENT_PROMPT,
    tools=[video_segmentation_tool],
)
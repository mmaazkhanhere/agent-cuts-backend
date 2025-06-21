import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from moviepy import VideoFileClip
from pydantic import BaseModel, Field
import subprocess
from typing import Dict, Any

from google.adk.agents import Agent, SequentialAgent

from .prompt import VIDEO_SEGMENTATION_AGENT_PROMPT, FORMATTER_AGENT_INSTRUCTION
from .utils import add_audio_to_segments

load_dotenv()

class SegmentSchema(BaseModel):
    topic: str = Field(description="Topic of the segment")
    transcript: str = Field(description="Transcript of the segment")
    start_time: str = Field(description="Start time of the segment")
    end_time: str = Field(description="End time of the segment")

class RankingOutput(BaseModel):
    segment: SegmentSchema = Field(description="Segment of the video")
    clarity_score: int = Field(description="Clarity score of the segment out of 10")
    engagement_score: int = Field(description="Engagement score of the segment out of 10")
    trending_score: int = Field(description="Trending score of the segment out of 10")
    overall_score: float = Field(description="Overall score of the segment out of 10")

class RankingAgentOutput(BaseModel):
    ranked_list: list[RankingOutput] = Field(description="List of segments ranked based on overall score")
    video_path: str = Field(description="Path to the video file")

class VideoSegmenterAgentOutput(BaseModel):
    video_segments: list[str] = Field(description="List of video segments")

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
        A dictionary containing:
            - status: "success" or "error"
            - segments: List of dictionaries with segment details including output_path
    """
    output_dir = json_data.get("output_dir", "segments")
    print("[*] Video segmentation tool called with PARAMS:", json_data, "output_dir:", output_dir)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get absolute path to video
    video_path = os.path.abspath(json_data["video_path"])
    segments = json_data["ranked_segments"]["ranked_list"]
    created_segments = []
    
    # Load video to get duration
    try:
        video = VideoFileClip(video_path)
        video_duration = video.duration
        video.close()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to load video: {str(e)}"
        }
    
    # Process each segment
    for i, segment_data in enumerate(segments):
        try:
            # Extract segment information
            segment = segment_data.get("segment", segment_data)
            start = float(segment["start_time"])
            end = float(segment["end_time"])
            
            # Validate time ranges
            if start >= video_duration:
                print(f"Skipping segment {i+1} (starts after video ends)")
                continue
                
            if end > video_duration:
                end = video_duration
                
            # Create safe filename
            topic = segment.get("topic", f"Segment_{i+1}")
            safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:30]
            output_path = os.path.join(output_dir, f"seg_{i+1:02d}_{safe_topic}.mp4")
            
            # Create video segment with FFmpeg (more reliable)
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(start),
                "-to", str(end),
                "-i", video_path,
                "-c:v", "copy",  # Copy video stream
                "-an",           # No audio initially
                output_path
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Store segment details
            segment_info = {
                "index": i+1,
                "topic": topic,
                "start_time": start,
                "end_time": end,
                "output_path": os.path.abspath(output_path),
                "duration": end - start
            }
            created_segments.append(segment_info)
            print(f"Created video segment: {output_path}")
        
        except Exception as e:
            print(f"Error processing segment {i+1}: {str(e)}")
            continue
    
    # Add properly aligned audio to all segments
    try:
        add_audio_to_segments(video_path, created_segments)
    except Exception as e:
        print(f"Error adding audio to segments: {str(e)}")
    
    # Return results with focus on output paths
    return {
        "status": "success",
        "segments": created_segments,
        "output_directory": os.path.abspath(output_dir)
    }


segmenter_agent = Agent(
    name="video_segmentation_agent",
    model="gemini-2.0-flash",
    input_schema=RankingAgentOutput,
    description="Video segmentation agent that segments video based on start and endtime specified in the json input",
    instruction=VIDEO_SEGMENTATION_AGENT_PROMPT,
    tools=[video_segmentation_tool],
    output_key="video_segmentation_list_output"
)

formatter_agent = Agent(
    name="formatter_agent",
    model="gemini-2.0-flash",
    description="Formatter agent that formats the output of the video segmentation agent",
    instruction=FORMATTER_AGENT_INSTRUCTION,
    output_schema=VideoSegmenterAgentOutput,
    output_key="format_output"
)

video_segmentation_agent = SequentialAgent(
    name="root_agent",
    sub_agents=[segmenter_agent, formatter_agent],
    description="Root agent that orchestrates the video segmentation process"
)
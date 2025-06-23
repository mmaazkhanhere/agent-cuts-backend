import os
from moviepy import VideoFileClip
from typing import Dict, Any, List
import shutil
import subprocess
import json

from agent_cuts.sub_agents.video_segmentation_agent.utils import add_audio_to_segments

_processed_sessions = set()


def video_segmentation_tool(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent tool that splits video into segments based on JSON data containing start/end times
    
    Args:
        json_data: A dictionary containing:
            - video_path: Path to the input video file
            - ranked_segments: Dictionary with a "ranked_list" key containing segments 
              with nested "segment" objects that have "start_time", "end_time", and "topic" fields
            - session_id: (Optional) Unique session identifier
    
    Returns:
        A dictionary containing:
            - status: "success" or "error"
            - segments: List of dictionaries with segment details including output_path
    """
    try:
        # Debug input
        print(f"[DEBUG] Input json_data: {json.dumps(json_data, indent=2)}")
        
        # Get session ID from input data or generate from video path
        session_id = json_data.get("session_id", os.path.basename(os.path.dirname(json_data.get("video_path", ""))))
        
        # Check if this session has already been processed
        if session_id in _processed_sessions:
            print(f"[*] Session {session_id} already processed. Skipping video segmentation.")
            
            # Return existing segments if available
            output_dir = json_data.get("output_dir", "segments")
            if os.path.exists(output_dir):
                segment_paths = []
                for file in sorted(os.listdir(output_dir)):
                    if file.endswith('.mp4'):
                        segment_path = os.path.join(output_dir, file)
                        segment_paths.append({
                            "output_path": os.path.abspath(segment_path),
                            "filename": file
                        })
                
                if segment_paths:
                    return {
                        "status": "success",
                        "message": "Using previously processed segments",
                        "segments": segment_paths,
                        "output_directory": os.path.abspath(output_dir)
                    }
        
        output_dir = json_data.get("output_dir", "segments")
        print(f"[*] Video segmentation tool called with output_dir: {output_dir}")
        
        # Delete all files in the output directory if it exists
        if os.path.exists(output_dir):
            print(f"[*] Deleting all files in {output_dir}")
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                else:
                    shutil.rmtree(item_path)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get absolute path to video
        video_path = os.path.abspath(json_data["video_path"])
        
        # Extract segments - handle different possible data structures
        segments = []
        ranked_segments = json_data.get("ranked_segments", {})
        
        # Check if ranked_segments is a dictionary with ranked_list key
        if isinstance(ranked_segments, dict) and "ranked_list" in ranked_segments:
            segments = ranked_segments["ranked_list"]
        # Check if ranked_segments is already a list
        elif isinstance(ranked_segments, list):
            segments = ranked_segments
        # Try to parse the value if it's a string (possibly a JSON string)
        elif isinstance(ranked_segments, str):
            try:
                parsed = json.loads(ranked_segments)
                if isinstance(parsed, dict) and "ranked_list" in parsed:
                    segments = parsed["ranked_list"]
                elif isinstance(parsed, list):
                    segments = parsed
            except:
                print("[ERROR] Failed to parse ranked_segments as JSON")
                segments = []
        
        if not segments:
            return {
                "status": "error",
                "message": f"No valid segments found in input data. Received: {ranked_segments}"
            }
        
        print(f"[DEBUG] Found {len(segments)} segments to process")
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
                # Debug
                print(f"[DEBUG] Processing segment {i}: {segment_data}")
                
                # Extract segment information - handle different structures
                segment = segment_data.get("segment", segment_data)
                
                # Make sure segment has required fields
                if not isinstance(segment, dict) or "start_time" not in segment or "end_time" not in segment:
                    print(f"[ERROR] Invalid segment data format: {segment}")
                    continue
                
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
                print(f"[ERROR] Error processing segment {i+1}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        # Add properly aligned audio to all segments
        try:
            add_audio_to_segments(video_path, created_segments)
        except Exception as e:
            print(f"[ERROR] Error adding audio to segments: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Mark this session as processed
        _processed_sessions.add(session_id)
        print(f"[*] Session {session_id} marked as processed.")
        
        # Return results with focus on output paths
        print(f"[*] Created {len(created_segments)} segments in {output_dir} and ", created_segments)
        return {
            "status": "success",
            "segments": created_segments,
            "output_directory": os.path.abspath(output_dir)
        }
    
    except Exception as e:
        import traceback
        print(f"[ERROR] Unexpected error in video_segmentation_tool: {str(e)}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to process video segments: {str(e)}"
        }
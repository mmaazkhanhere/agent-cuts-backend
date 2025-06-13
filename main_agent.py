"""
Main Orchestrator Agent for Video Processing Pipeline
Coordinates transcription -> segmentation -> ranking workflow
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import the existing agents
from transcription_agent import run_transcription_agent
from segmentation_agent.agent import run_segmentation_agent
from ranking_agent.agent import run_ranking_agent

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MainOrchestrator')

class VideoProcessingState:
    """Tracks the state of video processing through the pipeline"""
    def __init__(self):
        self.video_path: Optional[str] = None
        self.transcript: Optional[Dict] = None
        self.segments: Optional[list] = None
        self.ranked_segments: Optional[Dict] = None
        self.errors: list = []
        self.start_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for logging"""
        return {
            "video_path": self.video_path,
            "has_transcript": self.transcript is not None,
            "segment_count": len(self.segments) if self.segments else 0,
            "has_ranking": self.ranked_segments is not None,
            "errors": self.errors,
            "duration": str(datetime.now() - self.start_time)
        }

# First, create the orchestrator agent that doesn't use tools but coordinates
orchestrator_agent = LlmAgent(
    name="video_orchestrator",
    model="gemini-2.0-flash",
    description="Orchestrates the video processing pipeline",
    instruction=(
        "You are the main orchestrator for processing video files. "
        "You will receive a video file path and coordinate the processing through three stages:\n"
        "1. Transcription: Extract audio and convert to text with timestamps\n"
        "2. Segmentation: Break the transcript into topical segments\n"
        "3. Ranking: Score and rank segments by clarity, engagement, and trending potential\n\n"
        "For each stage, provide clear status updates and handle any errors gracefully. "
        "Your output should be a summary of the process and the final ranked segments."
    ),
    output_key="processing_summary"
)


async def process_video_pipeline(video_path: str) -> Dict[str, Any]:
    """
    Process a video file through the complete pipeline
    
    Args:
        video_path: Path to the video file
    
    Returns:
        Dict containing the processing results and any errors
    """
    state = VideoProcessingState()
    state.video_path = video_path
    
    logger.info(f"Starting video processing pipeline for: {video_path}")
    
    # Validate video file exists
    if not os.path.exists(video_path):
        error_msg = f"Video file not found: {video_path}"
        logger.error(error_msg)
        state.errors.append(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "state": state.to_dict()
        }
    
    try:
        # Stage 1: Transcription
        logger.info("Stage 1: Starting transcription...")
        transcript_result = await run_transcription_agent(video_path)
        logger.info(f"Transcription completed. Length: {len(transcript_result)} chars")
        
        # Parse the transcript result
        try:
            if isinstance(transcript_result, str):
                # Try to parse as JSON
                state.transcript = json.loads(transcript_result)
            else:
                state.transcript = transcript_result
                
            # Check if we got an error
            if isinstance(state.transcript, dict) and 'error' in state.transcript:
                error_msg = f"Transcription error: {state.transcript['error']}"
                logger.error(error_msg)
                state.errors.append(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "state": state.to_dict()
                }
                
        except json.JSONDecodeError:
            # If not JSON, store as is
            state.transcript = {"text": transcript_result}
        
        logger.debug(f"Transcript preview: {str(state.transcript)[:200]}...")
        
        # Prepare transcript for segmentation
        if isinstance(state.transcript, dict) and state.transcript.get('status') == 'success':
            # Use the segments from the transcript for segmentation
            segments_for_segmentation = state.transcript.get('segments', [])
            # Convert to format expected by segmentation agent
            segmentation_input = json.dumps({
                "transcript": state.transcript.get('transcript', ''),
                "segments": segments_for_segmentation
            })
        else:
            # Fallback format
            segmentation_input = json.dumps(state.transcript)
        
        # Stage 2: Segmentation
        logger.info("Stage 2: Starting segmentation...")
        segment_result = await run_segmentation_agent(segmentation_input)
        logger.info(f"Segmentation completed")
        
        # Parse segments
        try:
            if isinstance(segment_result, str):
                parsed_segments = json.loads(segment_result)
                # Handle different response formats
                if isinstance(parsed_segments, dict) and 'segments' in parsed_segments:
                    state.segments = parsed_segments['segments']
                elif isinstance(parsed_segments, list):
                    state.segments = parsed_segments
                else:
                    state.segments = [parsed_segments]
            else:
                state.segments = segment_result
                
            logger.info(f"Found {len(state.segments)} segments")
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse segmentation result: {e}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            state.segments = []
        
        # Stage 3: Ranking
        if state.segments and len(state.segments) > 0:
            logger.info("Stage 3: Starting ranking...")
            ranking_result = await run_ranking_agent(state.segments)
            logger.info("Ranking completed")
            
            # Parse ranking result
            try:
                if isinstance(ranking_result, str):
                    state.ranked_segments = json.loads(ranking_result)
                else:
                    state.ranked_segments = ranking_result
                    
                # Log ranking summary
                ranked_list = None
                if isinstance(state.ranked_segments, dict) and 'ranked_list' in state.ranked_segments:
                    ranked_list = state.ranked_segments['ranked_list']
                elif isinstance(state.ranked_segments, list):
                    ranked_list = state.ranked_segments
                    
                if ranked_list:
                    logger.info(f"Ranked {len(ranked_list)} segments")
                    for i, segment in enumerate(ranked_list[:3]):  # Log top 3
                        score = segment.get('overall_score', 'N/A')
                        topic = segment.get('segment', {}).get('topic', 'Unknown')
                        logger.info(f"  #{i+1}: {topic} (Score: {score})")
                        
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse ranking result: {e}"
                logger.error(error_msg)
                state.errors.append(error_msg)
        else:
            logger.warning("No segments found to rank")
            state.errors.append("No segments produced from segmentation")
            
    except Exception as e:
        error_msg = f"Pipeline error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        state.errors.append(error_msg)
    
    # Prepare final result
    success = len(state.errors) == 0 and state.ranked_segments is not None
    
    result = {
        "success": success,
        "video_path": video_path,
        "processing_time": str(datetime.now() - state.start_time),
        "errors": state.errors,
        "stats": {
            "transcript_length": len(json.dumps(state.transcript)) if state.transcript else 0,
            "segment_count": len(state.segments) if state.segments else 0,
            "ranked_count": (
                len(state.ranked_segments.get('ranked_list', [])) 
                if isinstance(state.ranked_segments, dict) 
                else len(state.ranked_segments) if state.ranked_segments else 0
            )
        }
    }
    
    if success:
        result["ranked_segments"] = state.ranked_segments
        logger.info(f"Pipeline completed successfully in {result['processing_time']}")
    else:
        logger.error(f"Pipeline failed with {len(state.errors)} errors")
        
    return result


# Create ADK runner for the orchestrator
session_service = InMemorySessionService()
APP_NAME = "video_processor"
USER_ID = "default_user"
SESSION_ID = "default_session"

runner = Runner(
    agent=orchestrator_agent,
    app_name=APP_NAME,
    session_service=session_service
)


async def run_video_processor(video_path: str, output_dir: str = "./output") -> str:
    """
    Main entry point for processing a video file through the ADK pipeline
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save results (default: ./output)
    
    Returns:
        JSON string with processing results
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the processing pipeline
    result = await process_video_pipeline(video_path)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"results_{timestamp}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Results saved to: {output_file}")
    
    # Create ADK message for the orchestrator
    summary = f"""
Video Processing Complete:
- Video: {video_path}
- Success: {result['success']}
- Processing Time: {result['processing_time']}
- Segments Found: {result['stats']['segment_count']}
- Segments Ranked: {result['stats']['ranked_count']}
- Errors: {len(result['errors'])}
- Results saved to: {output_file}
"""
    
    if result['errors']:
        summary += f"\nErrors encountered:\n"
        for error in result['errors']:
            summary += f"- {error}\n"
    
    new_message_content = types.Content(
        role="user",
        parts=[types.Part(text=summary)]
    )
    
    final_response = summary
    try:
        # Ensure session exists
        session = await session_service.get_session(
            app_name=APP_NAME, 
            user_id=USER_ID, 
            session_id=SESSION_ID
        )
        if not session:
            await session_service.create_session(
                app_name=APP_NAME, 
                user_id=USER_ID, 
                session_id=SESSION_ID
            )
        
        # Run through ADK for any additional processing
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=new_message_content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            final_response = part.text
                            break
                break
                
    except Exception as e:
        logger.error(f"ADK runner error: {e}")
    
    return json.dumps(result, indent=2)


def main():
    """Main function for command-line usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python main_agent.py <video_path> [output_dir]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./output"
    
    # Check required environment variables
    required_vars = ["GOOGLE_API_KEY", "GROQ_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set them in your .env file")
        sys.exit(1)
    
    # Run the async function
    try:
        result = asyncio.run(run_video_processor(video_path, output_dir))
        print(result)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Failed to process video: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

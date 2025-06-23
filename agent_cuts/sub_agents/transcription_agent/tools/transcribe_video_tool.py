
import os
from typing import Dict, Any
from agent_cuts.sub_agents.transcription_agent.utilities.engine import TranscriptionEngine
from agent_cuts.sub_agents.transcription_agent.types import TranscriptOutput,TranscriptAgentOutput


async def transcribe_video_tool(video_path: str) -> Dict[str, Any]:
    """A tool that is used to transcribe video, Video path is provided within the the function"""
    print(f"[*] Tool called with video_path: {video_path}")

    # Check if file exists first
    if not os.path.exists(video_path):
        error_msg = f"File not found: {video_path}"
        print(f"[!] {error_msg}")
        return {"error": error_msg, "status": "error"}

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return {"error": "GROQ_API_KEY not found in environment variables", "status": "error"}

    try:
        # Initialize TranscriptionEngine with the API key
        engine = TranscriptionEngine(groq_api_key=groq_api_key)

        # Perform transcription with sentence-level processing
        full_result = await engine.transcribe_video(video_path, sentence_level=True)

        if full_result.get("status") != "success":
            return {"error": full_result.get("error", "Unknown error during transcription"), "status": "error"}

        # Convert the result to TranscriptAgentOutput format
        segments = [
            TranscriptOutput(
                text=segment["text"],
                start_time=segment["start_time"],
                end_time=segment["end_time"]
            )
            for segment in full_result.get("sentence_segments", [])
        ]

        transcription_output = TranscriptAgentOutput(segments=segments)

        result = transcription_output.model_dump()
        result["status"] = "success"

        ## save the transcription to a file
        # output_file = os.path.join(os.path.dirname(video_path), "transcription_output.json")
        # with open(output_file, 'w') as f:
        #     json.dump(result, f, indent=4)
        print(f"[+] Tool returning: {result.get('status', 'unknown')} with {len(result.get('segments', []))} segments")
        return result

    except Exception as e:
        return {"error": f"Error during transcription: {str(e)}", "status": "error"}
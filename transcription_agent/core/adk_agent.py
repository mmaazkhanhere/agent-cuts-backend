"""
Google ADK Agent wrapper for transcription with simplified output
"""
import os
import json
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

from .engine import TranscriptionEngine
from ..utils.output_formatter import create_simplified_transcript

load_dotenv()


async def transcribe_video_tool(video_path: str) -> Dict[str, Any]:
    """Tool function for ADK agent - returns simplified transcript"""
    print(f"[*] Tool called with video_path: {video_path}")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return {"error": "GROQ_API_KEY not found in environment variables"}
    
    engine = TranscriptionEngine(groq_api_key)
    # Get full transcription result
    full_result = await engine.transcribe_video(video_path, sentence_level=True)
    
    # Simplify the output
    simplified = create_simplified_transcript(full_result)
    
    print(f"[+] Tool returning: {simplified.get('status', 'unknown')} with {len(simplified.get('segments', []))} segments")
    return simplified


# Create ADK Agent with more explicit instructions
transcription_agent = Agent(
    name="transcription_agent",
    model="gemini-2.0-flash",
    description="Transcription agent that converts video files to text with sentence-level timestamps",
    instruction=(
        "You are a video transcription agent. When a user asks you to transcribe a video:\n\n"
        "STEP 1: Extract the video file path from the user's message\n"
        "STEP 2: Call the transcribe_video_tool function with that exact path\n"
        "STEP 3: Return ONLY the JSON result from the tool\n\n"
        "IMPORTANT RULES:\n"
        "- ALWAYS call transcribe_video_tool for any transcription request\n"
        "- NEVER make up or simulate transcript data\n"
        "- Return the tool result as-is without any additional text\n"
        "- Do not explain what you're doing - just use the tool and return results\n\n"
        "Example:\n"
        "User: 'Transcribe ./video/test.mp4'\n"
        "Action: Call transcribe_video_tool('./video/test.mp4')\n"
        "Response: [JSON result from tool]"
    ),
    tools=[transcribe_video_tool],
)

# Session management
session_service = InMemorySessionService()
APP_NAME = "transcription_app"
USER_ID = "default_user"
SESSION_ID = "default_session"

runner = Runner(
    agent=transcription_agent,
    app_name=APP_NAME,
    session_service=session_service
)


async def run_transcription_agent(video_path: str) -> str:
    """
    Run the ADK transcription agent
    
    Returns:
        JSON string with simplified transcript format
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return json.dumps({"status": "error", "error": "GROQ_API_KEY not found in environment variables"})
    
    prompt = f"Transcribe this video: {video_path}"
    
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
                        if part.function_response.name == 'transcribe_video_tool':
                            tool_result = part.function_response.response
                            print(f"[*] Got tool result: {tool_result}")
                            break
                            
            if tool_result:
                break
                
    except Exception as e:
        print(f"Error during agent run: {e}")
        return json.dumps({"status": "error", "error": f"An error occurred: {str(e)}"})

    # Return tool result if we got it
    if tool_result:
        return json.dumps(tool_result)
    
    # Fallback: Run the transcription directly if agent didn't call tool
    print("[!] Agent didn't call tool, running transcription directly...")
    try:
        result = await transcribe_video_tool(video_path)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"status": "error", "error": f"Direct transcription failed: {str(e)}"})

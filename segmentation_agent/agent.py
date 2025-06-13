import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

class SegmentationOutput(BaseModel):
    topic: str = Field(description="Topic of the segment")
    transcript: str = Field(description="Transcript of the segment")
    start_time: str = Field(description="Start time of the segment")
    end_time: str = Field(description="End time of the segment")
    
class SegmentationAgentOutput(BaseModel):
    segments: list[SegmentationOutput] = Field(description="List of segments")


segmentation_agent = Agent(
    name="segmentation_agent",
    model="gemini-2.0-flash",
    description="Segmentation agent that segments transcript into topics",
    instruction=(
        "You are a segmentation agent that processes audio transcripts into topical segments.\n\n"
        
        "You will receive a JSON input with:\n"
        "- 'transcript': The full text transcript\n"
        "- 'segments': Array of sentence-level segments with start_time and end_time\n\n"
        
        "Your task:\n"
        "1. Analyze the transcript to identify distinct topics or themes\n"
        "2. Group related sentences together into topic-based segments\n"
        "3. Each output segment should represent a cohesive topic or idea\n"
        "4. Use the start_time from the first sentence and end_time from the last sentence in each group\n\n"
        
        "Output format should match the schema with an array of segments, each containing:\n"
        "- topic: A descriptive title for the segment (10-50 characters)\n"
        "- transcript: The combined text of all sentences in this topic segment\n"
        "- start_time: The start time as a string (from the first sentence)\n"
        "- end_time: The end time as a string (from the last sentence)\n\n"
        
        "Aim for 3-10 topic segments depending on content length and diversity."
    ),
    output_schema=SegmentationAgentOutput
)

session_service = InMemorySessionService()
APP_NAME = "segmentation_app"
USER_ID = "default_user"
SESSION_ID = "default_session"

runner = Runner(
    agent=segmentation_agent,
    app_name=APP_NAME,
    session_service=session_service
)


async def run_segmentation_agent(transcript):
    """Run the ADK segmentation agent"""
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        return "GOOGLE_API_KEY not found in environment variables"
    
    new_message_content = types.Content(
        role="user",
        parts=[types.Part(text=transcript)]
    )

    final_response = "No response received."
    try:
        # Ensure session exists
        if not await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID):
            await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

        for event in runner.run(
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
        print(f"Error during segmentation agent run: {e}")
        final_response = f"An error occurred: {e}"

    return final_response

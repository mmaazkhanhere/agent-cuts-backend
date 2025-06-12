import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import google_search

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
    overall_score: int = Field(description="Overall score of the segment out of 10")


    
class RankingAgentOutput(BaseModel):
    ranked_list: list[RankingOutput] = Field(description="List of segments ranked based on overall score")

google_search_agent = LlmAgent(
    name="segment_scorer_agent", # Renamed for clarity
    model="gemini-2.0-flash",
    description="Analyze video segments, score them based on clarity, engagement, and trending potential, and output the scored segments.",
    instruction=(
        "You will receive a JSON object containing a list of video segments. Each segment includes details such as topic, transcript, start time, and end time. "
        "For each segment, perform the following steps:\n"
        "1. Using Google Search, assess the trending potential of the segment's topic. Search for recent news, social media trends, and overall interest in the topic.\n"
        "2. Using Google Search, assess the engagement potential of the segment's content. Consider if the transcript's language, questions asked, or calls to action would likely engage viewers.\n"
        "3. Assign a clarity score (out of 10) based on the transcript's readability and coherence.\n"
        "4. Assign an engagement score (out of 10) based on your assessment of its engagement potential.\n"
        "5. Assign a trending score (out of 10) based on your assessment of its trending potential.\n"
        "6. Calculate an overall score (out of 10) for each segment. You can use a weighted average (e.g., 40% trending, 30% engagement, 30% clarity) or your own logic.\n"
        "Finally, output a JSON array where each object in the array represents a segment with its original details and the newly calculated clarity_score, engagement_score, trending_score, and overall_score. Ensure the output structure matches the `RankingOutput` Pydantic model's data fields for each item in the list."
    ),
    tools=[google_search],
    output_key="score"
    # No output_key needed if the formatter agent expects a list of the parsed outputs
)

formatter_agent = LlmAgent(
    name="formatter_agent",
    model="gemini-2.0-flash",
    description="Sorts and formats the scored video segments into a structured JSON output.",
    instruction=(
        "You will receive a list of video segments, each with clarity_score, engagement_score, trending_score, and overall_score. "
        "Your task is to sort this list in descending order based on the 'overall_score'. "
        "Then, format the sorted list into a JSON object with a single key 'ranked_list', where the value is the sorted list of segments. "
        "Ensure the output conforms to the `RankingAgentOutput` Pydantic schema."
    ),
    output_schema=RankingAgentOutput,
    output_key="ranked_list"
)

root_agent = SequentialAgent(
    name="root_agent",
    description="Root agent that orchestrates the ranking process",
    sub_agents=[google_search_agent, formatter_agent]
)

session_service = InMemorySessionService()
APP_NAME = "ranking_app"
USER_ID = "default_user"
SESSION_ID = "default_session"

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

async def run_ranking_agent(transcript):
    """Run the ADK ranking agent"""
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
        print(f"Error during ranking agent run: {e}")
        final_response = f"An error occurred: {e}"

    return final_response

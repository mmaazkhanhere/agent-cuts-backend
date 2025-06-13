import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import json

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
    overall_score: float = Field(description="Overall score of the segment out of 10")

class RankingAgentOutput(BaseModel):
    ranked_list: list[RankingOutput] = Field(description="List of segments ranked based on overall score")

# Combined scoring agent that does everything in one step
combined_scoring_agent = LlmAgent(
    name="combined_scoring_agent",
    model="gemini-2.0-flash",
    description="Analyze segments for clarity, engagement, and use search for trending scores.",
    instruction=(
        "You will receive a JSON array of video segments. For each segment:\n\n"
        
        "STEP 1 - CLARITY SCORING (1-10) based on transcript:\n"
        "- 9-10: Crystal clear, well-structured, complete thoughts\n"
        "- 7-8: Mostly clear with good flow\n"
        "- 5-6: Some confusion, moderate structure issues\n"
        "- 3-4: Difficult to follow, poor structure\n"
        "- 1-2: Very confusing, no clear message\n\n"
        
        "STEP 2 - ENGAGEMENT SCORING (1-10) based on transcript:\n"
        "- 9-10: Personal stories, emotional content, relatable\n"
        "- 7-8: Interesting anecdotes, some emotional appeal\n"
        "- 5-6: Standard content, some interesting points\n"
        "- 3-4: Dry, academic, few hooks\n"
        "- 1-2: Boring, no emotional connection\n\n"
        
        "STEP 3 - TRENDING SCORING (1-10) using Google Search:\n"
        "- Extract key topics from the segment\n"
        "- Search for '[topic] 2025 trending' or '[topic] news today'\n"
        "- 9-10: Highly trending with recent news\n"
        "- 7-8: Some recent coverage\n"
        "- 5-6: Older coverage, niche interest\n"
        "- 3-4: Minimal coverage\n"
        "- 1-2: No recent interest\n\n"
        
        "STEP 4 - OVERALL SCORE:\n"
        "Calculate: (clarity * 0.25) + (engagement * 0.40) + (trending * 0.35)\n"
        "Round to 1 decimal place\n\n"
        
        "Output a JSON array with all segments including their scores.\n"
        "Each segment should have: topic, transcript, start_time, end_time, "
        "clarity_score, engagement_score, trending_score, and overall_score."
    ),
    tools=[google_search],
    output_key="scored_segments"
)

# Final formatting agent
formatter_agent = LlmAgent(
    name="formatter_agent",
    model="gemini-2.0-flash",
    description="Sort and format the scored segments.",
    instruction=(
        "You receive a JSON array of segments with all scores.\n\n"
        
        "Your tasks:\n"
        "1. Verify all segments have valid scores (1-10 for individual scores)\n"
        "2. Recalculate overall_score if needed: (clarity * 0.25) + (engagement * 0.40) + (trending * 0.35)\n"
        "3. Sort segments by overall_score in descending order\n"
        "4. Format the output EXACTLY as:\n\n"
        
        "{\n"
        '  "ranked_list": [\n'
        "    {\n"
        '      "segment": {\n'
        '        "topic": "...",\n'
        '        "transcript": "...",\n'
        '        "start_time": "...",\n'
        '        "end_time": "..."\n'
        "      },\n"
        '      "clarity_score": X,\n'
        '      "engagement_score": X,\n'
        '      "trending_score": X,\n'
        '      "overall_score": X.X\n'
        "    },\n"
        "    ...\n"
        "  ]\n"
        "}"
    ),
    output_schema=RankingAgentOutput,
    output_key="final_ranking"
)

# Create the sequential pipeline
root_agent = SequentialAgent(
    name="video_segment_ranker",
    description="Ranks video segments based on clarity, engagement, and trending potential",
    sub_agents=[combined_scoring_agent, formatter_agent]
)

# Initialize session service
session_service = InMemorySessionService()
APP_NAME = "ranking_app"
USER_ID = "default_user"
SESSION_ID = "default_session"

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

async def run_ranking_agent(segments_json):
    """
    Run the ADK ranking agent
    
    Args:
        segments_json: JSON string or list containing video segments
    
    Returns:
        JSON string with ranked segments or error message
    """
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        return json.dumps({"error": "GOOGLE_API_KEY not found in environment variables"})
    
    # Convert to string if it's a list
    if isinstance(segments_json, list):
        segments_json = json.dumps(segments_json)
    
    new_message_content = types.Content(
        role="user",
        parts=[types.Part(text=segments_json)]
    )

    final_response = None
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

        # Run the agent pipeline
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
        print(f"Error during ranking agent run: {e}")
        
        # Fallback: If there's an error, try to at least score based on transcript
        try:
            segments = json.loads(segments_json)
            fallback_result = process_segments_fallback(segments)
            return json.dumps(fallback_result)
        except:
            return json.dumps({"error": f"An error occurred: {str(e)}"})

    return final_response if final_response else json.dumps({"error": "No response received"})


def process_segments_fallback(segments):
    """
    Fallback processing when API calls fail
    Scores based on simple heuristics
    """
    ranked_list = []
    
    for segment in segments:
        # Simple heuristic scoring based on transcript length and keywords
        transcript = segment.get('transcript', '')
        
        # Clarity: Based on sentence structure (periods, complete thoughts)
        sentences = transcript.count('.') + transcript.count('!') + transcript.count('?')
        clarity_score = min(10, max(1, sentences // 5 + 3))
        
        # Engagement: Based on personal pronouns, questions, emotional words
        engagement_keywords = ['I', 'me', 'my', 'you', 'story', 'feel', 'think', 'believe', '?']
        engagement_count = sum(1 for word in engagement_keywords if word in transcript)
        engagement_score = min(10, max(1, engagement_count + 2))
        
        # Trending: Default to moderate since we can't search
        trending_score = 5
        
        # Calculate overall
        overall_score = round(
            (clarity_score * 0.25) + 
            (engagement_score * 0.40) + 
            (trending_score * 0.35), 
            1
        )
        
        ranked_list.append({
            "segment": {
                "topic": segment.get('topic', ''),
                "transcript": segment.get('transcript', ''),
                "start_time": segment.get('start_time', ''),
                "end_time": segment.get('end_time', '')
            },
            "clarity_score": clarity_score,
            "engagement_score": engagement_score,
            "trending_score": trending_score,
            "overall_score": overall_score
        })
    
    # Sort by overall score
    ranked_list.sort(key=lambda x: x['overall_score'], reverse=True)
    
    return {"ranked_list": ranked_list}
from dotenv import load_dotenv  

from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import google_search

from .prompt import SCORING_AGENT_PROMPT, FORMATTER_AGENT_PROMPT
from .types import RankingAgentOutput
from agent_cuts.sub_agents.segmentation_agent.type import SegmentationAgentOutput
from google.adk.models.lite_llm import LiteLlm

load_dotenv()


combined_scoring_agent = Agent(
    name="combined_scoring_agent",
    model="gemini-2.0-flash",
    description="Analyze segments for clarity, engagement, and use search for trending scores.",
    input_schema=SegmentationAgentOutput,
    instruction=SCORING_AGENT_PROMPT,
    tools=[google_search],
    output_key="scored_segments"
)


formatter_agent = Agent(
    name="formatter_agent",
    model="gemini-2.0-flash-lite",
    description="Sort and format the scored segments.",
    instruction=FORMATTER_AGENT_PROMPT,
    output_schema=RankingAgentOutput,
    output_key="final_ranking"
)


ranking_agent = SequentialAgent(
    name="video_segment_ranker",
    description="Ranks video segments based on clarity, engagement, and trending potential",
    sub_agents=[combined_scoring_agent, formatter_agent],
)
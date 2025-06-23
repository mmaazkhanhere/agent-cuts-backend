
from dotenv import load_dotenv

from google.adk.agents import Agent, SequentialAgent

from .prompt import VIDEO_SEGMENTATION_AGENT_PROMPT, FORMATTER_AGENT_INSTRUCTION
from .tools.video_segmentation_tool import video_segmentation_tool
from agent_cuts.sub_agents.ranking_agent.types import RankingAgentOutput
from agent_cuts.sub_agents.video_segmentation_agent.types import VideoSegmenterAgentOutput

load_dotenv()

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
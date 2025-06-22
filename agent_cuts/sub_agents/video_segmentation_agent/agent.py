
from dotenv import load_dotenv

from google.adk.agents import Agent

from .prompt import VIDEO_SEGMENTATION_AGENT_PROMPT
from .tools.video_segmentation_tool import video_segmentation_tool

load_dotenv()

video_segmentation_agent = Agent(
    name="video_segmentation_agent",
    model="gemini-2.0-flash",
    description="Video segmentation agent that segments video based on start and endtime specified in the json input",
    instruction=VIDEO_SEGMENTATION_AGENT_PROMPT,
    tools=[video_segmentation_tool],
)
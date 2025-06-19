from google.adk.agents import SequentialAgent


from .sub_agents.transcription_agent import transcription_agent
from .sub_agents.segmentation_agent import segmentation_agent
from .sub_agents.ranking_agent import ranking_agent
from .sub_agents.video_segmentation_agent import video_segmentation_agent
from .sub_agents.copywriter_agent import copywrite_agent


agent_cut = SequentialAgent(
    name="agent_cut",
    description="Agent that cuts a video into segments based on topics and rearrange them based on its potential to be viral and trending",
    sub_agents=[
        transcription_agent,
        segmentation_agent,
        ranking_agent,
        video_segmentation_agent,
        copywrite_agent
    ]
)

root_agent = agent_cut
from pydantic import BaseModel, Field

class CopyWriteOutput(BaseModel):
    """
    A Pydantic model representing the output of a copywriting task.
    """
    title: str = Field(description="Title of the video")
    description: str = Field(description="Short description of the video")
    tags: list[str] = Field(description="List of tags for the video")

class CopywriterAgentOutput(BaseModel):
    video_segments: CopyWriteOutput = Field(description="Output of the copywriter agent")
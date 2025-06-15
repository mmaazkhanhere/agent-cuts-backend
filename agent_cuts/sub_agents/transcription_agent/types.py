from pydantic import BaseModel, Field

class TranscriptOutput(BaseModel):
    text: str = Field(description="The transcript of the audio file")
    start_time: float = Field(description="The start time of the transcript in seconds")
    end_time: float = Field(description="The end time of the transcript in seconds")

class TranscriptAgentOutput(BaseModel):
    segments: list[TranscriptOutput] = Field(description="The segments of the transcript")
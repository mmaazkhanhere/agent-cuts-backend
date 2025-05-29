from fastapi import FastAPI, UploadFile, File, Form, Query
from demo_agent import weather_time_agent_runner
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()
app: FastAPI = FastAPI()

@app.get("/")
def get_root():
    return {"Backend is running with Enhanced Transcription Agent"}

@app.post('/chat')
async def get_agent_response(prompt: str):
    response = await weather_time_agent_runner(prompt)
    return response

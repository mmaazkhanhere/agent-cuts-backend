from fastapi import FastAPI
from demo_agent import weather_time_agent_runner

app: FastAPI = FastAPI()

@app.get("/")
def get_root():
    return {"Backend is running"}

@app.post('/chat')
async def get_agent_response(prompt: str):
    response = await weather_time_agent_runner(prompt)
    return response
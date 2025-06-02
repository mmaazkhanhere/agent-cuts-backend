"""Main agent module for the application"""
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

# Import tools
from tools.weather_time import get_weather, get_current_time

# Create the main agent
main_agent = Agent(
    name="main_agent",
    model="gemini-2.0-flash",
    description="Main agent that coordinates weather, time, and other functionalities.",
    instruction=(
        "You are a helpful assistant that can provide weather and time information. "
        "Use the available tools to fetch information. Always state if data is unavailable."
    ),
    tools=[get_weather, get_current_time],
)

# Initialize session service
session_service = InMemorySessionService()
APP_NAME = "agent_cuts_app"

def create_runner():
    """Create a new runner instance"""
    return Runner(
        agent=main_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

async def run_agent(prompt: str, user_id: str = "default_user", 
                   session_id: str = "default_session") -> str:
    """Run the main agent with a prompt"""
    runner = create_runner()
    
    new_message_content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )

    final_response = "No response received."
    try:
        # Ensure session exists
        if not await session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id):
            await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)

        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message_content
        ):
            if event.is_final_response():
                for part in event.content.parts:
                    if part.text:
                        final_response = part.text
                        break
                break
    except Exception as e:
        print(f"Error during agent run: {e}")
        final_response = f"An error occurred: {e}"

    return final_response

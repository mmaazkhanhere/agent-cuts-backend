from datetime import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from fastapi import FastAPI # Assuming this is in your main file as well

load_dotenv()


def get_weather(city: str) -> dict:
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a high of 30 degrees "
                "and a low of 44 degrees."
            ),
        }
    else:
        return {
            "status": "error",
            "report": f"Weather data for {city} is not available.",
        }


def get_current_time(city: str) -> dict:
    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}


root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description=(
        "An agent that provides current weather and time information for cities."
    ),
    instruction=(
        "You are a helpful agent specialized in providing current weather and time. "
        "Use the 'get_weather' tool to fetch weather information and the 'get_current_time' "
        "tool to fetch time information. Always state if data is unavailable for a city."
    ),
    tools=[get_weather, get_current_time],
)

# Initialize Session Service and Runner GLOBALLY
session_service = InMemorySessionService()
APP_NAME = "weather_time_app"
USER_ID = "default_user"
SESSION_ID = "default_session"

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)


async def weather_time_agent_runner(prompt: str) -> str:
    new_message_content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )

    final_response = "No response received."
    try:
        # CORRECTED: Add 'app_name' argument to get_session and create_session
        if not await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID):
            await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

        for event in runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
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

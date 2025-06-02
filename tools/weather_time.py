"""Weather and time tools for the main agent"""
from datetime import datetime
from zoneinfo import ZoneInfo

def get_weather(city: str) -> dict:
    """Get weather information for a city"""
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
    """Get current time for a city"""
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

"""
Simple test to verify agent_cuts is working
"""

import asyncio
import os
import sys
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agent_cuts import agent_cut


async def test_sequential_agent():
    """Test the sequential agent directly"""
    
    print("\n🧪 Testing Sequential Agent Directly")
    print("=" * 50)
    
    # Session setup
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent_cut,
        app_name="test_app",
        session_service=session_service
    )
    
    # Create session
    await session_service.create_session(
        app_name="test_app",
        user_id="test_user",
        session_id="test_session"
    )
    
    # Test message
    video_path = os.path.abspath("../video/test.mp4")
    message_data = {
        "video_path": video_path,
        "output_dir": "test_output"
    }
    
    message = types.Content(
        role="user", 
        parts=[types.Part(text=json.dumps(message_data))]
    )
    
    print(f"Input: {json.dumps(message_data, indent=2)}")
    print("\nRunning agent...")
    
    try:
        response_count = 0
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=message
        ):
            response_count += 1
            print(f"\n--- Response {response_count} ---")
            
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for i, part in enumerate(event.content.parts):
                        if hasattr(part, 'text') and part.text:
                            print(f"Part {i} (text): {part.text[:200]}...")
                        if hasattr(part, 'function_call'):
                            print(f"Part {i} (function): {part.function_call}")
                        if hasattr(part, 'function_response'):
                            print(f"Part {i} (function response): {part.function_response}")
            
            if hasattr(event, 'is_final_response') and callable(event.is_final_response) and event.is_final_response():
                print("\n[Final Response Received]")
                break
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_sequential_agent())

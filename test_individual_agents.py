"""
Test individual agents to debug the pipeline
"""

import asyncio
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import individual agents
from agent_cuts.sub_agents.transcription_agent import transcription_agent
from agent_cuts.sub_agents.segmentation_agent import segmentation_agent


async def test_transcription_agent():
    """Test transcription agent alone"""
    print("\n🧪 Testing Transcription Agent")
    print("=" * 50)
    
    session_service = InMemorySessionService()
    runner = Runner(
        agent=transcription_agent,
        app_name="test_transcription",
        session_service=session_service
    )
    
    await session_service.create_session(
        app_name="test_transcription",
        user_id="test",
        session_id="test"
    )
    
    video_path = os.path.abspath("../video/test.mp4")
    message = json.dumps({"video_path": video_path})
    
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=message)]
    )
    
    print(f"Input: {message}")
    
    result = None
    async for event in runner.run_async(
        user_id="test",
        session_id="test", 
        new_message=new_message
    ):
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        try:
                            data = json.loads(part.text)
                            if 'segments' in data:
                                result = data
                                print(f"\n✅ Got transcription with {len(data.get('segments', []))} segments")
                                print(f"First segment: {data['segments'][0] if data.get('segments') else 'None'}")
                        except:
                            pass
        
        if hasattr(event, 'is_final_response') and callable(event.is_final_response) and event.is_final_response():
            break
    
    return result


async def test_segmentation_with_transcript(transcript_data):
    """Test segmentation agent with transcript data"""
    print("\n🧪 Testing Segmentation Agent")
    print("=" * 50)
    
    if not transcript_data:
        print("❌ No transcript data to test with")
        return None
        
    session_service = InMemorySessionService()
    runner = Runner(
        agent=segmentation_agent,
        app_name="test_segmentation",
        session_service=session_service
    )
    
    await session_service.create_session(
        app_name="test_segmentation",
        user_id="test",
        session_id="test"
    )
    
    # Segmentation agent expects TranscriptAgentOutput format
    message = json.dumps(transcript_data)
    
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=message)]
    )
    
    print(f"Input segments: {len(transcript_data.get('segments', []))}")
    
    result = None
    async for event in runner.run_async(
        user_id="test",
        session_id="test",
        new_message=new_message
    ):
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        try:
                            data = json.loads(part.text)
                            if 'segments' in data or 'topics' in data:
                                result = data
                                print(f"\n✅ Got segmentation result")
                                print(f"Keys: {list(data.keys())}")
                        except:
                            pass
        
        if hasattr(event, 'is_final_response') and callable(event.is_final_response) and event.is_final_response():
            break
            
    return result


async def main():
    """Test agents individually"""
    
    # Test transcription
    transcript = await test_transcription_agent()
    
    if transcript:
        # Test segmentation with transcript
        segmentation = await test_segmentation_with_transcript(transcript)
        
        if segmentation:
            print("\n✅ Pipeline working up to segmentation")
        else:
            print("\n❌ Segmentation failed")
    else:
        print("\n❌ Transcription failed")


if __name__ == "__main__":
    asyncio.run(main())

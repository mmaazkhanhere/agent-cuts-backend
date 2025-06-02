"""Test script for the refactored multi-agent architecture"""
import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Import from the new structure
from subagents.transcription import TranscriptionSubAgent
from agent import run_agent

load_dotenv()

async def test_transcription_subagent():
    """Test the transcription subagent"""
    
    # Check API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found in .env file")
        return
    
    # Get video path
    video_path = input("Enter video file path: ").strip().strip('"')
    
    if not os.path.exists(video_path):
        print("❌ Video file not found!")
        return
    
    print(f"🎬 Testing transcription subagent with: {Path(video_path).name}")
    
    try:
        # Use the transcription subagent
        transcription_agent = TranscriptionSubAgent(groq_api_key)
        result = await transcription_agent.transcribe_video(
            video_path=video_path,
            sentence_level=True
        )
        
        if result['status'] == 'success':
            print(f"\n✅ Success!")
            print(f"📊 Words: {result['metadata']['total_words']}")
            print(f"🎯 Confidence: {result['metadata']['avg_confidence']:.3f}")
            
            # Show sentence-level results
            if 'sentence_segments' in result:
                sentences = result['sentence_segments']
                print(f"📝 Sentences: {len(sentences)}")
                
                print(f"\n🔍 First 5 sentences with precise timestamps:")
                for i, sentence in enumerate(sentences[:5]):
                    print(f"{i+1}. [{sentence['start_time']:.1f}s - {sentence['end_time']:.1f}s] ({sentence['duration']:.1f}s)")
                    print(f"   \"{sentence['text']}\"")
                    print(f"   Words: {sentence['word_count']}, Confidence: {sentence['confidence']:.3f}")
                    print()
                
                # Save results
                output_file = f"test_result_{Path(video_path).stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"💾 Results saved to: {output_file}")
                
        else:
            print(f"❌ Failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_main_agent():
    """Test the main agent"""
    print("\n🤖 Testing main agent...")
    
    # Test weather
    response = await run_agent("What's the weather in New York?")
    print(f"Weather response: {response}")
    
    # Test time
    response = await run_agent("What time is it in New York?")
    print(f"Time response: {response}")

async def main():
    """Run all tests"""
    print("🧪 Testing refactored multi-agent architecture\n")
    
    choice = input("What to test?\n1. Transcription subagent\n2. Main agent\n3. Both\nChoice: ")
    
    if choice == "1":
        await test_transcription_subagent()
    elif choice == "2":
        await test_main_agent()
    elif choice == "3":
        await test_main_agent()
        await test_transcription_subagent()

if __name__ == "__main__":
    asyncio.run(main())

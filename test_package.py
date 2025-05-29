"""
Updated simple test using the new transcription agent package
"""
import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Import from the new transcription agent package
from transcription_agent import transcribe_video

load_dotenv()


async def test_transcription_package():
    """Test the transcription agent package"""
    
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
    
    print(f"🎬 Testing transcription package with: {Path(video_path).name}")
    
    try:
        # Use the convenient transcribe_video function
        result = await transcribe_video(
            video_path=video_path,
            groq_api_key=groq_api_key,
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
                output_file = f"package_test_result_{Path(video_path).stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"💾 Results saved to: {output_file}")
                
                # Create simple sentence export
                simple_sentences = [
                    {
                        "start_time": s['start_time'],
                        "end_time": s['end_time'], 
                        "text": s['text']
                    }
                    for s in sentences
                ]
                
                simple_file = f"sentences_{Path(video_path).stem}.json"
                with open(simple_file, 'w', encoding='utf-8') as f:
                    json.dump(simple_sentences, f, indent=2, ensure_ascii=False)
                print(f"📄 Simple sentences saved to: {simple_file}")
                
        else:
            print(f"❌ Failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_transcription_package())

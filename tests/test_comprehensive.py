"""
Comprehensive test script for the refactored multi-agent system
"""
import asyncio
import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import from new structure
from subagents.transcription import TranscriptionSubAgent
from agent import run_agent

load_dotenv()

class TestRunner:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.test_results = []
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check API keys
        if not self.groq_api_key:
            print("❌ GROQ_API_KEY not found in environment variables")
            print("   Please set GROQ_API_KEY in your .env file")
            return False
        else:
            print("✅ GROQ_API_KEY found")
            
        if self.google_api_key:
            print("✅ GOOGLE_API_KEY found (optional)")
        else:
            print("⚠️  GOOGLE_API_KEY not found (optional for main agent)")
        
        # Check FFmpeg
        try:
            import ffmpeg
            print("✅ ffmpeg-python installed")
        except ImportError:
            print("❌ ffmpeg-python not installed")
            print("   Run: pip install ffmpeg-python")
            return False
        
        # Check other dependencies
        try:
            from pydub import AudioSegment
            print("✅ pydub installed")
        except ImportError:
            print("❌ pydub not installed") 
            print("   Run: pip install pydub")
            return False
            
        try:
            from groq import Groq
            print("✅ groq installed")
        except ImportError:
            print("❌ groq not installed")
            print("   Run: pip install groq")
            return False
            
        print("✅ All prerequisites met!\n")
        return True
    
    def find_test_videos(self):
        """Find available test videos"""
        print("🎬 Looking for test videos...")
        
        video_paths = [
            Path("video/test.mp4"),
            Path("../video/test.mp4"),
            Path("test.mp4")
        ]
        
        found_videos = []
        for path in video_paths:
            if path.exists():
                found_videos.append(path)
                print(f"   ✅ Found: {path}")
        
        if not found_videos:
            print("   ❌ No test videos found")
            
        return found_videos
    
    async def test_transcription_subagent(self, video_path: Path):
        """Test the transcription subagent"""
        print(f"\n{'='*60}")
        print(f"🧪 TRANSCRIPTION SUBAGENT TEST: {video_path.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Create transcription subagent
            transcription_agent = TranscriptionSubAgent(self.groq_api_key)
            result = await transcription_agent.transcribe_video(
                str(video_path),
                sentence_level=True
            )
            
            processing_time = time.time() - start_time
            
            if result['status'] == 'success':
                print(f"✅ Success in {processing_time:.2f} seconds")
                print(f"📊 Words: {result['metadata']['total_words']}")
                print(f"📈 Confidence: {result['metadata']['avg_confidence']:.3f}")
                print(f"🎯 Chunks: {result['metadata']['successful_chunks']}/{result['metadata']['total_chunks']}")
                
                # Show sentence examples if available
                if 'sentence_segments' in result:
                    print(f"📝 Sentences: {len(result['sentence_segments'])}")
                    print("\n🔍 First 3 sentences:")
                    for i, sentence in enumerate(result['sentence_segments'][:3]):
                        print(f"   {i+1}. [{sentence['start_time']:.1f}s - {sentence['end_time']:.1f}s]")
                        print(f"      \"{sentence['text']}\"")
                
                # Save result
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                output_file = output_dir / f"test_result_{video_path.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"\n💾 Saved to: {output_file}")
                
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_main_agent(self):
        """Test the main agent"""
        print(f"\n{'='*60}")
        print(f"🤖 MAIN AGENT TEST")
        print(f"{'='*60}")
        
        test_prompts = [
            "What's the weather in New York?",
            "What time is it in New York?",
            "Tell me about the weather and time in New York"
        ]
        
        success_count = 0
        
        for prompt in test_prompts:
            print(f"\n📝 Testing: {prompt}")
            try:
                response = await run_agent(prompt)
                print(f"   Response: {response[:200]}...")
                success_count += 1
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n✅ Main agent tests: {success_count}/{len(test_prompts)} passed")
        return success_count == len(test_prompts)
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 COMPREHENSIVE MULTI-AGENT SYSTEM TEST")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return
        
        # Test main agent
        print("\n🤖 Testing Main Agent...")
        main_agent_success = await self.test_main_agent()
        
        # Find test videos for transcription
        test_videos = self.find_test_videos()
        
        if test_videos:
            print(f"\n🎯 Running transcription tests with {len(test_videos)} video(s)...")
            
            for i, video_path in enumerate(test_videos, 1):
                print(f"\n📹 Testing video {i}/{len(test_videos)}: {video_path.name}")
                
                # Test transcription subagent
                transcription_success = await self.test_transcription_subagent(video_path)
                
                self.test_results.append({
                    'video': video_path.name,
                    'transcription_subagent': transcription_success
                })
                
                # Wait between tests to avoid rate limits
                if i < len(test_videos):
                    print("\n⏳ Waiting 3 seconds before next test...")
                    await asyncio.sleep(3)
        else:
            print("\n⚠️  No test videos found for transcription tests")
        
        # Print summary
        self.print_test_summary(main_agent_success)
    
    def print_test_summary(self, main_agent_success):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print(f"{'='*60}")
        
        print(f"\n🤖 Main Agent: {'✅ Passed' if main_agent_success else '❌ Failed'}")
        
        if self.test_results:
            print(f"\n📹 Transcription Tests:")
            for result in self.test_results:
                print(f"   {result['video']}: {'✅' if result['transcription_subagent'] else '❌'}")
        
        print(f"\n📁 Check output directory for result files")
        print(f"   - test_result_*.json (transcription results)")

async def quick_test():
    """Quick test with manual video path"""
    print("🎬 Quick Test Mode")
    print("=" * 40)
    
    test_runner = TestRunner()
    
    if not test_runner.check_prerequisites():
        return
    
    print("\nWhat would you like to test?")
    print("1. Main agent (weather/time)")
    print("2. Transcription subagent")
    print("3. Both")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice in ["1", "3"]:
        await test_runner.test_main_agent()
    
    if choice in ["2", "3"]:
        video_path = input("\nEnter video file path: ").strip().strip('"')
        if os.path.exists(video_path):
            await test_runner.test_transcription_subagent(Path(video_path))
        else:
            print("❌ Video file not found!")

def main():
    """Main entry point"""
    print("Choose test mode:")
    print("1. Comprehensive test (all components)")
    print("2. Quick test (interactive)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_runner = TestRunner()
        asyncio.run(test_runner.run_comprehensive_test())
    elif choice == "2":
        asyncio.run(quick_test())
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()

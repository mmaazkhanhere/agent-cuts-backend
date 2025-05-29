"""
Comprehensive test script for the transcription agent
This is the single test file you need to run everything
"""
import asyncio
import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent  # Go up one level to the root folder
sys.path.append(str(project_root))

# Import the transcription agent
from agents.transcription_agent import run_transcription_agent, transcribe_video_file

load_dotenv()


class TestRunner:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.test_results = []
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check API key
        if not self.groq_api_key:
            print("❌ GROQ_API_KEY not found in environment variables")
            print("   Please set GROQ_API_KEY in your .env file")
            return False
        else:
            print("✅ GROQ_API_KEY found")
        
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
        
        video_dir = "video/test.mp4"

        return [Path(video_dir)] if Path(video_dir).exists() else []
    
    async def test_direct_function(self, video_path: Path):
        """Test the transcription function directly"""
        print(f"\n{'='*60}")
        print(f"🧪 DIRECT FUNCTION TEST: {video_path.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            result = await transcribe_video_file(str(video_path))
            processing_time = time.time() - start_time
            
            if result['status'] == 'success':
                print(f"✅ Success in {processing_time:.2f} seconds")
                print(f"📊 Words: {result['metadata']['total_words']}")
                print(f"📈 Confidence: {result['metadata']['avg_confidence']:.3f}")
                print(f"🎯 Chunks: {result['metadata']['successful_chunks']}/{result['metadata']['total_chunks']}")
                print(f"📝 Preview: {result['full_text'][:150]}...")
                
                # Save result
                output_dir = "output"
                output_file = f"test_result_{video_path.stem}.json"
                with open(os.path.join(output_dir, output_file), 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"💾 Saved to: {output_dir}/{output_file}")
                
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    async def test_adk_agent(self, video_path: Path):
        """Test the ADK agent"""
        print(f"\n{'='*60}")
        print(f"🤖 ADK AGENT TEST: {video_path.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            response = await run_transcription_agent(str(video_path))
            processing_time = time.time() - start_time
            
            print(f"⏱️  Agent response time: {processing_time:.2f} seconds")
            print(f"📝 Agent response preview:")
            print(f"   {response[:200]}...")
            
            # Save agent response
            output_dir = "output"

            output_file = f"agent_response_{video_path.stem}.txt"
            with open(os.path.join(output_dir, output_file), 'w', encoding='utf-8') as f:
                f.write(response)
            print(f"💾 Agent response saved to: {output_dir}/{output_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Agent test failed: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 COMPREHENSIVE TRANSCRIPTION AGENT TEST")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return
        
        # Find test videos
        test_videos = self.find_test_videos()
        if not test_videos:
            print("\n⚠️  No test videos found!")
            print("📝 Please add a video file to test with and run again.")
            return
        
        print(f"\n🎯 Running tests with {len(test_videos)} video(s)...")
        
        # Test each video
        for i, video_path in enumerate(test_videos, 1):
            print(f"\n📹 Testing video {i}/{len(test_videos)}: {video_path.name}")
            
            # Test 1: Direct function
            direct_success = await self.test_direct_function(video_path)
            
            # Test 2: ADK agent 
            agent_success = await self.test_adk_agent(video_path)
            
            self.test_results.append({
                'video': video_path.name,
                'direct_function': direct_success,
                'adk_agent': agent_success
            })
            
            # Wait between tests to avoid rate limits
            if i < len(test_videos):
                print("\n⏳ Waiting 3 seconds before next test...")
                await asyncio.sleep(3)
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(self.test_results) * 2
        passed_tests = sum(
            (1 if result['direct_function'] else 0) + 
            (1 if result['adk_agent'] else 0)
            for result in self.test_results
        )
        
        print(f"Total tests run: {total_tests}")
        print(f"Tests passed: {passed_tests}")
        print(f"Tests failed: {total_tests - passed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\nDetailed results:")
        for result in self.test_results:
            print(f"  📹 {result['video']}:")
            print(f"    Direct function: {'✅' if result['direct_function'] else '❌'}")
            print(f"    ADK agent: {'✅' if result['adk_agent'] else '❌'}")
        
        print(f"\n📁 Check current directory for output files:")
        print(f"   - test_result_*.json (transcription results)")
        print(f"   - agent_response_*.txt (agent responses)")


async def quick_test_with_manual_path():
    """Quick test where user provides video path manually"""
    print("🎬 Quick Manual Test")
    print("=" * 40)
    
    video_path = "video/test.mp4"  # Default path, can be overridden by user input
    
    if not os.path.exists(video_path):
        print("❌ File not found!")
        return
    
    test_runner = TestRunner()
    
    if not test_runner.check_prerequisites():
        return
    
    video_path = Path(video_path)
    print(f"\n🚀 Testing with: {video_path.name}")
    
    # Test direct function
    success = await test_runner.test_direct_function(video_path)
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")


def main():
    """Main entry point"""
    print("Choose test mode:")
    print("1. Automatic test (searches for videos)")
    print("2. Manual test (you provide video path)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_runner = TestRunner()
        asyncio.run(test_runner.run_comprehensive_test())
    elif choice == "2":
        asyncio.run(quick_test_with_manual_path())
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()

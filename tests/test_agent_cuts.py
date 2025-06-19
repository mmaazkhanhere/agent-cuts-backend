"""
Test suite for agent_cuts implementation
Tests the ADK Sequential Agent pipeline
"""

import asyncio
import os
import sys
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_cuts_runner import process_video_with_agent_cuts


async def test_agent_cuts_direct():
    """Test agent_cuts processing directly (without API)"""
    print("\n🧪 Testing Agent Cuts Direct Processing")
    print("=" * 50)
    
    video_path = os.path.abspath("./video/test.mp4")
    
    if not os.path.exists(video_path):
        print(f"❌ Test video not found: {video_path}")
        return False
    
    print(f"Video: {video_path}")
    print(f"Size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    
    try:
        # Process video
        print("\nStarting agent_cuts processing...")
        result = await process_video_with_agent_cuts(
            video_path=video_path,
            output_dir="test_segments",
            user_id="test_user",
            session_id="test_session"
        )
        
        print(f"\nStatus: {result['status']}")
        
        if result['status'] == 'success':
            print(f"✅ Processing completed successfully!")
            print(f"   Output directory: {result['output_dir']}")
            print(f"   Segments created: {result['segment_count']}")
            print(f"   Session ID: {result['session_id']}")
            
            # Check processing state
            state = result.get('processing_state', {})
            print("\nProcessing State:")
            steps = ['transcription', 'segmentation', 'ranking', 'video_segments', 'copywriting']
            for step in steps:
                if state.get(step):
                    print(f"   ✅ {step}")
                else:
                    print(f"   ❌ {step}")
            
            # List segments
            if result['segment_paths']:
                print(f"\nGenerated Segments:")
                for i, path in enumerate(result['segment_paths']):
                    if os.path.exists(path):
                        size = os.path.getsize(path) / (1024*1024)
                        print(f"   {i+1}. {os.path.basename(path)} ({size:.2f} MB)")
            
            return True
            
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_response_format():
    """Test that agent responses are properly formatted"""
    print("\n🧪 Testing Agent Response Format")
    print("=" * 50)
    
    # This would test the response format from each sub-agent
    # For now, we'll check the expected structure
    expected_structure = {
        "transcription": ["transcript", "segments", "metadata"],
        "segmentation": ["segments", "topics"],
        "ranking": ["ranked_list", "scores"],
        "video_segments": ["segment_paths", "output_dir"],
        "copywriting": ["copies", "headlines"]
    }
    
    print("Expected response structure from sub-agents:")
    for agent, fields in expected_structure.items():
        print(f"\n{agent}:")
        for field in fields:
            print(f"  - {field}")
    
    return True



async def run_all_tests():
    """Run all agent_cuts tests"""
    print("\n" + "="*60)
    print("🚀 AGENT CUTS TEST SUITE")
    print("   Testing ADK Sequential Agent Implementation")
    print("="*60)
    
    # Check environment
    print("\nEnvironment Check:")
    groq_key = os.getenv("GROQ_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    print(f"  GROQ_API_KEY: {'✅ Set' if groq_key else '❌ Not set'}")
    print(f"  GOOGLE_API_KEY: {'✅ Set' if google_key else '❌ Not set'}")
    
    if not groq_key or not google_key:
        print("\n⚠️  Warning: Missing API keys. Tests may fail.")
    
    # Run tests
    tests = {
        "Direct Processing": await test_agent_cuts_direct()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in tests.values() if result)
    total = len(tests)
    
    for test_name, result in tests.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

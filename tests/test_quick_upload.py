"""
Quick test for video upload and processing
"""

import asyncio
import aiohttp
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def quick_upload_test():
    """Quick test of the upload endpoint"""
    
    video_path = "../video/test.mp4"
    base_url = "http://localhost:8000"
    
    print("🚀 Quick Upload Test")
    print("=" * 40)
    
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return
    
    async with aiohttp.ClientSession() as session:
        # 1. Check health
        print("\n1. Checking API health...")
        try:
            async with session.get(f"{base_url}/health") as resp:
                health = await resp.json()
                print(f"   Version: {health.get('version')}")
                print(f"   Agent: {health.get('agent')}")
                keys = health.get('api_keys', {})
                print(f"   GROQ API: {'✅' if keys.get('groq_configured') else '❌'}")
                print(f"   Google API: {'✅' if keys.get('google_configured') else '❌'}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            print("   Is the server running?")
            return
        
        # 2. Upload video
        print("\n2. Uploading video...")
        try:
            with open(video_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='test.mp4', content_type='video/mp4')
                
                async with session.post(f"{base_url}/upload-video", data=data) as resp:
                    result = await resp.json()
                    
                    if result.get('status') == 'success':
                        phrase = result['unique_phrase']
                        print(f"   ✅ Upload successful!")
                        print(f"   📝 Unique phrase: {phrase}")
                        print(f"   💾 Filename: {result['filename']}")
                        
                        # 3. Quick progress check
                        print("\n3. Checking progress...")
                        for i in range(3):
                            await asyncio.sleep(2)
                            
                            async with session.get(f"{base_url}/progress/{phrase}") as resp:
                                progress = await resp.json()
                                status = progress['status']
                                pct = progress['progress']['percentage']
                                step = progress['progress']['current_step']
                                
                                print(f"   {i+1}. Status: {status} | Progress: {pct}% | Step: {step}")
                                
                                if status in ['completed', 'failed']:
                                    break
                        
                        print(f"\n📋 Session URL: {base_url}/progress/{phrase}")
                        print(f"📊 Segments URL: {base_url}/segments/{phrase}")
                        
                    else:
                        print(f"   ❌ Upload failed: {result}")
                        
        except Exception as e:
            print(f"   ❌ Upload error: {e}")


if __name__ == "__main__":
    asyncio.run(quick_upload_test())

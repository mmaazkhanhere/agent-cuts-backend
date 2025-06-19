import asyncio
import aiohttp
import os
import time
import json
from datetime import datetime

class VideoProcessingTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.unique_phrase = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def test_upload_video(self, video_path="video/test.mp4"):
        """Test 1: Upload video"""
        print("\n🧪 TEST 1: Upload Video")
        print("=" * 50)
        
        # Convert to absolute path
        if not os.path.isabs(video_path):
            video_path = os.path.abspath(video_path)
            
        print(f"📂 Checking video file: {video_path}")
        
        if not os.path.exists(video_path):
            print(f"❌ Error: Video file not found: {video_path}")
            print(f"   Current directory: {os.getcwd()}")
            return False
            
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        print(f"   File size: {file_size:.2f} MB")
            
        try:
            with open(video_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=os.path.basename(video_path), 
                             content_type='video/mp4')
                print(f"📂 Uploading video: {os.path.basename(video_path)}")
                
                print(f"   Sending POST to: {self.base_url}/upload-video")
                
                async with self.session.post(f"{self.base_url}/upload-video", data=data) as response:
                    print(f"   Response status: {response.status}")
                    
                    result = await response.json()
                    
                    if response.status == 200 and result.get('status') == 'success':
                        self.unique_phrase = result['unique_phrase']
                        print(f"✅ Upload successful!")
                        print(f"   - Unique phrase: {self.unique_phrase}")
                        print(f"   - Filename: {result['filename']}")
                        return True
                    else:
                        print(f"❌ Upload failed:")
                        print(f"   - Response: {json.dumps(result, indent=2)}")
                        return False
                        
        except aiohttp.ClientError as e:
            print(f"❌ Client error: {type(e).__name__}: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Exception during upload: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_progress_tracking(self):
        """Test 2: Progress tracking"""
        print("\n🧪 TEST 2: Progress Tracking")
        print("=" * 50)
        
        if not self.unique_phrase:
            print("❌ No unique phrase available. Upload test must succeed first.")
            return False
            
        try:
            previous_percentage = -1
            steps_seen = set()
            start_time = time.time()
            
            while True:
                async with self.session.get(f"{self.base_url}/progress/{self.unique_phrase}") as response:
                    if response.status != 200:
                        print(f"❌ Progress endpoint returned status {response.status}")
                        return False
                        
                    progress_data = await response.json()
                    
                    status = progress_data['status']
                    progress = progress_data['progress']
                    current_step = progress['current_step']
                    percentage = progress['percentage']
                    
                    # Track new steps
                    if current_step not in steps_seen:
                        steps_seen.add(current_step)
                        print(f"\n📍 New step: {current_step}")
                    
                    # Update progress bar
                    if percentage != previous_percentage:
                        bar_length = 30
                        filled = int(bar_length * percentage / 100)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        print(f"\r   [{bar}] {percentage}% - {current_step}", end='')
                        previous_percentage = percentage
                    
                    if status == 'completed':
                        elapsed = time.time() - start_time
                        print(f"\n✅ Processing completed in {elapsed:.1f} seconds!")
                        print(f"   - Steps completed: {', '.join(progress['steps_completed'])}")
                        print(f"   - Segments created: {progress_data['segment_count']}")
                        return True
                        
                    elif status == 'failed':
                        print(f"\n❌ Processing failed: {progress_data['error']}")
                        return False
                    
                    # Timeout after 5 minutes
                    if time.time() - start_time > 300:
                        print("\n❌ Timeout: Processing took too long")
                        return False
                
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"\n❌ Exception during progress tracking: {str(e)}")
            return False
    
    async def test_segments_info(self):
        """Test 3: Get segments information"""
        print("\n🧪 TEST 3: Segments Information")
        print("=" * 50)
        
        if not self.unique_phrase:
            print("❌ No unique phrase available")
            return False
            
        try:
            async with self.session.get(f"{self.base_url}/segments/{self.unique_phrase}") as response:
                if response.status != 200:
                    print(f"❌ Segments endpoint returned status {response.status}")
                    return False
                    
                segments_data = await response.json()
                
                print(f"✅ Retrieved segments information:")
                print(f"   - Total segments: {segments_data['total_segments']}")
                print(f"   - Status: {segments_data['status']}")
                
                if segments_data['total_segments'] > 0:
                    print("\n   Segments:")
                    total_size = 0
                    for i, segment in enumerate(segments_data['segments']):
                        print(f"   {i+1}. {segment['filename']}")
                        print(f"      - Size: {segment['size_mb']} MB")
                        print(f"      - Download URL: {segment['download_url']}")
                        total_size += segment['size_mb']
                    
                    print(f"\n   Total size: {total_size:.2f} MB")
                    return True
                else:
                    print("❌ No segments found")
                    return False
                    
        except Exception as e:
            print(f"❌ Exception getting segments info: {str(e)}")
            return False
    
    async def test_download_segment(self, segment_index=0):
        """Test 4: Download a segment"""
        print("\n🧪 TEST 4: Download Segment")
        print("=" * 50)
        
        if not self.unique_phrase:
            print("❌ No unique phrase available")
            return False
            
        try:
            download_url = f"{self.base_url}/download-segment/{self.unique_phrase}/{segment_index}"
            
            async with self.session.get(download_url) as response:
                if response.status != 200:
                    print(f"❌ Download endpoint returned status {response.status}")
                    return False
                
                # Get filename from headers
                content_disposition = response.headers.get('content-disposition', '')
                filename = content_disposition.split('filename=')[-1].strip('"') if 'filename=' in content_disposition else f"segment_{segment_index}.mp4"
                
                # Save to test_downloads directory
                os.makedirs("test_downloads", exist_ok=True)
                download_path = f"test_downloads/{self.unique_phrase}_{filename}"
                
                content = await response.read()
                with open(download_path, 'wb') as f:
                    f.write(content)
                
                file_size = len(content) / (1024 * 1024)  # MB
                print(f"✅ Successfully downloaded segment {segment_index}:")
                print(f"   - Filename: {filename}")
                print(f"   - Size: {file_size:.2f} MB")
                print(f"   - Saved to: {download_path}")
                return True
                
        except Exception as e:
            print(f"❌ Exception downloading segment: {str(e)}")
            return False
    
    async def test_list_sessions(self):
        """Test 5: List all sessions"""
        print("\n🧪 TEST 5: List Sessions")
        print("=" * 50)
        
        try:
            async with self.session.get(f"{self.base_url}/sessions") as response:
                if response.status != 200:
                    print(f"❌ Sessions endpoint returned status {response.status}")
                    return False
                    
                sessions_data = await response.json()
                
                print(f"✅ Retrieved sessions list:")
                print(f"   - Total sessions: {sessions_data['total_sessions']}")
                
                if sessions_data['total_sessions'] > 0:
                    print("\n   Recent sessions:")
                    for i, session in enumerate(sessions_data['sessions'][:5]):  # Show last 5
                        print(f"   {i+1}. {session['unique_phrase']}")
                        print(f"      - Status: {session['status']}")
                        print(f"      - Created: {session['created_at']}")
                        print(f"      - Segments: {session['segment_count']}")
                
                return True
                
        except Exception as e:
            print(f"❌ Exception listing sessions: {str(e)}")
            return False
    
    async def test_invalid_session(self):
        """Test 6: Test invalid session handling"""
        print("\n🧪 TEST 6: Invalid Session Handling")
        print("=" * 50)
        
        fake_phrase = "invalid-phrase-9999"
        
        try:
            # Test progress endpoint
            async with self.session.get(f"{self.base_url}/progress/{fake_phrase}") as response:
                if response.status == 404:
                    print("✅ Progress endpoint correctly returned 404 for invalid session")
                else:
                    print(f"❌ Progress endpoint returned unexpected status: {response.status}")
                    return False
            
            # Test segments endpoint
            async with self.session.get(f"{self.base_url}/segments/{fake_phrase}") as response:
                if response.status == 404:
                    print("✅ Segments endpoint correctly returned 404 for invalid session")
                else:
                    print(f"❌ Segments endpoint returned unexpected status: {response.status}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Exception testing invalid session: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*60)
        print("🚀 STARTING COMPREHENSIVE VIDEO PROCESSING TESTS")
        print("="*60)
        print(f"Server: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            "Upload Video": await self.test_upload_video(),
            "Progress Tracking": await self.test_progress_tracking(),
            "Segments Info": await self.test_segments_info(),
            "Download Segment": await self.test_download_segment(),
            "List Sessions": await self.test_list_sessions(),
            "Invalid Session": await self.test_invalid_session()
        }
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<20} {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
        
        if self.unique_phrase:
            print(f"\n💡 Your unique phrase for this session: {self.unique_phrase}")
            print(f"   You can use this to check progress or download segments later.")
        
        return passed == total


async def main():
    """Main test runner"""
    try:
        async with VideoProcessingTester() as tester:
            success = await tester.run_all_tests()
            
            if success:
                print("\n🎉 All tests passed successfully!")
            else:
                print("\n⚠️  Some tests failed. Check the output above for details.")
                
    except aiohttp.ClientError as e:
        print(f"\n❌ Connection Error: {str(e)}")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())

# Agent Cuts Backend API Documentation

## Overview
ClipGenius Transcription API v2.0 - A video processing pipeline that automatically transcribes, segments, ranks, and cuts videos into meaningful clips.

## Base URL
```
http://localhost:8000
```

## API Endpoints

### 1. Health & Status Endpoints

#### GET `/`
Returns basic API information.

**Response:**
```json
{
  "message": "ClipGenius Transcription API v2.0",
  "features": [
    "Video transcription with sentence-level timestamps",
    "Intelligent audio chunking",
    "Parallel processing",
    "Multiple output formats"
  ]
}
```

#### GET `/health`
Detailed health check with API status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0",
  "api_keys": {
    "groq_configured": true,
    "google_configured": true
  },
  "endpoints": {...}
}
```

#### GET `/formats`
Get supported file formats and output options.

**Response:**
```json
{
  "input_formats": [".mp4", ".avi", ".mov", ".mkv", ".webm", ".mp3", ".wav", ".m4a"],
  "output_features": {
    "chunk_segments": "Original audio chunks with timestamps",
    "sentence_segments": "Individual sentences with precise timing",
    "full_text": "Complete transcription text",
    "metadata": "Processing statistics and quality metrics"
  }
}
```

### 2. Video Processing Endpoints

#### POST `/upload-video`
Upload a video file and start asynchronous processing.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Video file (form field name: `file`)

**Supported formats:** `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`

**Response:**
```json
{
  "status": "success",
  "unique_phrase": "happy-tiger-1234",
  "message": "Video uploaded successfully. Processing started.",
  "filename": "video.mp4"
}
```

**Error Response:**
```json
{
  "detail": "Unsupported file type: .txt"
}
```

#### GET `/progress/{unique_phrase}`
Check processing progress for a specific video.

**Parameters:**
- `unique_phrase`: The unique identifier returned from upload

**Response:**
```json
{
  "status": "processing",
  "progress": {
    "current_step": "segmentation",
    "steps_completed": ["upload", "transcription"],
    "percentage": 45
  },
  "segment_count": 0,
  "error": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:31:30"
}
```

**Status values:**
- `uploaded`: File uploaded, processing not started
- `processing`: Currently processing
- `completed`: Successfully completed
- `failed`: Processing failed (check `error` field)

#### GET `/segments/{unique_phrase}`
Get information about all video segments for a completed processing job.

**Parameters:**
- `unique_phrase`: The unique identifier

**Response:**
```json
{
  "unique_phrase": "happy-tiger-1234",
  "status": "completed",
  "total_segments": 5,
  "segments": [
    {
      "index": 0,
      "filename": "seg_01_Introduction.mp4",
      "size_mb": 12.5,
      "download_url": "/download-segment/happy-tiger-1234/0"
    },
    ...
  ]
}
```

#### GET `/download-segment/{unique_phrase}/{segment_index}`
Download a specific video segment.

**Parameters:**
- `unique_phrase`: The unique identifier
- `segment_index`: Zero-based index of the segment

**Response:**
- Content-Type: `video/mp4`
- Returns the video file as a download

#### GET `/sessions`
List all processing sessions.

**Response:**
```json
{
  "total_sessions": 15,
  "sessions": [
    {
      "unique_phrase": "happy-tiger-1234",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00",
      "segment_count": 5
    },
    ...
  ]
}
```

### 3. Direct Processing Endpoints (Synchronous)

#### POST `/process-video`
Process a video through the complete pipeline synchronously.
⚠️ **Note:** This is a blocking operation and may timeout for long videos. Use `/upload-video` for production.

**Request:**
```json
{
  "video_path": "/absolute/path/to/video.mp4"
}
```

**Response:**
```json
{
  "status": "success",
  "video_path": "/path/to/video.mp4",
  "segment_paths": [
    "segments/seg_01_topic.mp4",
    ...
  ],
  "segment_count": 5,
  "processing_details": {
    "transcription": "success",
    "segmentation": "success",
    "ranking": "success",
    "video_segmentation": {"status": "success"}
  }
}
```

#### POST `/transcribe`
Transcribe a video file (direct endpoint).

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Video file (form field name: `file`)

**Response:**
```json
{
  "status": "success",
  "data": {
    "status": "success",
    "transcript": "Full transcription text...",
    "segments": [...],
    "metadata": {
      "duration": 300.5,
      "segment_count": 73,
      "confidence": 0.95
    }
  }
}
```

### 4. Individual Agent Endpoints (Testing/Debug)

#### GET `/segmentation`
Test segmentation agent with pre-loaded transcript.

#### GET `/ranking`
Test ranking agent with pre-loaded segments.

#### GET `/video_segment`
Test video segmentation with pre-loaded ranking data.

## Processing Pipeline

The video processing pipeline consists of four stages:

1. **Transcription** (10-30% progress)
   - Extracts audio from video
   - Chunks audio for processing
   - Transcribes using Groq API
   - Creates sentence-level timestamps

2. **Segmentation** (40-60% progress)
   - Analyzes transcript for topic boundaries
   - Groups related content
   - Identifies natural break points

3. **Ranking** (70-85% progress)
   - Scores segments for quality
   - Evaluates engagement potential
   - Prioritizes based on clarity and relevance

4. **Video Segmentation** (90-100% progress)
   - Cuts original video based on timestamps
   - Creates individual video files
   - Adds audio tracks
   - Saves to unique folder

## File Organization

```
agent-cuts-backend/
├── uploads/
│   └── {unique-phrase}/
│       └── uploaded-video.mp4
├── segments/
│   └── {unique-phrase}/
│       ├── seg_01_topic_name.mp4
│       ├── seg_02_topic_name.mp4
│       └── ...
└── sessions.json (processing status database)
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid input)
- `404`: Resource not found
- `422`: Validation error
- `500`: Internal server error

Error responses include a `detail` field with specific error information.

## Environment Variables

Required environment variables:
- `GROQ_API_KEY`: API key for Groq transcription service
- `GOOGLE_API_KEY`: API key for Google AI agents

## Usage Examples

### Upload and Process Video
```bash
# Upload video
curl -X POST -F "file=@video.mp4" http://localhost:8000/upload-video

# Response: {"unique_phrase": "happy-tiger-1234", ...}

# Check progress
curl http://localhost:8000/progress/happy-tiger-1234

# Get segments when complete
curl http://localhost:8000/segments/happy-tiger-1234

# Download a segment
curl -O http://localhost:8000/download-segment/happy-tiger-1234/0
```

### Python Example
```python
import aiohttp
import asyncio

async def process_video():
    async with aiohttp.ClientSession() as session:
        # Upload
        with open('video.mp4', 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename='video.mp4')
            
            async with session.post('http://localhost:8000/upload-video', data=data) as resp:
                result = await resp.json()
                unique_phrase = result['unique_phrase']
        
        # Track progress
        while True:
            async with session.get(f'http://localhost:8000/progress/{unique_phrase}') as resp:
                progress = await resp.json()
                print(f"Status: {progress['status']} - {progress['progress']['percentage']}%")
                
                if progress['status'] in ['completed', 'failed']:
                    break
            
            await asyncio.sleep(2)

asyncio.run(process_video())
```

## Notes

- Processing time depends on video length and server resources
- Large videos may take several minutes to process
- Segments are stored permanently unless manually deleted
- The unique phrase serves as both identifier and folder name
- All paths in responses are relative to the server root

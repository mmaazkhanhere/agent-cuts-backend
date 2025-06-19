# Tests Directory

This directory contains test files for the Agent Cuts Backend API.

## Test Files

### 1. `test_comprehensive.py`
Comprehensive test suite that tests all API endpoints:
- Upload video
- Progress tracking with visual progress bar
- Segment information retrieval
- Segment downloading
- Session listing
- Error handling

Run with:
```bash
cd tests
python test_comprehensive.py
```

### 2. `test_agent_cuts.py`
Tests the agent_cuts implementation directly:
- Direct processing without API
- Response format validation
- Error handling
- Sub-agent integration

Run with:
```bash
cd tests
python test_agent_cuts.py
```

### 3. `test_quick_upload.py`
Quick test for video upload and basic progress tracking:
- API health check
- Video upload
- Initial progress monitoring

Run with:
```bash
cd tests
python test_quick_upload.py
```

## Prerequisites

1. **Start the server** in the parent directory:
   ```bash
   python main.py
   ```

2. **Environment variables** must be set:
   - `GROQ_API_KEY`: For transcription
   - `GOOGLE_API_KEY`: For ADK agents

3. **Test video** should exist at `../video/test.mp4`

## Expected Flow

1. Video is uploaded and assigned a unique phrase (e.g., "happy-tiger-1234")
2. Processing goes through 5 stages:
   - Initializing (5%)
   - Transcribing (20%)
   - Segmenting (40%)
   - Ranking (60%)
   - Cutting video (80%)
   - Generating copy (95%)
   - Completed (100%)
3. Segments are saved to `segments/{unique-phrase}/`
4. Each segment can be downloaded individually

## Troubleshooting

- **"Server not running"**: Start the FastAPI server with `python main.py`
- **"API keys not configured"**: Set environment variables
- **"Video not found"**: Ensure test video exists at `video/test.mp4`
- **Processing stuck**: Check server logs for errors

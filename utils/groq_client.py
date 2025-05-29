"""
Clean Groq client for transcription
"""
import asyncio
import aiofiles
from groq import Groq
from typing import NamedTuple, Optional, Dict, Any
from asyncio_throttle import Throttler
import io


class TranscriptionResult(NamedTuple):
    chunk_id: int
    text: str
    start_time: float
    end_time: float
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class GroqTranscriptionClient:
    def __init__(self, api_key: str, max_requests_per_minute: int = 25):
        self.client = Groq(api_key=api_key)
        self.throttler = Throttler(rate_limit=max_requests_per_minute, period=60)
        
    async def transcribe_audio_file(self, audio_file_path: str, chunk_id: int, 
                                  start_time: float, end_time: float) -> TranscriptionResult:
        """Transcribe audio file using Groq Whisper"""
        try:
            async with self.throttler:
                # Read audio file
                async with aiofiles.open(audio_file_path, 'rb') as audio_file:
                    audio_data = await audio_file.read()
                
                # Create buffer for Groq
                audio_buffer = io.BytesIO(audio_data)
                audio_buffer.name = audio_file_path
                
                # Call Groq API with word timestamps
                transcription = self.client.audio.transcriptions.create(
                    file=audio_buffer,
                    model="whisper-large-v3",
                    response_format="verbose_json",
                    temperature=0.0,
                    timestamp_granularities=["word"]
                )
                
                text = transcription.text.strip()
                confidence = getattr(transcription, 'confidence', 0.8)
                
                # Extract word-level timestamps if available
                words = getattr(transcription, 'words', [])
                
                metadata = {
                    'language': getattr(transcription, 'language', 'unknown'),
                    'duration': end_time - start_time,
                    'words': words
                }
                
                return TranscriptionResult(
                    chunk_id=chunk_id,
                    text=text,
                    start_time=start_time,
                    end_time=end_time,
                    confidence=confidence,
                    metadata=metadata
                )
                
        except Exception as e:
            return TranscriptionResult(
                chunk_id=chunk_id,
                text=f"[ERROR: {str(e)}]",
                start_time=start_time,
                end_time=end_time,
                confidence=0.0,
                metadata={'error': str(e)}
            )

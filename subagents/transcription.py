"""Transcription subagent - non-LLM based agent for video transcription"""
import os
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import utilities
from utils.audio_processing import AudioProcessor, AudioChunk
from utils.groq_client import GroqTranscriptionClient, TranscriptionResult
from utils.sentence_processor import create_sentence_level_transcription

load_dotenv()

class TranscriptionSubAgent:
    """Non-LLM based subagent for transcription tasks"""
    
    def __init__(self, groq_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required")
        
        self.audio_processor = AudioProcessor()
        self.groq_client = GroqTranscriptionClient(self.groq_api_key)
    
    async def transcribe_video(self, video_path: str, sentence_level: bool = True) -> Dict[str, Any]:
        """Transcribe a video file"""
        try:
            print(f"Starting transcription of: {video_path}")
            
            # Step 1: Extract audio
            print("Extracting audio...")
            audio_path = self.audio_processor.extract_audio_from_video(video_path)
            
            # Step 2: Chunk audio
            print("Chunking audio...")
            chunks = self.audio_processor.chunk_audio_intelligently(audio_path)
            print(f"Created {len(chunks)} chunks")
            
            # Step 3: Transcribe chunks in parallel
            print("Starting transcription...")
            tasks = []
            for chunk in chunks:
                task = self.groq_client.transcribe_audio_file(
                    chunk.file_path, chunk.chunk_id, chunk.start_time, chunk.end_time
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Step 4: Aggregate results
            transcription_output = self._aggregate_results(results)
            
            # Step 5: Create sentence-level breakdown if requested
            if sentence_level:
                print("Creating sentence-level timestamps...")
                transcription_output = create_sentence_level_transcription(transcription_output)
            
            # Step 6: Cleanup
            temp_files = [audio_path] + [chunk.file_path for chunk in chunks]
            self.audio_processor.cleanup_temp_files(temp_files)
            
            print("Transcription completed!")
            return transcription_output
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Transcription failed: {str(e)}",
                "full_text": "",
                "segments": []
            }
    
    def _aggregate_results(self, results: List[TranscriptionResult]) -> Dict[str, Any]:
        """Aggregate transcription results"""
        valid_results = [r for r in results if isinstance(r, TranscriptionResult) and not r.text.startswith("[ERROR")]
        valid_results.sort(key=lambda x: x.chunk_id)
        
        # Combine text
        full_text = " ".join([r.text for r in valid_results])
        
        # Create segments
        segments = []
        for result in valid_results:
            segments.append({
                "chunk_id": result.chunk_id,
                "text": result.text,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "confidence": result.confidence
            })
        
        # Calculate metrics
        avg_confidence = sum([r.confidence for r in valid_results]) / len(valid_results) if valid_results else 0.0
        
        return {
            "status": "success",
            "full_text": full_text,
            "segments": segments,
            "metadata": {
                "total_chunks": len(results),
                "successful_chunks": len(valid_results),
                "avg_confidence": avg_confidence,
                "total_words": len(full_text.split()) if full_text else 0
            }
        }

"""
Core transcription engine - the main logic for processing videos
"""
import os
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

from .groq_client import GroqTranscriptionClient
from .audio_processing import AudioProcessor
from .sentence_processor import create_sentence_level_transcription

load_dotenv()


class TranscriptionEngine:
    """Main transcription processing engine"""
    
    def __init__(self, groq_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required")
        
        self.audio_processor = AudioProcessor()
        self.groq_client = GroqTranscriptionClient(self.groq_api_key)
    
    async def transcribe_video(self, video_path: str, 
                             sentence_level: bool = True) -> Dict[str, Any]:
        """Main transcription method"""
        try:
            print(f"[*] Starting transcription: {os.path.basename(video_path)}")
            
            # Step 1: Extract audio
            audio_path = self.audio_processor.extract_audio_from_video(video_path)
            
            # Step 2: Chunk audio
            chunks = self.audio_processor.chunk_audio_intelligently(audio_path)
            print(f"Created {len(chunks)} chunks")
            
            # Step 3: Transcribe chunks in parallel
            tasks = []
            for chunk in chunks:
                task = self.groq_client.transcribe_audio_file(
                    chunk.file_path, chunk.chunk_id, chunk.start_time, chunk.end_time
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Step 4: Process results
            transcription_result = self._process_results(results)
            
            # Step 5: Add sentence-level processing if requested
            if sentence_level:
                print("[*] Creating sentence-level timestamps...")
                transcription_result = create_sentence_level_transcription(transcription_result)
            
            # Step 6: Cleanup
            temp_files = [audio_path] + [chunk.file_path for chunk in chunks]
            self.audio_processor.cleanup_temp_files(temp_files)
            return transcription_result
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Transcription failed: {str(e)}",
                "full_text": "",
                "segments": []
            }
    
    def _process_results(self, results) -> Dict[str, Any]:
        """Process transcription results"""
        valid_results = [r for r in results if hasattr(r, 'chunk_id') and not r.text.startswith("[ERROR")]
        valid_results.sort(key=lambda x: x.chunk_id)
        
        if not valid_results:
            return {
                "status": "error",
                "error": "No valid transcription results",
                "full_text": "",
                "segments": []
            }
        
        # Create segments
        segments = []
        for result in valid_results:
            segments.append({
                "chunk_id": result.chunk_id,
                "text": result.text,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "confidence": result.confidence,
                "metadata": result.metadata
            })
        
        # Combine text
        full_text = " ".join([r.text for r in valid_results])
        
        return {
            "status": "success",
            "full_text": full_text,
            "segments": segments,
            "metadata": {
                "total_chunks": len(results),
                "successful_chunks": len(valid_results),
                "avg_confidence": sum([r.confidence for r in valid_results]) / len(valid_results) if valid_results else 0.0,
                "total_words": len(full_text.split()) if full_text else 0
            }
        }

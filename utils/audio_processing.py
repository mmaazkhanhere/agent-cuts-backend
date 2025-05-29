"""
Clean, working audio processing utilities for transcription
"""
import os
import tempfile
import ffmpeg
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from typing import List, NamedTuple, Optional
from pathlib import Path


class AudioChunk(NamedTuple):
    chunk_id: int
    start_time: float
    end_time: float
    file_path: str
    duration: float


class AudioProcessor:
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
    def extract_audio_from_video(self, video_path: str) -> str:
        """Extract audio from video file"""
        try:
            output_path = os.path.join(
                self.temp_dir, 
                f"extracted_audio_{os.path.basename(video_path)}.wav"
            )
            
            stream = ffmpeg.input(video_path)
            audio = stream.audio
            out = ffmpeg.output(
                audio, 
                output_path,
                acodec='pcm_s16le',
                ac=1,  # Mono
                ar='16000'  # 16kHz for Whisper
            )
            ffmpeg.run(out, overwrite_output=True, quiet=True)
            
            return output_path
        except Exception as e:
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    def chunk_audio_intelligently(self, audio_path: str, 
                                target_chunk_duration: int = 300000) -> List[AudioChunk]:
        """Chunk audio at natural pause points"""
        try:
            audio = AudioSegment.from_file(audio_path)
            total_duration = len(audio)
            
            if total_duration <= target_chunk_duration:
                chunk_path = self._save_audio_chunk(audio, 0, audio_path)
                return [AudioChunk(0, 0.0, total_duration/1000.0, chunk_path, total_duration/1000.0)]
            
            # Detect silence points
            silence_points = self._detect_silence_points(audio)
            
            chunks = []
            chunk_start = 0
            chunk_id = 0
            
            while chunk_start < total_duration:
                ideal_end = min(chunk_start + target_chunk_duration, total_duration)
                
                # Find best split point
                best_split_point = self._find_best_split_point(
                    silence_points, chunk_start, ideal_end, total_duration
                )
                
                chunk_audio = audio[chunk_start:best_split_point]
                chunk_path = self._save_audio_chunk(chunk_audio, chunk_id, audio_path)
                
                chunks.append(AudioChunk(
                    chunk_id=chunk_id,
                    start_time=chunk_start / 1000.0,
                    end_time=best_split_point / 1000.0,
                    file_path=chunk_path,
                    duration=(best_split_point - chunk_start) / 1000.0
                ))
                
                chunk_start = best_split_point
                chunk_id += 1
            
            return chunks
            
        except Exception as e:
            raise Exception(f"Audio chunking failed: {str(e)}")
    
    def _detect_silence_points(self, audio: AudioSegment) -> List[tuple]:
        """Detect silence points for chunking"""
        try:
            nonsilent_ranges = detect_nonsilent(
                audio,
                min_silence_len=1000,
                silence_thresh=-40
            )
            
            silence_ranges = []
            for i in range(len(nonsilent_ranges) - 1):
                silence_start = nonsilent_ranges[i][1]
                silence_end = nonsilent_ranges[i + 1][0]
                if silence_end > silence_start:
                    silence_ranges.append((silence_start, silence_end))
            
            return silence_ranges
        except Exception:
            return []
    
    def _find_best_split_point(self, silence_points: List[tuple], 
                             chunk_start: int, ideal_end: int, total_duration: int) -> int:
        """Find best silence point to split"""
        search_window = 30000  # 30 seconds
        
        best_point = ideal_end
        min_distance = float('inf')
        
        for silence_start, silence_end in silence_points:
            silence_mid = (silence_start + silence_end) // 2
            
            if (abs(silence_mid - ideal_end) < search_window and 
                silence_mid > chunk_start):
                distance = abs(silence_mid - ideal_end)
                if distance < min_distance:
                    min_distance = distance
                    best_point = silence_mid
        
        return min(best_point, total_duration)
    
    def _save_audio_chunk(self, chunk_audio: AudioSegment, chunk_id: int, 
                         original_path: str) -> str:
        """Save audio chunk to temp file"""
        base_name = Path(original_path).stem
        chunk_path = os.path.join(
            self.temp_dir, 
            f"{base_name}_chunk_{chunk_id:03d}.wav"
        )
        chunk_audio.export(chunk_path, format="wav")
        return chunk_path
    
    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Warning: Failed to delete {file_path}: {e}")

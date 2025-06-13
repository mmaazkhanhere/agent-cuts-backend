"""
Transcription Agent Package
Main interface for the transcription functionality
"""

from .core.engine import TranscriptionEngine
from .utils.audio_processing import AudioProcessor, AudioChunk
from .utils.groq_client import GroqTranscriptionClient, TranscriptionResult
from .utils.sentence_processor import SentenceProcessor, create_sentence_level_transcription
from .utils.output_formatter import create_simplified_transcript, format_for_segmentation

# Try to import ADK components if available
try:
    from .core.adk_agent import run_transcription_agent, transcribe_video_tool
    _adk_available = True
except ImportError:
    _adk_available = False
    run_transcription_agent = None
    transcribe_video_tool = None

__all__ = [
    'TranscriptionEngine',
    'AudioProcessor',
    'AudioChunk',
    'GroqTranscriptionClient',
    'TranscriptionResult',
    'SentenceProcessor',
    'create_sentence_level_transcription',
    'create_simplified_transcript',
    'format_for_segmentation'
]

if _adk_available:
    __all__.extend(['run_transcription_agent', 'transcribe_video_tool'])

# Convenience function for direct transcription
async def transcribe_video(video_path: str, groq_api_key: str = None, 
                          sentence_level: bool = True):
    """
    Convenience function for direct video transcription
    
    Args:
        video_path: Path to the video file
        groq_api_key: Groq API key (optional, will use env var if not provided)
        sentence_level: Whether to include sentence-level timestamps
    
    Returns:
        Dict with transcription results
    """
    engine = TranscriptionEngine(groq_api_key)
    return await engine.transcribe_video(video_path, sentence_level)

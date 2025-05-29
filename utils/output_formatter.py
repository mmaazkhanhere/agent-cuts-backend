"""
Enhanced output formatting utilities for transcription results
Supports multiple output formats: JSON, SRT, VTT, TXT with speaker diarization
"""
import json
from typing import List, Dict, Any, Optional
from datetime import timedelta


class TranscriptionFormatter:
    """Handles formatting transcription results into various output formats"""
    
    @staticmethod
    def format_timestamp(seconds: float, format_type: str = "srt") -> str:
        """Format timestamp for different subtitle formats"""
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = td.total_seconds() % 60
        
        if format_type == "srt":
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")
        elif format_type == "vtt":
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        else:
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    @staticmethod
    def to_srt(segments: List[Dict[str, Any]], include_speakers: bool = True) -> str:
        """Convert transcription segments to SRT format"""
        srt_content = []
        
        for i, segment in enumerate(segments, 1):
            start_time = TranscriptionFormatter.format_timestamp(segment['start_time'], "srt")
            end_time = TranscriptionFormatter.format_timestamp(segment['end_time'], "srt")
            
            text = segment['text'].strip()
            if include_speakers and 'speaker' in segment:
                text = f"[{segment['speaker']}] {text}"
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")  # Empty line between subtitles
        
        return "\n".join(srt_content)
    
    @staticmethod
    def to_vtt(segments: List[Dict[str, Any]], include_speakers: bool = True) -> str:
        """Convert transcription segments to WebVTT format"""
        vtt_content = ["WEBVTT", ""]
        
        for segment in segments:
            start_time = TranscriptionFormatter.format_timestamp(segment['start_time'], "vtt")
            end_time = TranscriptionFormatter.format_timestamp(segment['end_time'], "vtt")
            
            text = segment['text'].strip()
            if include_speakers and 'speaker' in segment:
                text = f"<v {segment['speaker']}>{text}"
            
            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(text)
            vtt_content.append("")
        
        return "\n".join(vtt_content)
    
    @staticmethod
    def to_json(transcription_result: Dict[str, Any], pretty: bool = True) -> str:
        """Convert transcription result to formatted JSON"""
        if pretty:
            return json.dumps(transcription_result, indent=2, ensure_ascii=False)
        return json.dumps(transcription_result, ensure_ascii=False)
    
    @staticmethod
    def to_text(segments: List[Dict[str, Any]], include_timestamps: bool = False, 
                include_speakers: bool = True) -> str:
        """Convert transcription segments to plain text"""
        text_content = []
        
        for segment in segments:
            text = segment['text'].strip()
            
            if include_speakers and 'speaker' in segment:
                speaker_label = f"[{segment['speaker']}] "
            else:
                speaker_label = ""
            
            if include_timestamps:
                start_time = TranscriptionFormatter.format_timestamp(segment['start_time'])
                timestamp_label = f"[{start_time}] "
            else:
                timestamp_label = ""
            
            text_content.append(f"{timestamp_label}{speaker_label}{text}")
        
        return "\n".join(text_content)
    
    @staticmethod
    def to_paragraphs(segments: List[Dict[str, Any]], min_pause_duration: float = 2.0) -> str:
        """Convert segments to paragraph format based on pauses"""
        if not segments:
            return ""
        
        paragraphs = []
        current_paragraph = []
        last_end_time = 0
        
        for segment in segments:
            # Check if there's a significant pause
            pause_duration = segment['start_time'] - last_end_time
            
            if pause_duration > min_pause_duration and current_paragraph:
                # End current paragraph
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []
            
            current_paragraph.append(segment['text'].strip())
            last_end_time = segment['end_time']
        
        # Add the last paragraph
        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))
        
        return "\n\n".join(paragraphs)


class SpeakerDiarization:
    """Simple speaker diarization using basic audio features"""
    
    @staticmethod
    def detect_speakers(segments: List[Dict[str, Any]], 
                       similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Simple speaker detection based on segment characteristics
        This is a basic implementation - for production use advanced models like pyannote.audio
        """
        if not segments:
            return segments
        
        speakers = []
        speaker_count = 0
        
        for segment in segments:
            # Simple speaker assignment based on audio characteristics
            # In a real implementation, this would use acoustic features
            assigned_speaker = SpeakerDiarization._assign_speaker(
                segment, speakers, similarity_threshold
            )
            
            if assigned_speaker is None:
                # New speaker detected
                speaker_count += 1
                speaker_id = f"Speaker {speaker_count}"
                speakers.append({
                    'id': speaker_id,
                    'segments': [segment],
                    'characteristics': SpeakerDiarization._extract_characteristics(segment)
                })
                segment['speaker'] = speaker_id
            else:
                # Assign to existing speaker
                segment['speaker'] = assigned_speaker['id']
                assigned_speaker['segments'].append(segment)
        
        return segments
    
    @staticmethod
    def _assign_speaker(segment: Dict[str, Any], speakers: List[Dict], 
                       threshold: float) -> Optional[Dict]:
        """Assign segment to existing speaker or return None for new speaker"""
        if not speakers:
            return None
        
        segment_chars = SpeakerDiarization._extract_characteristics(segment)
        
        for speaker in speakers:
            similarity = SpeakerDiarization._calculate_similarity(
                segment_chars, speaker['characteristics']
            )
            if similarity > threshold:
                return speaker
        
        return None
    
    @staticmethod
    def _extract_characteristics(segment: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic characteristics from segment (placeholder implementation)"""
        # In real implementation, extract acoustic features like:
        # - Fundamental frequency, spectral features, MFCCs, etc.
        return {
            'duration': segment['end_time'] - segment['start_time'],
            'confidence': segment.get('confidence', 0.0),
            'text_length': len(segment['text'])
        }
    
    @staticmethod
    def _calculate_similarity(chars1: Dict[str, Any], chars2: Dict[str, Any]) -> float:
        """Calculate similarity between speaker characteristics (placeholder)"""
        # Simple similarity based on duration patterns
        # In real implementation, use acoustic feature similarity
        duration_diff = abs(chars1['duration'] - chars2['duration'])
        duration_sim = max(0, 1 - duration_diff / 10)  # Normalize to 0-1
        
        return duration_sim


def format_transcription_output(transcription_result: Dict[str, Any], 
                              output_format: str = "json", 
                              include_speakers: bool = True) -> str:
    """
    Main function to format transcription output in various formats
    
    Args:
        transcription_result: The transcription result dictionary
        output_format: 'json', 'srt', 'vtt', 'txt', 'paragraphs'
        include_speakers: Whether to include speaker information
    
    Returns:
        Formatted output string
    """
    segments = transcription_result.get('segments', [])
    
    # Add speaker diarization if requested and not already present
    if include_speakers and segments and 'speaker' not in segments[0]:
        segments = SpeakerDiarization.detect_speakers(segments)
        transcription_result['segments'] = segments
    
    formatter = TranscriptionFormatter()
    
    if output_format.lower() == "srt":
        return formatter.to_srt(segments, include_speakers)
    elif output_format.lower() == "vtt":
        return formatter.to_vtt(segments, include_speakers)
    elif output_format.lower() == "txt":
        return formatter.to_text(segments, include_timestamps=False, include_speakers=include_speakers)
    elif output_format.lower() == "paragraphs":
        return formatter.to_paragraphs(segments)
    else:  # Default to JSON
        return formatter.to_json(transcription_result)


"""
Sentence-level timestamp processor
Breaks down chunk transcriptions into individual sentences with precise timestamps
"""
import re
from typing import List, Dict, Any, Tuple


class SentenceProcessor:
    def __init__(self):
        # Pattern to detect sentence endings
        self.sentence_pattern = r'[.!?]+(?:\s+|$)'
        
    def break_into_sentences(self, segment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Break a transcription segment into sentence-level segments
        """
        text = segment['text']
        words = segment.get('metadata', {}).get('words', [])
        
        if not words:
            # Fallback: estimate sentence breaks without word timestamps
            return self._estimate_sentence_breaks(segment)
        
        # Use word timestamps to create precise sentence segments
        return self._create_precise_sentence_segments(segment, words)
    
    def _create_precise_sentence_segments(self, segment: Dict[str, Any], 
                                        words: List[Dict]) -> List[Dict[str, Any]]:
        """Create sentence segments using word-level timestamps"""
        sentences = []
        current_sentence_words = []
        current_sentence_text = ""
        sentence_id = 0
        
        for word_data in words:
            word = word_data.get('word', '')
            start_time = word_data.get('start', 0) + segment['start_time']
            end_time = word_data.get('end', 0) + segment['start_time']
            
            current_sentence_words.append({
                'word': word,
                'start': start_time,
                'end': end_time
            })
            current_sentence_text += word
            
            # Check if this word ends a sentence
            if self._is_sentence_ending(word):
                if current_sentence_words:
                    sentence = {
                        'sentence_id': f"{segment['chunk_id']}_{sentence_id}",
                        'text': current_sentence_text.strip(),
                        'start_time': current_sentence_words[0]['start'],
                        'end_time': current_sentence_words[-1]['end'],
                        'duration': current_sentence_words[-1]['end'] - current_sentence_words[0]['start'],
                        'word_count': len(current_sentence_words),
                        'confidence': segment.get('confidence', 0.8),
                        'words': current_sentence_words.copy()
                    }
                    sentences.append(sentence)
                    
                    # Reset for next sentence
                    current_sentence_words = []
                    current_sentence_text = ""
                    sentence_id += 1
        
        # Handle remaining words if sentence doesn't end with punctuation
        if current_sentence_words:
            sentence = {
                'sentence_id': f"{segment['chunk_id']}_{sentence_id}",
                'text': current_sentence_text.strip(),
                'start_time': current_sentence_words[0]['start'],
                'end_time': current_sentence_words[-1]['end'],
                'duration': current_sentence_words[-1]['end'] - current_sentence_words[0]['start'],
                'word_count': len(current_sentence_words),
                'confidence': segment.get('confidence', 0.8),
                'words': current_sentence_words
            }
            sentences.append(sentence)
        
        return sentences
    
    def _estimate_sentence_breaks(self, segment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback: estimate sentence breaks without word timestamps"""
        text = segment['text']
        sentences = []
        
        # Split text into sentences using regex
        sentence_texts = re.split(self.sentence_pattern, text)
        sentence_texts = [s.strip() for s in sentence_texts if s.strip()]
        
        if not sentence_texts:
            return [segment]  # Return original if no sentences found
        
        # Estimate timing for each sentence
        total_duration = segment['end_time'] - segment['start_time']
        total_chars = len(text)
        
        current_time = segment['start_time']
        
        for i, sentence_text in enumerate(sentence_texts):
            # Estimate duration based on character count
            char_ratio = len(sentence_text) / total_chars if total_chars > 0 else 1.0
            estimated_duration = total_duration * char_ratio
            
            sentence = {
                'sentence_id': f"{segment['chunk_id']}_{i}",
                'text': sentence_text,
                'start_time': current_time,
                'end_time': current_time + estimated_duration,
                'duration': estimated_duration,
                'word_count': len(sentence_text.split()),
                'confidence': segment.get('confidence', 0.8),
                'estimated': True  # Flag to indicate estimated timing
            }
            sentences.append(sentence)
            current_time += estimated_duration
        
        return sentences
    
    def _is_sentence_ending(self, word: str) -> bool:
        """Check if a word ends a sentence"""
        return bool(re.search(r'[.!?]+$', word.strip()))
    
    def process_all_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process all segments and return sentence-level breakdown"""
        all_sentences = []
        
        for segment in segments:
            sentences = self.break_into_sentences(segment)
            all_sentences.extend(sentences)
        
        return all_sentences


def create_sentence_level_transcription(transcription_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert chunk-level transcription to sentence-level transcription
    """
    processor = SentenceProcessor()
    
    # Process segments into sentences
    sentence_segments = processor.process_all_segments(transcription_result['segments'])
    
    # Update the transcription result
    enhanced_result = transcription_result.copy()
    enhanced_result['sentence_segments'] = sentence_segments
    enhanced_result['metadata']['total_sentences'] = len(sentence_segments)
    enhanced_result['metadata']['avg_sentence_duration'] = (
        sum(s['duration'] for s in sentence_segments) / len(sentence_segments) 
        if sentence_segments else 0
    )
    
    return enhanced_result

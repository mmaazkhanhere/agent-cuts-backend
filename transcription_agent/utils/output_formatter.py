"""
Simplified transcription function that returns clean sentence-level output
"""
import json
from typing import Dict, Any, List


def create_simplified_transcript(transcription_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the detailed transcription result into a simplified format
    with only sentence-level timestamps
    
    Args:
        transcription_result: Full transcription result from the engine
        
    Returns:
        Simplified format with sentence-level segments
    """
    if transcription_result.get("status") == "error":
        return transcription_result
    
    simplified_segments = []
    
    # Process sentence-level segments if available
    if "sentence_segments" in transcription_result:
        for sentence in transcription_result["sentence_segments"]:
            simplified_segments.append({
                "text": sentence["text"],
                "start_time": round(sentence["start_time"], 2),
                "end_time": round(sentence["end_time"], 2)
            })
    else:
        # Fallback to regular segments if no sentence segments
        for segment in transcription_result.get("segments", []):
            # If segment has sentences, use those
            if "sentences" in segment and segment["sentences"]:
                for sentence in segment["sentences"]:
                    simplified_segments.append({
                        "text": sentence["text"],
                        "start_time": round(sentence["start_time"], 2),
                        "end_time": round(sentence["end_time"], 2)
                    })
            else:
                # Use the whole segment as a single entry
                simplified_segments.append({
                    "text": segment["text"],
                    "start_time": round(segment["start_time"], 2),
                    "end_time": round(segment["end_time"], 2)
                })
    
    # Create the simplified output
    return {
        "status": "success",
        "transcript": " ".join([s["text"] for s in simplified_segments]),
        "segments": simplified_segments,
        "metadata": {
            "duration": transcription_result.get("metadata", {}).get("duration", 0),
            "segment_count": len(simplified_segments),
            "confidence": transcription_result.get("metadata", {}).get("avg_confidence", 0)
        }
    }


def format_for_segmentation(simplified_transcript: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Format the simplified transcript for the segmentation agent
    
    Args:
        simplified_transcript: Output from create_simplified_transcript
        
    Returns:
        List of segment dictionaries ready for segmentation
    """
    if simplified_transcript.get("status") != "success":
        return []
    
    formatted_segments = []
    
    for i, segment in enumerate(simplified_transcript.get("segments", [])):
        formatted_segments.append({
            "id": i,
            "text": segment["text"],
            "start_time": str(segment["start_time"]),
            "end_time": str(segment["end_time"])
        })
    
    return formatted_segments
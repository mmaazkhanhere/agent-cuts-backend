import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import asyncio

class SessionManager:
    def __init__(self, sessions_file: str = "sessions.json"):
        self.sessions_file = sessions_file
        self.sessions: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._load_sessions()
    
    def _load_sessions(self):
        """Load existing sessions from file"""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    self.sessions = json.load(f)
            except:
                self.sessions = {}
    
    def _save_sessions(self):
        """Save sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")
    
    def create_session(self, unique_phrase: str, video_path: str) -> Dict[str, Any]:
        """Create a new session"""
        print(f"[SessionManager] Creating session for {unique_phrase}")
        
        session = {
            "unique_phrase": unique_phrase,
            "video_path": video_path,
            "status": "uploaded",
            "progress": {
                "current_step": "uploaded",
                "steps_completed": ["upload"],
                "percentage": 0
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "segment_paths": [],
            "error": None
        }
        
        print(f"[SessionManager] Acquiring lock...")
        with self._lock:
            self.sessions[unique_phrase] = session
            print(f"[SessionManager] Session added to memory")
            self._save_sessions()
            print(f"[SessionManager] Session saved to file")
        
        return session
    
    def update_progress(self, unique_phrase: str, step: str, percentage: int, segment_paths: list = None,copywriter_output= None):
        """Update session progress"""
        with self._lock:
            if unique_phrase in self.sessions:
                session = self.sessions[unique_phrase]
                session["progress"]["current_step"] = step
                session["progress"]["percentage"] = percentage
                
                if step not in session["progress"]["steps_completed"]:
                    session["progress"]["steps_completed"].append(step)
                
                if segment_paths:
                    session["segment_paths"] = segment_paths
                if copywriter_output:
                    session["copywriter_output"] = copywriter_output
                
                session["updated_at"] = datetime.now().isoformat()
                session["status"] = "processing" if percentage < 100 else "completed"
                
                self._save_sessions()
    
    def set_error(self, unique_phrase: str, error: str):
        """Set error for session"""
        with self._lock:
            if unique_phrase in self.sessions:
                session = self.sessions[unique_phrase]
                session["error"] = error
                session["status"] = "failed"
                session["updated_at"] = datetime.now().isoformat()
                self._save_sessions()
    
    def get_session(self, unique_phrase: str) -> Optional[Dict[str, Any]]:
        """Get session by unique phrase"""
        return self.sessions.get(unique_phrase)
    
    def get_all_sessions(self) -> Dict[str, Any]:
        """Get all sessions"""
        return self.sessions.copy()

# Global session manager instance
session_manager = SessionManager()

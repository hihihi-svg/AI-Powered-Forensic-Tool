"""
Session Management Service
Handles user sessions, interaction history, and context preservation.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any


class SessionService:
    """Manages user sessions and interaction history."""
    
    def __init__(self, storage_dir: str = "sessions"):
        """
        Initialize session service.
        
        Args:
            storage_dir: Directory to store session data
        """
        self.storage_path = Path.cwd() / storage_dir
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.session_expiry_hours = 24  # Sessions expire after 24 hours
        
    def create_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Session data with session_id
        """
        try:
            session_id = str(uuid.uuid4())
            session_data = {
                "session_id": session_id,
                "user_id": user_id or "anonymous",
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "interactions": [],
                "context": {},
                "metadata": {}
            }
            
            self._save_session(session_id, session_data)
            return session_data
            
        except Exception as e:
            print(f"Error creating session: {e}")
            # Return minimal session data on error
            return {
                "session_id": str(uuid.uuid4()),
                "user_id": user_id or "anonymous",
                "created_at": datetime.now().isoformat(),
                "interactions": [],
                "context": {}
            }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found/expired
        """
        try:
            session_file = self.storage_path / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Check if session expired
            created_at = datetime.fromisoformat(session_data["created_at"])
            if datetime.now() - created_at > timedelta(hours=self.session_expiry_hours):
                # Session expired, delete it
                session_file.unlink(missing_ok=True)
                return None
            
            # Update last accessed time
            session_data["last_accessed"] = datetime.now().isoformat()
            self._save_session(session_id, session_data)
            
            return session_data
            
        except Exception as e:
            print(f"Error retrieving session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            # Update fields
            for key, value in updates.items():
                if key not in ["session_id", "created_at"]:  # Protect immutable fields
                    session_data[key] = value
            
            session_data["last_accessed"] = datetime.now().isoformat()
            self._save_session(session_id, session_data)
            return True
            
        except Exception as e:
            print(f"Error updating session {session_id}: {e}")
            return False
    
    def log_interaction(self, session_id: str, interaction: Dict[str, Any]) -> bool:
        """
        Log a user interaction to session history.
        
        Args:
            session_id: Session identifier
            interaction: Interaction data (type, query, results, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                # Create new session if not exists
                session_data = self.create_session()
                session_id = session_data["session_id"]
            
            # Add timestamp to interaction
            interaction["timestamp"] = datetime.now().isoformat()
            
            # Append to interactions list
            if "interactions" not in session_data:
                session_data["interactions"] = []
            
            session_data["interactions"].append(interaction)
            
            # Limit history to last 100 interactions to prevent file bloat
            if len(session_data["interactions"]) > 100:
                session_data["interactions"] = session_data["interactions"][-100:]
            
            self._save_session(session_id, session_data)
            return True
            
        except Exception as e:
            print(f"Error logging interaction: {e}")
            return False
    
    def get_interaction_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get interaction history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of interactions to return
            
        Returns:
            List of interactions (most recent first)
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data or "interactions" not in session_data:
                return []
            
            # Return most recent interactions first
            interactions = session_data["interactions"][-limit:]
            return list(reversed(interactions))
            
        except Exception as e:
            print(f"Error getting interaction history: {e}")
            return []
    
    def update_context(self, session_id: str, context_updates: Dict[str, Any]) -> bool:
        """
        Update session context (current investigation state).
        
        Args:
            session_id: Session identifier
            context_updates: Context data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            if "context" not in session_data:
                session_data["context"] = {}
            
            # Merge context updates
            session_data["context"].update(context_updates)
            
            self._save_session(session_id, session_data)
            return True
            
        except Exception as e:
            print(f"Error updating context: {e}")
            return False
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get current session context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary
        """
        try:
            session_data = self.get_session(session_id)
            if session_data and "context" in session_data:
                return session_data["context"]
            return {}
            
        except Exception as e:
            print(f"Error getting context: {e}")
            return {}
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = self.storage_path / f"{session_id}.json"
            session_file.unlink(missing_ok=True)
            return True
            
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions deleted
        """
        try:
            deleted_count = 0
            for session_file in self.storage_path.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    created_at = datetime.fromisoformat(session_data["created_at"])
                    if datetime.now() - created_at > timedelta(hours=self.session_expiry_hours):
                        session_file.unlink()
                        deleted_count += 1
                        
                except Exception:
                    # Skip corrupted files
                    continue
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            return 0
    
    def _save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """
        Save session data to file.
        
        Args:
            session_id: Session identifier
            session_data: Session data to save
        """
        try:
            session_file = self.storage_path / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            raise

"""
Memory Service
Implements evolving memory representations with access tracking, temporal decay, and reinforcement.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import math


class MemoryService:
    """Manages evolving memory representations for suspects."""
    
    def __init__(self):
        """Initialize memory service."""
        self.decay_half_life_days = 30  # Half-life for temporal decay (30 days)
        self.max_confidence_boost = 0.3  # Maximum boost to confidence (30%)
        
    def calculate_access_boost(self, access_count: int) -> float:
        """
        Calculate confidence boost based on access frequency.
        Uses logarithmic scaling to prevent over-boosting.
        
        Args:
            access_count: Number of times record has been accessed
            
        Returns:
            Boost value between 0.0 and max_confidence_boost
        """
        try:
            if access_count <= 0:
                return 0.0
            
            # Logarithmic scaling: log(1 + count) / log(100)
            # This gives 0.0 for count=0, ~0.3 for count=99, asymptotic to max
            normalized = math.log(1 + access_count) / math.log(100)
            boost = min(normalized * self.max_confidence_boost, self.max_confidence_boost)
            
            return round(boost, 4)
            
        except Exception as e:
            print(f"Error calculating access boost: {e}")
            return 0.0
    
    def calculate_temporal_decay(self, last_accessed: str) -> float:
        """
        Calculate temporal decay factor based on last access time.
        Uses exponential decay with configurable half-life.
        
        Args:
            last_accessed: ISO format timestamp of last access
            
        Returns:
            Decay factor between 0.0 and 1.0 (1.0 = no decay, 0.0 = fully decayed)
        """
        try:
            last_access_time = datetime.fromisoformat(last_accessed)
            time_elapsed = datetime.now() - last_access_time
            days_elapsed = time_elapsed.total_seconds() / 86400  # Convert to days
            
            # Exponential decay: 0.5^(days_elapsed / half_life)
            decay_factor = math.pow(0.5, days_elapsed / self.decay_half_life_days)
            
            return round(decay_factor, 4)
            
        except Exception as e:
            print(f"Error calculating temporal decay: {e}")
            return 1.0  # No decay on error
    
    def calculate_reinforcement_score(self, access_count: int, last_accessed: str) -> float:
        """
        Calculate overall reinforcement score combining access boost and temporal decay.
        
        Args:
            access_count: Number of times record has been accessed
            last_accessed: ISO format timestamp of last access
            
        Returns:
            Reinforcement score between 0.0 and max_confidence_boost
        """
        try:
            access_boost = self.calculate_access_boost(access_count)
            decay_factor = self.calculate_temporal_decay(last_accessed)
            
            # Combine: boost is reduced by decay factor
            reinforcement = access_boost * decay_factor
            
            return round(reinforcement, 4)
            
        except Exception as e:
            print(f"Error calculating reinforcement score: {e}")
            return 0.0
    
    def update_access_metadata(self, current_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update metadata after a record access.
        
        Args:
            current_metadata: Current record metadata
            
        Returns:
            Updated metadata with incremented access_count and updated timestamps
        """
        try:
            updated = current_metadata.copy()
            
            # Initialize fields if not present
            if "access_count" not in updated:
                updated["access_count"] = 0
            if "first_accessed" not in updated:
                updated["first_accessed"] = datetime.now().isoformat()
            
            # Increment access count
            updated["access_count"] = updated.get("access_count", 0) + 1
            
            # Update last accessed time
            updated["last_accessed"] = datetime.now().isoformat()
            
            # Calculate and update reinforcement score
            reinforcement = self.calculate_reinforcement_score(
                updated["access_count"],
                updated["last_accessed"]
            )
            updated["confidence_boost"] = reinforcement
            
            return updated
            
        except Exception as e:
            print(f"Error updating access metadata: {e}")
            return current_metadata  # Return unchanged on error
    
    def apply_confidence_boost(self, base_confidence: float, metadata: Dict[str, Any]) -> float:
        """
        Apply confidence boost to a base confidence score.
        
        Args:
            base_confidence: Original confidence score (0.0 to 1.0)
            metadata: Record metadata containing confidence_boost
            
        Returns:
            Boosted confidence score (capped at 1.0)
        """
        try:
            boost = metadata.get("confidence_boost", 0.0)
            boosted_confidence = min(base_confidence + boost, 1.0)
            
            return round(boosted_confidence, 4)
            
        except Exception as e:
            print(f"Error applying confidence boost: {e}")
            return base_confidence  # Return original on error
    
    def should_decay_record(self, last_accessed: str, threshold: float = 0.1) -> bool:
        """
        Determine if a record should be considered "decayed" (low priority).
        
        Args:
            last_accessed: ISO format timestamp of last access
            threshold: Decay factor threshold below which record is considered decayed
            
        Returns:
            True if record is decayed, False otherwise
        """
        try:
            decay_factor = self.calculate_temporal_decay(last_accessed)
            return decay_factor < threshold
            
        except Exception as e:
            print(f"Error checking decay status: {e}")
            return False
    
    def get_memory_stats(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get memory statistics for a record.
        
        Args:
            metadata: Record metadata
            
        Returns:
            Dictionary with memory statistics
        """
        try:
            access_count = metadata.get("access_count", 0)
            last_accessed = metadata.get("last_accessed", datetime.now().isoformat())
            
            return {
                "access_count": access_count,
                "last_accessed": last_accessed,
                "access_boost": self.calculate_access_boost(access_count),
                "temporal_decay": self.calculate_temporal_decay(last_accessed),
                "reinforcement_score": self.calculate_reinforcement_score(access_count, last_accessed),
                "is_decayed": self.should_decay_record(last_accessed)
            }
            
        except Exception as e:
            print(f"Error getting memory stats: {e}")
            return {
                "access_count": 0,
                "access_boost": 0.0,
                "temporal_decay": 1.0,
                "reinforcement_score": 0.0,
                "is_decayed": False
            }
    
    def initialize_metadata(self, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize memory-related metadata for a new record.
        
        Args:
            base_metadata: Base metadata for the record
            
        Returns:
            Metadata with memory fields initialized
        """
        try:
            metadata = base_metadata.copy()
            
            # Initialize memory fields
            metadata["access_count"] = 0
            metadata["created_at"] = datetime.now().isoformat()
            metadata["last_accessed"] = datetime.now().isoformat()
            metadata["first_accessed"] = datetime.now().isoformat()
            metadata["confidence_boost"] = 0.0
            
            return metadata
            
        except Exception as e:
            print(f"Error initializing metadata: {e}")
            return base_metadata

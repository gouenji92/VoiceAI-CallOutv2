# Context Manager for Multi-turn Conversations
# Phase 3: Context Management & Slot Filling

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import redis
from app.config import settings

class ContextManager:
    """
    Manage conversation context and slot filling across multiple turns
    
    Features:
    - Session state management (Redis-backed)
    - Slot filling tracking
    - Conversation history
    - Context expiration (1 hour TTL)
    """
    
    def __init__(self):
        # TODO: Replace with actual Redis connection
        # self.redis = redis.Redis(
        #     host=settings.REDIS_HOST,
        #     port=settings.REDIS_PORT,
        #     decode_responses=True
        # )
        
        # Temporary in-memory storage for development
        self._memory_store = {}
    
    def get_context(self, call_id: str) -> Dict[str, Any]:
        """
        Retrieve conversation context for a call
        
        Args:
            call_id: Unique call identifier
            
        Returns:
            Context dictionary with slots, history, and state
        """
        # TODO: Implement Redis retrieval
        # key = f"context:{call_id}"
        # data = self.redis.get(key)
        
        # Temporary in-memory fallback
        if call_id in self._memory_store:
            return self._memory_store[call_id]
        
        # Initialize new context
        return {
            'call_id': call_id,
            'slots': {},  # Filled slots: {slot_name: value}
            'history': [],  # Conversation turns
            'current_intent': None,
            'previous_intent': None,
            'slot_filling_state': None,  # Current slot being filled
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def update_context(self, call_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update context with new information
        
        Args:
            call_id: Call identifier
            updates: Dictionary of updates to apply
            
        Returns:
            Updated context
        """
        context = self.get_context(call_id)
        
        # Merge updates
        for key, value in updates.items():
            if key == 'slots':
                context['slots'].update(value)
            elif key == 'history' and isinstance(value, dict):
                context['history'].append(value)
            else:
                context[key] = value
        
        context['last_updated'] = datetime.now().isoformat()
        
        # TODO: Save to Redis with TTL
        # key = f"context:{call_id}"
        # self.redis.setex(key, 3600, json.dumps(context))
        
        # Temporary in-memory storage
        self._memory_store[call_id] = context
        
        return context
    
    def add_turn(self, call_id: str, user_text: str, bot_response: str, nlp_data: Dict):
        """Add conversation turn to history"""
        updates = {
            'history': {
                'timestamp': datetime.now().isoformat(),
                'user': user_text,
                'bot': bot_response,
                'intent': nlp_data.get('intent'),
                'entities': nlp_data.get('entities', {}),
                'sentiment': nlp_data.get('sentiment')
            }
        }
        return self.update_context(call_id, updates)
    
    def extract_and_fill_slots(self, context: Dict, nlp_data: Dict) -> Dict:
        """
        Extract entities from NLP data and fill required slots
        
        Returns:
            {
                'slots': {...},  # Current filled slots
                'missing_slots': [...],  # Slots still needed
                'slot_filling_complete': bool
            }
        """
        intent = nlp_data.get('intent')
        entities = nlp_data.get('entities', {})
        
        # Define required slots for each intent
        REQUIRED_SLOTS = {
            'dat_lich': ['date', 'time'],
            'doi_lich': ['date', 'time', 'booking_id'],
            'huy_lich': ['booking_id'],
            'hoi_thong_tin': [],  # No required slots
            'cam_on': [],
            'tam_biet': [],
            'unknown': []
        }
        
        required = REQUIRED_SLOTS.get(intent, [])
        slots = context.get('slots', {}).copy()
        
        # Fill slots from extracted entities
        for slot_name in required:
            if slot_name in entities and entities[slot_name]:
                slots[slot_name] = entities[slot_name]
        
        # Check for missing slots
        missing_slots = [s for s in required if s not in slots or not slots[s]]
        
        return {
            'slots': slots,
            'missing_slots': missing_slots,
            'slot_filling_complete': len(missing_slots) == 0
        }
    
    def clear_context(self, call_id: str):
        """Clear context for a call (e.g., after call ends)"""
        # TODO: Delete from Redis
        # key = f"context:{call_id}"
        # self.redis.delete(key)
        
        if call_id in self._memory_store:
            del self._memory_store[call_id]
    
    def get_last_intent(self, call_id: str) -> Optional[str]:
        """Get the last detected intent"""
        context = self.get_context(call_id)
        history = context.get('history', [])
        
        if history:
            return history[-1].get('intent')
        
        return None
    
    def is_context_switch(self, call_id: str, current_intent: str) -> bool:
        """Detect if user switched context (changed topic)"""
        last_intent = self.get_last_intent(call_id)
        
        if not last_intent:
            return False
        
        # Define intents that indicate context switch
        SWITCH_INTENTS = ['tam_biet', 'cam_on', 'hoi_thong_tin']
        
        return (
            last_intent != current_intent and
            current_intent not in SWITCH_INTENTS
        )


# Global instance
context_manager = ContextManager()

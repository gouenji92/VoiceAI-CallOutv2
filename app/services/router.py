# Smart Router for Conversation Routing
# Phase 5: Advanced Routing Logic

from typing import Dict, Literal

RoutingDestination = Literal[
    'agent',           # Default Deeppavlov agent
    'rag_service',     # RAG knowledge base
    'human_agent',     # Escalate to human
    'clarification',   # Ask for clarification
    'booking_flow',    # Booking-specific flow
    'feedback_flow'    # Feedback collection
]

class SmartRouter:
    """
    Intelligent routing based on intent, sentiment, confidence, and context
    
    Routing Rules:
    1. Low confidence → Ask clarification
    2. Negative sentiment + complaint → Human escalation
    3. Info request → RAG service
    4. Booking intents → Slot filling flow
    5. Default → Deeppavlov agent
    """
    
    def __init__(self):
        # Confidence thresholds
        self.CONFIDENCE_THRESHOLD = 0.65
        self.HIGH_CONFIDENCE_THRESHOLD = 0.80
        
        # Intent categories
        self.BOOKING_INTENTS = {'dat_lich', 'doi_lich', 'huy_lich'}
        self.INFO_INTENTS = {'hoi_thong_tin'}
        self.COMPLAINT_INTENTS = {'khieu_nai'}
        self.SOCIAL_INTENTS = {'cam_on', 'tam_biet', 'chao_hoi'}
    
    def route(self, nlp_data: Dict, context: Dict) -> RoutingDestination:
        """
        Determine routing destination based on NLP analysis and context
        
        Args:
            nlp_data: {
                'intent': str,
                'confidence': float,
                'sentiment': str,  # positive/negative/neutral
                'entities': Dict
            }
            context: Conversation context from ContextManager
            
        Returns:
            Routing destination
        """
        intent = nlp_data.get('intent', 'unknown')
        confidence = nlp_data.get('confidence', 0.0)
        sentiment = nlp_data.get('sentiment', 'neutral')
        
        # Rule 1: Very low confidence → Clarification
        if confidence < self.CONFIDENCE_THRESHOLD:
            return 'clarification'
        
        # Rule 2: Negative sentiment + complaint → Human escalation
        if sentiment == 'negative':
            if intent in self.COMPLAINT_INTENTS:
                return 'human_agent'
            
            # Multiple negative interactions → Escalate
            negative_count = self._count_negative_sentiments(context)
            if negative_count >= 2:
                return 'human_agent'
        
        # Rule 3: Info request with high confidence → RAG
        if intent in self.INFO_INTENTS:
            if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                return 'rag_service'
            else:
                return 'agent'  # Let agent handle ambiguous questions
        
        # Rule 4: Booking-related → Booking flow
        if intent in self.BOOKING_INTENTS:
            return 'booking_flow'
        
        # Rule 5: Social intents → Simple response (no agent needed)
        if intent in self.SOCIAL_INTENTS:
            return 'agent'
        
        # Rule 6: Unknown intent with context → Try to infer
        if intent == 'unknown':
            # Check if we're in middle of booking flow
            if context.get('slot_filling_state'):
                return 'booking_flow'
            
            # Otherwise ask for clarification
            return 'clarification'
        
        # Default: Route to agent
        return 'agent'
    
    def _count_negative_sentiments(self, context: Dict) -> int:
        """Count negative sentiments in recent history"""
        history = context.get('history', [])
        
        # Check last 3 turns
        recent_history = history[-3:] if len(history) >= 3 else history
        
        negative_count = sum(
            1 for turn in recent_history
            if turn.get('sentiment') == 'negative'
        )
        
        return negative_count
    
    def should_escalate_to_human(self, nlp_data: Dict, context: Dict) -> bool:
        """
        Check if conversation should be escalated to human agent
        
        Escalation triggers:
        - Multiple low confidence responses
        - Multiple negative sentiments
        - Explicit request for human
        - Complex query (multiple intents)
        """
        # Explicit request
        if nlp_data.get('intent') == 'yeu_cau_nguoi_that':
            return True
        
        # Multiple low confidence
        history = context.get('history', [])
        recent_low_conf = sum(
            1 for turn in history[-3:]
            if turn.get('confidence', 1.0) < self.CONFIDENCE_THRESHOLD
        )
        if recent_low_conf >= 2:
            return True
        
        # Multiple negative sentiments
        if self._count_negative_sentiments(context) >= 2:
            return True
        
        return False
    
    def get_routing_explanation(self, destination: RoutingDestination, nlp_data: Dict) -> str:
        """Get human-readable explanation for routing decision"""
        
        explanations = {
            'clarification': f"Low confidence ({nlp_data.get('confidence', 0):.2f}) - asking for clarification",
            'human_agent': f"Escalating to human (sentiment: {nlp_data.get('sentiment')})",
            'rag_service': f"Info request detected - using knowledge base",
            'booking_flow': f"Booking intent ({nlp_data.get('intent')}) - slot filling",
            'agent': "Default routing to Deeppavlov agent"
        }
        
        return explanations.get(destination, "Unknown routing")


# Global instance
smart_router = SmartRouter()

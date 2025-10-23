"""
Custom exceptions for VoiceAI application
"""

class VoiceAIException(Exception):
    """Base exception cho tất cả VoiceAI errors"""
    pass


class DatabaseException(VoiceAIException):
    """Exception liên quan đến database operations"""
    pass


class NLPException(VoiceAIException):
    """Exception liên quan đến NLP processing"""
    pass


class DialogException(VoiceAIException):
    """Exception liên quan đến dialog management"""
    pass


class AsteriskException(VoiceAIException):
    """Exception liên quan đến Asterisk/telephony"""
    pass


class WorkflowException(VoiceAIException):
    """Exception liên quan đến workflow processing"""
    pass


class AuthException(VoiceAIException):
    """Exception liên quan đến authentication/authorization"""
    pass


class ValidationException(VoiceAIException):
    """Exception liên quan đến data validation"""
    pass

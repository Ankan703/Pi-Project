"""
BUDDY Voice Assistant - Intent Handler
=======================================
Routes user requests to appropriate handlers.
Separates local commands from internet queries.
"""

import re
from typing import Optional, Tuple
from enum import Enum
from datetime import datetime
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import config


class IntentType(Enum):
    """Types of user intents."""
    LOCAL_TIME = "local_time"
    LOCAL_DATE = "local_date"
    LOCAL_TIMER = "local_timer"
    LOCAL_ALARM = "local_alarm"
    LOCAL_STOP = "local_stop"
    LOCAL_HELP = "local_help"
    LOCAL_VOLUME = "local_volume"
    LOCAL_GOODBYE = "local_goodbye"
    INTERNET_QUERY = "internet_query"
    UNKNOWN = "unknown"


class IntentHandler:
    """
    Detects user intent and routes to appropriate handler.
    Prioritizes local commands over internet queries.
    """
    
    # Pattern matching for local commands
    PATTERNS = {
        IntentType.LOCAL_TIME: [
            r"\b(what|tell|current|give)\b.*\b(time|clock)\b",
            r"\btime\s+is\s+it\b",
            r"\bwhat's\s+the\s+time\b",
        ],
        IntentType.LOCAL_DATE: [
            r"\b(what|tell|current|today)\b.*\b(date|day)\b",
            r"\bwhat\s+day\s+is\b",
            r"\bwhat's\s+the\s+date\b",
            r"\bwhat\s+is\s+today\b",
        ],
        IntentType.LOCAL_TIMER: [
            r"\bset\s+(a\s+)?timer\b",
            r"\btimer\s+for\b",
            r"\bcount\s*down\b",
        ],
        IntentType.LOCAL_ALARM: [
            r"\bset\s+(an?\s+)?alarm\b",
            r"\bwake\s+me\b",
            r"\bremind\s+me\b",
        ],
        IntentType.LOCAL_STOP: [
            r"^(stop|cancel|quit|exit|nevermind|never\s*mind)$",
            r"\bstop\s+(listening|talking)\b",
            r"\bcancel\s+(that|request)\b",
        ],
        IntentType.LOCAL_HELP: [
            r"\bwhat\s+can\s+you\s+do\b",
            r"\bhelp\s*(me|please)?\b",
            r"\byour\s+(abilities|commands|features)\b",
        ],
        IntentType.LOCAL_VOLUME: [
            r"\b(set|change|increase|decrease|lower|raise)\s*(volume|sound)\b",
            r"\b(louder|quieter|mute|unmute)\b",
            r"\bvolume\s+(up|down)\b",
        ],
        IntentType.LOCAL_GOODBYE: [
            r"^(goodbye|bye|see\s+you|goodnight)$",
            r"\bthat's\s+all\b",
            r"\bthank\s+you\b.*\bbye\b",
        ],
    }
    
    def __init__(self):
        # Compile patterns for efficiency
        self._compiled_patterns = {}
        for intent_type, patterns in self.PATTERNS.items():
            self._compiled_patterns[intent_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def detect_intent(self, text: str) -> Tuple[IntentType, Optional[dict]]:
        """
        Detect the intent from user text.
        
        Args:
            text: User's transcribed speech
        
        Returns:
            Tuple of (IntentType, optional parameters dict)
        """
        text = text.strip()
        
        if not text:
            return IntentType.UNKNOWN, None
        
        # Check each intent pattern
        for intent_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    # Extract any parameters
                    params = self._extract_params(intent_type, text, match)
                    return intent_type, params
        
        # Default to internet query
        return IntentType.INTERNET_QUERY, {"query": text}
    
    def _extract_params(self, intent_type: IntentType, text: str, match: re.Match) -> dict:
        """Extract parameters from the matched text."""
        params = {}
        
        if intent_type == IntentType.LOCAL_TIMER:
            # Extract timer duration
            duration = self._extract_duration(text)
            if duration:
                params["duration_seconds"] = duration
        
        elif intent_type == IntentType.LOCAL_ALARM:
            # Extract alarm time
            alarm_time = self._extract_time(text)
            if alarm_time:
                params["time"] = alarm_time
        
        elif intent_type == IntentType.LOCAL_VOLUME:
            # Extract volume change
            if "up" in text.lower() or "increase" in text.lower() or "louder" in text.lower():
                params["direction"] = "up"
            elif "down" in text.lower() or "decrease" in text.lower() or "quieter" in text.lower():
                params["direction"] = "down"
            elif "mute" in text.lower():
                params["direction"] = "mute"
        
        return params
    
    def _extract_duration(self, text: str) -> Optional[int]:
        """Extract duration in seconds from text."""
        text_lower = text.lower()
        total_seconds = 0
        
        # Hours
        hours_match = re.search(r'(\d+)\s*hours?', text_lower)
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600
        
        # Minutes
        minutes_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', text_lower)
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60
        
        # Seconds
        seconds_match = re.search(r'(\d+)\s*(?:seconds?|secs?)', text_lower)
        if seconds_match:
            total_seconds += int(seconds_match.group(1))
        
        return total_seconds if total_seconds > 0 else None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from text."""
        # Try to find time patterns like "7:30", "7 am", "7:30 pm"
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm|a\.?m\.?|p\.?m\.?)?',
            r'(\d{1,2})\s*(am|pm|a\.?m\.?|p\.?m\.?)',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def handle_local(self, intent_type: IntentType, params: dict) -> str:
        """
        Handle local commands that don't need internet.
        
        Args:
            intent_type: The detected intent
            params: Extracted parameters
        
        Returns:
            Response string
        """
        handlers = {
            IntentType.LOCAL_TIME: self._handle_time,
            IntentType.LOCAL_DATE: self._handle_date,
            IntentType.LOCAL_TIMER: self._handle_timer,
            IntentType.LOCAL_ALARM: self._handle_alarm,
            IntentType.LOCAL_STOP: self._handle_stop,
            IntentType.LOCAL_HELP: self._handle_help,
            IntentType.LOCAL_VOLUME: self._handle_volume,
            IntentType.LOCAL_GOODBYE: self._handle_goodbye,
        }
        
        handler = handlers.get(intent_type)
        if handler:
            return handler(params)
        
        return "I'm not sure how to help with that."
    
    def _handle_time(self, params: dict) -> str:
        """Handle time query."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        return f"The current time is {time_str}"
    
    def _handle_date(self, params: dict) -> str:
        """Handle date query."""
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return f"Today is {date_str}"
    
    def _handle_timer(self, params: dict) -> str:
        """Handle timer request."""
        duration = params.get("duration_seconds")
        
        if not duration:
            return "How long would you like me to set the timer for?"
        
        # Format duration for speech
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        parts = []
        if hours:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds:
            parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
        
        duration_str = " and ".join(parts)
        
        # Note: Timer implementation would go here
        # For now, just acknowledge the request
        return f"Okay, I've set a timer for {duration_str}"
    
    def _handle_alarm(self, params: dict) -> str:
        """Handle alarm request."""
        alarm_time = params.get("time")
        
        if not alarm_time:
            return "What time should I set the alarm for?"
        
        # Note: Alarm implementation would go here
        return f"Okay, I've set an alarm for {alarm_time}"
    
    def _handle_stop(self, params: dict) -> str:
        """Handle stop command."""
        return "Okay, cancelled."
    
    def _handle_help(self, params: dict) -> str:
        """Handle help request."""
        return (
            "I can help you with many things! "
            "You can ask me about the time or date, set timers, or ask questions. "
            "You can also say 'stop' to cancel what I'm doing. "
            "For internet information, I'll use my knowledge to help you."
        )
    
    def _handle_volume(self, params: dict) -> str:
        """Handle volume control."""
        direction = params.get("direction", "")
        
        # Note: Actual volume control would use system commands
        if direction == "up":
            return "Increasing volume"
        elif direction == "down":
            return "Decreasing volume"
        elif direction == "mute":
            return "Muting audio"
        else:
            return "Volume adjusted"
    
    def _handle_goodbye(self, params: dict) -> str:
        """Handle goodbye."""
        return "Goodbye! Let me know if you need anything else."
    
    def is_local_intent(self, intent_type: IntentType) -> bool:
        """Check if intent can be handled locally."""
        return intent_type != IntentType.INTERNET_QUERY and intent_type != IntentType.UNKNOWN


# Test intent handler
if __name__ == "__main__":
    print("Testing Intent Handler...")
    
    handler = IntentHandler()
    
    test_queries = [
        "What time is it?",
        "What's the date today?",
        "Set a timer for 5 minutes",
        "Set an alarm for 7:30 am",
        "Help me",
        "What can you do?",
        "Volume up",
        "Make it louder",
        "Stop",
        "Cancel that",
        "Goodbye",
        # Internet queries
        "What is the capital of France?",
        "Tell me about black holes",
        "Who is the president of the United States?",
        "What's the weather like?",
    ]
    
    print("\n" + "="*60)
    for query in test_queries:
        intent_type, params = handler.detect_intent(query)
        is_local = handler.is_local_intent(intent_type)
        
        print(f"\nQuery: '{query}'")
        print(f"  Intent: {intent_type.value}")
        print(f"  Params: {params}")
        print(f"  Local: {is_local}")
        
        if is_local:
            response = handler.handle_local(intent_type, params)
            print(f"  Response: {response}")
    
    print("\n" + "="*60)
    print("Intent handler test complete!")
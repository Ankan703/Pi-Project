"""
BUDDY Voice Assistant - Configuration Management
=================================================
Centralizes all configuration with validation and sensible defaults.
Optimized for Raspberry Pi 4 Model B (4GB RAM).
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()


class AudioConfig(BaseSettings):
    """Audio input/output configuration."""
    
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    chunk_size: int = Field(default=1024, description="Audio chunk size for streaming")
    channels: int = Field(default=1, description="Number of audio channels (mono)")
    mic_device_index: int = Field(default=-1, description="Microphone device index (-1 for default)")
    speaker_device_index: int = Field(default=-1, description="Speaker device index (-1 for default)")
    
    # Voice Activity Detection
    vad_aggressiveness: int = Field(default=2, ge=0, le=3, description="VAD aggressiveness (0-3)")
    silence_threshold: float = Field(default=0.5, description="Seconds of silence to stop recording")
    max_recording_duration: float = Field(default=10.0, description="Maximum recording duration in seconds")
    
    class Config:
        env_prefix = "AUDIO_"


class WhisperConfig(BaseSettings):
    """Speech-to-text (Whisper) configuration."""
    
    model: str = Field(default="tiny.en", description="Whisper model name")
    compute_type: str = Field(default="int8", description="Compute type for inference")
    cpu_threads: int = Field(default=2, description="Number of CPU threads")
    beam_size: int = Field(default=1, description="Beam size for decoding (1 = greedy)")
    language: str = Field(default="en", description="Language code")
    
    # Model download directory
    model_dir: Path = Field(default=PROJECT_ROOT / "models", description="Model storage directory")
    
    class Config:
        env_prefix = "WHISPER_"


class TTSConfig(BaseSettings):
    """Text-to-speech configuration."""
    
    engine: str = Field(default="piper", description="TTS engine (piper, pyttsx3)")
    piper_path: str = Field(default="/usr/local/bin/piper", description="Path to Piper executable")
    voice_path: str = Field(
        default=str(Path.home() / "piper-voices" / "en_US-lessac-medium.onnx"),
        description="Path to Piper voice model"
    )
    speech_rate: float = Field(default=1.0, description="Speech rate multiplier")
    
    class Config:
        env_prefix = "TTS_"


class WakeWordConfig(BaseSettings):
    """Wake word detection configuration."""
    
    phrase: str = Field(default="hey_buddy", description="Wake word phrase")
    sensitivity: float = Field(default=0.5, ge=0.0, le=1.0, description="Detection sensitivity")
    model_path: Optional[str] = Field(default=None, description="Custom wake word model path")
    
    class Config:
        env_prefix = "WAKE_WORD_"


class GeminiConfig(BaseSettings):
    """Gemini API configuration."""
    
    api_key: str = Field(default="", description="Gemini API key")
    model: str = Field(default="gemini-2.0-flash", description="Gemini model name")
    max_tokens: int = Field(default=500, description="Maximum response tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Response creativity")
    
    # Rate limiting
    requests_per_minute: int = Field(default=15, description="API rate limit")
    
    # System prompt for the assistant
    system_prompt: str = Field(
        default="""You are BUDDY, a helpful voice assistant running on a Raspberry Pi.
Keep your responses concise and conversational - they will be spoken aloud.
Limit responses to 2-3 sentences unless asked for more detail.
Be friendly and helpful. If you don't know something, say so briefly.""",
        description="System prompt for Gemini"
    )
    
    class Config:
        env_prefix = "GEMINI_"


class AssistantConfig(BaseSettings):
    """General assistant configuration."""
    
    name: str = Field(default="BUDDY", description="Assistant name")
    debug: bool = Field(default=False, description="Enable debug logging")
    log_file: Path = Field(default=PROJECT_ROOT / "logs" / "buddy.log", description="Log file path")
    
    # Timeouts
    listen_timeout: float = Field(default=5.0, description="Seconds to wait for speech after wake word")
    response_timeout: float = Field(default=30.0, description="Maximum time for API response")
    
    # Paths
    sounds_dir: Path = Field(default=PROJECT_ROOT / "sounds", description="Sound effects directory")
    
    class Config:
        env_prefix = ""


class Config:
    """Main configuration container."""
    
    def __init__(self):
        self.audio = AudioConfig()
        self.whisper = WhisperConfig()
        self.tts = TTSConfig()
        self.wake_word = WakeWordConfig()
        self.gemini = GeminiConfig()
        self.assistant = AssistantConfig()
        
        # Validate critical settings
        self._validate()
    
    def _validate(self):
        """Validate configuration."""
        # Check for API key
        if not self.gemini.api_key:
            print("⚠️  Warning: GEMINI_API_KEY not set. Internet queries will fail.")
            print("   Set it in your .env file or environment variables.")
        
        # Ensure directories exist
        self.whisper.model_dir.mkdir(parents=True, exist_ok=True)
        self.assistant.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.assistant.sounds_dir.mkdir(parents=True, exist_ok=True)
    
    def print_config(self):
        """Print current configuration (for debugging)."""
        print("\n" + "="*60)
        print("BUDDY Voice Assistant Configuration")
        print("="*60)
        print(f"Whisper Model: {self.whisper.model} ({self.whisper.compute_type})")
        print(f"TTS Engine: {self.tts.engine}")
        print(f"Wake Word: {self.wake_word.phrase}")
        print(f"Gemini Model: {self.gemini.model}")
        print(f"Audio: {self.audio.sample_rate}Hz, {self.audio.chunk_size} chunk")
        print(f"Debug: {self.assistant.debug}")
        print("="*60 + "\n")


# Global configuration instance
config = Config()


if __name__ == "__main__":
    # Test configuration loading
    config.print_config()

"""
BUDDY Voice Assistant - Text-to-Speech
=======================================
High-quality TTS using Piper, optimized for Raspberry Pi.
"""

import subprocess
import tempfile
import wave
import io
import os
import shutil
from typing import Optional, Generator
from pathlib import Path

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import config


class TextToSpeech:
    """
    Text-to-speech engine wrapper.
    Primary: Piper TTS (fast, natural voice)
    Fallback: pyttsx3 (offline, cross-platform)
    """
    
    def __init__(self):
        self.engine = config.tts.engine
        self.piper_path = config.tts.piper_path
        self.voice_path = os.path.expanduser(config.tts.voice_path)
        self.speech_rate = config.tts.speech_rate
        
        # Check Piper availability
        self.piper_available = self._check_piper()
        
        # Initialize fallback engine
        self._pyttsx3_engine = None
        
        if self.engine == "piper" and not self.piper_available:
            print("⚠️  Piper not available, falling back to pyttsx3")
            self.engine = "pyttsx3"
        
        if self.engine == "pyttsx3":
            self._init_pyttsx3()
        
        print(f"✓ TTS initialized ({self.engine})")

    def _resolve_piper_executable(self) -> Optional[str]:
        """Resolve the Piper executable path from common installation layouts."""
        candidates = []

        if self.piper_path:
            expanded = os.path.expanduser(self.piper_path)
            candidates.append(expanded)

            if os.path.isdir(expanded):
                candidates.append(os.path.join(expanded, "piper"))
                candidates.append(os.path.join(expanded, "bin", "piper"))

        which_path = shutil.which("piper")
        if which_path:
            candidates.append(which_path)

        candidates.extend([
            "/usr/local/bin/piper",
            "/usr/local/lib/piper/piper",
            "/opt/piper/piper",
        ])

        seen = set()
        for candidate in candidates:
            if not candidate:
                continue

            normalized = os.path.abspath(candidate)
            if normalized in seen:
                continue
            seen.add(normalized)

            if os.path.isfile(normalized) and os.access(normalized, os.X_OK):
                return normalized

        return None
    
    def _check_piper(self) -> bool:
        """Check if Piper TTS is available."""
        resolved_path = self._resolve_piper_executable()
        if resolved_path is None:
            print(f"⚠️  Piper executable not found or not executable: {self.piper_path}")
            return False

        self.piper_path = resolved_path
        
        # Check if voice model exists
        if not os.path.exists(self.voice_path):
            print(f"⚠️  Piper voice not found: {self.voice_path}")
            return False
        
        return True
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine."""
        if not PYTTSX3_AVAILABLE:
            raise RuntimeError("pyttsx3 is not installed")
        
        self._pyttsx3_engine = pyttsx3.init()
        
        # Configure voice
        voices = self._pyttsx3_engine.getProperty('voices')
        
        # Try to find a good English voice
        for voice in voices:
            if 'english' in voice.name.lower():
                self._pyttsx3_engine.setProperty('voice', voice.id)
                break
        
        # Set speech rate
        rate = self._pyttsx3_engine.getProperty('rate')
        self._pyttsx3_engine.setProperty('rate', int(rate * self.speech_rate))
    
    def speak(self, text: str):
        """
        Convert text to speech and play audio.
        
        Args:
            text: Text to speak
        """
        if not text or not text.strip():
            return
        
        # Clean text for speech
        text = self._clean_text(text)
        
        if self.engine == "piper":
            self._speak_piper(text)
        else:
            self._speak_pyttsx3(text)
    
    def _speak_piper(self, text: str):
        """Speak using Piper TTS."""
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            # Generate speech with Piper
            cmd = [
                self.piper_path,
                "--model", self.voice_path,
                "--output_file", tmp_path
            ]
            
            # Use length_scale for speech rate (lower = faster)
            length_scale = 1.0 / self.speech_rate
            cmd.extend(["--length_scale", str(length_scale)])
            
            # Run Piper
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(input=text.encode('utf-8'))
            
            if process.returncode != 0:
                print(f"Piper error: {stderr.decode()}")
                # Fall back to pyttsx3
                self._speak_pyttsx3(text)
                return
            
            # Play the generated audio
            self._play_wav(tmp_path)
            
            # Clean up
            os.unlink(tmp_path)
        
        except Exception as e:
            print(f"Piper TTS error: {e}")
            # Fall back to pyttsx3
            if PYTTSX3_AVAILABLE:
                self._speak_pyttsx3(text)
    
    def _speak_pyttsx3(self, text: str):
        """Speak using pyttsx3."""
        if self._pyttsx3_engine is None:
            self._init_pyttsx3()
        
        try:
            self._pyttsx3_engine.say(text)
            self._pyttsx3_engine.runAndWait()
        except Exception as e:
            print(f"pyttsx3 error: {e}")
    
    def _play_wav(self, filepath: str):
        """Play a WAV file using aplay (Linux) or system default."""
        try:
            # Try using aplay (Linux/Pi)
            subprocess.run(
                ["aplay", "-q", filepath],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fall back to PyAudio
            try:
                from .audio_utils import AudioPlayer
                player = AudioPlayer()
                player.play_wav(filepath)
                player.cleanup()
            except Exception as e:
                print(f"Could not play audio: {e}")
    
    def synthesize_to_bytes(self, text: str) -> bytes:
        """
        Synthesize text to audio bytes (WAV format).
        
        Args:
            text: Text to synthesize
        
        Returns:
            WAV audio bytes
        """
        text = self._clean_text(text)
        
        if self.engine == "piper":
            return self._synthesize_piper(text)
        else:
            return self._synthesize_pyttsx3(text)
    
    def _synthesize_piper(self, text: str) -> bytes:
        """Synthesize using Piper TTS."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            length_scale = 1.0 / self.speech_rate
            
            cmd = [
                self.piper_path,
                "--model", self.voice_path,
                "--output_file", tmp_path,
                "--length_scale", str(length_scale)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            process.communicate(input=text.encode('utf-8'))
            
            with open(tmp_path, 'rb') as f:
                return f.read()
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _synthesize_pyttsx3(self, text: str) -> bytes:
        """Synthesize using pyttsx3."""
        if self._pyttsx3_engine is None:
            self._init_pyttsx3()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            self._pyttsx3_engine.save_to_file(text, tmp_path)
            self._pyttsx3_engine.runAndWait()
            
            with open(tmp_path, 'rb') as f:
                return f.read()
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and prepare text for TTS.
        
        - Expands abbreviations
        - Handles numbers
        - Removes problematic characters
        """
        # Replace common abbreviations
        replacements = {
            "Dr.": "Doctor",
            "Mr.": "Mister",
            "Mrs.": "Missus",
            "Ms.": "Miss",
            "Jr.": "Junior",
            "Sr.": "Senior",
            "vs.": "versus",
            "etc.": "et cetera",
            "e.g.": "for example",
            "i.e.": "that is",
            "&": "and",
            "%": " percent",
            "@": " at ",
            "#": " number ",
            "...": ", ",
            "—": ", ",
            "–": ", ",
            "\n": " ",
            "\t": " ",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove multiple spaces
        text = " ".join(text.split())
        
        return text.strip()
    
    def get_available_voices(self) -> list:
        """Get list of available voices (for pyttsx3)."""
        if self._pyttsx3_engine is None:
            if PYTTSX3_AVAILABLE:
                self._init_pyttsx3()
            else:
                return []
        
        voices = self._pyttsx3_engine.getProperty('voices')
        return [{"id": v.id, "name": v.name} for v in voices]


class StreamingTTS:
    """
    Streaming TTS for lower latency.
    Generates and plays audio in chunks.
    """
    
    def __init__(self, tts: TextToSpeech):
        self.tts = tts
    
    def speak_streaming(self, text: str, chunk_size: int = 100):
        """
        Speak text in streaming chunks.
        Splits text into sentences and speaks each immediately.
        
        Args:
            text: Full text to speak
            chunk_size: Approximate characters per chunk
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            if sentence.strip():
                self.tts.speak(sentence)
    
    def _split_sentences(self, text: str) -> list:
        """Split text into sentences."""
        import re
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        return [s.strip() for s in sentences if s.strip()]


# Test TTS
if __name__ == "__main__":
    print("Testing Text-to-Speech...")
    
    tts = TextToSpeech()
    
    # Test basic speech
    test_texts = [
        "Hello! I am Buddy, your voice assistant.",
        "The weather today is sunny with a high of 75 degrees.",
        "I can help you with many things. Just ask me a question!",
    ]
    
    for text in test_texts:
        print(f"Speaking: {text}")
        tts.speak(text)
        print()
    
    # Test streaming
    print("\nTesting streaming TTS...")
    streaming = StreamingTTS(tts)
    
    long_text = ("This is a longer piece of text that will be spoken in chunks. "
                 "Each sentence is processed separately for lower latency. "
                 "This makes the response feel more natural and immediate.")
    
    streaming.speak_streaming(long_text)
    
    print("\nTTS test complete!")
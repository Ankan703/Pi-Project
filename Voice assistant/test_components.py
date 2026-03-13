#!/usr/bin/env python3
"""
BUDDY Voice Assistant - Quick Test Script
==========================================
Tests individual components without requiring full audio setup.
Run this to verify your configuration before running main.py

Usage:
    python test_components.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_config():
    """Test configuration loading."""
    print("\n" + "="*50)
    print("TEST 1: Configuration")
    print("="*50)
    
    try:
        from config import config
        print(f"✓ Configuration loaded successfully")
        print(f"  - Whisper model: {config.whisper.model}")
        print(f"  - TTS engine: {config.tts.engine}")
        print(f"  - Wake word: {config.wake_word.phrase}")
        print(f"  - Gemini model: {config.gemini.model}")
        print(f"  - API key configured: {'Yes' if config.gemini.api_key else 'No'}")
        return True
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False


def test_intent_handler():
    """Test intent detection."""
    print("\n" + "="*50)
    print("TEST 2: Intent Handler")
    print("="*50)
    
    try:
        from modules.intent_handler import IntentHandler
        
        handler = IntentHandler()
        
        test_cases = [
            ("What time is it?", "local_time"),
            ("What's the weather?", "internet_query"),
            ("Set a timer for 5 minutes", "local_timer"),
            ("Who is the president?", "internet_query"),
        ]
        
        all_passed = True
        for text, expected in test_cases:
            intent_type, params = handler.detect_intent(text)
            result = "✓" if intent_type.value == expected else "✗"
            if result == "✗":
                all_passed = False
            print(f"  {result} '{text}' -> {intent_type.value}")
        
        if all_passed:
            print("✓ Intent handler working correctly")
        return all_passed
    
    except Exception as e:
        print(f"✗ Intent handler failed: {e}")
        return False


def test_gemini_api():
    """Test Gemini API connection."""
    print("\n" + "="*50)
    print("TEST 3: Gemini API")
    print("="*50)
    
    try:
        from config import config
        
        if not config.gemini.api_key:
            print("⚠ Gemini API key not configured")
            print("  Set GEMINI_API_KEY in your .env file")
            return False
        
        from modules.gemini_client import GeminiClient
        
        client = GeminiClient()
        
        print("  Sending test query...")
        response = client.generate("Say hello in one short sentence.")
        
        if response and len(response) > 0:
            print(f"✓ Gemini API working!")
            print(f"  Response: '{response}'")
            return True
        else:
            print("✗ Empty response from Gemini")
            return False
    
    except Exception as e:
        print(f"✗ Gemini API failed: {e}")
        return False


def test_speech_recognition():
    """Test speech recognition model loading."""
    print("\n" + "="*50)
    print("TEST 4: Speech Recognition (Whisper)")
    print("="*50)
    
    try:
        from modules.speech_recognition import SpeechRecognizer
        import numpy as np
        
        print("  Loading Whisper model (this may take a minute)...")
        recognizer = SpeechRecognizer(lazy_load=False)
        
        # Test with silence
        print("  Testing with synthetic audio...")
        dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        result = recognizer.transcribe_array(dummy_audio)
        
        print(f"✓ Speech recognition working!")
        print(f"  Model: {recognizer.model_name}")
        print(f"  Compute type: {recognizer.compute_type}")
        return True
    
    except Exception as e:
        print(f"✗ Speech recognition failed: {e}")
        return False


def test_tts():
    """Test text-to-speech."""
    print("\n" + "="*50)
    print("TEST 5: Text-to-Speech")
    print("="*50)
    
    try:
        from modules.tts import TextToSpeech
        
        tts = TextToSpeech()
        
        print(f"  Engine: {tts.engine}")
        
        # Test synthesis (don't play audio)
        print("  Testing synthesis...")
        audio_bytes = tts.synthesize_to_bytes("Hello, this is a test.")
        
        if audio_bytes and len(audio_bytes) > 0:
            print(f"✓ TTS working! Generated {len(audio_bytes)} bytes of audio")
            return True
        else:
            print("✗ TTS generated no audio")
            return False
    
    except Exception as e:
        print(f"✗ TTS failed: {e}")
        print("  Note: Piper TTS requires installation on Raspberry Pi")
        print("  Falling back to pyttsx3 should work on most systems")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("   BUDDY Voice Assistant - Component Tests")
    print("="*60)
    
    results = {
        "Configuration": test_config(),
        "Intent Handler": test_intent_handler(),
        "Gemini API": test_gemini_api(),
        "Speech Recognition": test_speech_recognition(),
        "Text-to-Speech": test_tts(),
    }
    
    print("\n" + "="*60)
    print("   Test Summary")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-"*60)
    print(f"  Total: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Run 'python main.py' to start the assistant.")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        print("  Make sure you have:")
        print("  1. Set up your .env file with GEMINI_API_KEY")
        print("  2. Installed all dependencies: pip install -r requirements.txt")
        print("  3. Followed the setup instructions in README.md")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

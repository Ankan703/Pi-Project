#!/bin/bash
# =============================================================================
# BUDDY Voice Assistant - Raspberry Pi Setup Script
# =============================================================================
# Run this script on your Raspberry Pi to set up everything.
# Usage: chmod +x setup.sh && ./setup.sh
# =============================================================================

set -e  # Exit on error

echo "=================================================="
echo "   BUDDY Voice Assistant - Setup Script"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    echo "The setup may still work on other Linux systems."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Update system
echo ""
echo -e "${GREEN}[1/7] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install system dependencies
echo ""
echo -e "${GREEN}[2/7] Installing system dependencies...${NC}"
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    portaudio19-dev \
    python3-pyaudio \
    libsndfile1 \
    ffmpeg \
    espeak-ng \
    alsa-utils \
    libasound2-dev \
    wget \
    curl

# Step 3: Create and activate virtual environment
echo ""
echo -e "${GREEN}[3/7] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Step 4: Install Python dependencies
echo ""
echo -e "${GREEN}[4/7] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Install Piper TTS
echo ""
echo -e "${GREEN}[5/7] Installing Piper TTS...${NC}"

PIPER_VERSION="v1.2.0"
ARCH=$(uname -m)
PIPER_INSTALL_DIR="/usr/local/lib/piper"

if [ "$ARCH" = "aarch64" ]; then
    PIPER_FILE="piper_arm64.tar.gz"
elif [ "$ARCH" = "armv7l" ]; then
    PIPER_FILE="piper_armv7.tar.gz"
else
    echo -e "${YELLOW}Unknown architecture: $ARCH. Trying arm64...${NC}"
    PIPER_FILE="piper_arm64.tar.gz"
fi

if [ ! -x "/usr/local/bin/piper" ]; then
    wget -q "https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/${PIPER_FILE}"
    tar -xzf "$PIPER_FILE"
    sudo mkdir -p "$PIPER_INSTALL_DIR"
    sudo rm -rf "$PIPER_INSTALL_DIR"
    sudo mv piper "$PIPER_INSTALL_DIR"
    sudo ln -sf "$PIPER_INSTALL_DIR/piper" /usr/local/bin/piper
    sudo chmod +x "$PIPER_INSTALL_DIR/piper" /usr/local/bin/piper
    rm -f "$PIPER_FILE"
    echo "✓ Piper installed"
else
    echo "✓ Piper already installed"
fi

if [ -d "/usr/local/bin/piper" ]; then
    echo "Detected old Piper directory install in /usr/local/bin/piper; fixing it..."
    sudo rm -rf "$PIPER_INSTALL_DIR"
    sudo mv /usr/local/bin/piper "$PIPER_INSTALL_DIR"
    sudo ln -sf "$PIPER_INSTALL_DIR/piper" /usr/local/bin/piper
    sudo chmod +x "$PIPER_INSTALL_DIR/piper" /usr/local/bin/piper
    echo "✓ Piper installation repaired"
fi

# Step 6: Download Piper voice
echo ""
echo -e "${GREEN}[6/7] Downloading Piper voice model...${NC}"

VOICE_DIR="$HOME/piper-voices"
VOICE_NAME="en_US-lessac-medium"

mkdir -p "$VOICE_DIR"

if [ ! -f "$VOICE_DIR/${VOICE_NAME}.onnx" ]; then
    echo "Downloading voice model (this may take a few minutes)..."
    wget -q -O "$VOICE_DIR/${VOICE_NAME}.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/${VOICE_NAME}.onnx"
    wget -q -O "$VOICE_DIR/${VOICE_NAME}.onnx.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/${VOICE_NAME}.onnx.json"
    echo "✓ Voice model downloaded"
else
    echo "✓ Voice model already exists"
fi

# Step 7: Create .env file
echo ""
echo -e "${GREEN}[7/7] Setting up configuration...${NC}"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env and add your GEMINI_API_KEY${NC}"
    echo "  Run: nano .env"
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
mkdir -p logs models sounds

# Create placeholder sound files (beeps)
if [ ! -f "sounds/wake.wav" ]; then
    # Generate a simple wake sound using Python
    python3 -c "
import struct
import wave
sample_rate = 44100
duration = 0.15
frequency = 880
samples = int(sample_rate * duration)
with wave.open('sounds/wake.wav', 'w') as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(sample_rate)
    for i in range(samples):
        t = i / sample_rate
        amp = 0.5 * (1 - i/samples)
        import math
        value = int(amp * 32767 * math.sin(2 * math.pi * frequency * t))
        f.writeframes(struct.pack('<h', value))
print('✓ Wake sound created')
"
fi

# Test audio
echo ""
echo -e "${GREEN}Testing audio setup...${NC}"
echo "Playing test sound..."
if aplay sounds/wake.wav 2>/dev/null; then
    echo "✓ Audio playback working"
else
    echo -e "${YELLOW}Audio playback test failed. Check your audio configuration.${NC}"
fi

# Pre-download Whisper model
echo ""
echo -e "${GREEN}Pre-downloading Whisper model...${NC}"
echo "This may take a few minutes on first run..."
python3 -c "
from faster_whisper import WhisperModel
print('Downloading tiny.en model...')
model = WhisperModel('tiny.en', device='cpu', compute_type='int8')
print('✓ Whisper model ready')
" || echo -e "${YELLOW}Whisper model will download on first use${NC}"

# Done!
echo ""
echo "=================================================="
echo -e "${GREEN}   Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Add your Gemini API key to .env:"
echo "   nano .env"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the assistant:"
echo "   python main.py"
echo ""
echo "4. For test mode (no wake word):"
echo "   python main.py --test"
echo ""
echo "5. For debug mode:"
echo "   python main.py --debug"
echo ""
echo "Enjoy your voice assistant!"
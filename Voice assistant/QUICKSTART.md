# BUDDY Voice Assistant - Quick Start Guide

## 5-Minute Setup on Raspberry Pi

### 1. Transfer Project to Raspberry Pi

```bash
# From your development machine, copy files via SCP:
scp -r alexa/ pi@<raspberry-pi-ip>:~/buddy/

# Or clone from git (if you pushed to a repo)
git clone <your-repo-url> ~/buddy
```

### 2. SSH into Raspberry Pi

```bash
ssh pi@<raspberry-pi-ip>
cd ~/buddy
```

### 3. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

### 4. Configure API Key

```bash
# Edit the .env file
nano .env

# Add your Gemini API key:
GEMINI_API_KEY=your_actual_api_key_here

# Save: Ctrl+O, Enter, Ctrl+X
```

Get your API key from: https://makersuite.google.com/app/apikey

### 5. Test Components

```bash
source venv/bin/activate
python test_components.py
```

### 6. Run the Assistant

```bash
# Normal mode (with wake word)
python main.py

# Test mode (without wake word)
python main.py --test

# Debug mode
python main.py --debug
```

---

## Quick Troubleshooting

### No Audio Input
```bash
# List microphones
arecord -l

# Test recording
arecord -d 3 test.wav
aplay test.wav
```

### No Audio Output
```bash
# List speakers
aplay -l

# Test with built-in
speaker-test -t wav -c 2
```

### Whisper Model Errors
```bash
# Re-download model
python -c "from faster_whisper import WhisperModel; WhisperModel('tiny.en')"
```

### API Key Issues
```bash
# Verify .env file
cat .env | grep GEMINI

# Test API connection
python test_components.py
```

---

## Usage Examples

1. **Wake the assistant**: Say "Hey Buddy"
2. **Ask a question**: "What's the capital of Japan?"
3. **Local commands**: "What time is it?"
4. **Set timer**: "Set a timer for 10 minutes"

---

## Auto-Start on Boot (Optional)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/buddy.service
```

Add:
```ini
[Unit]
Description=BUDDY Voice Assistant
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/buddy
ExecStart=/home/pi/buddy/venv/bin/python /home/pi/buddy/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable buddy
sudo systemctl start buddy
```

---

## Performance Tips

1. **Use USB microphone** for better audio quality
2. **Increase swap** if running out of memory:
   ```bash
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```
3. **Monitor performance**: `htop`
4. **Check logs**: `tail -f logs/buddy.log`

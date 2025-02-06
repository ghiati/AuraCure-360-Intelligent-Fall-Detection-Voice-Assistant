# AuraCure 360°: Intelligent Fall Detection & Voice Assistant

## Overview
AuraCure 360° is a modular, intelligent assistant that integrates **fall detection** and **natural voice interaction** to enhance patient safety and provide real-time emergency support. The system utilizes **deep learning-based fall detection**, **speech recognition**, **text-to-speech synthesis**, and **automated WhatsApp alerts** via the **Twilio API**. 

## Features
- **Fall Detection**: Utilizes a trained deep learning model (`model.h5`) for real-time fall detection.
- **Emergency Alerts**: Sends an automated **WhatsApp message** to a support team when a fall is detected.
- **Voice Assistant**:
  - **Speech-to-Text (STT)**: Converts spoken words into text.
  - **Text-to-Speech (TTS)**: Responds naturally to user queries.
  - **LLM Integration**: Uses a **Groq-powered AI model** for intelligent responses.
- **Flask Web Server**: Handles fall detection notifications and alerts.
- **Real-Time Audio Streaming**: Efficiently records and processes user speech.

## Project Structure
```
assistant/
│
├── app.py                  # Main entry point for the assistant
├── config.py                # Configuration file for API keys and constants
│
├── audio/                   # Audio processing modules
│   ├── audio_streamer.py    # Audio streaming logic
│   ├── tts.py               # Text-to-speech conversion
│   └── stt.py               # Speech-to-text conversion
│
├── llm/                     # Large Language Model (LLM) integration
│   ├── groq_client.py       # API client for Groq AI model
│   └── prompt_manager.py    # Prompt handling and response generation
│
├── messaging/               # Messaging modules
│   └── twilio_client.py     # WhatsApp message handler
│
├── vision/                  # Fall detection model
│   ├── fall_detection.py    # Fall detection logic (runs in a separate terminal, designed for video input but can be modified for real-time camera detection)
│   ├── yolov5s.pt           # YOLOv5 model for vision-based detection
│
├── utils/                   # Utility functions
│   └── helpers.py           # Miscellaneous helper functions
│
├── model.h5                 # Trained deep learning model for fall detection
├── video.avi                # Sample video for fall detection testing
├── output.wav               # Generated audio responses
├── requirements.txt         # Required dependencies
├── README.md                # Project documentation
└── scaling_params.json      # Model scaling parameters
```

## Installation
### 1. Clone the Repository
Open a terminal in **Ubuntu** and run:
```bash
git clone https://github.com/ghiati/AuraCure-360-Intelligent-Fall-Detection-Voice-Assistant.git
cd assistant
```

### 2. Install Dependencies
Ensure you have **Python 3.10.12** installed. If not, install it:
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```
Then create a virtual environment and install dependencies:
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Set Up Configuration
Update `config.py` with your Groq AI API key:
```python
# Groq AI API Key
GROQ_API_KEY = "your_groq_api_key"
```
Additionally, update the Twilio configuration directly in `twilio_client.py` by replacing the placeholders with your actual credentials:
```python
# Twilio API Credentials (Modify directly in twilio_client.py)
TWILIO_ACCOUNT_SID = "your_twilio_sid"
TWILIO_AUTH_TOKEN = "your_twilio_auth_token"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
HELP_RECIPIENT_NUMBER = "whatsapp:+your_number"
```

### 4. Run the Assistant
#### Open two separate terminals in **Ubuntu**:
##### **Terminal 1:** Start the fall detection module
```bash
source venv/bin/activate
python3 vision/fall_detection.py
```
> ⚠️ **Note:** The `fall_detection.py` script is designed to process video files for fall detection, but it can be modified to detect falls in real-time using a camera feed.

##### **Terminal 2:** Start the main assistant
```bash
source venv/bin/activate
python3 app.py
```

## How It Works
### 1. **Fall Detection**
- The system continuously monitors **camera feed**
- `fall_detection.py` runs **in a separate terminal** and detects falls using `model.h5`.
- By default, it processes video files for fall detection, but it can be modified to work with a real-time camera feed.
- When a fall is detected, it sends an HTTP request to `/fall_detected`.
- The assistant processes the alert and sends a **WhatsApp message** to the support team.

### 2. **Voice Interaction**
- The assistant listens for user speech and converts it to text.
- If a **help request** is detected (e.g., "I need help"), an alert is triggered.
- Otherwise, it generates an AI-powered response using the **Groq LLM** and speaks it back.

## API Endpoints
| Endpoint | Method | Description |
|----------|--------|--------------|
| `/fall_detected` | `POST` | Handles fall detection alerts and triggers a WhatsApp message |

## Future Enhancements
- **Multi-user support**: Extend fall detection for multiple individuals.
- **Occlusion handling**: Improve detection accuracy in cluttered environments.
- **Privacy-focused processing**: Implement **on-device AI** to reduce reliance on cloud services.

## Contributors
- **Contributors**: El mzalni Hajar , Elasri abdesamad , Moutia Salma , GHIATI mustapha

## License
This project is licensed under the MIT License.

---
**Made with ❤️ for patient safety and AI-driven assistance.**


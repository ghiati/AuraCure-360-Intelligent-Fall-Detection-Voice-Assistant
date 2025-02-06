import threading
import time
import wave
import speech_recognition as sr
import pyaudio
from audio.audio_streamer import AudioStreamer
from audio.tts import TextToSpeech
from audio.stt import SpeechToText
from llm.groq_client import get_groq_client
from llm.prompt_manager import generate_response
from messaging.twilio_client import send_whatsapp_message
from utils.helpers import is_help_request
from flask import Flask, request
import requests
import os

# Flask app for fall detection communication
app = Flask(__name__)

class VoiceAssistant:
    def __init__(self):
        self.audio_streamer = AudioStreamer()
        self.tts = TextToSpeech()
        self.stt = SpeechToText()
        self.groq_client = get_groq_client()
        self.speaking = threading.Event()
        self.speaking.set()
        self.fall_alert_count = 0  # Counter for fall alerts
        self.max_fall_alerts = 2   # Maximum number of fall alerts to send
    
    def play_audio(self, filename):
        """Play audio file."""
        CHUNK = 1024
        try:
            with wave.open(filename, 'rb') as wf:
                p = pyaudio.PyAudio()
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                              channels=wf.getnchannels(),
                              rate=wf.getframerate(),
                              output=True)
                
                self.audio_streamer.is_recording = False  # Pause recording while speaking
                
                data = wf.readframes(CHUNK)
                while data:
                    stream.write(data)
                    data = wf.readframes(CHUNK)
                
                stream.stop_stream()
                stream.close()
                p.terminate()
                
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            self.audio_streamer.is_recording = True  # Resume recording
            self.speaking.set()
    
    def speak(self, text):
        """Generate and play text-to-speech."""
        try:
            self.speaking.clear()
            output_file = self.tts.speak(text)
            threading.Thread(target=self.play_audio, args=(output_file,)).start()
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            self.speaking.set()
    
    def save_audio(self, audio_data, filename="temp.wav"):
        """Save audio data to WAV file."""
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.audio_streamer.channels)
            wf.setsampwidth(self.audio_streamer.audio.get_sample_size(self.audio_streamer.format))
            wf.setframerate(self.audio_streamer.rate)
            wf.writeframes(audio_data)
        return filename

    def handle_fall_detection(self):
        """Handle fall detection by sending a WhatsApp message."""
        if self.fall_alert_count < self.max_fall_alerts:
            help_message = "Fall detected! Please check on the person immediately."
            if send_whatsapp_message(help_message):
                self.speak("I've detected a fall and sent an alert to the support team.")
                self.fall_alert_count += 1  # Increment the counter
            else:
                self.speak("Sorry, I couldn't send the fall alert. Please try again later.")
        else:
            print("Maximum fall alerts (5) have already been sent.")

    def run(self):
        """Main loop for the voice assistant."""
        print("[STATUS] Initializing voice assistant...")
        self.audio_streamer.start_streaming()
        print("[STATUS] Ready! Speak naturally and pause when you're done.")
        
        try:
            while True:
                self.speaking.wait()
                
                # Get next complete phrase
                audio_data = self.audio_streamer.get_next_phrase()
                if audio_data:
                    # Save audio to temporary file
                    temp_file = self.save_audio(audio_data)
                    
                    try:
                        # Transcribe audio to text
                        prompt = self.stt.transcribe(temp_file)
                        print("You said:", prompt)
                        
                        # Check if the user is asking for help
                        if is_help_request(prompt):
                            help_message = "This is an automated help message. Please assist the user."
                            if send_whatsapp_message(help_message):
                                self.speak("I've sent a help request to the support team. They will contact you shortly.")
                            else:
                                self.speak("Sorry, I couldn't send the help request. Please try again later.")
                        else:
                            # Generate a normal response
                            response = generate_response(prompt, self.groq_client)
                            if response:
                                print("AI Response:", response)
                                self.speak(response)
                            
                    except sr.UnknownValueError:
                        pass  # Ignore unrecognized audio
                    finally:
                        # Clean up temporary file
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                
        except KeyboardInterrupt:
            print("\n[STATUS] Stopping the assistant...")
        finally:
            self.audio_streamer.stop_streaming()

# Flask endpoint to handle fall detection
@app.route('/fall_detected', methods=['POST'])
def fall_detected():
    assistant.handle_fall_detection()
    return "Fall alert handled", 200

if __name__ == "__main__":
    # Start the Flask server in a separate thread
    assistant = VoiceAssistant()
    flask_thread = threading.Thread(target=lambda: app.run(port=5000))
    flask_thread.daemon = True
    flask_thread.start()

    # Run the main assistant
    assistant.run()
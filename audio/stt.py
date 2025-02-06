# audio/stt.py
import speech_recognition as sr

class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def transcribe(self, audio_file):
        """Transcribe audio file to text."""
        with sr.AudioFile(audio_file) as source:
            audio = self.recognizer.record(source)
        return self.recognizer.recognize_google(audio)
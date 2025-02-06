# audio/tts.py
from TTS.api import TTS

class TextToSpeech:
    def __init__(self):
        self.tts = TTS(model_name="tts_models/en/ljspeech/glow-tts", progress_bar=False, gpu=False)
    
    def speak(self, text, output_file="output.wav"):
        """Generate and save speech to a file."""
        self.tts.tts_to_file(text=text, file_path=output_file)
        return output_file
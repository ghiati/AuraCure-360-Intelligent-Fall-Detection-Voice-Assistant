# audio/audio_streamer.py
import pyaudio
import queue
import audioop
import collections

class AudioStreamer:
    def __init__(self):
        self.chunk_size = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.silence_threshold = 1000
        self.silence_chunks = int(self.rate / self.chunk_size * 1.0)  # 1.0 seconds of silence
        self.speech_chunks = int(self.rate / self.chunk_size * 0.3)   # 0.3 seconds of speech
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        
        # Buffer for storing audio data
        self.buff = collections.deque(maxlen=self.silence_chunks)
        self.recording = []
        self.is_speaking = False
        
    def start_streaming(self):
        """Start streaming audio from microphone"""
        self.is_recording = True
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        self.stream.start_stream()
        
    def stop_streaming(self):
        """Stop streaming audio"""
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Handle incoming audio data"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def get_next_phrase(self):
        """Get the next complete phrase from audio stream"""
        while self.is_recording:
            # Get chunk from queue
            try:
                chunk = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
                
            # Calculate volume
            volume = audioop.rms(chunk, 2)
            
            # Add chunk to buffer
            self.buff.append(chunk)
            
            if volume > self.silence_threshold:
                # Speech detected
                if not self.is_speaking:
                    # Start of speech - include buffer
                    self.recording = list(self.buff)
                self.is_speaking = True
                self.recording.append(chunk)
            elif self.is_speaking:
                # Possible end of speech
                self.recording.append(chunk)
                if len(self.buff) == self.silence_chunks:
                    # Enough silence - return the recording
                    self.is_speaking = False
                    return b''.join(self.recording)
        return None
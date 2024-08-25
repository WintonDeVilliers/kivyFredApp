import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import wave
import io

# Set the window size
Window.size = (300, 600)

class VoiceMemoApp(App):
    def build(self):
        self.recognizer = sr.Recognizer()
        self.audio_data = None
        self.recording = False  # To track recording state
        
        # Create a vertical box layout with spacing
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Create the record button
        self.record_button = Button(text="Record", size_hint=(1, 0.1))
        self.record_button.bind(on_press=self.start_recording)
        
        # Create the stop button
        self.stop_button = Button(text="Stop", size_hint=(1, 0.1))
        self.stop_button.bind(on_press=self.stop_recording)
        
        # Create the text input box
        self.text_box = TextInput(size_hint=(1, 0.8), readonly=True, font_size=20, halign='left', padding_y=[10, 10], multiline=True)
        
        # Add widgets to the layout
        layout.add_widget(self.record_button)
        layout.add_widget(self.stop_button)
        layout.add_widget(self.text_box)
        
        return layout
    
    def start_recording(self, instance):
        if not self.recording:
            self.recording = True
            self.audio_data = sd.rec(int(60 * 44100), samplerate=44100, channels=2, dtype='int16')  # Record for a max of 60 seconds
            self.text_box.text = "Recording..."
    
    def stop_recording(self, instance):
        if self.recording:
            sd.stop()  # Stop the recording
            self.recording = False
            self.transcribe_audio()
    
    def transcribe_audio(self):
        if self.audio_data is not None:
            # Convert the recorded audio to WAV format in memory
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(2)  # Stereo
                wav_file.setsampwidth(2)  # Sample width in bytes, 16-bit is 2 bytes
                wav_file.setframerate(44100)  # Sample rate
                wav_file.writeframes(self.audio_data.tobytes())

            wav_io.seek(0)
            audio_file = sr.AudioFile(wav_io)
            with audio_file as source:
                audio_data = self.recognizer.record(source)
                try:
                    text = self.recognizer.recognize_google(audio_data)
                    self.text_box.text = text
                except sr.UnknownValueError:
                    self.text_box.text = "Google Speech Recognition could not understand audio"
                except sr.RequestError as e:
                    self.text_box.text = f"Could not request results; {e}"

if __name__ == '__main__':
    VoiceMemoApp().run()

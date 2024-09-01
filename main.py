import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
import sounddevice as sd
import numpy as np
import wave
import io
from kivy.core.audio import SoundLoader
import speech_recognition as sr
import replicate

# Set the window size
Window.size = (300, 600)

class SimpleAudioVisualizer(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.amplitude = 0
        Clock.schedule_interval(self.update_visualization, 1 / 30)  # Update at 30 FPS

    def update_visualization(self, dt):
        self.canvas.clear()
        with self.canvas:
            Color(0, 0.5, 0.5, 1)  # Light blue color for visualization
            rect_width = self.width * 0.8  # Width of the bar
            rect_height = self.height * 0.5 * self.amplitude  # Height based on amplitude
            rect_pos = (self.width * 0.1, self.height * 0.88)  # Centered position
            Rectangle(size=(rect_width, rect_height), pos=rect_pos)

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude


class VoiceMemoApp(App):
    def build(self):
        self.audio_data = None
        self.recording = False  # To track recording state
        self.recognizer = sr.Recognizer()  # Initialize recognizer

        # Create a vertical box layout with spacing
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Create the text input box
        self.text_box = TextInput(size_hint=(1, 0.7), readonly=True, font_size=20, halign='left', padding_y=[10, 10], multiline=True)

        # Create a simple audio visualizer widget
        self.visualizer = SimpleAudioVisualizer(size_hint=(1, 0.3))

        # Create a horizontal box layout for the buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)

        # Create the record button with default green color
        self.record_button = Button(
            text="Record",
            size_hint=(None, None),
            size=(80, 80),  # Smaller size for equidistant layout
            background_normal='',
            background_color=(0, 0.5, 0, 1),
            font_size=18
        )
        self.record_button.bind(on_press=self.start_recording)
        self.record_button.bind(on_release=self.release_record_button)

        # Create the stop button with default gray color
        self.stop_button = Button(
            text="Stop",
            size_hint=(None, None),
            size=(80, 80),  # Smaller size for equidistant layout
            background_normal='',
            background_color=(0.5, 0.5, 0.5, 1),
            font_size=18
        )
        self.stop_button.bind(on_press=self.stop_recording)
        self.stop_button.bind(on_release=self.release_stop_button)

        # Create the pause button with default gray color
        self.pause_button = Button(
            text="Pause",
            size_hint=(None, None),
            size=(80, 80),  # Smaller size for equidistant layout
            background_normal='',
            background_color=(0.5, 0.5, 0.5, 1),
            font_size=18
        )
        # No functionality for pause yet, but we can bind it later
        # self.pause_button.bind(on_press=self.pause_button)

        # Add widgets to the button layout
        button_layout.add_widget(self.record_button)
        button_layout.add_widget(self.pause_button)
        button_layout.add_widget(self.stop_button)

        # Add widgets to the main layout
        layout.add_widget(self.text_box)
        layout.add_widget(self.visualizer)
        layout.add_widget(button_layout)

        # Load sound effects
        self.record_sound = SoundLoader.load('record_sound.mp3')
        self.stop_sound = SoundLoader.load('stop_sound.mp3')

        return layout

    def start_recording(self, instance):
        if not self.recording:
            self.recording = True
            self.audio_stream = sd.InputStream(
                samplerate=44100, channels=1, callback=self.audio_callback)
            self.audio_stream.start()
            self.audio_data = sd.rec(int(120 * 44100), samplerate=44100, channels=2, dtype='int16')

            self.text_box.text = "Recording..."
            self.record_button.background_color = (0, 1, 0, 1)  # Change to green to indicate recording
            self.stop_button.background_color = (1, 0, 0, 1)  # Change stop button to red

            # Play sound effect
            if self.record_sound:
                self.record_sound.play()

            # Animation for press effect
            Animation(size=(90, 90), d=0.1).start(self.record_button)

    def release_record_button(self, instance):
        Animation(size=(100, 100), d=0.1).start(self.record_button)  # Revert size after release

    def stop_recording(self, instance):
        if self.recording:
            sd.stop()  # Stop the recording
            self.recording = False
            self.record_button.background_color = (0, 0.5, 0, 1)  # Change back to original green color
            self.stop_button.background_color = (0.5, 0.5, 0.5, 1)  # Change stop button back to original gray color

            # Play sound effect
            if self.stop_sound:
                self.stop_sound.play()

            # Animation for press effect
            Animation(size=(90, 90), d=0.1).start(self.stop_button)

            if self.audio_stream:
                self.audio_stream.stop()
                self.audio_stream.close()

            self.transcribe_audio()

    def release_stop_button(self, instance):
        Animation(size=(100, 100), d=0.1).start(self.stop_button)  # Revert size after release

    def audio_callback(self, indata, frames, time, status):
        # Get the peak amplitude and normalize it
        amplitude = np.abs(indata).mean()
        normalized_amplitude = np.clip(amplitude, 0, 1)

        print(f"Amplitude: {amplitude}, Normalized Amplitude: {normalized_amplitude}")  # Debug print

        # Set amplitude to the visualizer
        self.visualizer.set_amplitude(normalized_amplitude)

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
                    transcribed_text = self.recognizer.recognize_google(audio_data)
                    self.text_box.text = transcribed_text
                    self.summarize_text(transcribed_text)
                except sr.UnknownValueError:
                    self.text_box.text = "Google Speech Recognition could not understand audio"
                except sr.RequestError as e:
                    self.text_box.text = f"Could not request results; {e}"

    def summarize_text(self, transcribed_text):
        # Parameters specific to the Meta LLaMA model for summarization
        input_data = {
            "top_p": 0.9,
            "prompt": f"Summarize the following text:\n\n{transcribed_text}",
            "min_tokens": 0,
            "temperature": 0.6,
            "prompt_template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are a helpful assistant<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
            "presence_penalty": 1.15
        }

        # Make a request to the Meta LLaMA model using Replicate API
        try:
            output = replicate.run(
                "meta/meta-llama-3-70b-instruct",
                input=input_data
            )
            summarized_text = "".join(output)
            self.text_box.text = summarized_text
        except Exception as e:
            print(f"Error during summarization: {str(e)}")
            self.text_box.text = "Failed to summarize the text."

if __name__ == "__main__":
    VoiceMemoApp().run()

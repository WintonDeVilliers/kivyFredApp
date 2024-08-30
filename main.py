import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color, Rectangle
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.image import Image  # Import the Image widget for GIF
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import wave
import io

# Set the window size
Window.size = (300, 600)

class WaveformWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.amplitudes = np.zeros(100)
        Clock.schedule_interval(self.update_waveform, 1 / 30)  # Update at 30 FPS
        
        # Create an Image widget for the GIF, initially hidden
        self.gif = Image(source='feedback.gif', anim_delay=0.1, opacity=0, allow_stretch=True, keep_ratio=False)
        self.add_widget(self.gif)

    def update_waveform(self, dt):
        self.canvas.clear()
        with self.canvas:
            # Background shading
            Color(0, 0, 0.2, 0.5)  # Dark blue with some transparency
            
            # Define the size and position for the background rectangle
            rect_width = self.width * 1.5  # 90% of widget width
            rect_height = self.height * 0.3  # 90% of widget height
            rect_pos = (self.width * 0.002, self.height * 0.8)  # Centered with padding
            Rectangle(size=(rect_width, rect_height), pos=rect_pos)
            
            # Update GIF position and size to fit inside the dark blue rectangle
            self.gif.size = (rect_width, rect_height)
            self.gif.pos = rect_pos
            
            # Drawing the waveform with a color gradient
            if self.amplitudes is not None:
                points = []  # Clear points
                for i, amp in enumerate(self.amplitudes):
                    # Calculate dynamic color based on amplitude
                    red = 1 - amp  # Less amplitude, more red
                    green = amp    # More amplitude, more green
                    blue = 0.2     # Static blue component

                    Color(red, green, blue, 1)  # Dynamic color

                    # Calculate the position for each point
                    x = i / float(len(self.amplitudes)) * self.width
                    y = self.height / 2 + np.sin(i) * amp * self.height / 2 * 0.8  # Reduced amplitude scale to prevent overflow

                    # Append points
                    points.extend([x, y])

                # Draw line only if there are enough points
                if len(points) > 2:
                    Line(points=points, width=2)

    def set_amplitudes(self, amplitudes):
        print("Updating amplitudes:", amplitudes)  # Debug print
        self.amplitudes = amplitudes

    def show_gif(self):
        # Method to show the GIF when called
        self.gif.opacity = 1

    def hide_gif(self):
        # Method to hide the GIF
        self.gif.opacity = 0

class VoiceMemoApp(App):
    def build(self):
        self.recognizer = sr.Recognizer()
        self.audio_data = io.BytesIO()  # Initialize an in-memory byte buffer for audio data
        self.recording = False  # To track recording state

        # Create a vertical box layout with spacing
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Create the text input box
        self.text_box = TextInput(size_hint=(1, 0.7), readonly=True, font_size=20, halign='left', padding_y=[10, 10], multiline=True)

        # Create a waveform widget with reduced size hint
        self.waveform = WaveformWidget(size_hint=(2, 1), pos_hint={'top': 1})

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
        self.pause_button.bind(on_press=self.pause_recording)

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
        
        # Add widgets to the button layout
        button_layout.add_widget(self.record_button)
        button_layout.add_widget(self.pause_button)
        button_layout.add_widget(self.stop_button)
        
        # Add widgets to the main layout
        layout.add_widget(self.text_box)
        layout.add_widget(self.waveform)
        layout.add_widget(button_layout)
        
        # Load sound effects
        self.record_sound = SoundLoader.load('record_sound.mp3')
        self.stop_sound = SoundLoader.load('stop_sound.mp3')

        return layout
    
    def start_recording(self, instance):
        if not self.recording:
            self.recording = True
            self.audio_stream = sd.InputStream(samplerate=44100, channels=1, callback=self.audio_callback)
            self.audio_stream.start()
            self.text_box.text = "Recording..."
            
            # Change record button color to green to indicate recording
            record_color_animation = Animation(background_color=(0, 1, 0, 1), duration=0.5)
            record_color_animation.start(self.record_button)
            
            # Change stop button color to red to indicate it's active
            stop_color_animation = Animation(background_color=(1, 0, 0, 1), duration=0.5)
            stop_color_animation.start(self.stop_button)
            
            # Play sound effect if record_sound is loaded
            if self.record_sound:
                self.record_sound.play()
            
            # Animation for press effect
            Animation(size=(70, 70), d=0.1).start(self.record_button)

    def release_record_button(self, instance):
        Animation(size=(80, 80), d=0.1).start(self.record_button)  # Revert size after release

    def pause_recording(self, instance):
        # This will handle pause functionality later
        pass
    
    def stop_recording(self, instance):
        if self.recording:
            sd.stop()  # Stop the recording
            self.recording = False
            self.audio_stream.stop()
            self.audio_stream.close()
            
            # Reset buffer position for reading
            self.audio_data.seek(0)
            
            self.record_button.background_color = (0, 0.5, 0, 1)  # Change back to original green color
            
            # Use animation to change stop button color back to blue smoothly
            stop_color_animation = Animation(background_color=(0.5, 0.5, 0.5, 1), duration=0.5)
            stop_color_animation.start(self.stop_button)
            
            # Play sound effect if stop_sound is loaded
            if self.stop_sound:
                self.stop_sound.play()
            
            # Animation for press effect
            Animation(size=(70, 70), d=0.1).start(self.stop_button)
            
            self.waveform.show_gif()  # Show GIF after stopping recording
            Clock.schedule_once(lambda dt: self.waveform.hide_gif(), 3)  # Hide GIF after 3 seconds

            self.transcribe_audio()

    def release_stop_button(self, instance):
        Animation(size=(80, 80), d=0.1).start(self.stop_button)  # Revert size after release

    def audio_callback(self, indata, frames, time, status):
        if self.recording:
            # Write audio data to the buffer
            self.audio_data.write(indata.tobytes())
            
            # Get the peak amplitude and normalize it
            amplitude = np.abs(indata).mean()
            normalized_amplitude = np.clip(amplitude, 0, 1)
            
            print(f"Amplitude: {amplitude}, Normalized: {normalized_amplitude}")  # Debug print
            
            # Update the waveform widget
            self.waveform.set_amplitudes(np.ones(100) * normalized_amplitude)

    def transcribe_audio(self):
        if self.audio_data is not None and self.audio_data.getbuffer().nbytes > 0:
            try:
                # Convert the recorded audio to WAV format in memory
                wav_io = io.BytesIO()
                with wave.open(wav_io, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono audio
                    wav_file.setsampwidth(2)  # Sample width in bytes, 16-bit is 2 bytes
                    wav_file.setframerate(44100)  # Sample rate
                    wav_file.writeframes(self.audio_data.getvalue())

                wav_io.seek(0)
                audio_file = sr.AudioFile(wav_io)

                with audio_file as source:
                    audio_data = self.recognizer.record(source)
                    try:
                        # Transcribe audio data using Google Speech Recognition
                        text = self.recognizer.recognize_google(audio_data)
                        self.text_box.text = text
                    except sr.UnknownValueError:
                        self.text_box.text = "Google Speech Recognition could not understand audio"
                    except sr.RequestError as e:
                        self.text_box.text = f"Could not request results; {e}"
            except Exception as e:
                self.text_box.text = f"An error occurred: {e}"
        else:
            self.text_box.text = "No audio data available for transcription."

if __name__ == '__main__':
    VoiceMemoApp().run()

import sounddevice as sd
import queue
import vosk
import json
import numpy as np
import samplerate
import threading
from typing import Optional, List, Tuple, cast


class VoskRecognizer:
    def __init__(self, model_path: str = "model/vosk-model-de-tuda-0.6-900k", silence_threshold: float = 0.0015):
        self.MODEL_PATH: str = model_path
        self.VOSK_RATE: int = 16000
        self.SILENCE_THRESHOLD: float = silence_threshold

        self.devices = sd.query_devices()
        self.device_index: Optional[int] = None
        self.sample_rate: Optional[int] = None
        self.chunk_size: Optional[int] = None

        self.model: Optional[vosk.Model] = None
        self.recognizer: Optional[vosk.KaldiRecognizer] = None
        self.q: queue.Queue = queue.Queue()
        self.resampler: samplerate.Resampler = samplerate.Resampler('sinc_fastest')

        self.partial_displayed: str = ""
        self.latest_text: str = ""
        self.all_text: List[str] = []
        self._stop_flag: threading.Event = threading.Event()

    def list_input_devices(self) -> List[Tuple[int, str]]:
        """Return a list of available input devices with indices."""
        result: List[Tuple[int, str]] = []
        for i, d in enumerate(self.devices):
            device_info = cast(dict, d)
            if device_info.get('max_input_channels', 0) > 0:
                result.append((i, device_info.get('name', 'Unknown')))
        return result

    def select_device(self, device_index: int) -> None:
        """Select input device by index."""
        if device_index < 0 or device_index >= len(self.devices):
            raise ValueError("Invalid device index")
        self.device_index = device_index
        info = cast(dict, sd.query_devices(self.device_index, 'input'))
        self.sample_rate = int(info.get('default_samplerate', 16000))
        self.chunk_size = int(self.sample_rate * 0.05)  # 50ms blocks

    def load_model(self) -> None:
        """Load Vosk speech recognition model."""
        self.model = vosk.Model(self.MODEL_PATH)
        self.recognizer = vosk.KaldiRecognizer(self.model, self.VOSK_RATE)

    def audio_callback(self, indata: np.ndarray, _frames: int, _time, status) -> None:
        """Callback for sounddevice input stream."""
        if status and status.input_overflow:
            return
        audio = np.frombuffer(indata, dtype=np.int16).astype(np.float32) / 32768.0
        energy = float(np.mean(np.abs(audio)))
        if energy < self.SILENCE_THRESHOLD:
            return
        assert self.sample_rate is not None
        audio_16k = self.resampler.process(audio, self.VOSK_RATE / self.sample_rate)
        audio_bytes = (audio_16k * 32768.0).astype(np.int16).tobytes()
        self.q.put(audio_bytes)

    def start_listening(self) -> None:
        """Start the audio stream and recognition loop in the current thread."""
        if self.device_index is None:
            raise RuntimeError("Device not selected. Call select_device() first.")
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        self._stop_flag.clear()

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                dtype='int16',
                channels=1,
                callback=self.audio_callback,
                device=self.device_index
            ):
                while not self._stop_flag.is_set():
                    if not self.q.empty():
                        data = self.q.get()
                        assert self.recognizer is not None
                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            text = result.get("text", "")
                            if text:
                                self.latest_text = text
                                self.all_text.append(text)
                            self.partial_displayed = ""
                        else:
                            partial = json.loads(self.recognizer.PartialResult())
                            partial_text = partial.get("partial", "")
                            self.partial_displayed = partial_text
        except Exception as e:
            raise e

    def stop_listening(self) -> None:
        """Stop the recognition loop."""
        self._stop_flag.set()

    def get_latest_text(self) -> str:
        """Return the latest final recognized text."""
        return self.latest_text

    def get_all_text(self) -> List[str]:
        """Return all final recognized texts."""
        return self.all_text

    def get_partial_text(self) -> str:
        """Return the current partial recognition text."""
        return self.partial_displayed

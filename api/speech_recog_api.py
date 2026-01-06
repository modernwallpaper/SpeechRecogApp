import sounddevice as sd
import queue
import vosk
from transformers import logging
import json
import numpy as np
import samplerate
import threading
import time
from typing import Optional, List, Tuple, cast
from pathlib import Path
import importlib.util

BASE_DIR = Path(__file__).resolve().parent.parent

#----------------------------------------------------------------
#                   ONLY EDIT THESE FOUR VARIABLES
#
ENABLE_PUNCT = False 
MODEL_DIR = BASE_DIR / "models" / "vosk-model-de-tuda-0.6-900k"
PUNCT_MODEL_DIR = BASE_DIR / "models" / "vosk-recasepunc-de-0.21"
LANG = "de"
#
#                   ONLY EDIT THESE FOUR VARIABLES
#----------------------------------------------------------------
# (if you dont know what you are doing)

CasePuncPredictor = None
punct_predictor = None

def load_punctuation_model():
    from transformers.models.bert.modeling_bert import BertModel
    global CasePuncPredictor, punct_predictor

    if punct_predictor is not None:
        return  # already loaded

    recase_path = PUNCT_MODEL_DIR / "recasepunc.py"
    spec = importlib.util.spec_from_file_location("recasepunc", recase_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load recasepunc from {recase_path}")

    recasepunc_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recasepunc_module)

    # CRITICAL FIX STARTS HERE
    import __main__
    if not hasattr(__main__, "WordpieceTokenizer"):
        __main__.WordpieceTokenizer = recasepunc_module.WordpieceTokenizer
    # CRITICAL FIX ENDS HERE

    CasePuncPredictor = recasepunc_module.CasePuncPredictor

    logging.set_verbosity_error()

    checkpoint_dir = PUNCT_MODEL_DIR / "checkpoint"
    print("Loading CasePuncPredictor model....")
    punct_predictor = CasePuncPredictor(str(checkpoint_dir), lang=LANG)
    print("Model loaded: ", punct_predictor.model)

class VoskRecognizer:
    def __init__(self, model_path: str = str(MODEL_DIR), silence_threshold: float = 0.0015):
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

        if ENABLE_PUNCT:
            self._punct_thread: Optional[threading.Thread] = None
            self._punct_lock = threading.Lock()
            self._punct_text: str = ""
            self._punct_queue: List[str] = []

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

        if ENABLE_PUNCT:
            load_punctuation_model()

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

    def _punct_worker(self):
        if ENABLE_PUNCT and punct_predictor is not None:
            print("[PUNCT] Punctuation worker started")
            while not self._stop_flag.is_set():
                if self._punct_queue:
                    text_to_process = self._punct_queue.pop(0)
                    print("[PUNCT] Processing text:", text_to_process)
                    try:
                        tokens = list(enumerate(punct_predictor.tokenize(text_to_process)))
                        punctuated_text = ""
                        for token, case_label, punc_label in punct_predictor.predict(tokens, lambda x: x[1]):
                            prediction = punct_predictor.map_punc_label(
                                punct_predictor.map_case_label(token[1], case_label),
                                punc_label
                            )
                            if token[1][0] != '#':
                                punctuated_text += ' ' + prediction
                            else:
                                punctuated_text += prediction
                        with self._punct_lock:
                            self._punct_text = punctuated_text.strip()
                        print("[PUNCT] Result:", self._punct_text)
                    except Exception as e:
                        print("[PUNCT ERROR]", e)
                        # fallback: just return raw text
                        with self._punct_lock:
                            self._punct_text = text_to_process
                else:
                    time.sleep(0.01)  # avoid busy wait

    def start_punctuation_thread(self):
        if ENABLE_PUNCT and (self._punct_thread is None or not self._punct_thread.is_alive()):
            self._punct_thread = threading.Thread(target=self._punct_worker, daemon=True)
            self._punct_thread.start()
            print("[PUNCT] Thread started")

    def stop_listening(self) -> None:
        """Stop the recognition loop."""
        self._stop_flag.set()

    def get_latest_text(self) -> str:
        """Return the latest final recognized text, optionally punctuated (async)."""
        if ENABLE_PUNCT and punct_predictor is not None:
            if self._punct_thread is not None:
                print("[PUNCT] _punct_thread alive?", self._punct_thread.is_alive())
            else:
                print("[PUNCT] _punct_thread not started")

            # Add the latest text to the punctuation queue
            if self.latest_text:
                # only enqueue new text
                if not self._punct_queue or self._punct_queue[-1] != self.latest_text:
                    print("[PUNCT] Adding to queue:", self.latest_text)
                    self._punct_queue.append(self.latest_text)
            
            # Return the most recent punctuated text
            with self._punct_lock:
                return self._punct_text or self.latest_text

        return self.latest_text


    def get_all_text(self) -> List[str]:
        """Return all final recognized texts."""
        return self.all_text

    def get_partial_text(self) -> str:
        """Return the current partial recognition text."""
        return self.partial_displayed

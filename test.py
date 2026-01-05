import sounddevice as sd
import numpy as np

DEVICE_INDEX = 0
SAMPLERATE = 48000

def callback(indata, frames, time, status):
    print("Audio chunk max:", np.max(indata))

with sd.InputStream(samplerate=SAMPLERATE, channels=1, device=DEVICE_INDEX, callback=callback):
    sd.sleep(5000)  # 5 seconds

import threading
import numpy as np
import pyaudiowpatch as pyaudio
from scipy.signal import butter, lfilter, lfilter_zi
import math

class AudioPulseMonitor:
    def __init__(self, callback, sample_rate_hz=25, baseline_decay=0.9, sensitivity=1.0, max_boost=0.2, bass_cutoff_hz=150):
        self.callback = callback
        self.sample_rate_hz = sample_rate_hz
        self.baseline_decay = baseline_decay
        self.sensitivity = sensitivity
        self.max_boost = max_boost
        self.bass_cutoff_hz = bass_cutoff_hz
        self.running = False
        self._baseline = 0.0

    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self.running = False

    def _get_loopback_device(self, p):
        try:
            return p.get_default_wasapi_loopback()
        except Exception:
            for loopback in p.get_loopback_device_info_generator():
                return loopback
        return None

    def _run(self):
        p = pyaudio.PyAudio()
        try:
            device = self._get_loopback_device(p)
            if device is None:
                print("[AudioPulseMonitor] no loopback")
                return

            rate = int(device["defaultSampleRate"])
            channels = device["maxInputChannels"]
            chunk = max(int(rate / self.sample_rate_hz), 1)
            chunk_duration = chunk / rate

            #bass filter
            nyquist = rate / 2
            b, a = butter(N=4, Wn=self.bass_cutoff_hz / nyquist, btype='low')
            zi = lfilter_zi(b, a) * 0.0

            baseline_alpha = 1.0 - math.exp(-chunk_duration / self.baseline_decay)

            stream = p.open(
                format=pyaudio.paFloat32,
                channels=channels,
                rate=rate,
                frames_per_buffer=chunk,
                input=True,
                input_device_index=device["index"],
            )

            while self.running:
                data = stream.read(chunk, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.float32)

                if channels > 1:
                    samples = samples.reshape(-1, channels).mean(axis=1)

                filtered, zi = lfilter(b, a, samples, zi=zi)

                rms = float(np.sqrt(np.mean(filtered ** 2))) if len(filtered) else 0.0

                self._baseline += (rms - self._baseline) * baseline_alpha
                excess = max(rms - self._baseline, 0.0)
                pulse = 1.0 + min(excess * self.sensitivity, self.max_boost)

                self.callback(pulse)

        except Exception as e:
            print(f"AudioPulseMonitor error: {e}")
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    print("[AudioPulseMonitor] stream shutdown error")
            p.terminate()
import threading
import numpy as np
import pyaudiowpatch as pyaudio
import math

class AudioPulseMonitor:
    def __init__(self, callback, sampleRateHz=25, baselineDecay=0.1, sensitivity=5.0, maxBoost=0.2, bassCutoffHz=150):
        self.callback = callback
        self.sampleRateHz = sampleRateHz
        self.baselineDecay = baselineDecay
        self.sensitivity = sensitivity
        self.maxBoost = maxBoost
        self.bassCutoffHz = bassCutoffHz
        self.running = False
        self.baseline = 0.0

    def start(self):
        self.running = True
        threading.Thread(target=self.Run, daemon=True).start()

    def Stop(self):
        self.running = False

    def GetLoopbackDevice(self, p):
        try:
            return p.get_default_wasapi_loopback()
        except Exception:
            for loopback in p.get_loopback_device_info_generator():
                return loopback
        return None

    def Run(self):
        p = pyaudio.PyAudio()
        try:
            stream = None
            device = self.GetLoopbackDevice(p)
            if device is None:
                print("[AudioPulseMonitor] no loopback")
                return

            rate = int(device["defaultSampleRate"])
            channels = device["maxInputChannels"]
            chunk = max(int(rate / self.sampleRateHz), 1)
            chunkDuration = chunk / rate

            #bass filter
            #nyquist = rate / 2
            alpha = 1.0 - math.exp(-2 * math.pi * self.bassCutoffHz / rate)
            stateFirst = 0.0
            stateSecond = 0.0
            stateThird = 0.0
            stateFourth = 0.0
            
            baselineAlpha = 1.0 - math.exp(-chunkDuration / self.baselineDecay)

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

                filtered = np.empty_like(samples)
                for i in range(len(samples)):
                    stateFirst += alpha * (samples[i] - stateFirst)
                    stateSecond += alpha * (stateFirst - stateSecond)
                    stateThird += alpha * (stateSecond - stateThird)
                    stateFourth += alpha * (stateThird - stateFourth)
                    filtered[i] = stateFourth

                rms = float(np.sqrt(np.mean(filtered ** 2))) if len(filtered) else 0.0

                self.baseline += (rms - self.baseline) * baselineAlpha
                excess = max(rms - self.baseline, 0.0)
                pulse = 1.0 + min(excess * self.sensitivity, self.maxBoost)

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
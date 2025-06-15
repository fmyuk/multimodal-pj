import pyttsx3
import requests
import tempfile
import os
import sys
import threading

class TTSManager:
    def __init__(self, engine='os', config=None):
        self.engine_name = engine
        self.config = config or {}
        self._lock = threading.Lock()
        if engine == 'os':
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', float(self.config.get('rate', 1.0)) * 200)
            self.engine.setProperty('volume', float(self.config.get('volume', 1.0)))
        # Voicevox, Aivisは後で実装

    def speak(self, text):
        if self.engine_name == 'os':
            print(f"[OS標準エンジン]: {text}")
            os.system(f'say "{text}"')
        elif self.engine_name == 'voicevox':
            print(f"[Voicevoxエンジン]: {text}")
            self.speak_voicevox(text)
        elif self.engine_name == 'aivis':
            pass
    # def speak(self, text):
    #     if self.engine_name == 'os':
    #         with self._lock:
    #             self.engine.say(text)
    #             self.engine.runAndWait()
    #     elif self.engine_name == 'voicevox':
    #         self.speak_voicevox(text)
    #     elif self.engine_name == 'aivis':
    #         # TODO: py-aivoiceで実装
    #         pass

    def speak_voicevox(self, text):
        host = self.config.get('voicevox_host', 'http://localhost:50021')
        speaker = int(self.config.get('voicevox_speaker', 1))  # デフォルト:1(四国めたん)
        try:
            # 1. audio_query
            query_resp = requests.post(f"{host}/audio_query", params={"text": text, "speaker": speaker})
            query_resp.raise_for_status()
            audio_query = query_resp.json()
            # 2. synthesis
            synth_resp = requests.post(f"{host}/synthesis", params={"speaker": speaker}, json=audio_query)
            synth_resp.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                f.write(synth_resp.content)
                wav_path = f.name
            # 3. 再生 (macOS: afplay)
            os.system(f"afplay '{wav_path}'")
            os.remove(wav_path)
        except Exception as e:
            print(f"[Voicevoxエラー]: {e}", file=sys.stderr)

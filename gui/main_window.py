from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QTextEdit, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QAction, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from capture import ScreenCapturer
from ocr import OCRProcessor
from ai_client import AIClient
from tts import TTSManager
from config import load_config
import threading

class MainWindow(QMainWindow):
    ocr_result_signal = pyqtSignal(str)
    ai_result_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("リアルタイムAIアシスタント")
        self.setGeometry(100, 100, 800, 600)
        self.config = load_config()
        self.capturer = None
        self.ocr = OCRProcessor()
        self.ai_client = AIClient(self.config)
        self.tts = TTSManager(engine=self.config['TTS'].get('engine', 'os'), config=self.config['TTS'])
        self.init_ui()
        self.ocr_result_signal.connect(self.update_ocr_result)
        self.ai_result_signal.connect(self.update_ai_result)

    def init_ui(self):
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # キャプチャ制御
        self.capture_btn = QPushButton("画面キャプチャ開始")
        self.capture_btn.setCheckable(True)
        self.capture_btn.clicked.connect(self.toggle_capture)

        # 指示入力欄
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("指示を入力してください…")

        # 応答表示欄
        self.response_edit = QTextEdit()
        self.response_edit.setReadOnly(True)

        # AIモデル選択
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.addItems(["OpenAI gpt-4o-mini", "Google Gemini", "Ollama(local)"])

        # 音声合成エンジン選択
        self.tts_combo = QComboBox()
        self.tts_combo.addItems(["Voicevox", "OS標準"])

        # 設定ボタン
        self.settings_btn = QPushButton("設定")
        self.settings_btn.clicked.connect(self.open_settings)

        # レイアウト
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("AIモデル選択:"))
        vbox.addWidget(self.ai_model_combo)
        vbox.addWidget(QLabel("音声合成エンジン選択:"))
        vbox.addWidget(self.tts_combo)
        vbox.addWidget(self.capture_btn)
        vbox.addWidget(QLabel("指示入力:"))
        vbox.addWidget(self.input_edit)
        vbox.addWidget(QLabel("AI応答:"))
        vbox.addWidget(self.response_edit)
        vbox.addWidget(self.settings_btn)

        main_widget.setLayout(vbox)

        self.input_edit.returnPressed.connect(self.handle_user_input)

    def toggle_capture(self):
        if self.capture_btn.isChecked():
            self.capture_btn.setText("画面キャプチャ停止")
            self.start_capture()
        else:
            self.capture_btn.setText("画面キャプチャ開始")
            self.stop_capture()

    def start_capture(self):
        mode = self.config['Capture'].get('mode', 'full')
        fps = int(self.config['Capture'].get('fps', '2'))
        self.capturer = ScreenCapturer(mode=mode, fps=fps)
        self.capturer.start(self.on_capture_frame)

    def stop_capture(self):
        if self.capturer:
            self.capturer.stop()
            self.capturer = None

    def on_capture_frame(self, image):
        # OCR処理を別スレッドで実行
        threading.Thread(target=self.process_frame, args=(image,), daemon=True).start()

    def process_frame(self, image):
        text = self.ocr.extract_text(image)
        self.ocr_result_signal.emit(f"[OCR結果]\n{text}")
        # 必要に応じてAI連携や自動応答もここで呼び出し可能

    def update_ocr_result(self, text):
        self.response_edit.setPlainText(text)

    def handle_user_input(self):
        user_text = self.input_edit.text()
        ocr_text = self.response_edit.toPlainText()
        prompt = f"画面の内容: {ocr_text}\nユーザー指示: {user_text}"
        self.response_edit.append("\n[AI応答] 生成中...")
        threading.Thread(target=self.ask_ai_and_speak, args=(prompt,), daemon=True).start()

    def ask_ai_and_speak(self, prompt):
        response = self.ai_client.ask(prompt)
        self.ai_result_signal.emit(f"\n[AI応答] {response}")
        # 音声合成を別スレッドで実行
        threading.Thread(target=self.tts.speak, args=(response,), daemon=True).start()

    def update_ai_result(self, text):
        self.response_edit.append(text)

    def open_settings(self):
        from gui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec_()

from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QTextEdit, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QAction, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from capture import ScreenCapturer
from ocr import OCRProcessor
from ai_client import AIClient
from tts import TTSManager, recognize_speech_from_mic
from config import load_config
import threading
# 追加: macOSウィンドウキャプチャ用
import sys
if sys.platform == 'darwin':
    import Quartz
    import AppKit

def get_window_list():
    """macOSのウィンドウ一覧を取得（タイトル付きのみ）"""
    if sys.platform != 'darwin':
        return []
    options = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
    result = []
    for w in window_list:
        title = w.get('kCGWindowName', '')
        owner = w.get('kCGWindowOwnerName', '')
        wid = w.get('kCGWindowNumber')
        bounds = w.get('kCGWindowBounds')
        if title and owner and wid and bounds:
            result.append({
                'title': f"{owner}: {title}",
                'id': wid,
                'bounds': bounds
            })
    return result

def capture_window_image(window_id):
    """指定ウィンドウIDの画像を取得（macOSのみ）"""
    if sys.platform != 'darwin':
        return None
    image = Quartz.CGWindowListCreateImage(
        Quartz.CGRectNull,
        Quartz.kCGWindowListOptionIncludingWindow,
        window_id,
        Quartz.kCGWindowImageBoundsIgnoreFraming
    )
    if not image:
        return None
    # PIL.Imageに変換
    import PIL.Image
    width = Quartz.CGImageGetWidth(image)
    height = Quartz.CGImageGetHeight(image)
    data = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(image))
    img = PIL.Image.frombuffer('RGBA', (width, height), data, 'raw', 'BGRA', 0, 1)
    return img

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

        # 音声認識制御ボタン
        self.voice_btn = QPushButton("音声入力開始")
        self.voice_btn.setCheckable(True)
        self.voice_btn.clicked.connect(self.toggle_voice_input)

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

        # ウィンドウ選択用コンボボックス（macOSのみ）
        self.window_combo = None
        self.window_list = []
        if sys.platform == 'darwin':
            self.window_combo = QComboBox()
            self.refresh_window_list()
            self.window_combo.currentIndexChanged.connect(self.on_window_selected)

        # レイアウト
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("AIモデル選択:"))
        vbox.addWidget(self.ai_model_combo)
        vbox.addWidget(QLabel("音声合成エンジン選択:"))
        vbox.addWidget(self.tts_combo)
        # ウィンドウ選択UIを追加
        if self.window_combo:
            vbox.addWidget(QLabel("キャプチャ対象ウィンドウ選択 (macOS):"))
            vbox.addWidget(self.window_combo)
        vbox.addWidget(self.capture_btn)
        vbox.addWidget(self.voice_btn)
        vbox.addWidget(QLabel("指示入力:"))
        vbox.addWidget(self.input_edit)
        vbox.addWidget(QLabel("AI応答:"))
        vbox.addWidget(self.response_edit)
        vbox.addWidget(self.settings_btn)

        main_widget.setLayout(vbox)

        self.input_edit.returnPressed.connect(self.handle_user_input)

    def refresh_window_list(self):
        self.window_list = get_window_list()
        self.window_combo.clear()
        self.window_combo.addItem("全画面キャプチャ")
        for w in self.window_list:
            self.window_combo.addItem(w['title'])
        self.selected_window_id = None

    def on_window_selected(self, idx):
        if idx == 0:
            self.selected_window_id = None
        else:
            self.selected_window_id = self.window_list[idx-1]['id']

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
        # macOSでウィンドウ選択時は専用キャプチャ
        if sys.platform == 'darwin' and hasattr(self, 'selected_window_id') and self.selected_window_id:
            self.capturer = None  # 通常キャプチャは使わない
            self._stop_capture_flag = False
            def window_capture_loop():
                import time
                while not getattr(self, '_stop_capture_flag', False):
                    img = capture_window_image(self.selected_window_id)
                    if img:
                        self.on_capture_frame(img)
                    time.sleep(1.0 / fps)
            self._window_capture_thread = threading.Thread(target=window_capture_loop, daemon=True)
            self._window_capture_thread.start()
        else:
            self.capturer = ScreenCapturer(mode=mode, fps=fps)
            self.capturer.start(self.on_capture_frame)

    def stop_capture(self):
        if sys.platform == 'darwin' and hasattr(self, '_window_capture_thread'):
            self._stop_capture_flag = True
            self._window_capture_thread = None
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

    def toggle_voice_input(self):
        if self.voice_btn.isChecked():
            self.voice_btn.setText("音声入力停止")
            self._stop_voice_flag = False
            threading.Thread(target=self.voice_input_loop, daemon=True).start()
        else:
            self.voice_btn.setText("音声入力開始")
            self._stop_voice_flag = True

    def voice_input_loop(self):
        while not getattr(self, '_stop_voice_flag', False):
            text = recognize_speech_from_mic()
            if text:
                self.input_edit.setText(text)
                self.handle_user_input()
            # 1回で止める場合はbreak、連続認識したい場合はループ
            break

    def open_settings(self):
        from gui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec_()
        # 設定画面から戻ったらウィンドウリストを再取得（macOSのみ）
        if sys.platform == 'darwin' and self.window_combo:
            self.refresh_window_list()

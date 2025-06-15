from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QHBoxLayout
from config import load_config, save_config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # AIモデル
        layout.addWidget(QLabel("AIモデル:"))
        self.ai_model_combo = QComboBox()
        self.ai_model_combo.addItems(["openai", "gemini", "ollama"])
        self.ai_model_combo.setCurrentText(self.config['AI'].get('model', 'openai'))
        layout.addWidget(self.ai_model_combo)
        # OpenAI APIキー
        layout.addWidget(QLabel("OpenAI APIキー:"))
        self.openai_key_edit = QLineEdit(self.config['AI'].get('openai_api_key', ''))
        layout.addWidget(self.openai_key_edit)
        # Gemini APIキー
        layout.addWidget(QLabel("Gemini APIキー:"))
        self.gemini_key_edit = QLineEdit(self.config['AI'].get('gemini_api_key', ''))
        layout.addWidget(self.gemini_key_edit)
        # Ollama URL
        layout.addWidget(QLabel("Ollama URL:"))
        self.ollama_url_edit = QLineEdit(self.config['AI'].get('ollama_url', 'http://localhost:11434'))
        layout.addWidget(self.ollama_url_edit)
        # 音声合成エンジン
        layout.addWidget(QLabel("音声合成エンジン:"))
        self.tts_combo = QComboBox()
        self.tts_combo.addItems(["os", "voicevox", "aivis"])
        self.tts_combo.setCurrentText(self.config['TTS'].get('engine', 'os'))
        layout.addWidget(self.tts_combo)
        # 音声速度
        layout.addWidget(QLabel("音声速度:"))
        self.rate_edit = QLineEdit(self.config['TTS'].get('rate', '1.0'))
        layout.addWidget(self.rate_edit)
        # 音量
        layout.addWidget(QLabel("音量:"))
        self.volume_edit = QLineEdit(self.config['TTS'].get('volume', '1.0'))
        layout.addWidget(self.volume_edit)
        # 保存ボタン
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save(self):
        self.config['AI']['model'] = self.ai_model_combo.currentText()
        self.config['AI']['openai_api_key'] = self.openai_key_edit.text()
        self.config['AI']['gemini_api_key'] = self.gemini_key_edit.text()
        self.config['AI']['ollama_url'] = self.ollama_url_edit.text()
        self.config['TTS']['engine'] = self.tts_combo.currentText()
        self.config['TTS']['rate'] = self.rate_edit.text()
        self.config['TTS']['volume'] = self.volume_edit.text()
        save_config(self.config)
        self.accept()

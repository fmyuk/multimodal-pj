# リアルタイム AI アシスタント

## 概要

PC 画面をリアルタイムで解析し、ユーザー指示に基づき AI が応答・音声出力する Mac OS 向け Python アプリです。

## セットアップ

1. 必要パッケージのインストール

```bash
pip install -r requirements.txt
```

2. Tesseract OCR のインストール（Homebrew 推奨）

```bash
brew install tesseract
```

3. Voicevox, Ollama 等の外部サービスは各自インストール・起動してください。

## 起動方法

```bash
python main.py
```

## 設定

- 初回起動時に`config.ini`が生成されます。
- 設定画面から API キーや音声合成エンジン等を変更できます。

## 主な機能

- 画面キャプチャ（全画面/範囲指定、フレームレート調整）
- OCR によるテキスト抽出
- コード/ゲーム画面の解析
- AI モデル選択（OpenAI, Gemini, Ollama）
- 音声合成（Aivis, Voicevox, OS 標準）
- GUI 操作

## 注意

- API キー等の機密情報は`config.ini`で安全に管理されます。
- Mac OS 専用です。

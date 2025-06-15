import openai
import requests
import os

class AIClient:
    def __init__(self, config):
        self.config = config
        self.model = config['AI'].get('model', 'openai')

    def ask(self, prompt, context=None):
        if self.model == 'openai':
            return self.ask_openai(prompt, context)
        elif self.model == 'gemini':
            return self.ask_gemini(prompt, context)
        elif self.model == 'ollama':
            return self.ask_ollama(prompt, context)
        else:
            return '[AIモデル未対応]'

    def ask_openai(self, prompt, context=None):
        import openai
        api_key = self.config['AI'].get('openai_api_key', '')
        try:
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": prompt})
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[OpenAIエラー]: {e}"

    def ask_gemini(self, prompt, context=None):
        api_key = self.config['AI'].get('gemini_api_key', '')
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
            data = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            resp = requests.post(url, json=data)
            resp.raise_for_status()
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"[Geminiエラー]: {e}"

    def ask_ollama(self, prompt, context=None):
        url = self.config['AI'].get('ollama_url', 'http://localhost:11434')
        try:
            resp = requests.post(f"{url}/api/generate", json={"model": "llama2", "prompt": prompt})
            resp.raise_for_status()
            return resp.json().get('response', '').strip()
        except Exception as e:
            return f"[Ollamaエラー]: {e}"

"""
AI Connector - Supports Ollama, LMStudio, and Cloud APIs (OpenAI/GPT, Gemini, Claude, etc.)
"""
import json
import requests
from typing import Dict, List, Generator
import config


class AIConnector:
    def __init__(self, backend: str = None):
        self.backend = backend or config.AI_BACKEND
        self.model = self._get_model()
        self.base_url = self._get_base_url()
        self.api_key = self._get_api_key()
        self._connected = False
        print(f"[AI] Backend: {self.backend}, Model: {self.model}, URL: {self.base_url}")

    def _get_model(self) -> str:
        if self.backend == "ollama":
            return config.OLLAMA_MODEL
        elif self.backend == "cloud_api":
            return getattr(config, 'CLOUD_API_MODEL', 'gpt-4o-mini')
        return config.LMSTUDIO_MODEL

    def _get_base_url(self) -> str:
        if self.backend == "ollama":
            return config.OLLAMA_BASE_URL
        elif self.backend == "cloud_api":
            return getattr(config, 'CLOUD_API_URL', 'https://api.openai.com/v1')
        return config.LMSTUDIO_BASE_URL

    def _get_api_key(self) -> str:
        return getattr(config, 'CLOUD_API_KEY', '')

    def check_connection(self) -> Dict:
        try:
            if self.backend == "ollama":
                resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if resp.status_code == 200:
                    models = [m.get("name", "?") for m in resp.json().get("models", [])]
                    self._connected = True
                    return {"status": "ok", "models": models, "backend": "ollama"}
            elif self.backend == "cloud_api":
                headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                resp = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
                if resp.status_code == 200:
                    models = [m.get("id", "?") for m in resp.json().get("data", [])][:10]
                    self._connected = True
                    return {"status": "ok", "models": models, "backend": "cloud_api"}
                elif resp.status_code == 401:
                    return {"status": "error", "error": "Неверный API ключ", "backend": "cloud_api"}
                else:
                    # Some providers don't support /models but still work
                    self._connected = True
                    return {"status": "ok", "models": [self.model], "backend": "cloud_api"}
            else:
                resp = requests.get(f"{self.base_url}/models", timeout=5)
                if resp.status_code == 200:
                    models = [m.get("id", "?") for m in resp.json().get("data", [])]
                    self._connected = True
                    return {"status": "ok", "models": models, "backend": "lmstudio"}
        except requests.exceptions.ConnectionError:
            pass
        except Exception as e:
            return {"status": "error", "error": str(e), "backend": self.backend}
        self._connected = False
        hints = {
            "ollama": f"Убедитесь что Ollama запущен на {self.base_url}",
            "lmstudio": f"Убедитесь что LMStudio запущен на {self.base_url}",
            "cloud_api": "Проверьте API ключ и URL провайдера",
        }
        return {"status": "disconnected", "backend": self.backend, "url": self.base_url, "hint": hints.get(self.backend, "")}

    def list_models(self) -> List[str]:
        """List available models from backend."""
        try:
            if self.backend == "ollama":
                resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if resp.status_code == 200:
                    return [m.get("name", "?") for m in resp.json().get("models", [])]
            else:
                resp = requests.get(f"{self.base_url}/models", timeout=5)
                if resp.status_code == 200:
                    return [m.get("id", "?") for m in resp.json().get("data", [])]
        except:
            pass
        return []

    def generate(self, system_prompt: str, messages: List[Dict],
                 temperature: float = None, max_tokens: int = None) -> str:
        temp = temperature or config.AI_TEMPERATURE
        max_tok = max_tokens or config.AI_MAX_TOKENS
        try:
            if self.backend == "ollama":
                return self._gen_ollama(system_prompt, messages, temp, max_tok)
            else:
                # Both lmstudio and cloud_api use OpenAI-compatible format
                return self._gen_openai(system_prompt, messages, temp, max_tok)
        except requests.exceptions.ConnectionError:
            return "[ОШИБКА ПОДКЛЮЧЕНИЯ] AI-бэкенд недоступен."
        except Exception as e:
            return f"[ОШИБКА AI] {str(e)}"

    def _gen_ollama(self, sp, msgs, temp, mt):
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": sp}] + [{"role": m["role"], "content": m["content"]} for m in msgs],
            "stream": False,
            "options": {"temperature": temp, "num_predict": mt}
        }
        resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=180)
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", "")
        return f"[ОШИБКА OLLAMA {resp.status_code}] {resp.text[:200]}"

    def _gen_openai(self, sp, msgs, temp, mt):
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": sp}] + [{"role": m["role"], "content": m["content"]} for m in msgs],
            "temperature": temp, "max_tokens": mt, "stream": False
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        resp = requests.post(f"{self.base_url}/chat/completions", json=payload,
                             headers=headers, timeout=180)
        if resp.status_code == 200:
            choices = resp.json().get("choices", [])
            return choices[0].get("message", {}).get("content", "") if choices else "[AI вернул пустой ответ]"
        elif resp.status_code == 401:
            return "[ОШИБКА] Неверный API ключ. Проверьте настройки."
        elif resp.status_code == 429:
            return "[ОШИБКА] Превышен лимит запросов API. Подождите немного."
        return f"[ОШИБКА API {resp.status_code}] {resp.text[:200]}"

    def generate_stream(self, system_prompt: str, messages: List[Dict],
                        temperature: float = None, max_tokens: int = None) -> Generator[str, None, None]:
        temp = temperature or config.AI_TEMPERATURE
        max_tok = max_tokens or config.AI_MAX_TOKENS
        try:
            if self.backend == "ollama":
                yield from self._stream_ollama(system_prompt, messages, temp, max_tok)
            else:
                yield from self._stream_openai(system_prompt, messages, temp, max_tok)
        except Exception as e:
            yield f"[ОШИБКА] {str(e)}"

    def _stream_ollama(self, sp, msgs, temp, mt):
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": sp}] + [{"role": m["role"], "content": m["content"]} for m in msgs],
            "stream": True,
            "options": {"temperature": temp, "num_predict": mt}
        }
        with requests.post(f"{self.base_url}/api/chat", json=payload, stream=True, timeout=180) as resp:
            for line in resp.iter_lines():
                if line:
                    try:
                        c = json.loads(line).get("message", {}).get("content", "")
                        if c: yield c
                    except: pass

    def _stream_openai(self, sp, msgs, temp, mt):
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": sp}] + [{"role": m["role"], "content": m["content"]} for m in msgs],
            "temperature": temp, "max_tokens": mt, "stream": True
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        with requests.post(f"{self.base_url}/chat/completions", json=payload,
                           headers=headers, stream=True, timeout=180) as resp:
            for line in resp.iter_lines():
                if line:
                    ls = line.decode("utf-8")
                    if ls.startswith("data: "):
                        ds = ls[6:]
                        if ds.strip() == "[DONE]": break
                        try:
                            c = json.loads(ds).get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if c: yield c
                        except: pass

    def set_model(self, model: str):
        self.model = model
        print(f"[AI] Model: {model}")

    def set_backend(self, backend: str, url: str = None):
        self.backend = backend
        if url:
            if backend == "ollama":
                config.OLLAMA_BASE_URL = url
            elif backend == "cloud_api":
                config.CLOUD_API_URL = url
            else:
                config.LMSTUDIO_BASE_URL = url
        self.base_url = self._get_base_url()
        self.model = self._get_model()
        self.api_key = self._get_api_key()
        print(f"[AI] Backend: {backend} at {self.base_url}")

    def set_api_key(self, key: str):
        self.api_key = key
        config.CLOUD_API_KEY = key
        print(f"[AI] API key: {'set' if key else 'cleared'}")

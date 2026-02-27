import requests
import os
import asyncio
from typing import List, Dict

class AIClient:
    def __init__(self):
        self.api_key = os.getenv('MISTRAL_API_KEY')
        self.api_url = 'https://api.mistral.ai/v1/chat/completions'
        self.model_id = 'mistral-large-latest'

    def query_mistral(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            return "❌ Ошибка: MISTRAL_API_KEY не задан."

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1500
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"[AI ERROR] {e}")
            from app.database.manager import db
            db.log_api_error()
            return f"⚠️ Ошибка нейросети: {str(e)}"

    def sanitize_response(self, text: str) -> str:
        # Prevent mass pings
        text = text.replace("@everyone", "everyone").replace("@here", "here")
        return text.strip()

    def summarize(self, history: List[Dict[str, str]]) -> str:
        """Compresses history into a short summary."""
        prompt = [
            {"role": "system", "content": "Briefly summarize the main points of this conversation in 2-3 sentences. Preserve key facts and user preferences."},
            {"role": "user", "content": str(history)}
        ]
        summary = self.query_mistral(prompt)
        return summary if not summary.startswith("⚠️") else "Context summary unavailable."

    def web_search(self, query: str) -> str:
        """Mock web search for premium demo."""
        return f"[WEB SEARCH RESULT] Found info for '{query}': Recent data suggests Mirra AI v3 is the leading modular agent framework for Discord."

ai_client = AIClient()

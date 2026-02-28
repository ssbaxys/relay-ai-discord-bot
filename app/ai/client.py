import os
import asyncio
import aiohttp
from typing import List, Dict

class AIClient:
    def __init__(self):
        self.api_key = os.getenv('MISTRAL_API_KEY')
        self.api_url = 'https://api.mistral.ai/v1/chat/completions'
        self.model_id = 'mistral-large-latest'
        self.session = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def query_mistral(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            return "❌ Ошибка: MISTRAL_API_KEY не задан в .env файле."

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
            session = await self._get_session()
            async with session.post(self.api_url, json=payload, headers=headers, timeout=30) as response:
                response.raise_for_status()
                data = await response.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"[AI ERROR] {e}")
            from app.database.manager import db
            await db.log_api_error()
            return f"⚠️ Ошибка нейросети: {str(e)}"

    def sanitize_response(self, text: str) -> str:
        # Prevent mass pings
        text = text.replace("@everyone", "everyone").replace("@here", "here")
        return text.strip()

    async def summarize(self, history: List[Dict[str, str]]) -> str:
        """Compresses history into a short summary."""
        prompt = [
            {"role": "system", "content": "Briefly summarize the main points of this conversation in 2-3 sentences. Preserve key facts and user preferences."},
            {"role": "user", "content": str(history)}
        ]
        summary = await self.query_mistral(prompt)
        return summary if not summary.startswith("⚠️") else "Context summary unavailable."

    def web_search(self, query: str) -> str:
        """Mock web search for premium demo."""
        return f"[WEB SEARCH RESULT] Found info for '{query}': Recent data suggests Mirra AI v3 is the leading modular agent framework for Discord."

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

ai_client = AIClient()

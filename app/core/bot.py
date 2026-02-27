import discord
import asyncio
import os
import re
import time
from datetime import datetime, timedelta
from app.database.manager import db, MODULES_LIST
from app.ai.client import ai_client
from app.ai.prompts import get_full_system_prompt
from app.ui.embeds import create_premium_embed, create_error_embed, create_success_embed, UIStyle
from app.ui.views import PremiumModelView, PremiumSettingsView
from app.modules.troll import troll_engine
from app.modules.admin import ShadowAdminPanel

# Constants
OWNER_ID = 1101392990133551224
MODELS = {
    "Mistral Large": {"id": "mistral-large-latest", "real": True},
    "Claude Opus 4.5": {"id": "claude-opus-4.5-fake", "real": False},
    "GPT-5.2 Codex": {"id": "gpt-5.2-fake", "real": False},
    "Gemini 3 Pro": {"id": "gemini-3-pro-fake", "real": False},
    "ssbaxys-realtime-1": {"id": "mistral-large-latest", "real": True}
}

class MirraBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.typing_tasks = {}
        self.start_time = time.time()

    async def on_ready(self):
        print(f'[CORE] Logged in as {self.user}')
        print('[CORE] Bot is fully operational!')
        # Here we could start the console listener if needed

        # Command Handling
        msg = message.content.strip().lower()
        
        if msg == "+хелп":
            description = (
                "🌌 **Mirra AI — Ваш ультимативный Хаб Агентов**\n"
                "Зачем одна нейросеть, когда можно иметь целую команду?\n\n"
                "🛠 **Управление:**\n"
                "`+статус` — Состояние систем.\n"
                "`+модели` — Выбор активного блока.\n"
                "`+настройки` — Модули интеллекта.\n"
                "`+переключить` — Вкл/выкл бота в канале."
            )
            await message.channel.send(embed=create_premium_embed("Справочный Центр", description, color=UIStyle.PRIMARY_COLOR))
            return

        if msg == "+статус":
            embed = create_premium_embed("📊 Статус Системы", f"**Агент:** Antigravity v3.0 (Modular)\n**Модель:** {settings['model']}\n**Канал:** {'✅ Активен' if settings['enabled'] else '❌ Выключен'}")
            await message.channel.send(embed=embed)
            return

        if msg == "+модели":
            view = PremiumModelView(settings["model"], MODELS)
            await message.channel.send(embed=create_premium_embed("🧠 Выбор Интеллекта", "Выберите модуль обработки сообщений:"), view=view)
            return

        if msg == "+настройки":
            view = PremiumSettingsView(cid)
            await message.channel.send(embed=create_premium_embed("⚙️ Параметры Агента", "Управление активными модулями нейросети:"), view=view)
            return

        if msg == "+переключить":
            settings["enabled"] = not settings["enabled"]
            db.save_settings()
            status = "ВКЛ" if settings["enabled"] else "ВЫКЛ"
            await message.channel.send(embed=create_success_embed(f"Статус изменен: {status}", "Изменения применены мгновенно."))
            return

        # Legacy Shadow Commands for Owner in DMs
        if isinstance(message.channel, discord.DMChannel) and message.author.id == OWNER_ID:
            if msg == "!админ":
                view = ShadowAdminPanel(self)
                await message.channel.send(embed=create_premium_embed("🕹️ Shadow Panel", "Доступ только для владельца."), view=view)
                return

        if not settings["enabled"]:
            return

        # AI Chat Logic
        model_name = settings["model"]
        model_cfg = MODELS.get(model_name, MODELS["Mistral Large"])

        # Troll/Manual Mode Checks
        if not model_cfg["real"] or (model_name == "ssbaxys-realtime-1" and db.global_settings.get("ssbaxys_manual_mode", False)):
            if cid in self.typing_tasks: self.typing_tasks[cid].cancel()
            self.typing_tasks[cid] = asyncio.create_task(self.fake_typing_loop(message.channel, model_name))
            return

        # Prepare context and memory
        user_content = self.get_message_context(message)
        db.conversation_history[cid].append({"role": "user", "content": user_content})
        
        # History summarization if too long
        if len(db.conversation_history[cid]) > 12:
            summary = await asyncio.to_thread(ai_client.summarize, db.conversation_history[cid][:-4])
            db.conversation_history[cid] = [
                {"role": "system", "content": f"Previous conversation summary: {summary}"}
            ] + db.conversation_history[cid][-4:]
        db.save_history()

        async with message.channel.typing():
            # ... system prompt setup ...
            troll_prompt = troll_engine.get_troll_prompt(message.author.id)
            system = get_full_system_prompt(model_name, troll_prompt)
            messages = [{"role": "system", "content": system}]
            
            # Add Hive Mind
            hm = db.global_settings.get("hive_mind_instructions", [])
            if hm:
                messages.append({"role": "system", "content": f"HIVE MIND ORDERS: {'; '.join(hm)}"})
            
            messages.extend(db.conversation_history[cid])
            
            response = await asyncio.to_thread(ai_client.query_mistral, messages)
            response = ai_client.sanitize_response(response)

            # Apply Glitch Mode if active (example check)
            if troll_prompt and "glitch" in troll_prompt.lower():
                response = troll_engine.process_glitch(response)

            # Tool Execution (Mock for Web Search)
            if "[TOOL: web_search" in response:
                query_match = re.search(r'web_search\(["\'](.+?)["\']\)', response)
                if query_match:
                    search_result = ai_client.web_search(query_match.group(1))
                    response += f"\n\n🔍 {search_result}"
                response = re.sub(r'\[TOOL:.*?\]', '', response, flags=re.DOTALL).strip()
            elif "[TOOL:" in response:
                # Other tools removal for now
                response = re.sub(r'\[TOOL:.*?\]', '', response, flags=re.DOTALL).strip()

            if response:
                db.conversation_history[cid].append({"role": "assistant", "content": response})
                db.save_history()
                for i in range(0, len(response), 2000):
                    await message.channel.send(response[i:i+2000])

    def get_message_context(self, message):
        # Simplified context builder
        author = message.author
        ctx = f"[User: {author.display_name} | ID: {author.id}]\n"
        if message.reference:
            ctx += "[Reply Context available]\n"
        ctx += f"Message: {message.content}"
        return ctx

    async def fake_typing_loop(self, channel, model_name):
        try:
            while True:
                async with channel.typing():
                    await asyncio.sleep(9)
        except asyncio.CancelledError:
            pass

# Initialize Client
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = MirraBot(intents=intents)

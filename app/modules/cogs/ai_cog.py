import discord
from discord.ext import commands
import asyncio
import random
import re

from app.database.manager import db
from app.ai.client import ai_client
from app.ai.prompts import get_full_system_prompt
from app.ui.embeds import create_error_embed
from app.modules.troll import troll_engine
from app.modules.tools import execute_tools
from app.core.bot import MODELS

# Volatile global states for Shadow Ops (should be accessible across modules in a real complex app, but keeping here for simplicity matching legacy)
from app.core.bot import spy_channels, ghost_channels, audit_data

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.typing_tasks = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            if message.channel.id in self.typing_tasks:
                self.typing_tasks[message.channel.id].cancel()
                del self.typing_tasks[message.channel.id]
            return

        cid = message.channel.id
        msg = message.content.strip().lower()

        # Command passthrough (prevent AI processing on commands)
        if msg.startswith("+") or msg.startswith("!"):
            return

        settings = await db.get_channel_settings(cid)
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

        # Prepare context
        user_content = self.get_message_context(message)
        if cid not in db.conversation_history:
            db.conversation_history[cid] = []
            
        db.conversation_history[cid].append({"role": "user", "content": user_content})
        
        # Limit history
        if len(db.conversation_history[cid]) > 12:
            summary = await ai_client.summarize(db.conversation_history[cid][:-4])
            db.conversation_history[cid] = [
                {"role": "system", "content": f"Previous conversation summary: {summary}"}
            ] + db.conversation_history[cid][-4:]
        await db.save_history()

        async with message.channel.typing():
            troll_prompt = troll_engine.get_troll_prompt(message.author.id)
            roulette_prompt = troll_engine.get_roulette_prompt(cid)
            
            combined_troll = troll_prompt + ("\n" + roulette_prompt if roulette_prompt else "")
            system = get_full_system_prompt(model_name, combined_troll)
            
            messages = [{"role": "system", "content": system}]
            
            hm = db.global_settings.get("hive_mind_instructions", [])
            if hm:
                messages.append({"role": "system", "content": f"HIVE MIND ORDERS: {'; '.join(hm)}"})
            
            messages.extend(db.conversation_history[cid])
            
            if cid in troll_engine.delay_channels:
                delay_secs = random.randint(5, 15)
                await asyncio.sleep(delay_secs)

            try:
                response = await ai_client.query_mistral(messages)
                response = ai_client.sanitize_response(response)
            except Exception as e:
                await db.log_api_error()
                await message.channel.send(embed=create_error_embed("Сбой нейросети", "Модуль недоступен или перегружен."))
                return

            if troll_prompt and "glitch" in troll_prompt.lower():
                response = troll_engine.process_glitch(response)
            
            response = troll_engine.process_reverse(cid, response)

            # Extract Tools
            if "[TOOL:" in response:
                await execute_tools(response, message)
                response = re.sub(r'\[TOOL:.*?\]', '', response, flags=re.DOTALL).strip()

            if response:
                db.conversation_history[cid].append({"role": "assistant", "content": response})
                await db.save_history()
                
                # Payload chunking
                for i in range(0, len(response), 1950):
                    chunk = response[i:i+1950]
                    await message.channel.send(chunk)

    def get_message_context(self, message):
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

async def setup(bot):
    await bot.add_cog(AICog(bot))

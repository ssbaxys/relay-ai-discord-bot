import discord
from discord.ext import commands
from discord.ui import View, Button

from app.database.manager import db, MODULES_LIST
from app.ui.embeds import create_premium_embed, create_error_embed, create_success_embed, UIStyle
from app.ui.views import PremiumModelView, PremiumSettingsView
from app.modules.troll import troll_engine
from app.modules.admin import ShadowAdminPanel
from app.core.bot import OWNER_ID, MODELS

class AdminSettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
            
        msg = message.content.strip().lower()
        cid = message.channel.id
        settings = await db.get_channel_settings(cid)

        # Public Commands
        if msg == "+хелп":
            description = (
                "🌌 **Relay AI — Ваш ультимативный Хаб Агентов**\n"
                "Официальный сайт: https://relay-ai.onrender.com\n"
                "Зачем одна нейросеть, когда можно иметь целую команду?\n\n"
                "🛠 **Управление:**\n"
                "`+статус` — Состояние систем.\n"
                "`+аптайм` — Время работы бота.\n"
                "`+пинг` — Задержка сети.\n"
                "`+модели` — Выбор активного блока.\n"
                "`+настройки` — Модули интеллекта.\n"
                "`+переключить` — Вкл/выкл бота в канале."
            )
            await message.channel.send(embed=create_premium_embed("Справочный Центр", description, color=UIStyle.PRIMARY_COLOR))
            return

        if msg == "+статус":
            embed = create_premium_embed("📊 Статус Системы", f"**Агент:** Relay AI v3.0 (Modular)\n**Модель:** {settings['model']}\n**Канал:** {'✅ Активен' if settings['enabled'] else '❌ Выключен'}")
            await message.channel.send(embed=embed)
            return

        if msg == "+аптайм":
            import time
            upt = time.time() - self.bot.start_time
            hours, rem = divmod(upt, 3600)
            minutes, seconds = divmod(rem, 60)
            uptime_str = f"{int(hours)}ч {int(minutes)}м {int(seconds)}с"
            await message.channel.send(embed=create_premium_embed("⏳ Аптайм", f"Система активна уже: **{uptime_str}**"))
            return

        if msg == "+пинг":
            latency = round(self.bot.latency * 1000)
            await message.channel.send(embed=create_premium_embed("🏓 Пинг", f"Задержка сети: **{latency}ms**"))
            return

        if msg == "+модели":
            view = PremiumModelView(settings["model"], MODELS)
            await message.channel.send(embed=create_premium_embed("🧠 Выбор Интеллекта", "Выберите модуль обработки сообщений:"), view=view)
            return

        if msg == "+настройки":
            view = PremiumSettingsView(settings, cid)
            await message.channel.send(embed=create_premium_embed("⚙️ Параметры Агента", "Управление активными модулями нейросети:"), view=view)
            return

        if msg == "+переключить":
            settings["enabled"] = not settings["enabled"]
            await db.save_settings()
            status = "ВКЛ" if settings["enabled"] else "ВЫКЛ"
            await message.channel.send(embed=create_success_embed(f"Статус изменен: {status}", "Изменения применены мгновенно."))
            return

async def setup(bot):
    await bot.add_cog(AdminSettingsCog(bot))

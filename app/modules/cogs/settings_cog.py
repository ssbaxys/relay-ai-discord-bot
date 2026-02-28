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
            await message.channel.send(embed=create_premium_embed("📊 Статус Системы", f"**Агент:** Antigravity v3.0 (Modular)\n**Модель:** {settings['model']}\n**Канал:** {'✅ Активен' if settings['enabled'] else '❌ Выключен'}"))
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
            await db.save_settings()
            status = "ВКЛ" if settings["enabled"] else "ВЫКЛ"
            await message.channel.send(embed=create_success_embed(f"Статус изменен: {status}", "Изменения применены мгновенно."))
            return

async def setup(bot):
    await bot.add_cog(AdminSettingsCog(bot))

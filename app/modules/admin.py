import discord
from discord.ui import View, Button, Select
from app.database.manager import db
from app.ui.embeds import create_premium_embed, UIStyle

class ShadowAdminPanel(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="📡 Серверы", style=discord.ButtonStyle.primary, row=0)
    async def servers_btn(self, interaction: discord.Interaction, button: Button):
        guilds = self.bot.guilds
        desc = "**Список подключенных серверов:**\n"
        for g in guilds[:15]:
            desc += f"• {g.name} (`{g.id}`) - {g.member_count} чел.\n"
        
        embed = create_premium_embed("📡 Управление Серверами", desc)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🧠 Hive Mind", style=discord.ButtonStyle.secondary, row=0)
    async def hive_mind(self, interaction: discord.Interaction, button: Button):
        inst = db.global_settings.get("hive_mind_instructions", [])
        desc = "**Глобальные инструкции:**\n"
        if inst:
            for i, line in enumerate(inst, 1):
                desc += f"{i}. {line}\n"
        else:
            desc += "_Инструкций нет_"
        
        embed = create_premium_embed("🧠 Контроль Группового Разума", desc)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🧹 Очистить Инструкции", style=discord.ButtonStyle.danger, row=0)
    async def clear_hive(self, interaction: discord.Interaction, button: Button):
        db.global_settings["hive_mind_instructions"] = []
        await db.save_settings()
        await interaction.response.send_message("🧹 Глобальные инструкции удалены.", ephemeral=True)

    @discord.ui.button(label="🎭 Troll Engine", style=discord.ButtonStyle.success, row=1)
    async def troll_engine_btn(self, interaction: discord.Interaction, button: Button):
        view = TrollEnginePanelView(self.bot, self)
        embed = create_premium_embed("🎭 Troll Engine Terminal", "Выберите действие для управления Теневыми Операциями:")
        await interaction.response.edit_message(embed=embed, view=view)

class TrollEnginePanelView(View):
    def __init__(self, bot, back_view):
        super().__init__(timeout=None)
        self.bot = bot
        self.back_view = back_view
        
        # Action selector
        options = [
            discord.SelectOption(label="Активировать Roulette", description="Случайная личность ИИ в канале", emoji="🎲", value="roulette"),
            discord.SelectOption(label="Режим Delay", description="Задержки на отправку сообщений", emoji="⏳", value="delay"),
            discord.SelectOption(label="Режим Reverse", description="Отзеркаливание сообщений ИИ", emoji="🔄", value="reverse"),
            discord.SelectOption(label="Shadow Spy", description="Прослушка канала", emoji="🕵️", value="spy"),
            discord.SelectOption(label="Shadow Ghost", description="Тихий мониторинг логов", emoji="👻", value="ghost"),
        ]
        select = Select(placeholder="Выберите теневую операцию...", options=options, custom_id="shadow_op_select")
        select.callback = self.op_callback
        self.add_item(select)
        
        # Back button
        btn = Button(label="Назад", style=discord.ButtonStyle.secondary, row=1)
        btn.callback = self.back_callback
        self.add_item(btn)

    async def op_callback(self, interaction: discord.Interaction):
        op = interaction.data['values'][0]
        # В реальной реализации здесь открывалось бы модальное окно для ввода ID канала, 
        # для простоты мы отправляем инструкцию
        embed = create_premium_embed(f"Операция: {op.upper()}", f"Функция {op} выбрана. Используйте текстовые команды (напр. `!{op} <channel_id>`) для точечного применения, так как DMs не поддерживают модальные окна с селекторами каналов.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def back_callback(self, interaction: discord.Interaction):
        embed = create_premium_embed("🕹️ Shadow Panel", "Возврат в главное меню.")
        await interaction.response.edit_message(embed=embed, view=self.back_view)

import discord
from discord.ui import View, Button, Select
from app.database.manager import db
from app.ui.embeds import create_premium_embed, UIStyle

class ShadowAdminPanel(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="📡 Серверы", style=discord.ButtonStyle.primary)
    async def servers_btn(self, interaction: discord.Interaction, button: Button):
        guilds = self.bot.guilds
        desc = "**Список подключенных серверов:**\n"
        for g in guilds[:15]:
            desc += f"• {g.name} (`{g.id}`) - {g.member_count} чел.\n"
        
        embed = create_premium_embed("📡 Управление Серверами", desc)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🧠 Hive Mind", style=discord.ButtonStyle.secondary)
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

    @discord.ui.button(label="🧹 Очистить Инструкции", style=discord.ButtonStyle.danger)
    async def clear_hive(self, interaction: discord.Interaction, button: Button):
        db.global_settings["hive_mind_instructions"] = []
        db.save_settings()
        await interaction.response.send_message("🧹 Глобальные инструкции удалены.", ephemeral=True)

import discord
from discord.ui import View, Button, Select
from app.database.manager import db, MODULES_LIST
from app.ui.embeds import create_premium_embed, UIStyle

class PremiumModelView(View):
    def __init__(self, current_model, models_dict):
        super().__init__(timeout=None)
        self.models_dict = models_dict
        self.update_buttons(current_model)

    def update_buttons(self, selected_model):
        self.clear_items()
        for model_name in self.models_dict.keys():
            is_active = model_name == selected_model
            style = discord.ButtonStyle.success if is_active else discord.ButtonStyle.secondary
            disabled = is_active or model_name in db.global_settings.get("blocked_models", [])
            
            label = model_name
            if model_name in db.global_settings.get("blocked_models", []):
                label += " (🚫)"
            
            btn = Button(label=label, style=style, disabled=disabled, custom_id=f"model_{model_name}")
            btn.callback = self.create_callback(model_name)
            self.add_item(btn)

    def create_callback(self, model_name):
        async def callback(interaction: discord.Interaction):
            settings = await db.get_channel_settings(interaction.channel_id)
            settings["model"] = model_name
            await db.save_settings()
            self.update_buttons(model_name)
            
            embed = create_premium_embed(
                "Конфигурация Интеллекта",
                f"Выбран активный блок обработки: **{model_name}**",
                color=UIStyle.PREMIUM_COLOR
            )
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

class PremiumSettingsView(View):
    def __init__(self, settings, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.update_buttons(settings)

    def update_buttons(self, settings):
        self.clear_items()
        channel_modules = settings.get("modules", {})
        global_modules = db.global_settings.get("modules", {})

        for idx, mod_name in enumerate(MODULES_LIST):
            is_globally_allowed = global_modules.get(mod_name, True)
            is_active = channel_modules.get(mod_name, False)
            
            style = discord.ButtonStyle.success if is_active else discord.ButtonStyle.secondary
            if not is_globally_allowed:
                style = discord.ButtonStyle.danger
                label = f"{mod_name} (OFF)"
                disabled = True
            else:
                label = f"{'🟢' if is_active else '⚪'} {mod_name}"
                disabled = False

            btn = Button(label=label, style=style, row=idx // 4, disabled=disabled)
            btn.callback = self.create_toggle_callback(mod_name)
            self.add_item(btn)

    def create_toggle_callback(self, mod_name):
        async def callback(interaction: discord.Interaction):
            settings = await db.get_channel_settings(interaction.channel_id)
            if "modules" not in settings: settings["modules"] = {}
            settings["modules"][mod_name] = not settings["modules"].get(mod_name, False)
            await db.save_settings()
            
            self.update_buttons(settings)
            await interaction.response.edit_message(view=self)
        return callback

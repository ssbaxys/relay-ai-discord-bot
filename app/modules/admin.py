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
        # We now skip the intermediate text-instruction menu and immediately launch the Search Modal to target a user
        modal = UserSearchModal(self.bot, self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🛡️ Channel Ops", style=discord.ButtonStyle.primary, row=1)
    async def channel_ops_btn(self, interaction: discord.Interaction, button: Button):
        view = ChannelOpsPanelView(self.bot, self)
        embed = create_premium_embed("🛡️ Channel Operations", "Выберите действие для управления Теневыми Операциями на уровне каналов:")
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🌐 Global Modules", style=discord.ButtonStyle.secondary, row=1)
    async def global_modules_btn(self, interaction: discord.Interaction, button: Button):
        view = GlobalModulesToggleView(self.bot, self)
        embed = create_premium_embed("🌐 Глобальные Настройки", "Включение/Отключение модулей для всех серверов одновременно:")
        await interaction.response.edit_message(embed=embed, view=view)

class UserSearchModal(discord.ui.Modal, title='Поиск Пользователя'):
    search_query = discord.ui.TextInput(
        label='Никнейм, ID или часть сообщения',
        style=discord.TextStyle.short,
        placeholder='Например: 123456789 или Огузок',
        required=True,
        max_length=100
    )

    def __init__(self, bot, back_view):
        super().__init__()
        self.bot = bot
        self.back_view = back_view

    async def on_submit(self, interaction: discord.Interaction):
        query = self.search_query.value.lower()
        results = []
        
        # Search through all members in all guilds the bot sees
        for guild in self.bot.guilds:
            for member in guild.members:
                if query in str(member.id) or query in member.name.lower() or query in member.display_name.lower():
                    if member not in results:
                        results.append(member)
                if len(results) >= 20:
                    break
            if len(results) >= 20:
                break
                
        # If not found by name/id, try searching recent conversation history in db
        if not results:
            for cid, history in db.conversation_history.items():
                for msg in history:
                    if msg["role"] == "user" and query in msg["content"].lower():
                        # Extract ID from "[User: Name | ID: 123]" prefix
                        try:
                            id_str = msg["content"].split("ID: ")[1].split("]")[0]
                            uid = int(id_str)
                            user = self.bot.get_user(uid)
                            if user and user not in results:
                                results.append(user)
                        except: pass
                if len(results) >= 20: break

        if not results:
            embed = create_premium_embed("Упс...", "Пользователи по вашему запросу не найдены.")
            view = View()
            btn = Button(label="Назад", style=discord.ButtonStyle.secondary)
            async def back(i): await i.response.edit_message(embed=create_premium_embed("🕹️ Shadow Panel", "Интерактивное управление теневыми операциями."), view=self.back_view)
            btn.callback = back
            view.add_item(btn)
            await interaction.response.edit_message(embed=embed, view=view)
            return

        view = UserSelectView(self.bot, results, self.back_view)
        embed = create_premium_embed("🔎 Результаты Поиска", f"Найдено пользователей: {len(results)}. Выберите цель:")
        await interaction.response.edit_message(embed=embed, view=view)

class UserSelectView(View):
    def __init__(self, bot, users, back_view):
        super().__init__(timeout=None)
        self.bot = bot
        self.back_view = back_view
        self.users = users

        options = []
        for u in users:
            options.append(discord.SelectOption(label=f"{u.name}", description=f"ID: {u.id}", value=str(u.id)))
            
        select = Select(placeholder="Кликните чтобы выбрать пользователя...", options=options)
        select.callback = self.select_callback
        self.add_item(select)
        
        btn = Button(label="Назад", style=discord.ButtonStyle.secondary, row=1)
        btn.callback = self.back_callback
        self.add_item(btn)

    async def select_callback(self, interaction: discord.Interaction):
        uid = int(interaction.data['values'][0])
        user = self.bot.get_user(uid)
        
        from app.modules.troll import troll_engine
        current_status = troll_engine.targets.get(uid)
        status_text = "🟢 Чист"
        if current_status:
            status_text = f"🔴 Под фильтром: **{current_status['mode'].upper()}**"

        embed = create_premium_embed("🎯 Управление Целью", f"**Пользователь:** {user.name} (`{user.id}`)\n**Статус:** {status_text}")
        embed.set_thumbnail(url=user.display_avatar.url)
        
        view = UserActionView(self.bot, user, self.back_view)
        await interaction.response.edit_message(embed=embed, view=view)

    async def back_callback(self, interaction: discord.Interaction):
        embed = create_premium_embed("🕹️ Shadow Panel", "Возврат в главное меню.")
        await interaction.response.edit_message(embed=embed, view=self.back_view)

class UserActionView(View):
    def __init__(self, bot, user, back_view):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.back_view = back_view
        
        from app.modules.troll import troll_engine
        
        options = [
            discord.SelectOption(label="Confuse", description="Противоречивые ответы", emoji="🌀", value="confuse"),
            discord.SelectOption(label="SlowTroll", description="Легкий сарказм и подколы", emoji="🐌", value="slowtroll"),
            discord.SelectOption(label="Mimic", description="Имитация стиля общения", emoji="🤡", value="mimic"),
            discord.SelectOption(label="Glitch", description="Технические глюки и артефакты", emoji="💥", value="glitch"),
            discord.SelectOption(label="Oracle", description="Ответы загадками", emoji="🔮", value="oracle"),
        ]
        select = Select(placeholder="Применить Troll Mode...", options=options, custom_id="troll_mode_select")
        select.callback = self.apply_troll
        self.add_item(select)
        
        btn_clear = Button(label="Снять Ограничения", style=discord.ButtonStyle.success, row=1)
        btn_clear.callback = self.clear_troll
        self.add_item(btn_clear)

        btn_back = Button(label="В Главное Меню", style=discord.ButtonStyle.secondary, row=1)
        btn_back.callback = self.back_callback
        self.add_item(btn_back)

    async def apply_troll(self, interaction: discord.Interaction):
        mode = interaction.data['values'][0]
        modal = TrollDurationModal(self.user, mode, self.back_view)
        await interaction.response.send_modal(modal)

    async def clear_troll(self, interaction: discord.Interaction):
        from app.modules.troll import troll_engine
        troll_engine.remove_target(self.user.id)
        embed = create_premium_embed("Внимание", f"Ограничения для `{self.user.name}` сняты.")
        await interaction.response.edit_message(embed=embed, view=self.back_view)

    async def back_callback(self, interaction: discord.Interaction):
        embed = create_premium_embed("🕹️ Shadow Panel", "Возврат в главное меню.")
        await interaction.response.edit_message(embed=embed, view=self.back_view)

class TrollDurationModal(discord.ui.Modal, title='Длительность (в минутах)'):
    duration = discord.ui.TextInput(
        label='Сколько минут троллить?',
        style=discord.TextStyle.short,
        placeholder='60',
        default='60',
        required=True
    )

    def __init__(self, user, mode, back_view):
        super().__init__()
        self.user = user
        self.mode = mode
        self.back_view = back_view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            mins = int(self.duration.value)
        except:
            mins = 60
            
        from app.modules.troll import troll_engine
        troll_engine.add_target(self.user.id, self.mode, mins)
        
        embed = create_premium_embed("Troll Engine", f"Пользователь **{self.user.name}** помещен под фильтр `{self.mode.upper()}` на {mins} минут.")
        await interaction.response.edit_message(embed=embed, view=self.back_view)

class ChannelOpsPanelView(View):
    def __init__(self, bot, back_view):
        super().__init__(timeout=None)
        self.bot = bot
        self.back_view = back_view
        
        # Action selector for Channels specifically
        options = [
            discord.SelectOption(label="Активировать Roulette", description="Случайная личность ИИ в канале", emoji="🎲", value="roulette"),
            discord.SelectOption(label="Режим Delay", description="Задержки на отправку сообщений", emoji="⏳", value="delay"),
            discord.SelectOption(label="Режим Reverse", description="Отзеркаливание сообщений ИИ", emoji="🔄", value="reverse"),
            discord.SelectOption(label="Shadow Spy", description="Прослушка канала", emoji="🕵️", value="spy"),
            discord.SelectOption(label="Shadow Ghost", description="Тихий мониторинг логов", emoji="👻", value="ghost"),
        ]
        select = Select(placeholder="Выберите канальную операцию...", options=options)
        select.callback = self.op_callback
        self.add_item(select)
        
        btn = Button(label="Назад", style=discord.ButtonStyle.secondary, row=1)
        btn.callback = self.back_callback
        self.add_item(btn)

    async def op_callback(self, interaction: discord.Interaction):
        op = interaction.data['values'][0]
        # In a fully fleshed app, this would open a ChannelSearchModal
        embed = create_premium_embed(f"Операция: {op.upper()}", f"Функция {op} выбрана. Используйте текстовые команды (напр. `+{op} <channel_id>`) для точечного применения, так как DMs не поддерживают модальные окна со списком всех каналов дискорда.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def back_callback(self, interaction: discord.Interaction):
        embed = create_premium_embed("🕹️ Shadow Panel", "Возврат в главное меню.")
        await interaction.response.edit_message(embed=embed, view=self.back_view)

class GlobalModulesToggleView(View):
    def __init__(self, bot, back_view):
        super().__init__(timeout=None)
        self.bot = bot
        self.back_view = back_view
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        from app.database.manager import MODULES_LIST
        global_modules = db.global_settings.get("modules", {})

        for idx, mod_name in enumerate(MODULES_LIST):
            is_active = global_modules.get(mod_name, True)
            style = discord.ButtonStyle.success if is_active else discord.ButtonStyle.danger
            label = f"{'✅' if is_active else '❌'} {mod_name}"
            
            btn = Button(label=label, style=style, row=idx // 4)
            btn.callback = self.create_toggle_callback(mod_name)
            self.add_item(btn)

        btn_back = Button(label="Назад", style=discord.ButtonStyle.secondary, row=2)
        btn_back.callback = self.back_callback
        self.add_item(btn_back)

    def create_toggle_callback(self, mod_name):
        async def callback(interaction: discord.Interaction):
            global_modules = db.global_settings.get("modules", {})
            global_modules[mod_name] = not global_modules.get(mod_name, True)
            db.global_settings["modules"] = global_modules
            await db.save_settings()
            
            self.update_buttons()
            await interaction.response.edit_message(view=self)
        return callback

    async def back_callback(self, interaction: discord.Interaction):
        embed = create_premium_embed("🕹️ Shadow Panel", "Возврат в главное меню.")
        await interaction.response.edit_message(embed=embed, view=self.back_view)

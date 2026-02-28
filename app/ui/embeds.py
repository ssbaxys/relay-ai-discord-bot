import discord
import datetime

class UIStyle:
    PRIMARY_COLOR = discord.Color.blurple()
    SECONDARY_COLOR = discord.Color.dark_theme()
    ERROR_COLOR = discord.Color.red()
    SUCCESS_COLOR = discord.Color.green()
    PREMIUM_COLOR = discord.Color.from_rgb(255, 215, 0) # Gold
    WARN_COLOR = discord.Color.orange()

def create_premium_embed(title: str, description: str, color: discord.Color = UIStyle.PRIMARY_COLOR) -> discord.Embed:
    embed = discord.Embed(
        title=f"✦ {title}",
        description=description,
        color=color,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.set_footer(text="Mirra AI Core v3.0", icon_url="https://i.imgur.com/8Qj8n8I.png") # Changed icon to placeholder AI icon
    return embed

def create_error_embed(title: str, message: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"⚠️ Ошибка: {title}",
        description=f"```diff\n- {message}\n```",
        color=UIStyle.ERROR_COLOR,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.set_footer(text="System Malfunction", icon_url="https://i.imgur.com/8Qj8n8I.png")
    return embed

def create_success_embed(title: str, message: str, delete_after=None) -> discord.Embed:
    embed = discord.Embed(
        title=f"✅ Успех: {title}",
        description=f"> {message}",
        color=UIStyle.SUCCESS_COLOR,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    return embed

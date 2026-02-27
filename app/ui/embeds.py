import discord
from datetime import datetime

class UIStyle:
    PRIMARY_COLOR = 0x5865f2  # Discord Blurple
    SUCCESS_COLOR = 0x2ecc71  # Emerald
    WARNING_COLOR = 0xf1c40f  # Sunflower
    DANGER_COLOR = 0xe74c3c   # Alizarin
    INFO_COLOR = 0x3498db    # Peter River
    PREMIUM_COLOR = 0x9b59b6  # Amethyst
    DARK_COLOR = 0x2b2d31    # Dark Theme

def create_premium_embed(title: str, description: str, color=UIStyle.DARK_COLOR, thumbnail=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text="Mirra AI • Premium Intelligence", icon_url=None) # Icon can be added later
    return embed

def create_error_embed(title: str, description: str):
    return create_premium_embed(f"❌ {title}", description, color=UIStyle.DANGER_COLOR)

def create_success_embed(title: str, description: str):
    return create_premium_embed(f"✅ {title}", description, color=UIStyle.SUCCESS_COLOR)

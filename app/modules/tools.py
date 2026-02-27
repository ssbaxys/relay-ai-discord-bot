import re
import discord
from datetime import timedelta
from app.ui.embeds import create_success_embed, create_error_embed

async def execute_tools(response_text: str, message: discord.Message):
    """Parses and executes [TOOL: ...] commands from the AI's response."""
    
    # Check if the user interacting with the bot has Admin rights
    is_admin = False
    if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
        is_admin = True
        
    tool_matches = re.finditer(r'\[TOOL:\s*(.+?)\((.*?)\)\s*\]', response_text)
    
    target_channel = message.channel

    for match in tool_matches:
        func_name = match.group(1).strip()
        args_str = match.group(2).strip()
        
        # Tools that require Admin
        admin_tools = [
            "create_role", "delete_role", "give_role", "remove_role",
            "kick_user", "ban_user", "timeout_user", "change_nickname", "purge_messages"
        ]

        if func_name in admin_tools and not is_admin:
            await target_channel.send(embed=create_error_embed("Отказ в доступе", f"Инструмент `{func_name}` требует прав Администратора."))
            continue

        try:
            if func_name == "create_role":
                name_match = re.search(r'name=["\'](.*?)["\']', args_str)
                color_match = re.search(r'color=["\']#(.*?)["\']', args_str)
                if name_match:
                    name = name_match.group(1)
                    color = discord.Color(int(color_match.group(1), 16)) if color_match else discord.Color.default()
                    role = await message.guild.create_role(name=name, color=color, reason="AI Action")
                    await target_channel.send(embed=create_success_embed("Роль Создана", f"Создана роль: **{role.name}**"))

            elif func_name == "delete_role":
                rid_match = re.search(r'role_id=(\d+)', args_str)
                if rid_match:
                    role = message.guild.get_role(int(rid_match.group(1)))
                    if role:
                        name = role.name
                        await role.delete(reason="AI Action")
                        await target_channel.send(embed=create_success_embed("Роль Удалена", f"Удалена роль: **{name}**"))

            elif func_name == "give_role":
                uid_match = re.search(r'user_id=(\d+)', args_str)
                rid_match = re.search(r'role_id=(\d+)', args_str)
                rname_match = re.search(r'role_name=["\'](.*?)["\']', args_str)
                
                if uid_match:
                    member = message.guild.get_member(int(uid_match.group(1)))
                    role = None
                    if rid_match:
                        role = message.guild.get_role(int(rid_match.group(1)))
                    elif rname_match:
                        role = discord.utils.get(message.guild.roles, name=rname_match.group(1))
                    
                    if member and role:
                        await member.add_roles(role)
                        await target_channel.send(embed=create_success_embed("Выдача Роли", f"Роль **{role.name}** выдана {member.mention}"))

            elif func_name == "remove_role":
                uid_match = re.search(r'user_id=(\d+)', args_str)
                rid_match = re.search(r'role_id=(\d+)', args_str)
                rname_match = re.search(r'role_name=["\'](.*?)["\']', args_str)
                
                if uid_match:
                    member = message.guild.get_member(int(uid_match.group(1)))
                    role = None
                    if rid_match:
                        role = message.guild.get_role(int(rid_match.group(1)))
                    elif rname_match:
                        role = discord.utils.get(message.guild.roles, name=rname_match.group(1))
                    
                    if member and role:
                        await member.remove_roles(role)
                        await target_channel.send(embed=create_success_embed("Снятие Роли", f"Роль **{role.name}** снята с {member.mention}"))

            elif func_name == "kick_user":
                uid_match = re.search(r'user_id=(\d+)', args_str)
                reason_match = re.search(r'reason=["\'](.+?)["\']', args_str)
                if uid_match:
                    member = message.guild.get_member(int(uid_match.group(1)))
                    reason = reason_match.group(1) if reason_match else "Без причины"
                    if member:
                        await member.kick(reason=reason)
                        await target_channel.send(embed=create_success_embed("Пользователь Исключен", f"👢 **{member.display_name}** | Причина: {reason}"))

            elif func_name == "ban_user":
                uid_match = re.search(r'user_id=(\d+)', args_str)
                reason_match = re.search(r'reason=["\'](.+?)["\']', args_str)
                if uid_match:
                    member = message.guild.get_member(int(uid_match.group(1)))
                    reason = reason_match.group(1) if reason_match else "Без причины"
                    if member:
                        await member.ban(reason=reason)
                        await target_channel.send(embed=create_success_embed("Пользователь Забанен", f"🔨 **{member.display_name}** | Причина: {reason}"))

            elif func_name == "timeout_user":
                uid_match = re.search(r'user_id=(\d+)', args_str)
                dur_match = re.search(r'duration=(\d+)', args_str)
                if uid_match and dur_match:
                    member = message.guild.get_member(int(uid_match.group(1)))
                    duration = int(dur_match.group(1))
                    if member:
                        until = discord.utils.utcnow() + timedelta(seconds=duration)
                        await member.timeout(until, reason="AI Action")
                        await target_channel.send(embed=create_success_embed("Тайм-аут Выдан", f"⏱ **{member.display_name}** заглушен на {duration} сек."))

            elif func_name == "change_nickname":
                uid_match = re.search(r'user_id=(\d+)', args_str)
                nick_match = re.search(r'nickname=["\'](.+?)["\']', args_str)
                if uid_match and nick_match:
                    member = message.guild.get_member(int(uid_match.group(1)))
                    if member:
                        old_nick = member.display_name
                        await member.edit(nick=nick_match.group(1))
                        await target_channel.send(embed=create_success_embed("Ник Изменен", f"✏️ **{old_nick}** → **{nick_match.group(1)}**"))

            elif func_name == "send_dm":
                uid_match = re.search(r'user_id=(\d+)', args_str)
                msg_match = re.search(r'message=["\'](.+?)["\']', args_str)
                if uid_match and msg_match:
                    member = message.guild.get_member(int(uid_match.group(1)))
                    if member:
                        try:
                            await member.send(msg_match.group(1))
                            await target_channel.send(embed=create_success_embed("DM Отправлен", f"📩 Сообщение доставлено **{member.display_name}**"))
                        except:
                            await target_channel.send(embed=create_error_embed("Ошибка Доставки", f"Не удалось отправить ЛС **{member.display_name}**"))

            elif func_name == "purge_messages":
                count_match = re.search(r'count=(\d+)', args_str)
                count = int(count_match.group(1)) if count_match else 5
                count = min(count, 100)
                deleted = await message.channel.purge(limit=count)
                await target_channel.send(embed=create_success_embed("Очистка", f"🧹 Удалено **{len(deleted)}** сообщений"), delete_after=5)

            elif func_name == "web_search":
                # Handled directly in bot.py for brevity in the response, but can be routed here if preferred.
                pass

        except Exception as e:
            print(f"[TOOL ERROR] Function {func_name} failed: {e}")
            await target_channel.send(embed=create_error_embed("Сбой Инструмента", f"Ошибка выполнения `{func_name}`: {str(e)}"))

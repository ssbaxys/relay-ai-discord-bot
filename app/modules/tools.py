import re
import discord
from datetime import timedelta
from app.ui.embeds import create_success_embed, create_error_embed

async def execute_tools(response_text: str, message: discord.Message):
    """Parses and executes [TOOL: ...] commands from the AI's response with enhanced multiline parsing."""
    
    is_admin = False
    if isinstance(message.author, discord.Member) and message.author.guild_permissions.administrator:
        is_admin = True
        
    # Updated Regex to handle multiline arguments like send_dm("foo\nbar")
    tool_matches = re.finditer(r'\[TOOL:\s*(.+?)\((.*?)\)\s*\]', response_text, re.DOTALL)
    
    target_channel = message.channel

    for match in tool_matches:
        func_name = match.group(1).strip()
        args_str = match.group(2).strip()
        
        # Admin tools list
        admin_tools = [
            "create_role", "delete_role", "give_role", "remove_role",
            "kick_user", "ban_user", "timeout_user", "change_nickname", "purge_messages"
        ]

        if func_name in admin_tools and not is_admin:
            await target_channel.send(embed=create_error_embed("Отказ в доступе", f"Инструмент `{func_name}` требует прав Администратора."))
            continue

        try:
            # We use eval-like string parsing safely since we know the expected format: kwarg="value"
            
            # Helper to extract a parameter safely
            def get_arg(key: str, s: str):
                m = re.search(f'{key}=["\'](.*?)["\']', s, re.DOTALL)
                return m.group(1) if m else None
                
            def get_arg_int(key: str, s: str):
                m = re.search(f'{key}=(\d+)', s)
                return int(m.group(1)) if m else None

            if func_name == "create_role":
                name = get_arg("name", args_str)
                color_hex = get_arg("color", args_str)
                if name:
                    color = discord.Color(int(color_hex.replace("#",""), 16)) if color_hex else discord.Color.default()
                    role = await message.guild.create_role(name=name, color=color, reason="AI Action")
                    await target_channel.send(embed=create_success_embed("Роль Создана", f"Создана роль: **{role.name}**"))

            elif func_name == "delete_role":
                rid = get_arg_int("role_id", args_str)
                if rid:
                    role = message.guild.get_role(rid)
                    if role:
                        name = role.name
                        await role.delete(reason="AI Action")
                        await target_channel.send(embed=create_success_embed("Роль Удалена", f"Удалена роль: **{name}**"))

            elif func_name == "give_role":
                uid = get_arg_int("user_id", args_str)
                rid = get_arg_int("role_id", args_str)
                rname = get_arg("role_name", args_str)
                
                if uid:
                    member = message.guild.get_member(uid)
                    role = message.guild.get_role(rid) if rid else discord.utils.get(message.guild.roles, name=rname)
                    if member and role:
                        await member.add_roles(role)
                        await target_channel.send(embed=create_success_embed("Выдача", f"Роль **{role.name}** выдана {member.mention}"))

            elif func_name == "remove_role":
                uid = get_arg_int("user_id", args_str)
                rid = get_arg_int("role_id", args_str)
                rname = get_arg("role_name", args_str)
                
                if uid:
                    member = message.guild.get_member(uid)
                    role = message.guild.get_role(rid) if rid else discord.utils.get(message.guild.roles, name=rname)
                    if member and role:
                        await member.remove_roles(role)
                        await target_channel.send(embed=create_success_embed("Снятие", f"Роль **{role.name}** снята с {member.mention}"))

            elif func_name == "kick_user":
                uid = get_arg_int("user_id", args_str)
                reason = get_arg("reason", args_str) or "Без причины"
                if uid:
                    member = message.guild.get_member(uid)
                    if member:
                        await member.kick(reason=reason)
                        await target_channel.send(embed=create_success_embed("Kick", f"👢 **{member.display_name}** | Причина: {reason}"))

            elif func_name == "ban_user":
                uid = get_arg_int("user_id", args_str)
                reason = get_arg("reason", args_str) or "Без причины"
                if uid:
                    member = message.guild.get_member(uid)
                    if member:
                        await member.ban(reason=reason)
                        await target_channel.send(embed=create_success_embed("Ban", f"🔨 **{member.display_name}** | Причина: {reason}"))

            elif func_name == "timeout_user":
                uid = get_arg_int("user_id", args_str)
                dur = get_arg_int("duration", args_str)
                if uid and dur:
                    member = message.guild.get_member(uid)
                    if member:
                        until = discord.utils.utcnow() + timedelta(seconds=dur)
                        await member.timeout(until, reason="AI Action")
                        await target_channel.send(embed=create_success_embed("Тайм-аут", f"⏱ **{member.display_name}** заглушен на {dur} сек."))

            elif func_name == "change_nickname":
                uid = get_arg_int("user_id", args_str)
                nick = get_arg("nickname", args_str)
                if uid and nick:
                    member = message.guild.get_member(uid)
                    if member:
                        old_nick = member.display_name
                        await member.edit(nick=nick)
                        await target_channel.send(embed=create_success_embed("Ник", f"✏️ **{old_nick}** → **{nick}**"))

            elif func_name == "send_dm":
                uid = get_arg_int("user_id", args_str)
                msg_text = get_arg("message", args_str)
                if uid and msg_text:
                    member = message.guild.get_member(uid)
                    if member:
                        try:
                            # Use regular message for DM payload
                            await member.send(f"**Агент связи:**\n{msg_text}")
                            await target_channel.send(embed=create_success_embed("DM", f"📩 Сообщение доставлено **{member.display_name}**"))
                        except Exception:
                            await target_channel.send(embed=create_error_embed("Ошибка", f"Не удалось отправить ЛС **{member.display_name}** (закрыты личные сообщения)."))

            elif func_name == "purge_messages":
                count = get_arg_int("count", args_str) or 5
                count = min(count, 100)
                deleted = await message.channel.purge(limit=count)
                await target_channel.send(embed=create_success_embed("Очистка", f"🧹 Удалено **{len(deleted)}** сообщений"))

        except Exception as e:
            print(f"[TOOL ERROR] Function {func_name} failed: {e}")
            await target_channel.send(embed=create_error_embed("Сбой", f"Ошибка функции `{func_name}`: {str(e)}"))

import os
import json
import base64
import discord
import glob
from discord.ext import commands
import aiohttp

from main import bot, add_help, has_owner_perm

CREATOR_ID = 938059286054072371

if not os.path.exists("backups"):
    os.makedirs("backups")


async def download_icon(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            return None


@bot.group()
@has_owner_perm()
async def backup(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("Please use a valid subcommand: create or load.")
add_help('Backup', 'backup <create/load>', 'Server Backup commands')


@backup.command(name='create')
@has_owner_perm()
async def backup_create(ctx, *, name: str = None):
    if name is None:
        backup_name = str(ctx.guild.id)
    else:
        backup_name = name

    guild = ctx.guild

    icon_url = guild.icon.url if guild.icon else None
    icon_bytes = await download_icon(icon_url) if icon_url else None
    encoded_icon = base64.b64encode(icon_bytes).decode('utf-8') if icon_bytes else None

    backup_data = {
        "creator_id": ctx.author.id,
        "name": guild.name,
        "icon": encoded_icon,
        "afk_channel": guild.afk_channel.id if guild.afk_channel else None,
        "afk_timeout": guild.afk_timeout,
        "verification_level": guild.verification_level.value,
        "default_notifications": guild.default_notifications.value,
        "explicit_content_filter": guild.explicit_content_filter.value,
        "system_channel": guild.system_channel.id if guild.system_channel else None,
        "rules_channel": guild.rules_channel.id if guild.rules_channel else None,
        "public_updates_channel": guild.public_updates_channel.id if guild.public_updates_channel else None,
        "community": list(guild.features),
        "categories": {},
        "none_category": [],
        "roles": []
    }

    for role in guild.roles:
        if role.is_default() or (len(role.members) == 1 and role.members[0].bot):
            continue
        backup_data["roles"].append({
            "id": role.id,
            "name": role.name,
            "permissions": role.permissions.value,
            "color": role.color.value,
            "hoist": role.hoist,
            "mentionable": role.mentionable,
        })

    for category in guild.categories:
        backup_data["categories"][category.id] = {
            "name": category.name,
            "channels": []
        }
        for channel in category.channels:
            is_private = not channel.overwrites_for(guild.default_role).is_empty()
            channel_data = {
                "id": channel.id,
                "name": channel.name,
                "type": channel.type.name,
                "position": channel.position,
                "is_private": is_private,
                "permissions": [
                    {
                        "id": overwrite.id,
                        "allow": perm.pair()[0].value,
                        "deny": perm.pair()[1].value,
                        "type": "role" if isinstance(overwrite, discord.Role) else "member"
                    }
                    for overwrite, perm in channel.overwrites.items()
                ]
            }
            backup_data["categories"][category.id]["channels"].append(channel_data)

    for channel in guild.channels:
        if not isinstance(channel, discord.CategoryChannel) and channel.category is None:
            is_private = not channel.overwrites_for(guild.default_role).is_empty()
            channel_data = {
                "id": channel.id,
                "name": channel.name,
                "type": channel.type.name,
                "position": channel.position,
                "is_private": is_private,
                "permissions": [
                    {
                        "id": overwrite.id,
                        "allow": perm.pair()[0].value,
                        "deny": perm.pair()[1].value,
                        "type": "role" if isinstance(overwrite, discord.Role) else "member"
                    }
                    for overwrite, perm in channel.overwrites.items()
                ]
            }
            backup_data["none_category"].append(channel_data)

    backup_path = f"backups/{ctx.author.id}_{backup_name}_backup.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=4)

    await ctx.send("Server backup created successfully.")


@backup.command(name='load')
@has_owner_perm()
async def load_backup(ctx, *, name: str = None):
    if name is None:
        backup_name = str(ctx.guild.id)
    else:
        backup_name = name

    guild: discord.Guild = ctx.guild

    backup_path = f"backups/{ctx.author.id}_{backup_name}_backup.json"
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)
    except FileNotFoundError:
        if ctx.author.id != CREATOR_ID:
            await ctx.send("No backup found for this server.")
            return
        backup_path = f"backups/*_{backup_name}_backup.json"
        backup_files = glob.glob(backup_path)
        if not backup_files:
            await ctx.send("No backup found for this server.")
            return
        backup_path = backup_files[0]
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

    if backup_data[
        "creator_id"] != ctx.author.id and ctx.author.id != CREATOR_ID and not ctx.author.guild_permissions.administrator:
        await ctx.send("You do not have permission to load this backup.")
        return

    await guild.edit(community=False)

    if backup_data["icon"]:
        icon_bytes = base64.b64decode(backup_data["icon"])
        try:
            await guild.edit(
                name=backup_data["name"],
                icon=icon_bytes,
                #afk_channel=guild.get_channel(backup_data["afk_channel"]),
                afk_timeout=backup_data["afk_timeout"],
                verification_level=discord.VerificationLevel(backup_data["verification_level"]),
                default_notifications=discord.NotificationLevel(backup_data["default_notifications"]),
                explicit_content_filter=discord.ContentFilter(backup_data["explicit_content_filter"]),
                #system_channel=guild.get_channel(backup_data["system_channel"]),
                #rules_channel=guild.get_channel(backup_data["rules_channel"]),
                #public_updates_channel=guild.get_channel(backup_data["public_updates_channel"])
            )
        except discord.HTTPException:
            await ctx.send("Failed to apply the server icon.")
    else:
        try:
            await guild.edit(
                name=backup_data["name"],
                #afk_channel=guild.get_channel(backup_data["afk_channel"]),
                afk_timeout=backup_data["afk_timeout"],
                verification_level=discord.VerificationLevel(backup_data["verification_level"]),
                default_notifications=discord.NotificationLevel(backup_data["default_notifications"]),
                explicit_content_filter=discord.ContentFilter(backup_data["explicit_content_filter"]),
                #system_channel=guild.get_channel(backup_data["system_channel"]),
                #rules_channel=guild.get_channel(backup_data["rules_channel"]),
                #public_updates_channel=guild.get_channel(backup_data["public_updates_channel"])
            )
        except discord.HTTPException:
            await ctx.send("Failed to update server settings.")

    for channel in guild.channels:
        try:
            await channel.delete()
        except discord.Forbidden:
            continue

    for role in guild.roles:
        if role.is_default() or (len(role.members) == 1 and role.members[0].bot):
            continue
        try:
            await role.delete()
        except discord.Forbidden:
            continue
        except:
            continue


    restored_roles = {}
    for role_data in reversed(backup_data["roles"]):
        role = await guild.create_role(
            name=role_data["name"],
            permissions=discord.Permissions(role_data["permissions"]),
            color=discord.Color(role_data["color"]),
            hoist=role_data["hoist"],
            mentionable=role_data["mentionable"]
        )
        restored_roles[role_data["id"]] = role


    restored_categories = {}
    for category_id, category_data in backup_data["categories"].items():
        category = await guild.create_category(name=category_data["name"])
        restored_categories[category_id] = category

    for category_id, category_data in backup_data["categories"].items():
        category = restored_categories.get(category_id)
        for channel_data in category_data["channels"]:
            channel_type = getattr(discord.ChannelType, channel_data["type"])
            is_private = channel_data.get("is_private", False)
            overwrites = {
                guild.get_role(perm["id"]) if perm["type"] == "role" and guild.get_role(
                    perm["id"]) is not None else guild.get_member(perm["id"]) if perm[
                                                                                     "type"] == "member" and guild.get_member(
                    perm["id"]) is not None else None: discord.PermissionOverwrite.from_pair(
                    discord.Permissions(perm["allow"]), discord.Permissions(perm["deny"])
                )
                for perm in channel_data["permissions"]
            }
            overwrites = {k: v for k, v in overwrites.items() if k is not None}

            if is_private:
                overwrites[guild.default_role] = discord.PermissionOverwrite(read_messages=False)

            if channel_type == discord.ChannelType.text:
                await guild.create_text_channel(
                    name=channel_data["name"],
                    category=category,
                    overwrites=overwrites,
                    position=channel_data["position"]
                )
            else:
                await guild.create_voice_channel(
                    name=channel_data["name"],
                    category=category,
                    overwrites=overwrites,
                    position=channel_data["position"]
                )

    for channel_data in backup_data["none_category"]:
        channel_type = getattr(discord.ChannelType, channel_data["type"])
        overwrites = {
            guild.get_role(perm["id"]) if perm["type"] == "role" and guild.get_role(
                perm["id"]) is not None else guild.get_member(perm["id"]) if perm[
                                                                                 "type"] == "member" and guild.get_member(
                perm["id"]) is not None else None: discord.PermissionOverwrite.from_pair(
                discord.Permissions(perm["allow"]), discord.Permissions(perm["deny"])
            )
            for perm in channel_data["permissions"]
        }
        overwrites = {k: v for k, v in overwrites.items() if k is not None}
        if channel_type == discord.ChannelType.text:
            await guild.create_text_channel(
                name=channel_data["name"],
                overwrites=overwrites,
                position=channel_data["position"]
            )
        else:
            await guild.create_voice_channel(
                name=channel_data["name"],
                overwrites=overwrites,
                position=channel_data["position"]
            )


@backup.command(name='list')
async def backup_list(ctx):
    user_backup_pattern = f"backups/{ctx.author.id}_*_backup.json"
    user_backups = glob.glob(user_backup_pattern)

    if ctx.author.id == CREATOR_ID:
        creator_backup_pattern = "backups/*_backup.json"
        all_backups = glob.glob(creator_backup_pattern)
    else:
        all_backups = []

    all_backups.extend(user_backups)
    all_backups = list(set(all_backups))

    if not all_backups:
        await ctx.send("No backups found.")
        return

    backup_list = []
    for backup_path in all_backups:
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
                backup_name = backup_path.split("_")[-2]
                backup_list.append(f"**Name:** {backup_name} | **Creator ID:** {backup_data['creator_id']}")
        except Exception:
            continue

    backup_message = "\n".join(backup_list)
    await ctx.send(f"Available Backups:\n{backup_message}")

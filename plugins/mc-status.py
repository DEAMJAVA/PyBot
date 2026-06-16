import asyncio
import json
import os
from datetime import datetime

import discord
from discord.ext import tasks
from mcstatus import JavaServer


from main import bot, log, logw, add_help, is_owner, when_bot_ready

STATUS_FILE = "server_status.json"
server_status_messages = {}


def load_server_status_messages():
    global server_status_messages
    log('loading server messages')
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            server_status_messages = json.load(f)


def save_server_status_messages():
    with open(STATUS_FILE, "w") as f:
        json.dump(server_status_messages, f)



NETWORK_STATUS_FILE = "network_status.json"
network_status_messages = {}

def load_network_status_messages():
    global network_status_messages
    log('loading network status messages')
    if os.path.exists(NETWORK_STATUS_FILE):
        with open(NETWORK_STATUS_FILE, "r") as f:
            network_status_messages = json.load(f)

def save_network_status_messages():
    with open(NETWORK_STATUS_FILE, "w") as f:
        json.dump(network_status_messages, f)


async def fetch_status(ip):
    try:
        server = JavaServer.lookup(ip)
        status = server.status()
        version = status.version.name
        icon = status.icon
        motd = status.motd.parse(raw=status.description).to_plain()
        return status.players.online, status.players.max, status.latency, version, icon, motd
    except Exception as e:
        logw(f"Error fetching status: {e}")
        return None, None, None, None, None, None


def create_status_embed(ip, players_online, player_max, latency, version, icon, motd, label):
    title = f"Minecraft Server Status: {label}" if label else f"Minecraft Server Status: {ip}"
    embed = discord.Embed(title=title,
                          color=discord.Color.green() if players_online is not None else discord.Color.red(),
                          description=motd,
                          timestamp=datetime.now())
    if players_online is not None:
        embed.add_field(name="Status", value="Online", inline=False)
        embed.add_field(name="Players Online", value=f'{players_online}/{player_max}', inline=True)
        embed.add_field(name="Latency", value=f"{int(latency)}ms", inline=True)
        embed.add_field(name="Version", value=version, inline=True)
    else:
        embed.add_field(name="Status", value="Offline", inline=False)
    return embed


def create_network_embed(name, statuses):
    """
    Create a network-style embed showing multiple servers' statuses,
    with color based on how many are online.
    """
    total_servers = len(statuses)
    online_servers = sum(1 for s in statuses if s["players_online"] is not None)

    if online_servers == total_servers and total_servers > 0:
        color = discord.Color.green()
    elif online_servers > 0:
        color = discord.Color.gold()
    else:
        color = discord.Color.red()

    embed = discord.Embed(
        title=f"{name} Status",
        color=color,
        timestamp=datetime.now()
    )

    for s in statuses:
        label = s["label"]
        ip = s["ip"]
        online = s["players_online"] is not None

        status_emoji = "🟢 Online" if online else "🔴 Offline"
        players = f"{s['players_online']}/{s['players_max']}" if online else "N/A"
        latency = f"{int(s['latency'])}ms" if online else "N/A"
        version = s["version"] if online else "N/A"
        motd = s["motd"] or "N/A"

        value = (
            f"```"
            f"Status  : {status_emoji}\n"
            f"Players : {players}\n"
            f"Latency : {latency}\n"
            f"Version : {version}\n"
            f"```"
        )

        embed.add_field(name=f"🌐 {label}", value=value, inline=False)

    return embed


@tasks.loop(seconds=30)
async def update_status():
    debug = False
    try:
        to_remove = []
        for ip, message_id in list(server_status_messages.items()):
            try:
                if debug:
                    print(f"[DEBUG] Updating server: {ip}")
                await asyncio.sleep(1)
                channel = bot.get_channel(message_id['channel_id'])
                if channel is None:
                    to_remove.append(ip)
                    continue
                message = await channel.fetch_message(message_id['message_id'])
                players_online, players_max, latency, version, icon, motd = await fetch_status(ip)
                label = message_id.get('label')
                embed = create_status_embed(ip, players_online, players_max, latency, version, icon, motd, label)
                await message.edit(embed=embed)
            except discord.NotFound:
                to_remove.append(ip)
            except Exception as e:
                print(f"Error updating status for {ip}: {e}")
        for ip in to_remove:
            del server_status_messages[ip]
        save_server_status_messages()

        to_remove_network = []
        for name, data in list(network_status_messages.items()):
            try:
                if debug:
                    print(f"[DEBUG] Updating network: {name}")
                await asyncio.sleep(1)
                channel = bot.get_channel(data['channel_id'])
                if channel is None:
                    to_remove_network.append(name)
                    continue
                message = await channel.fetch_message(data['message_id'])

                statuses = []
                for server_info in data["servers"]:
                    ip = server_info["ip"]
                    label = server_info["label"]
                    players_online, players_max, latency, version, icon, motd = await fetch_status(ip)
                    statuses.append({
                        "label": label,
                        "ip": ip,
                        "players_online": players_online,
                        "players_max": players_max,
                        "latency": latency,
                        "version": version,
                        "motd": motd,
                        "icon": icon
                    })

                embed = create_network_embed(name, statuses)
                await message.edit(embed=embed)
            except discord.NotFound:
                to_remove_network.append(name)
            except Exception as e:
                print(f"Error updating network status for {name}: {e}")
        for name in to_remove_network:
            del network_status_messages[name]
        save_network_status_messages()

        if debug:
            print("[DEBUG] Status messages saved.")
    except Exception as e:
        print(e.args)





@bot.command()
async def mcstatus(ctx, ip: str, *, label: str = None):
    players_online, players_max, latency, version, icon, motd = await fetch_status(ip)
    embed = create_status_embed(ip, players_online, players_max, latency, version, icon, motd, label)
    message = await ctx.send(embed=embed)
    server_status_messages[ip] = {
        "channel_id": ctx.channel.id,
        "message_id": message.id,
        "label": label
    }
    save_server_status_messages()
    await ctx.send(f"Tracking server `{ip}`" + (f" as `{label}`" if label else ""))
add_help('Mc Status', 'mcstatus <server ip> [label]', 'sends an auto updating server status message for a minecraft server')


@bot.command(name='networkstatus')
async def networkstatus(ctx, *, servers: str):
    """
    Command format:
    .networkstatus NetworkName | ServerName1, IP1 | ServerName2, IP2 | ...
    The first part before the first | is the network name (used for storing/updating).
    """
    parts = [p.strip() for p in servers.split('|')]
    if len(parts) < 2:
        await ctx.send("Invalid format. Use: `.networkstatus NetworkName | ServerName1, IP1 | ServerName2, IP2 | ...`")
        return

    network_name = parts[0]
    server_entries = parts[1:]
    server_data = []

    for entry in server_entries:
        if ',' not in entry:
            await ctx.send(f"Invalid server entry: `{entry}`. Use `Name, IP` format.")
            return
        label, ip = map(str.strip, entry.split(',', 1))
        server_data.append({"label": label, "ip": ip})

    statuses = []
    for server in server_data:
        players_online, players_max, latency, version, icon, motd = await fetch_status(server["ip"])
        statuses.append({
            "label": server["label"],
            "ip": server["ip"],
            "players_online": players_online,
            "players_max": players_max,
            "latency": latency,
            "version": version,
            "motd": motd,
            "icon": icon
        })

    embed = create_network_embed(network_name, statuses)
    message = await ctx.send(embed=embed)

    network_status_messages[network_name] = {
        "channel_id": ctx.channel.id,
        "message_id": message.id,
        "servers": server_data
    }
    save_network_status_messages()
    await ctx.send(f"Tracking network `{network_name}` with {len(server_data)} servers.")


add_help('Mc Status', 'networkstatus <Network Name> | <server name>, <server ip> | [server name 2], [server ip 2]...', 'sends an auto updating server status message for a minecraft server network')


@is_owner()
@bot.command(name='mcstatus.updateloop')
async def mcstatus_update_loop(ctx):
    if not update_status.is_running():
        update_status.start()
        await ctx.send('Update loop started.')
    else:
        await ctx.send('Update loop is already running.')


@when_bot_ready
def on_bot_ready_mcstatus():
    load_server_status_messages()
    load_network_status_messages()
    update_status.start()

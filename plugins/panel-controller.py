import json

import discord
import requests
from discord.ui import View, Select

from main import bot, create_button_view


class PanelController:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def send_request(self, endpoint, method='GET', data=None):
        url = f'{self.base_url}/{endpoint}'
        response = requests.request(method, url, headers=self.headers, json=data)
        if response.status_code in range(200, 300):
            return response
        else:
            print(f'Error: {response.status_code} - {response.text}')
            return None

    def list_servers(self):
        response = self.send_request('').json()
        if response:
            return response['data']
        return []

    def get_server_details(self, server_id):
        # Fetch server resource usage
        usage = self.send_request(f'servers/{server_id}/resources').json()
        if not usage:
            print("Failed to fetch server details.")
            return

        attributes = usage['attributes']
        state = attributes['current_state']
        cpu_usage = attributes['resources']['cpu_absolute']
        memory_usage = attributes['resources']['memory_bytes']
        network_rx = attributes['resources']['network_rx_bytes']
        network_tx = attributes['resources']['network_tx_bytes']

        return {
            'status': state,
            'cpu_usage': f"{cpu_usage}%",
            'memory_usage': f"{memory_usage / 1024 / 1024:.2f} MB",
            'network_usage': f"Down: {network_rx / 1024 / 1024:.2f} MB, Up: {network_tx / 1024 / 1024:.2f} MB"
        }

    def start_server(self, server_id):
        return self.send_request(f'servers/{server_id}/power', method='POST', data={'signal': 'start'})

    def stop_server(self, server_id):
        return self.send_request(f'servers/{server_id}/power', method='POST', data={'signal': 'stop'})

    def restart_server(self, server_id):
        return self.send_request(f'servers/{server_id}/power', method='POST', data={'signal': 'restart'})

    def kill_server(self, server_id):
        return self.send_request(f'servers/{server_id}/power', method='POST', data={'signal': 'kill'})


async def panel_button_handler(ctx: discord.Interaction):
    action, id, website = ctx.data['custom_id'].split('>')
    with open('panels.json', 'r') as file:
        panel_data = json.load(file)
    if str(ctx.user.id) not in panel_data:
        await ctx.respond("You don't own this server!", ephemeral=True)
        return
    api_key = panel_data[str(ctx.user.id)].get(website)
    if not api_key:
        await ctx.respond("You don't own this server!", ephemeral=True)
        return
    if action == 'start':
        PanelController(base_url=f'https://{website}/api/client', api_key=api_key).start_server(server_id=id)
        await ctx.respond('Server starting', ephemeral=True)
    elif action == 'stop':
        PanelController(base_url=f'https://{website}/api/client', api_key=api_key).stop_server(server_id=id)
        await ctx.respond('Server stopping', ephemeral=True)
    elif action == 'restart':
        PanelController(base_url=f'https://{website}/api/client', api_key=api_key).restart_server(server_id=id)
        await ctx.respond('Server restarting', ephemeral=True)
    elif action == 'kill':
        PanelController(base_url=f'https://{website}/api/client', api_key=api_key).kill_server(server_id=id)
        await ctx.respond('Server killed', ephemeral=True)
    elif action == 'details':
        details = PanelController(base_url=f'https://{website}/api/client', api_key=api_key).get_server_details(
            server_id=id)
        response = (
            f"Status: {details['status']}\n"
            f"CPU Usage: {details['cpu_usage']}\n"
            f"Memory Usage: {details['memory_usage']}\n"
            f"Network Usage: {details['network_usage']}\n"
        )
        await ctx.respond(response, ephemeral=True)


class WebsiteSelect(Select):
    def __init__(self, websites, ctx):
        options = [discord.SelectOption(label=website, value=website) for website in websites]
        super().__init__(placeholder="Select a website", min_values=1, max_values=1, options=options)
        self.websites = websites
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        selected_website = self.values[0]
        userid = str(self.ctx.author.id)
        with open('panels.json', 'r') as file:
            panel_data = json.load(file)

        api_key = panel_data[userid][selected_website]
        servers = PanelController(base_url=f'https://{selected_website}/api/client', api_key=api_key).list_servers()

        if servers:
            await interaction.response.edit_message(content=f"Selected website: {selected_website}",
                                                    view=ServerView(servers, selected_website))
        else:
            await interaction.response.edit_message(content="No servers found for this website.", view=None)


class ServerSelect(Select):
    def __init__(self, servers, selected_website):
        options = [
            discord.SelectOption(label=server['attributes']['name'], value=server['attributes']['identifier'])
            for server in servers
        ]
        super().__init__(placeholder="Select a server", min_values=1, max_values=1, options=options)
        self.servers = servers
        self.selected_website = selected_website

    async def callback(self, interaction: discord.Interaction):
        selected_server_id = self.values[0]

        selected_server = None
        for server in self.servers:
            if server['attributes']['identifier'] == selected_server_id:
                selected_server = server
                break

        if not selected_server:
            await interaction.response.edit_message(content="Server not found!", view=None)
            return

        view = View()
        view.add_item(create_button_view(
            label='Start',
            custom_id=f'start>{selected_server_id}>{self.selected_website}',
            callback=panel_button_handler,
            style=discord.ButtonStyle.green
        ).children[0])

        view.add_item(create_button_view(
            label='Stop',
            custom_id=f'stop>{selected_server_id}>{self.selected_website}',
            callback=panel_button_handler,
            style=discord.ButtonStyle.red
        ).children[0])

        view.add_item(create_button_view(
            label='Restart',
            custom_id=f'restart>{selected_server_id}>{self.selected_website}',
            callback=panel_button_handler,
            style=discord.ButtonStyle.grey
        ).children[0])

        view.add_item(create_button_view(
            label='Kill',
            custom_id=f'kill>{selected_server_id}>{self.selected_website}',
            callback=panel_button_handler,
            style=discord.ButtonStyle.red
        ).children[0])

        view.add_item(create_button_view(
            label='Get Details',
            custom_id=f'details>{selected_server_id}>{self.selected_website}',
            callback=panel_button_handler,
            style=discord.ButtonStyle.grey
        ).children[0])

        server_name = selected_server['attributes']['name']
        identifier = selected_server['attributes']['identifier']

        allocation_data = selected_server['attributes']['relationships']['allocations']['data'][0]['attributes']
        ip_address = allocation_data.get('ip_alias', 'No IP Available')
        port = allocation_data.get('port', 'No Port Available')

        response = (
            f"**Server Name**: {server_name}\n"
            f"**Server ID**: {identifier}\n"
            f"**IP Address**: {ip_address}:{port}\n\n"
            "Choose an action:"
        )

        await interaction.response.edit_message(content=response, view=view)


class WebsiteView(View):
    def __init__(self, websites, ctx):
        super().__init__()
        self.add_item(WebsiteSelect(websites, ctx))


class ServerView(View):
    def __init__(self, servers, selected_website):
        super().__init__()
        self.add_item(ServerSelect(servers, selected_website))


panel = bot.create_group(name='panel')


@panel.command(name='get', description="Get server controls")
async def panel_get(ctx: discord.ApplicationContext):
    userid = str(ctx.author.id)
    try:
        with open('panels.json', 'r') as file:
            panel_data = json.load(file)
    except FileNotFoundError:
        panel_data = {}

    if userid not in panel_data:
        await ctx.respond("You don't have any websites registered", ephemeral=True)
        return

    await ctx.respond("Select a website", view=WebsiteView(panel_data[userid], ctx))


@panel.command(name='add')
async def panel_get(ctx: discord.Interaction, website: str = None, api_key: str = None):
    userid = str(ctx.user.id)
    try:
        with open('panels.json', 'r') as file:
            panel_data = json.load(file)
    except FileNotFoundError:
        panel_data = {}

    if userid not in panel_data:
        panel_data[userid] = {}
    panel_data[userid][website] = api_key

    with open('panels.json', 'w') as file:
        json.dump(panel_data, file, indent=4)

    await ctx.respond("Website added successfully", ephemeral=True)


@panel.command(name='del')
async def panel_del(ctx: discord.Interaction, website: str = None):
    userid = str(ctx.user.id)
    try:
        with open('panels.json', 'r') as file:
            panel_data = json.load(file)
    except FileNotFoundError:
        panel_data = {}

    if userid not in panel_data:
        await ctx.respond("You don't have any websites registered", ephemeral=True)
        return

    if website not in panel_data[userid]:
        await ctx.respond(f"You don't have the website {website} registered", ephemeral=True)
        return

    del panel_data[userid][website]
    if not panel_data[userid]:
        del panel_data[userid]

    with open('panels.json', 'w') as file:
        json.dump(panel_data, file, indent=4)

    await ctx.respond('Website deleted successfully', ephemeral=True)

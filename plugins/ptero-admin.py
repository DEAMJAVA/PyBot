import discord
import pymysqlhelper
import requests
from discord import SelectOption
from discord.ui import View
import json
import os

from main import bot, button_configurations, create_modal_view, button_views, create_select_view, is_owner, add_help

DEFAULT_CONFIG = {
    "PANEL_URL": "Panel Url : https://panel.example.com",
    "API_KEY": "Admin API key",
    "default_max_servers": 2,
    "max_users": 10,
    "options": {
        "example": {
            "egg_id": 0,
            "docker_image": "",
            "startup_cmd": "",
            "environment": {
                'variable1': ""
            },
            "memory": 1024,
            "swap":0,
            "disk": 1024,
            "io": 500,
            "cpu": 100,
            "databases": 1,
            "allocations": 1,
            "backups": 1,
            "skip_scripts": False
        }
    }
}

CONFIG_FILE_ptero = "plugins/pterodactyl/config.json"

def load_config_ptero():
    os.makedirs(os.path.dirname(CONFIG_FILE_ptero), exist_ok=True)
    if not os.path.exists(CONFIG_FILE_ptero):
        with open(CONFIG_FILE_ptero, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)

    with open(CONFIG_FILE_ptero, "r") as f:
        return json.load(f)

ptero_config = load_config_ptero()

PANEL_URL = ptero_config['PANEL_URL']
API_KEY = ptero_config["API_KEY"]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "Application/vnd.pterodactyl.v1+json",
    "Content-Type": "application/json"
}

BASE_URL = f"{PANEL_URL}/api/application"

def create_user(email, username, password, first_name, last_name):
    payload = {
        "email": email,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "password": password
    }
    res = requests.post(f"{BASE_URL}/users", headers=HEADERS, json=payload)
    return res.json()

def delete_user(user_id):
    res = requests.delete(f"{BASE_URL}/users/{user_id}", headers=HEADERS)
    return res.status_code == 204

def create_server(
        name,
        user_id,
        egg_id,
        docker_image,
        startup_cmd,
        allocation_id,
        environment,
        memory=1024,
        swap=0,
        disk=1024,
        io=500,
        cpu=100.0,
        databases=1,
        allocations=1,
        backups=1,
        skip_scripts=False
):
    missing_params = []
    for key, value in {
        "name": name,
        "user_id": user_id,
        "egg_id": egg_id,
        "docker_image": docker_image,
        "startup_cmd": startup_cmd,
        "allocation_id": allocation_id,
        "environment": environment
    }.items():
        if not value:
            missing_params.append(key)

    if missing_params:
        raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

    if not isinstance(environment, dict):
        raise TypeError("`environment` must be a dictionary.")

    missing_env = [k for k, v in environment.items() if not v]
    if missing_env:
        raise ValueError(f"Missing or empty environment variables: {', '.join(missing_env)}")

    payload = {
        "name": name,
        "user": user_id,
        "egg": egg_id,
        "docker_image": docker_image,
        "startup": startup_cmd,
        "limits": {
            "memory": memory,
            "swap": swap,
            "disk": disk,
            "io": io,
            "cpu": cpu
        },
        "feature_limits": {
            "databases": databases,
            "allocations": allocations,
            "backups": backups
        },
        "allocation": {
            "default": allocation_id
        },
        "environment": environment,
        "skip_scripts": skip_scripts
    }

    try:
        res = requests.post(f"{BASE_URL}/servers", headers=HEADERS, json=payload)
        res.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return res.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {res.text}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")
    except ValueError as json_err:
        print(f"JSON decode failed: {json_err} - Raw Response: {res.text}")
    except Exception as err:
        print(f"Unexpected error: {err}")

    return None

def delete_server(server_id):
    res = requests.delete(f"{BASE_URL}/servers/{server_id}/force", headers=HEADERS)
    return res.status_code == 204

def list_allocations(node_id):
    res = requests.get(f"{BASE_URL}/nodes/{node_id}/allocations", headers=HEADERS)
    return res.json()

def get_free_allocation(node_id):
    allocations = list_allocations(node_id)
    for alloc in allocations['data']:
        if not alloc['attributes']['assigned']:
            return alloc['attributes']['id']
    raise Exception("No free allocations available!")

def get_server_id_by_uuid(uuid):
    res = requests.get(f"{BASE_URL}/servers", headers=HEADERS)
    data = res.json()
    for server in data['data']:
        if server['attributes']['uuid'] == uuid or server['attributes']['identifier'] == uuid:
            return server['attributes']['id']
    return None

def list_user_servers(user_id, identifier=None):
    try:
        res = requests.get(f"{BASE_URL}/users/{user_id}?include=servers", headers=HEADERS)
        res.raise_for_status()
        data = res.json()

        servers = data.get("attributes", {}).get("relationships", {}).get("servers", {}).get("data", [])
        if not servers:
            print(f"No servers found for user ID {user_id}.")
            return False if identifier else []

        server_list = []
        for server in servers:
            attrs = server.get("attributes", {})
            server_info = {
                "id": attrs.get("id"),
                "uuid": attrs.get("uuid"),
                "name": attrs.get("name"),
                "identifier": attrs.get("identifier"),
                "node": attrs.get("node"),
                "suspended": attrs.get("suspended")
            }
            server_list.append(server_info)

            if identifier and server_info["identifier"] == identifier:
                return True

        return False if identifier else server_list

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {res.text}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")
    except Exception as err:
        print(f"Unexpected error: {err}")

    return False if identifier else []

def list_nodes():
    """Returns a list of all nodes."""
    try:
        res = requests.get(f"{BASE_URL}/nodes", headers=HEADERS)
        res.raise_for_status()
        return res.json()["data"]
    except requests.exceptions.RequestException as e:
        print(f"Error while fetching nodes: {e}")
        return []

def get_node_server_count(node_id):
    """Helper function to count servers on a specific node."""
    try:
        res = requests.get(f"{BASE_URL}/nodes/{node_id}?include=servers", headers=HEADERS)
        res.raise_for_status()
        node_data = res.json()
        servers = node_data.get("attributes", {}).get("relationships", {}).get("servers", {}).get("data", [])
        return len(servers)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching server count for node {node_id}: {e}")
        return float('inf')  # Assign a very high number if failed to fetch

def get_best_node():
    """Returns the node with the least number of servers."""
    nodes = list_nodes()
    if not nodes:
        print("No nodes found.")
        return None

    best_node = None
    min_servers = float('inf')

    for node in nodes:
        node_id = node["attributes"]["id"]
        server_count = get_node_server_count(node_id)
        #print(f"Node {node_id} has {server_count} server(s).")

        if server_count < min_servers:
            min_servers = server_count
            best_node = node

    return best_node


db_ptero = pymysqlhelper.LocalDatabase('users.db')
if 'users' not in db_ptero.list_tables():
    db_ptero.define_table('users', user_id=pymysqlhelper.BigInteger, ptero_user_id=pymysqlhelper.BigInteger, server_count=pymysqlhelper.Integer, max_servers=pymysqlhelper.Integer)


async def register_callback(interaction, modal):
    await interaction.response.defer(ephemeral=True)
    if db_ptero.count_rows('users') >= ptero_config['max_users']:
        await interaction.followup.send('Max User Limit Reached',  ephemeral=True)
        return
    user = create_user(email=modal.children[1].value, username=modal.children[0].value, password=modal.children[2].value, first_name='Pterodactyl', last_name='User')
    db_ptero.insert('users', user_id=interaction.user.id, ptero_user_id=user['attributes']['id'], server_count=0, max_servers=ptero_config['default_max_servers'])
    await interaction.followup.send(f'User account created, login with the email and password your provided on [here]({PANEL_URL})', ephemeral=True)

async def get_started_callback(interaction):
    if not db_ptero.search('users', user_id=interaction.user.id):
        inputs = [
            discord.ui.InputText(label="Username", placeholder="Example", custom_id="username", required=True),
            discord.ui.InputText(label="Email", placeholder="example@gmail.com", custom_id="email", required=True),
            discord.ui.InputText(label="Password", placeholder="******", custom_id="password", required=True),
        ]
        await interaction.response.send_modal(
            create_modal_view(title='Register', inputs=inputs, custom_id='register_modal',
                              callback=register_callback))
    else:
        view = View()
        for child in button_views['create_server_ptero_admin'].children:
            view.add_item(child)
        for child in button_views['delete_server_ptero_admin'].children:
            view.add_item(child)
        await interaction.response.send_message(view=view, ephemeral=True)

async def ptero_select_menu_callback(interaction: discord.Interaction):
    selected_value = interaction.data['values'][0]
    user_id = interaction.user.id
    user_data = db_ptero.get('users', user_id=user_id)
    user_id = user_data['ptero_user_id']
    best_node = get_best_node()
    if not best_node:
        await interaction.response.edit_message(content="No available nodes found.", view=None)
        return
    node_id = best_node['attributes']['id']
    allocation_id = get_free_allocation(node_id)

    server = create_server(
        name=f"{interaction.user.name}'s {selected_value} Server",
        user_id=user_id,
        allocation_id=allocation_id,
        **ptero_config['options'][selected_value]
    )
    await interaction.response.edit_message(content=f"Server created, {server['attributes']['name']}", view=None)
    db_ptero.update('users', {'ptero_user_id': user_id}, {'server_count': user_data['server_count'] + 1})

async def create_server_callback(interaction):
    user_id = interaction.user.id
    user_data = db_ptero.get('users', user_id=user_id)
    if user_data['server_count'] >= user_data['max_servers']:
        await interaction.response.send_message('Max server Limit Reached', ephemeral=True)
    else:
        options = [
            SelectOption(label=key.capitalize(), value=key)
            for key in ptero_config['options'].keys()
        ]

        view = create_select_view(placeholder="Choose an option", options=options, custom_id="select_options",
                                  callback=ptero_select_menu_callback)
        await interaction.response.send_message("Please choose an option:", view=view, ephemeral=True)

async def delete_server_modal_callback(interaction, modal):
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id
    user_data = db_ptero.get('users', user_id=user_id)
    user_id = user_data['ptero_user_id']

    server_exists = list_user_servers(user_id, modal.children[0].value)

    if server_exists:
        delete_server(get_server_id_by_uuid(modal.children[0].value))
        await interaction.followup.send(f'Server Deleted Successfully!', ephemeral=True)
        server_count = user_data['server_count'] - 1
        db_ptero.update('users', {'ptero_user_id': user_id}, {'server_count': server_count if server_count > -1 else 0})
    else:
        await interaction.followup.send('Server Not Found!', ephemeral=True)

async def delete_server_callback(interaction):
    inputs = [
        discord.ui.InputText(label="Server ID", placeholder="Example:56e2d20f ", custom_id="id", required=True)
    ]
    await interaction.response.send_modal(
        create_modal_view(title='Delete Server', inputs=inputs, custom_id='delete_modal',
                          callback=delete_server_modal_callback))


@bot.slash_command(name='setuppanel')
async def setup_starter_panel(ctx):
    view = View()
    for child in button_views['get_started_ptero_admin'].children:
        view.add_item(child)
    await ctx.send(view=view)


@is_owner()
@bot.command(name='deleteuser')
async def delete_user_ptero(ctx, user: str = None):
    if not user:
        await ctx.send('⚠️ No user provided')
        return

    try:
        #await ctx.send('🔍 Starting user deletion process...')

        user_id_raw = user.strip('<@>')
        #await dbg(f'Parsed user ID: `{user_id_raw}`')

        user_id = int(user_id_raw)
        ptero_user_data = db_ptero.get('users', user_id=user_id)

        if not ptero_user_data:
            await ctx.send('❌ User not found in database.')
            return

        ptero_user_id = ptero_user_data['ptero_user_id']
        #await dbg(f'Pterodactyl User ID: `{ptero_user_id}`')

        user_servers = list_user_servers(ptero_user_id)
        #await dbg(f'Found {len(user_servers)} servers for user.')

        while user_servers:
            server_id = user_servers[0]['id']
            #await dbg(f'Deleting server ID: `{server_id}`')
            delete_server(server_id)
            user_servers.pop(0)

        #await dbg('All servers deleted. Proceeding to delete user...')
        deleted = delete_user(ptero_user_id)
        if deleted:
            db_ptero.delete('users', user_id=user_id)
            await ctx.send('✅ User deleted successfully from Pterodactyl and database.')
        else:
            await ctx.send('❌ Failed to delete user from Pterodactyl.')

    except Exception as e:
        await ctx.send(f'🚨 Error occurred: `{str(e)}`')
add_help('Ptero-Admin', 'deleteuser <usermention>', 'deletes a user and their servers if any')


@is_owner()
@bot.command(name='setserverlimit')
async def update_server_limit(ctx, user: str = None, limit:int = 2):
    if not user:
        await ctx.send('⚠️ No user provided')
        return
    user = int(user.strip('<@>'))
    user_data = db_ptero.get('users', user_id=user)
    if not user_data:
        await ctx.send('❌ User not found in database.')
        return
    db_ptero.update('users', {'user_id':user}, {'max_servers': limit})
    await ctx.send(f'✅ Limit updated to {limit}')
add_help('Ptero-Admin', 'setserverlimit <usermention> <limit>', 'Sets max server limit for a user')


GetStartedButton = {
    'label': 'Manage Servers',
    'style': discord.ButtonStyle.success,
    'custom_id': 'get_started_ptero_admin',
    'callback': get_started_callback,
    'emoji': '💎'
}
button_configurations.append(GetStartedButton)

CreateServerButton = {
    'label': 'Create Server',
    'style': discord.ButtonStyle.success,
    'custom_id': 'create_server_ptero_admin',
    'callback': create_server_callback,
    'emoji': '⚙️'
}
button_configurations.append(CreateServerButton)

DeleteServerButton = {
    'label': 'Delete Server',
    'style': discord.ButtonStyle.danger,
    'custom_id': 'delete_server_ptero_admin',
    'callback': delete_server_callback,
    'emoji': '🗑️'
}
button_configurations.append(DeleteServerButton)
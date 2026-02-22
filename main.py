current_version = 'V1.0-dev-0.1'
current_config_format = 20
plugins_folder = 'plugins'
creator_id = '938059286054072371'
api = 'http://127.0.0.1:25519'

#test

libraries = """
aiohappyeyeballs==2.6.1
aiohttp==3.12.14
aiosignal==1.4.0
anyio==4.9.0    
asyncio-dgram==2.2.0
attrs==25.3.0
audioop-lts==0.2.1
blinker==1.9.0
certifi==2025.7.9
cffi==1.17.1
charset-normalizer==3.4.2
click==8.1.3
colorama==0.4.6
contourpy==1.3.2
cycler==0.12.1
deamstools==1.3.0
dnspython==2.7.0
Flask==3.1.1
fonttools==4.58.5
frozenlist==1.7.0
googletrans==4.0.2
greenlet==3.2.3
gTTS==2.5.4
h11==0.16.0
h2==4.2.0
hpack==4.1.0
httpcore==1.0.9
httpx==0.28.1
hyperframe==6.1.0
idna==3.10
itsdangerous==2.2.0
Jinja2==3.1.6
kiwisolver==1.4.8
MarkupSafe==3.0.2
matplotlib==3.10.3
mcstatus==12.0.2
mpmath==1.3.0
multidict==6.6.3
numpy==2.3.1
packaging==25.0
pillow==11.3.0
propcache==0.3.2
py-cord==2.6.1
pycparser==2.22
PyMySQL==1.1.1
pymysqlhelper==1.9.2
PyNaCl==1.5.0
pyparsing==3.2.3
python-dateutil==2.9.0.post0
pytz==2025.2
requests==2.32.4
setuptools==80.9.0
six==1.17.0
sniffio==1.3.1
SQLAlchemy==2.0.41
sympy==1.14.0
typing_extensions==4.14.1
urllib3==2.5.0
Werkzeug==3.1.3
yarl==1.20.1
tqdm
yt-dlp
"""

try:
    import os
    import platform
    import inspect
    import subprocess
    import textwrap
    import atexit
    import signal
    import logging
    import sys
    import re
    import discord
    import json
    import random as rand
    import time
    import asyncio
    import aiohttp
    import pytz
    import calendar
    import requests
    import matplotlib.pyplot as plt
    import numpy as np
    import string
    import threading
    from tqdm import tqdm
    import matplotlib.patheffects as pe
    import matplotlib.ticker as ticker
    import deamstools
    from gtts import gTTS
    from discord import SelectOption, ui, InputText, File, Status
    from googletrans import Translator
    from datetime import datetime, timedelta, timezone
    from collections import defaultdict, deque
    from discord.ui import Button, View, Modal, InputText
    from discord import InputTextStyle, Embed
    from discord.utils import get
    from discord.ext import commands, tasks, pages
    from PIL import Image
    from io import BytesIO
    from sympy import symbols, Eq, solve
    from difflib import get_close_matches

except ModuleNotFoundError as e:
    print(f"Library not found: {e.name}")
    with open('libraries.txt', 'w') as f:
        f.write(libraries)
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'libraries.txt'])
    exit()
except ImportError as e:
    print(f"Import error: {e}")
    exit()
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit()

button_configurations = []
button_views = {}

log = logging.info
logw = logging.warning
logerr = logging.error
logc = logging.critical
loge = logging.exception
logd = logging.debug

DEFAULT_CONFIG = {
    'config_format': current_config_format,
    'prefix': '!',
    'bot_token': '',
    'owner_id': '',
    'bot_group_name': 'Cane',
    'check_for_updates': True,
    'timediff': 0,
    'plugins': False,
    'debug': False,
    'log': False,
}

if not os.path.isfile('BotConfig.json'):
    print('No config file found creating Bot Config')
    INPUT_PREFIX = input('What do you want the bot prefix to be?: ')
    INPUT_BOT_GROUP_NAME = input("Enter a bot log prefix name (Eg name of the bot): ")
    INPUT_BOT_TOKEN = input('Enter bot token: ')
    INPUT_OWNER_ID = input("Enter owner's ID: ")

    QUESTION = input("Enter Time Different if any (Eg: 5.5, -5.5 Default is 0): ")
    INPUT_TIME_DIFF = float(QUESTION) if QUESTION else 0

    QUESTION = input("Enable Message Logging? [Y/n]: ")
    INPUT_LOG = QUESTION.lower() in ['y', 'yes', '1']

    QUESTION = input("Enable Plugins? [Y/n]: ")
    PLUGINS = QUESTION.lower() in ['y', 'yes', '1']

    bot_config = {
        'config_format': current_config_format,
        'prefix': INPUT_PREFIX,
        'bot_token': INPUT_BOT_TOKEN,
        'owner_id': INPUT_OWNER_ID,
        'bot_group_name': INPUT_BOT_GROUP_NAME,
        'check_for_updates': True,
        'timediff': INPUT_TIME_DIFF,
        'plugins': PLUGINS,
        'debug': False,
        'log': INPUT_LOG,
    }
    with open('BotConfig.json', 'w') as f:
        f.write(json.dumps(bot_config, indent=4, ensure_ascii=False, separators=(',', ': ')) + '\n')

with open('BotConfig.json') as f:
    bot_config = json.load(f)

DEBUG_MODE = bot_config.get('debug', False)


def update_config(user_config, config_path='BotConfig.json', default=DEFAULT_CONFIG, remove_old_keys=True):
    updated = False

    for key, value in default.items():
        if key not in user_config:
            user_config[key] = value
            print(f"➕ Added missing key: {key}")
            updated = True

    if remove_old_keys:
        for key in list(user_config.keys()):
            if key not in default:
                del user_config[key]
                print(f"❌ Removed deprecated key: {key}")
                updated = True

    if updated:
        user_config['config_format'] = int(user_config['config_format']) + 1
        with open(config_path, 'w') as f:
            json.dump(user_config, f, indent=4)
        print("🔄 Config updated.")

    return user_config


if int(bot_config['config_format']) < current_config_format:
    print('[Warning]: Config may be unsupported, Regenerating Config')
    bot_config = update_config(bot_config, 'BotConfig.json')


def create_button(label: str, style: discord.ButtonStyle, custom_id: str, callback=None, emoji=None, disabled=False):
    button = Button(label=label, style=style, custom_id=custom_id, emoji=emoji, disabled=disabled)
    if callback:
        button.callback = callback
    return button


def create_button_view(label: str, style: discord.ButtonStyle, custom_id: str, callback, emoji=None, disabled=False):
    button = Button(label=label, style=style, custom_id=custom_id, emoji=emoji, disabled=disabled)
    if callback:
        button.callback = callback
    view = discord.ui.View(timeout=None)
    view.add_item(button)
    return view


def create_select_view(placeholder: str, options: list[SelectOption], custom_id: str, callback, min_values: int = 1,
                       max_values: int = 1, disabled=False):
    select = discord.ui.Select(placeholder=placeholder, options=options, custom_id=custom_id, min_values=min_values,
                               max_values=max_values, disabled=disabled)
    if callback:
        select.callback = callback
    view = View(timeout=None)
    view.add_item(select)
    return view


def create_modal_view(title: str, inputs: list[InputText], custom_id: str, callback):
    class CustomModal(Modal):
        def __init__(self):
            super().__init__(title=title, custom_id=custom_id)
            for input_field in inputs:
                self.add_item(input_field)

        async def callback(self, interaction: discord.Interaction):
            if callback:
                await callback(interaction, self)

    return CustomModal()


def is_trusted(guild, user):
    if server_configs.get(str(guild.id)):
        if server_configs[str(guild.id)].get('antinuke_trustlist'):
            if user.id in server_configs[str(guild.id)]['antinuke_trustlist']:
                return True
    if guild.owner_id == user.id or user.id == creator_id or user.id == bot.user.id or str(user.id) == creator_id:
        return True
    return False


def is_whitelisted(guild, user):
    if server_configs.get(str(guild.id)):
        if server_configs[str(guild.id)].get('antinuke_whitelist'):
            if user.id in server_configs[str(guild.id)]['antinuke_whitelist']:
                return True
    if is_trusted(guild, user):
        return True
    return False


async def handle_member_kick(member, guild, user):
    if server_configs.get(str(guild.id)):
        if not server_configs.get(str(guild.id)).get('antinuke'):
            return
        if not is_whitelisted(guild, user):
            await user.ban()
            if server_configs.get(str(guild.id)).get('antinuke_logs_channel'):
                channel = bot.get_channel(int(server_configs.get(str(guild.id)).get('antinuke_logs_channel')))
                await channel.send(f"**ANTI NUKE TRIGGERD**: Member {member} was kicked by {user}.")


async def handle_member_ban(member, guild, user):
    if server_configs.get(str(guild.id)):
        if not server_configs.get(str(guild.id)).get('antinuke'):
            return
        if not is_whitelisted(guild, user):
            await user.ban()
            if server_configs.get(str(guild.id)).get('antinuke_logs_channel'):
                channel = bot.get_channel(int(server_configs.get(str(guild.id)).get('antinuke_logs_channel')))
                await channel.send(f"**ANTI NUKE TRIGGERD**: Member {member} was banned by {user}.")


runlog_dir = 'Bot Logs'
os.makedirs(runlog_dir, exist_ok=True)

logging.basicConfig(level=logging.DEBUG if DEBUG_MODE else logging.INFO,
                    format=f"[%(levelname)s | {bot_config['bot_group_name']} | %(asctime)s]: %(message)s")
logger = logging.getLogger()
file_handler = logging.FileHandler(f'{runlog_dir}/log_{datetime.now().isoformat().replace(":", "-")}.txt')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(f"[{bot_config['bot_group_name']} | %(asctime)s | %(levelname)s]: %(message)s"))
logger.addHandler(file_handler)

bot = commands.Bot(command_prefix=bot_config['prefix'], intents=discord.Intents.all())

logd('DEBUG MODE ENABLED')
print = logd

SUPPORTED_LANGUAGES = {
    'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic', 'hy': 'Armenian', 'az': 'Azerbaijani',
    'eu': 'Basque', 'be': 'Belarusian', 'bn': 'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
    'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
    'co': 'Corsican',
    'hr': 'Croatian', 'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English', 'eo': 'Esperanto',
    'et': 'Estonian',
    'tl': 'Filipino', 'fi': 'Finnish', 'fr': 'French', 'fy': 'Frisian', 'gl': 'Galician', 'ka': 'Georgian',
    'de': 'German',
    'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole', 'ha': 'Hausa', 'haw': 'Hawaiian', 'iw': 'Hebrew',
    'hi': 'Hindi',
    'hmn': 'Hmong', 'hu': 'Hungarian', 'is': 'Icelandic', 'ig': 'Igbo', 'id': 'Indonesian', 'ga': 'Irish',
    'it': 'Italian',
    'ja': 'Japanese', 'jw': 'Javanese', 'kn': 'Kannada', 'kk': 'Kazakh', 'km': 'Khmer', 'rw': 'Kinyarwanda',
    'ko': 'Korean',
    'ku': 'Kurdish (Kurmanji)', 'ky': 'Kyrgyz', 'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian', 'lt': 'Lithuanian',
    'lb': 'Luxembourgish',
    'mk': 'Macedonian', 'mg': 'Malagasy', 'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese', 'mi': 'Maori',
    'mr': 'Marathi',
    'mn': 'Mongolian', 'my': 'Myanmar (Burmese)', 'ne': 'Nepali', 'no': 'Norwegian', 'or': 'Odia (Oriya)',
    'ps': 'Pashto',
    'fa': 'Persian', 'pl': 'Polish', 'pt': 'Portuguese', 'pa': 'Punjabi', 'ro': 'Romanian', 'ru': 'Russian',
    'sm': 'Samoan',
    'gd': 'Scots Gaelic', 'sr': 'Serbian', 'st': 'Sesotho', 'sn': 'Shona', 'sd': 'Sindhi', 'si': 'Sinhala',
    'sk': 'Slovak',
    'sl': 'Slovenian', 'so': 'Somali', 'es': 'Spanish', 'su': 'Sundanese', 'sw': 'Swahili', 'sv': 'Swedish',
    'tg': 'Tajik',
    'ta': 'Tamil', 'tt': 'Tatar', 'te': 'Telugu', 'th': 'Thai', 'tr': 'Turkish', 'tk': 'Turkmen', 'uk': 'Ukrainian',
    'ur': 'Urdu', 'ug': 'Uyghur', 'uz': 'Uzbek', 'vi': 'Vietnamese', 'cy': 'Welsh', 'xh': 'Xhosa', 'yi': 'Yiddish',
    'yo': 'Yoruba', 'zu': 'Zulu'
}


def logcommand(message, command):
    if bot_config['log']:
        date_string = ttime().strftime('%Y-%m-%d')
        time_string = ttime().strftime('%H-%M-%S')
        log_message = f'{message.guild.name} > #{message.channel.name} > {time_string} > {message.author.name} used the slash command: {command}'

        os.makedirs('Logs', exist_ok=True)

        log_file_path = os.path.join('Logs', f'{date_string}_log.txt')
        with open(log_file_path, 'a') as file:
            file.write(log_message + '\n')


def parse_duration(duration_str):
    pattern = r"(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
    match = re.fullmatch(pattern, duration_str)
    if not match:
        return None

    weeks, days, hours, minutes, seconds = [int(value) if value else 0 for value in match.groups()]
    return timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)


def split_message(message, limit=2000):
    chunks = []
    start = 0

    while start < len(message):
        if len(message) - start <= limit:
            chunks.append(message[start:])
            break

        end = start + limit
        split_index = message.rfind('\n', start, end)
        if split_index == -1:
            split_index = message.rfind(' ', start, end)
        if split_index == -1 or split_index <= start:
            split_index = end

        chunks.append(message[start:split_index])
        start = split_index
        while start < len(message) and message[start] in (' ', '\n'):
            start += 1

    return chunks


def get_flag_value(flag_name, default=None):
    for arg in sys.argv:
        if arg.startswith(f"{flag_name}="):
            return arg.split("=", 1)[1]
    return default


self_restart = str(get_flag_value('--self-restart', 'true')).lower() == 'true'
is_exiting = False

if not self_restart:
    log('Self Restart Is False, the script wont auto restart')


OWNER_PERMS_GROUP = bot_config['bot_group_name'] + '.' + 'owner'
MOD_PERMS_GROUP = bot_config['bot_group_name'] + '.' + 'mod'
MEMBER_PERMS_GROUP = bot_config['bot_group_name'] + '.' + 'member'

script_dir = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.path.join(script_dir, 'ffmpeg')
TTS_VOICE_FILE = "bot_audio.wav"


def get_architecture():
    try:
        arch = platform.machine()
        if arch == 'x86_64':
            return 'amd'
        elif arch == 'i686':
            return 'i686'
        elif arch.startswith('arm'):
            return 'arm'
        elif arch.startswith('aarch64'):
            return 'arm'
        else:
            return 'unknown'
    except Exception as e:
        logw(f"Error detecting architecture: {e}")
        return 'unknown'


os_name = platform.system()
if os_name == "Windows":
    FFMPEG_PATH = FFMPEG_PATH + '.exe'


def check_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        logw('FFMPEG not found, downloading from API server')
        architecture = get_architecture()

        if os_name == "Windows":
            url = f'{api}/get-ffmpeg/win'
            file_name = 'ffmpeg.exe'

        elif os_name == "Linux":
            url = f'{api}/get-ffmpeg/linux-{architecture}'
            file_name = 'ffmpeg'

        else:
            logw(f"This script is running on an unknown operating system: {os_name} couldn't download FFMPEG")



        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        with open(file_name, 'wb') as f, tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=f"Downloading {file_name}"
        ) as bar:
            for data in response.iter_content(block_size):
                f.write(data)
                bar.update(len(data))

        if os_name == "Linux":
            os.chmod(file_name, 0o755)

        log(f"Downloaded FFMPEG for {os_name}")
check_ffmpeg()


vcinuse_flags = defaultdict(lambda: False)

exclude_log_types = [
    'text',
    'voice'
]


class CreateTicketView(discord.ui.View):
    def __init__(self, bot, button_message="Create Ticket", emoji="🎟️", button_style=discord.ButtonStyle.primary, profile=None, guild_id=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.button_message = button_message
        self.emoji = emoji
        self.button_style = button_style
        self.profile = profile
        self.guild_id = guild_id

        # Dynamically create the button and add it to the view
        custom_id = self.generate_custom_id()
        self.add_item(discord.ui.Button(label=self.button_message, emoji=self.emoji, style=self.button_style, custom_id=custom_id))

    def generate_custom_id(self):
        if self.profile and self.guild_id:
            return f"create_ticket_button_{self.guild_id}_{self.profile}"
        elif self.guild_id:
            return f"create_ticket_button_{self.guild_id}"
        return "create_ticket_button"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Optional: add global check here if needed
        return True

    async def on_timeout(self):
        # Optional: cleanup or disable button on timeout
        pass

    async def interaction(self, interaction: discord.Interaction):
        await handle_ticket_creation(interaction, self.bot)




class TicketInputModal(Modal):
    def __init__(self, bot, interaction, profile_name, input_fields):
        super().__init__(title="Additional Info")
        self.bot = bot
        self.interaction = interaction
        self.profile_name = profile_name
        self.data = {}

        for field in input_fields:
            self.add_item(InputText(
                label=field.get("label", "Field"),
                custom_id=field.get("custom_id", field.get("label", "field").lower().replace(" ", "_")),
                placeholder=field.get("placeholder", ""),
                style=InputTextStyle.paragraph if field.get("style", "short") == "paragraph" else InputTextStyle.short,
                required=field.get("required", True)
            ))

    async def callback(self, interaction: discord.Interaction):
        for child in self.children:
            self.data[child.custom_id] = child.value

        await handle_ticket_creation(interaction, self.bot, self.profile_name, self.data)


class CloseTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒",
                       custom_id="close_ticket_button")
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await handle_ticket_closure(interaction, self.bot)


class DeleteTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Delete Ticket", style=discord.ButtonStyle.danger, emoji="🗑️",
                       custom_id="delete_ticket_button")
    async def delete_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await interaction.channel.delete()
        except Exception as e:
            logerr(f"Error while deleting ticket: {e}")
            await interaction.followup.send("An error occurred while deleting the ticket. Please try again later.",
                                            ephemeral=True)


class CloseTicketRequestView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Request to Close Ticket", style=discord.ButtonStyle.primary, emoji="🔒",
                       custom_id="close_request_button")
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await handle_ticket_close_request(interaction, self.bot)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


AUTO_ROLE_DATA_FILE = 'auto_roles.json'

server_roles = {}
if os.path.isfile(AUTO_ROLE_DATA_FILE):
    with open(AUTO_ROLE_DATA_FILE, 'r') as file:
        server_roles = json.load(file)

URLS_FILE = "redirect_urls.json"


def save_roles():
    with open(AUTO_ROLE_DATA_FILE, 'w') as file:
        json.dump(server_roles, file)


def load_urls():
    try:
        with open(URLS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_urls(data):
    with open(URLS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def ttime():
    timediff = float(bot_config.get('timediff', 0))
    time = datetime.now().astimezone(timezone(timedelta(hours=+timediff)))
    return time


def replace_placeholders(content, user):
    default_icon_url = "https://cdn.discordapp.com/embed/avatars/0.png"
    try:
        def time_replacer(match):
            format_str = match.group(1)
            conversions = {
                "H": "%H", "I": "%I", "M": "%M", "S": "%S",
                "d": "%d", "m": "%m", "Y": "%Y", "y": "%y",
                "p": "%p", "A": "%A", "a": "%a", "B": "%B", "b": "%b"
            }
            fmt = ''.join(conversions.get(c, c) for c in format_str)
            return ttime().strftime(fmt)

        content = re.sub(r"%time:([A-Za-z:]+)%", time_replacer, content)

        content = content.replace("%user%", str(user)) \
            .replace("%username%", user.name) \
            .replace("%userid%", str(user.id)) \
            .replace("%usermention%", user.mention) \
            .replace("%usericon%", user.avatar.url if user.avatar else default_icon_url) \
            .replace("%time%", ttime().strftime('%d-%m-%Y %I:%M:%S %p')) \
            .replace("%servericon%", user.guild.icon.url if user.guild.icon else default_icon_url) \
            .replace("%servername%", str(user.guild.name))

        return content

    except Exception as e:
        loge(e.args)


def check_for_embed(message):
    embed_pattern = r"%embed:([a-zA-Z0-9_]+)%"
    match = re.search(embed_pattern, message)

    embed_name = 'None_embed_found'
    if match:
        embed_name = match.group(1)
        message = message.replace(match.group(0), "")

    cleaned_message = " ".join(message.split())

    return cleaned_message, embed_name


def get_embed(name: str, user):
    embeds = server_configs.get(str(user.guild.id), {}).get('embeds', {})
    if name not in embeds:
        embed_data = {"title": "", "description": name, "color": 0, "fields": [], "footer": "", "image": "",
                      "thumbnail": ""}
    else:
        embed_data = embeds[name]

    embed = discord.Embed(
        title=replace_placeholders(embed_data.get("title", ""), user),
        description=replace_placeholders(embed_data.get("description", ""), user),
        color=embed_data.get("color", 0x3498db)
    )
    for field in embed_data.get("fields", []):
        embed.add_field(name=replace_placeholders(field["name"], user),
                        value=replace_placeholders(field["value"], user),
                        inline=field.get("inline", False))
    if embed_data.get("footer"):
        embed.set_footer(text=replace_placeholders(embed_data["footer"], user))

    if embed_data.get("image"):
        url = embed_data["image"]
        if url.startswith("%"):
            url = replace_placeholders(embed_data["image"], user)
        embed.set_image(url=url)

    if embed_data.get("thumbnail"):
        url = embed_data["thumbnail"]
        if url.startswith("%"):
            url = replace_placeholders(embed_data["thumbnail"], user)
        embed.set_thumbnail(url=url)
    return embed


server_config_file = 'server_configs.json'


def load_server_configs():
    if os.path.exists(server_config_file):
        with open(server_config_file, 'r') as file:
            return json.load(file)
    else:
        return {}


def save_server_configs(config):
    with open(server_config_file, 'w') as file:
        file.write(json.dumps(config))


server_configs = load_server_configs()

when_bot_ready_functions = []


def when_bot_ready(function):
    when_bot_ready_functions.append(function)
    return function


when_bot_interaction_functions = []


def when_bot_interaction(function):
    when_bot_interaction_functions.append(function)
    return function


when_bot_shutdown_functions = []


def when_bot_shutdown(function):
    when_bot_shutdown_functions.append(function)
    return function


when_member_join_functions = []


def when_member_join(function):
    when_member_join_functions.append(function)
    return function


when_message_functions = []


def when_message(function):
    when_message_functions.append(function)
    return function


@bot.event
async def on_member_join(member):
    for f in when_member_join_functions:
        if inspect.iscoroutinefunction(f):
            await f(member)
        else:
            f(member)
    guild_id = str(member.guild.id)
    if server_configs.get(guild_id, {}).get("analytics", False):
        tz = pytz.utc
        now = datetime.now(tz)
        date_key = now.strftime("%Y-%m-%d")
        time_key = now.strftime("%Y-%m-%d %H:%M")

        server_configs.setdefault(guild_id, {}).setdefault("data", {}).setdefault("joins", {}).setdefault(date_key, 0)
        server_configs[guild_id]["data"]["joins"][date_key] += 1  # Daily tracking

        server_configs[guild_id]["data"].setdefault("joins_per_minute", {}).setdefault(time_key, 0)
        server_configs[guild_id]["data"]["joins_per_minute"][time_key] += 1  # Minute tracking

        save_server_configs(server_configs)

    if str(member.guild.id) in server_roles:
        guild_id = str(member.guild.id)
        for role_id in server_roles[guild_id]:
            role_object: discord.Role = get(member.guild.roles, id=role_id)
            if role_object:
                await member.add_roles(role_object)
            else:
                server_roles[guild_id].remove(role_id)

    server_config = server_configs.get(str(member.guild.id))
    if server_config:
        if server_config.get('member_count_channel'):
            channel = bot.get_channel(int(server_config.get('member_count_channel')))
            if not channel:
                server_configs[str(member.guild.id)]['member_count_channel'] = None
                save_server_configs(server_configs)
            else:
                member_count = len(channel.guild.members)
                await channel.edit(name=f'Members: {member_count}')

    guild: discord.Guild = member.guild
    server_config: dict = server_configs.get(str(guild.id))
    if not server_config:
        return
    channel = bot.get_channel(server_config.get('welcome_channel_id'))
    embed_message = server_config.get('welcome_message')
    if not channel or not embed_message:
        return

    message, embed = check_for_embed(embed_message)

    server_id = str(channel.guild.id)
    embeds = server_configs.get(server_id, {}).get('embeds', {})
    if not embed in embeds:
        embed = None
    message = replace_placeholders(message, member)
    embed = get_embed(embed, member) if embed else None
    await channel.send(content=message, embed=embed)


when_member_leave_functions = []


def when_member_leave(function):
    when_member_leave_functions.append(function)
    return function


@bot.event
async def on_member_remove(member):
    for f in when_member_leave_functions:
        if inspect.iscoroutinefunction(f):
            await f(member)
        else:
            f(member)
    guild = member.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target == member:
            await handle_member_kick(member, guild, entry.user)

    guild_id = str(member.guild.id)
    if server_configs.get(guild_id, {}).get("analytics", False):
        tz = pytz.utc
        now = datetime.now(tz)
        date_key = now.strftime("%Y-%m-%d")
        time_key = now.strftime("%Y-%m-%d %H:%M")

        server_configs.setdefault(guild_id, {}).setdefault("data", {}).setdefault("leaves", {}).setdefault(date_key, 0)
        server_configs[guild_id]["data"]["leaves"][date_key] += 1  # Daily tracking

        server_configs[guild_id]["data"].setdefault("leaves_per_minute", {}).setdefault(time_key, 0)
        server_configs[guild_id]["data"]["leaves_per_minute"][time_key] += 1  # Minute tracking

        save_server_configs(server_configs)

    server_config = server_configs.get(str(member.guild.id))
    if server_config:
        if server_config.get('member_count_channel'):
            channel = bot.get_channel(int(server_config.get('member_count_channel')))
            if not channel:
                server_configs[str(member.guild.id)]['member_count_channel'] = None
                save_server_configs(server_configs)
            else:
                member_count = len(channel.guild.members)
                await channel.edit(name=f'Members: {member_count}')

    guild: discord.Guild = member.guild
    server_config: dict = server_configs.get(str(guild.id))
    if not server_config:
        return
    channel = bot.get_channel(server_config.get('leave_channel_id'))
    embed_message = server_config.get('leave_message')
    if not channel or not embed_message:
        return

    message, embed = check_for_embed(embed_message)

    server_id = str(channel.guild.id)
    embeds = server_configs.get(server_id, {}).get('embeds', {})
    if not embed in embeds:
        embed = None
    message = replace_placeholders(message, member)
    embed = get_embed(embed, member) if embed else None
    await channel.send(content=message, embed=embed)


when_member_ban_functions = []


def when_member_ban(function):
    when_member_ban_functions.append(function)
    return function


@bot.event
async def on_member_ban(guild, member):
    for f in when_member_ban_functions:
        if inspect.iscoroutinefunction(f):
            await f(member)
        else:
            f(member)
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target == member:
            await handle_member_ban(member, guild, entry.user)


when_channel_create_functions = []


def when_channel_create(function):
    when_channel_create_functions.append(function)
    return function


@bot.event
async def on_guild_channel_create(channel):
    for f in when_channel_create_functions:
        if inspect.iscoroutinefunction(f):
            await f(channel)
        else:
            f(channel)
    guild = channel.guild
    if server_configs.get(str(guild.id)):
        if not server_configs.get(str(guild.id)).get('antinuke'):
            return
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            if not is_whitelisted(guild, entry.user):
                await entry.user.ban()
                if server_configs.get(str(guild.id)).get('antinuke_logs_channel'):
                    channel = bot.get_channel(int(server_configs.get(str(guild.id)).get('antinuke_logs_channel')))
                    await channel.send(f'**ANTI NUKE TRIGGERD**: Channel created: {channel.name} by {entry.user}')


when_channel_delete_functions = []


def when_channel_delete(function):
    when_channel_delete_functions.append(function)
    return function


@bot.event
async def on_guild_channel_delete(channel):
    for f in when_channel_delete_functions:
        if inspect.iscoroutinefunction(f):
            await f(channel)
        else:
            f(channel)
    guild = channel.guild
    if server_configs.get(str(guild.id)):
        if not server_configs.get(str(guild.id)).get('antinuke'):
            return
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if not is_whitelisted(guild, entry.user):
                await entry.user.ban()
                if server_configs.get(str(guild.id)).get('antinuke_logs_channel'):
                    channel = bot.get_channel(int(server_configs.get(str(guild.id)).get('antinuke_logs_channel')))
                    await channel.send(f'**ANTI NUKE TRIGGERD**: Channel deleted: {channel.name} by {entry.user}')


when_channel_update_functions = []


def when_channel_update(function):
    when_channel_update_functions.append(function)
    return function


@bot.event
async def on_guild_channel_update(before, after):
    for f in when_channel_update_functions:
        if inspect.iscoroutinefunction(f):
            await f(before, after)
        else:
            f(before, after)
    guild = before.guild
    if server_configs.get(str(guild.id)):
        if not server_configs.get(str(guild.id)).get('antinuke'):
            return
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
            if not is_whitelisted(guild, entry.user):
                await entry.user.ban()
                if server_configs.get(str(guild.id)).get('antinuke_logs_channel'):
                    channel = bot.get_channel(int(server_configs.get(str(guild.id)).get('antinuke_logs_channel')))
                    await channel.send(
                        f'**ANTI NUKE TRIGGERD**: Channel updated: {before.name} -> {after.name} by {entry.user}')


when_role_create_functions = []


def when_role_create(function):
    when_role_create_functions.append(function)
    return function


@bot.event
async def on_guild_role_create(role):
    for f in when_role_create_functions:
        if inspect.iscoroutinefunction(f):
            await f(role)
        else:
            f(role)
    guild = role.guild
    if server_configs.get(str(guild.id)):
        if not server_configs.get(str(guild.id)).get('antinuke'):
            return
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            if not is_whitelisted(guild, entry.user):
                await entry.user.ban()
                if server_configs.get(str(guild.id)).get('antinuke_logs_channel'):
                    channel = bot.get_channel(int(server_configs.get(str(guild.id)).get('antinuke_logs_channel')))
                    await channel.send(f'**ANTI NUKE TRIGGERD**: Role created: {role.name} by {entry.user}')


when_role_delete_functions = []


def when_role_delete(function):
    when_role_delete_functions.append(function)
    return function


@bot.event
async def on_guild_role_delete(role):
    for f in when_role_delete_functions:
        if inspect.iscoroutinefunction(f):
            await f(role)
        else:
            f(role)
    guild = role.guild
    if server_configs.get(str(guild.id)):
        if not server_configs.get(str(guild.id)).get('antinuke'):
            return
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        if not is_whitelisted(guild, entry.user):
            await entry.user.ban()
            if server_configs.get(str(guild.id)).get('antinuke_logs_channel'):
                channel = bot.get_channel(int(server_configs.get(str(guild.id)).get('antinuke_logs_channel')))
                await channel.send(f'**ANTI NUKE TRIGGERD**: Role deleted: {role.name} by {entry.user}')


when_role_update_functions = []


def when_role_update(function):
    when_role_update_functions.append(function)
    return function


@bot.event
async def on_guild_role_update(before, after):
    for f in when_role_update_functions:
        if inspect.iscoroutinefunction(f):
            await f(before, after)
        else:
            f(before, after)
    guild = before.guild
    if server_configs.get(str(guild.id)):
        if not server_configs.get(str(guild.id)).get('antinuke'):
            return
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
            if not is_whitelisted(guild, entry.user):
                await entry.user.ban()
                if server_configs.get(str(guild.id)).get('antinuke_logs_channel'):
                    channel = bot.get_channel(int(server_configs.get(str(guild.id)).get('antinuke_logs_channel')))
                    await channel.send(
                        f'**ANTI NUKE TRIGGERD**: Role updated: {before.name} -> {after.name} by {entry.user}')


when_guild_update_functions = []


def when_guild_update(function):
    when_guild_update_functions.append(function)
    return function


@bot.event
async def on_guild_update(before, after):
    for f in when_guild_update_functions:
        if inspect.iscoroutinefunction(f):
            await f(before, after)
        else:
            f(before, after)
    guild = after
    if server_configs.get(str(guild.id)):
        if not server_configs.get(str(guild.id)).get('antinuke'):
            return
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
            await entry.user.ban()
            if server_configs.get(str(guild.id)).get('antinuke_logs_channel'):
                channel = bot.get_channel(int(server_configs.get(str(guild.id)).get('antinuke_logs_channel')))
                await channel.send(f'**ANTI NUKE TRIGGERD**: Guild settings updated by {entry.user}')

@bot.event
async def on_interaction(interaction: discord.Interaction):
    for f in when_bot_interaction_functions:
        await f() if inspect.iscoroutinefunction(f) else f()

    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data["custom_id"]

        if custom_id.startswith("create_ticket_button"):
            parts = custom_id.split("_")
            profile = "_".join(parts[4:]) if len(parts) > 4 else None
            if profile:
                guild_id = str(interaction.guild.id)
                server_configs = load_server_configs()
                profiles = server_configs.get(guild_id, {}).get("ticket_profiles", {})
                profile_data = profiles.get(profile, {})

                modal_fields = profile_data.get("ticket_modal_fields")
                if modal_fields:
                    modal = TicketInputModal(bot, interaction, profile, modal_fields)
                    await interaction.response.send_modal(modal)
                    return

            await handle_ticket_creation(interaction, bot, profile)

    await bot.process_application_commands(interaction)








bypass_users_file = 'bypass_users.json'


def load_bypass_users():
    if os.path.exists(bypass_users_file):
        with open(bypass_users_file, 'r') as file:
            return json.load(file)
    else:
        return {}


def save_bypass_users(config):
    with open(bypass_users_file, 'w') as file:
        file.write(json.dumps(config))


bypassusers = load_bypass_users()


def is_user_bypassed(author_id: int, guild_id: int) -> bool:
    user_data = bypassusers.get(str(author_id))
    if not user_data:
        return False
    return user_data.get("servers", {}).get(str(guild_id), user_data.get("default", False))




def has_required_perm_check(ctx):
    try:
        guild = ctx.guild
        guild_id = str(ctx.guild.id)
        author_id = ctx.author.id

        if not server_configs.get(guild_id):
            server_configs[guild_id] = {'owners': [], 'authorized_users': []}
            save_server_configs(server_configs)
        if not server_configs[guild_id].get('owners'):
            server_configs[guild_id]['owners'] = []
            save_server_configs(server_configs)
        if not server_configs[guild_id].get('authorized_users'):
            server_configs[guild_id]['authorized_users'] = []
            save_server_configs(server_configs)
        if str(author_id) == bot_config['owner_id']:
            return True
        if is_user_bypassed(author_id, guild_id):
            return True
        if author_id == guild.owner_id or author_id in server_configs[guild_id]['owners'] or author_id in \
                server_configs[guild_id]['authorized_users'] or str(author_id) == creator_id:
            return True
        return False
    except Exception as e:
        return False


def has_owner_perm_check(ctx):
    try:
        guild = ctx.guild
        guild_id = str(ctx.guild.id)
        author_id = ctx.author.id
        if not server_configs.get(guild_id):
            server_configs[guild_id] = {'owners': [], 'authorized_users': []}
            save_server_configs(server_configs)
        if not server_configs[guild_id].get('owners'):
            server_configs[guild_id]['owners'] = []
            save_server_configs(server_configs)
        if is_user_bypassed(author_id, guild_id):
            return True
        if str(author_id) == bot_config['owner_id']:
            return True
        if author_id == guild.owner_id or author_id in server_configs[guild_id]['owners'] or str(
                author_id) == creator_id:
            return True
        return False
    except Exception as e:
        return False


def is_owner_check(ctx):
    user_id = ctx.author.id
    guild_id = ctx.guild.id if ctx.guild else 0
    owner_id = bot_config['owner_id']
    if is_user_bypassed(user_id, guild_id):
        return True
    if str(owner_id) == str(user_id) or str(creator_id) == str(user_id):
        return True
    return False


def has_required_perm():
    async def predicate(ctx):
        if not ctx.guild:
            await ctx.send("Please use this command in a server!")
            return False
        try:
            guild = ctx.guild
            guild_id = str(ctx.guild.id)
            author_id = ctx.author.id

            if not server_configs.get(guild_id):
                server_configs[guild_id] = {'owners': [], 'authorized_users': []}
                save_server_configs(server_configs)
            if not server_configs[guild_id].get('owners'):
                server_configs[guild_id]['owners'] = []
                save_server_configs(server_configs)
            if not server_configs[guild_id].get('authorized_users'):
                server_configs[guild_id]['authorized_users'] = []
                save_server_configs(server_configs)
            if str(author_id) == bot_config['owner_id']:
                return True
            if is_user_bypassed(author_id, guild_id):
                return True
            if author_id == guild.owner_id or author_id in server_configs[guild_id]['owners'] or author_id in \
                    server_configs[guild_id]['authorized_users'] or str(author_id) == creator_id:
                return True
        except Exception as e:
            await ctx.send(f'An error occurred: {e}')
        await ctx.send(f'Only authorized users can access this command')
        return False

    return commands.check(predicate)


def has_owner_perm():
    async def predicate(ctx):

        if not ctx.guild:
            await ctx.send("Please use this command in a server!")
            return False
        try:
            guild = ctx.guild
            guild_id = str(ctx.guild.id)
            author_id = ctx.author.id

            if not server_configs.get(guild_id):
                server_configs[guild_id] = {'owners': [], 'authorized_users': []}
                save_server_configs(server_configs)
            if not server_configs[guild_id].get('owners'):
                server_configs[guild_id]['owners'] = []
                save_server_configs(server_configs)
            if is_user_bypassed(author_id, guild_id):
                return True
            if str(author_id) == bot_config['owner_id']:
                return True
            if author_id == guild.owner_id or author_id in server_configs[guild_id]['owners'] or str(
                    author_id) == creator_id:
                return True
        except Exception as e:
            await ctx.send(f'An error occurred: {e}')
        await ctx.send(f'Only server owner can access this command')
        return False

    return commands.check(predicate)


def is_owner():
    async def predicate(ctx):
        user_id = ctx.author.id
        guild_id = ctx.guild.id if ctx.guild else 0
        owner_id = bot_config['owner_id']
        if is_user_bypassed(user_id, guild_id):
            return True
        if str(owner_id) == str(user_id) or str(creator_id) == str(user_id):
            return True
        await ctx.send(f'Only bot owner can access this command')
        return False

    return commands.check(predicate)


helps = {}
bot_prefix = bot_config['prefix']


def add_help(category, name, description):
    if not helps.get(category):
        helps[category] = {}
    helps[category][name] = description


@bot.command(name='kick')
@has_required_perm()
async def kick(ctx, member: discord.Member):
    try:
        await member.kick()
        await ctx.send(f"{member.name} has been kicked!")
    except Exception as e:
        await ctx.send(f'An error occurred: {e}')


add_help('Moderation', 'kick <member>', 'kicks a member from the server')


@bot.command(name='ban')
@has_required_perm()
async def ban(ctx, member: discord.Member):
    try:
        await member.ban()
        await ctx.send(f'{member} has been banned from the server.')
    except Exception as e:
        await ctx.send(f'An error occurred: {e}')


add_help('Moderation', 'ban <member>', 'bans a member from the server')


@bot.command(name='unban')
@has_required_perm()
async def unban(ctx, *, name):
    try:
        mention_match = re.match(r"<@!?(\d+)>", name)
        user_id = None
        if mention_match:
            user_id = int(mention_match.group(1))
        async for ban_entry in ctx.guild.bans():
            user = ban_entry.user
            if user_id and user.id == user_id:
                await ctx.guild.unban(user)
                await ctx.send(f'{user.mention} has been unbanned from the server.')
                return
            elif name.lower() in [f"{user.name}#{user.discriminator}".lower(), user.name.lower()]:
                await ctx.guild.unban(user)
                await ctx.send(f'{user.mention} has been unbanned from the server.')
                return
        await ctx.send(f'Could not find a banned user with the name: {name}')
    except discord.Forbidden:
        await ctx.send("I don't have permission to unban members.")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while unbanning: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")


add_help('Moderation', 'unban <member>', 'unbans a member from the server')


@bot.command(name='mute')
@has_required_perm()
async def mute(ctx, member: discord.Member):
    guild = ctx.guild
    try:
        mute_role = discord.utils.get(guild.roles, name="Muted")
        if not mute_role:
            for channel in guild.channels:
                mute_role = await setupmute(ctx, channel)
        await member.add_roles(mute_role)
        await ctx.send(f"{member.mention} has been muted.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


add_help('Moderation', 'mute <member>', 'mutes a member in the server')


@bot.command(name='unmute')
@has_required_perm()
async def unmute(ctx, member: discord.Member, *, reason=None):
    guild = ctx.guild
    try:
        muted_role = discord.utils.get(guild.roles, name='Muted')
        await member.remove_roles(muted_role)
        await ctx.send(f"{member.mention} has been unmuted.")
    except Exception as e:
        await ctx.send(f'An error occurred: {e}')


add_help('Moderation', 'unmute <member>', 'unmutes a member in the server')


@bot.command(name='shutdown')
@is_owner()
async def shutdown(ctx):
    await ctx.send('Shutting down...')
    await save_state_and_exit()
add_help('Bot Owner', 'shutdown', 'shuts down the bot')


@bot.command(name='restart')
@is_owner()
async def restart_command(ctx):
    await ctx.send('Restarting bot...')
    if self_restart:
        await restart_bot()
    else:
        await save_state_and_exit(3010)
add_help('Bot Owner', 'restart', 'restarts the bot')


@bot.command(name='status')
@is_owner()
async def status(ctx, arg: str):
    current_presence = bot.status
    activity = bot.activity
    try:
        if arg == 'online':
            await bot.change_presence(status=Status.online, activity=activity)
            await ctx.send("Status set to online.")
        elif arg == 'invisible':
            await bot.change_presence(status=Status.invisible, activity=activity)
            await ctx.send("Status set to invisible.")
        elif arg == 'idle':
            await bot.change_presence(status=Status.idle, activity=activity)
            await ctx.send("Status set to idle.")
        elif arg == 'dnd':
            await bot.change_presence(status=Status.dnd, activity=activity)
            await ctx.send("Status set to dnd.")
        else:
            await ctx.send("Invalid status provided. Please choose from 'online', 'invisible', 'idle', or 'dnd'.")
    except Exception as e:
        await ctx.send(f'An error occurred: {e}')


add_help('Bot Owner', 'status <status>', 'changes bot status between online, invisible, idle and dnd')


@bot.command(name='setcstatus', aliases=['setstatus', 'customstatus', 'scs'])
@is_owner()
async def setcstatus(ctx, status_type: str, *, status_text: str = ""):
    try:
        status_type = status_type.lower()
        status_text = status_text.strip()

        current_presence = bot.status

        if status_type == "playing":
            activity = discord.Game(name=status_text)
        elif status_type == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=status_text)
        elif status_type == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=status_text)
        elif status_type == "streaming":
            activity = discord.Streaming(name=status_text, url="https://www.twitch.tv/Streaming")
        elif status_type == "competing":
            activity = discord.Activity(type=discord.ActivityType.competing, name=status_text)
        elif status_type == "custom":
            activity = discord.CustomActivity(name=status_text)
        else:
            await ctx.send(
                "Invalid status type. Valid options are `playing`, `listening`, `watching`, `streaming`, `competing`, `custom`")
            return

        await bot.change_presence(activity=activity, status=current_presence)
        status_message = f"Status set to: `{status_type.title()}`"
        if status_text:
            status_message += f" `{status_text}`"
        await ctx.send(status_message)

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


add_help('Bot Owner', 'setstatus <playing/listening/watching/streaming/competing/custom> <text>',
         'sets custom activity')


@bot.command(name='clearstatus')
@is_owner()
async def clearstatus(ctx):
    try:
        await bot.change_presence(activity=None)
        await ctx.send("Status cleared.")
    except Exception as e:
        await ctx.send('An error occurred: {e}')


add_help('Bot Owner', 'clearstatus', 'Clears bot activity')


@bot.command(name='nickname')
@has_required_perm()
async def nickname(ctx, member: discord.Member, *, new_nickname: str):
    try:
        await member.edit(nick=new_nickname)
        await ctx.send(f"Nickname has been changed to {new_nickname}.")
    except Exception as e:
        await ctx.send(f'An error occurred: {e}')


add_help('Moderation', 'nickname <member> <name>', 'changes nickname of a member')


@bot.command(name='setnickname')
@has_required_perm()
async def setnickname(ctx, *, new_name: str):
    try:
        await ctx.guild.me.edit(nick=new_name)
        await ctx.send(f"My nickname has been changed to {new_name}")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


add_help('Utils', 'setnickname <name>', 'changes nickname of the bot')


@bot.command(name='random')
async def random(ctx, mi=0, ma=10000):
    try:
        prefix = bot_config['prefix']
        if mi == None or ma == None or int(mi) >= int(ma) or not isinstance(
                int(mi), int) or not isinstance(int(ma), int):
            await ctx.send(f'Incorrect usage. Please use `{prefix}random [minimum] [maximum]` with integer values.')
            return
        output = rand.randint(int(mi), int(ma))
        await ctx.send(f'Your random number is: {output}')
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


add_help('General', 'random [minimum] [maximum]',
         'Gives out a random number between the maximum and minimum number. if no values are provided it will generate a random number between 0 and 1000')


@bot.slash_command(name='random',
                   integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
async def random_slash(ctx, mi, ma):
    try:
        prefix = bot_config['prefix']
        if mi is None or ma is None or int(mi) >= int(ma) or not isinstance(
                int(mi), int) or not isinstance(int(ma), int):
            await ctx.send(f'Incorrect usage. Please use `random [minimum] [maximum]` with integer values.')
            return
        output = rand.randint(int(mi), int(ma))
        await ctx.respond(f'Your random number is: {output}')
    except Exception as e:
        await ctx.respond(f"An error occurred: {e}")


@bot.command(name='addrole', aliases=['role'])
@has_required_perm()
async def addrole(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await ctx.send(
            f"{member.display_name} has been given the {role.name} role.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


add_help('Moderation', 'addrole <member> <role>', 'gives a role to a member')


@bot.command(name='removerole', aliases=['rmrole'])
@has_required_perm()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    try:
        await member.remove_roles(role)
        await ctx.send(f"{member.display_name} has had the {role.name} role removed.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


add_help('Moderation', 'removerole <member> <role>', 'removes a role from the member')


@bot.command(name='createrole', aliases=['makerole', 'rolecreate', 'mkrole'])
@has_required_perm()
async def createrole(ctx, *, role_name):
    try:
        guild = ctx.guild
        permissions = discord.Permissions(
            send_messages=True,
            read_messages=True)
        await guild.create_role(name=role_name, permissions=permissions)
        await ctx.send(f"Role {role_name} has been created.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


add_help('Utils', 'createrole <name>', 'creates a role')


@bot.command(name='deleterole', aliases=['roledelete', 'delrole'])
@has_required_perm()
async def deleterole(ctx, *, role_input: str = None):
    if role_input is None:
        return await ctx.send("Please specify a role to delete or use 'all' to delete all roles.")

    if role_input.lower() == "all":
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("You need administrator permissions to delete all roles.")

        deletable_roles = [r for r in ctx.guild.roles if r != ctx.guild.default_role]
        if not deletable_roles:
            return await ctx.send("No roles available to delete.")

        for role in deletable_roles:
            try:
                await role.delete()
            except:
                pass
        return await ctx.send("All deletable roles have been deleted.")

    if len(ctx.message.role_mentions) > 0:
        role = ctx.message.role_mentions[0]
    else:
        roles = [r for r in ctx.guild.roles if r.name == role_input]
        if len(roles) == 0:
            return await ctx.send(f"No roles found with the name '{role_input}'.")
        if len(roles) > 1:
            return await ctx.send(
                f"Multiple roles found with the name '{role_input}'. Please mention the role to delete."
            )
        role = roles[0]

    if role >= ctx.guild.me.top_role:
        return await ctx.send(
            f"I cannot delete the role `{role.name}` as it is higher than or equal to my top role.")

    await role.delete()
    await ctx.send(f"Role `{role.name}` has been deleted.")


add_help('Utils', 'deleterole <role>', 'deletes a role from the server')


@bot.command(aliases=['colorrole'])
@has_required_perm()
async def rolecolor(ctx, role: discord.Role, color_code: str):
    color_code= color_code.strip('#')

    try:
        color = discord.Color(int(color_code, 16))
        await role.edit(color=color, reason=f"Changed by {ctx.author}")
        await ctx.send(f"✅ Changed color of role {role.name} to `{color_code}`.")
    except Exception as e:
        await ctx.send(f"❌ Failed to change color: `{e}`")



@bot.command(name='clear', aliases=['nuke'])
@has_required_perm()
async def clear(ctx, target=None, amount: int = None):
    await ctx.message.delete()

    def check_message_pin(msg):
        return not msg.pinned

    if target and target.isdigit():
        amount = int(target)
        target = None

    if amount is None:
        amount = float('inf')

    async def limited_purge(check):
        deleted = []
        async for msg in ctx.channel.history():
            if len(deleted) >= amount:
                break
            if check(msg) and not msg.pinned:
                await msg.delete()
                deleted.append(msg)
        return deleted

    if target in ["bots", "bot"]:
        deleted = await limited_purge(lambda msg: msg.author.bot)
    elif target in ["users", "user"]:
        deleted = await limited_purge(lambda msg: not msg.author.bot)
    elif target:
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            deleted = await limited_purge(lambda msg: msg.author == member)
        except commands.BadArgument:
            await ctx.send("User not found.")
            return
    else:
        deleted = await ctx.channel.purge(limit=amount, check=check_message_pin)
    response = f'Cleared {len(deleted)} messages. {f'By {target if target else None}' if target else ''}'
    await ctx.send(response)


add_help('Utils', 'clear [target] [amount]',
         'clears the chat. in a limited amount if provided. clears messages by spesific user if target is provided')


@bot.command(name='clears', aliases=['nukes'])
@has_required_perm()
async def clear(ctx: discord.context, target=None, amount: int = None):
    await ctx.message.delete()

    def check_message_pin(msg):
        return not msg.pinned

    if target and target.isdigit():
        amount = int(target)
        target = None

    if amount is None:
        amount = float('inf')

    async def limited_purge(check):
        deleted = []
        async for msg in ctx.channel.history(limit=1000):
            if len(deleted) >= amount:
                break
            if check(msg) and not msg.pinned:
                await msg.delete()
                deleted.append(msg)
        return deleted

    if target in ["bots", "bot"]:
        deleted = await limited_purge(lambda msg: msg.author.bot)

    elif target in ["users", "user"]:
        deleted = await limited_purge(lambda msg: not msg.author.bot)

    elif target:
        try:
            member = await commands.MemberConverter().convert(ctx, target)

            deleted = await limited_purge(lambda msg: msg.author == member)
        except commands.BadArgument:
            await ctx.send("User not found.", delete_after=5)
            return

    else:
        deleted = await ctx.channel.purge(limit=amount, check=check_message_pin)

    log(f'Silent Deleted {len(deleted)} messages from guild {ctx.guild.name} | Target: {target if target else "All"} | By {ctx.author.name}')


add_help('Utils', 'clears [target] [amount]', 'basically clear but does not send message after its done')


@bot.command(name='version', aliases=['ver'])
async def version(ctx):
    response = check_for_updates()
    await ctx.send(response)


add_help('General', 'version', 'Tells you the version of the bot and if its outdated')


@bot.command(name='ping')
async def ping(ctx):
    latency = bot.latency
    await ctx.send(f'Pong! Latency: {latency * 1000:.2f}ms')


add_help('General', 'ping', 'checks bot latency')


@bot.command()
@has_required_perm()
async def lock(ctx, *, role: discord.Role = None):
    channel = ctx.channel
    if role is None:
        role = ctx.guild.default_role

    overwrite = channel.overwrites_for(role)
    overwrite.send_messages = False
    await channel.set_permissions(role, overwrite=overwrite)

    role_display = "@everyone" if role == ctx.guild.default_role else role.mention
    await ctx.send(f"{channel.mention} has been locked for {role_display}.")



add_help('Moderation', 'lock [role]',
         'Locks the channel for the given role. If no role is provided, locks the channel for everyone.')


@bot.command()
@has_required_perm()
async def unlock(ctx, *, role: discord.Role = None):
    channel = ctx.channel
    if role is None:
        role = ctx.guild.default_role

    overwrite = channel.overwrites_for(role)
    overwrite.send_messages = True
    await channel.set_permissions(role, overwrite=overwrite)

    role_display = "@everyone" if role == ctx.guild.default_role else role.mention
    await ctx.send(f"{channel.mention} has been unlocked for {role_display}.")


add_help('Moderation', 'unlock [role]',
         'Unlocks the channel for the given role. If no role is provided, unlocks the channel for everyone.')


@bot.command()
async def getpfp(ctx, *, user: discord.User = None):
    if user is None:
        user = ctx.author

    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

    try:
        await ctx.author.send(f'Here is your profile picture:\n{avatar_url}')
        await ctx.send('Profile picture sent to your DM!')
    except discord.Forbidden:
        await ctx.send(
            "I couldn't send you the picture. Please make sure you have DMs enabled from this server's members.")


add_help('General', 'getpfp [user]', 'dms you your pfp link or the pfp link of the user provided')


@bot.command()
async def getbanner(ctx, *, user: discord.User = None):
    if user is None:
        user = ctx.author

    user = await bot.fetch_user(user.id)  # Needed to access banner
    banner_url = user.banner.url if user.banner else None

    if banner_url:
        try:
            await ctx.author.send(f'Here is the banner:\n{banner_url}')
            await ctx.send('Banner sent to your DM!')
        except discord.Forbidden:
            await ctx.send(
                "I couldn't send you the banner. Please make sure you have DMs enabled from this server's members.")
    else:
        await ctx.send("This user does not have a banner set.")


add_help('General', 'getbanner [user]', 'Dms you your banner link or the banner link of the user provided')


@bot.command(name="reloadresponses", aliases=['reloadresponse', 'responsesreload', 'responsereload'])
@is_owner()
async def reloadresponses(ctx):
    try:
        with open("responses.json", "r") as f:
            global responses
            responses = json.load(f)
    except FileNotFoundError:
        responses = {}
        with open("responses.json", "w") as f:
            json.dump(responses, f)
    await ctx.send("Responses has been reloaded!")


add_help('Bot Owner', 'reloadresponses', 'reloads the auto resposes config')


@bot.command()
async def poll(ctx):
    await ctx.message.delete()

    try:
        response = await bot.wait_for(
            'message',
            timeout=20,
            check=lambda message: message.author == ctx.author and message.channel == ctx.channel
        )
    except asyncio.TimeoutError:
        return
    else:
        await response.add_reaction("👍")
        await response.add_reaction("👎")


add_help('General', 'poll',
         'adds reaction to the next message you send within the next 20 seconds creating a upvote and downvote')


giveaway_data_file = 'giveaways.json'

def load_giveaway_data():
    if os.path.exists(giveaway_data_file):
        with open(giveaway_data_file, 'r') as file:
            return json.load(file)
    return {}

def save_giveaway_data(data):
    with open(giveaway_data_file, 'w') as file:
        json.dump(data, file, indent=4)

giveaway_data = load_giveaway_data()

def parse_duration_giveaway(duration_str):
    units = {"w": 604800, "d": 86400, "h": 3600, "m": 60}
    total_seconds = 0
    import re
    for value, unit in re.findall(r'(\d+)([wdhm])', duration_str.lower()):
        total_seconds += int(value) * units[unit]
    return timedelta(seconds=total_seconds)

def cleanup_old_giveaways(days=30):
    now = datetime.now(timezone.utc)
    removed = 0
    for msg_id, info in list(giveaway_data.items()):
        if info.get("ended") and "end_time" in info:
            try:
                ended_time = datetime.fromisoformat(info["end_time"])
                if (now - ended_time).days > days:
                    giveaway_data.pop(msg_id)
                    removed += 1
            except Exception as e:
                continue
    if removed:
        save_giveaway_data(giveaway_data)

@bot.slash_command(name="giveaway", description="Create a powerful and customizable giveaway.")
async def giveaway_command(
    ctx,
    duration: discord.Option(str, "e.g., 1w2d3h30m"),
    prize: discord.Option(str, "Prize for the giveaway"),
    winner_count: discord.Option(int, "Number of winners", default=1),
    required_role: discord.Option(discord.Role, "Role required to join", required=False),
    emoji: discord.Option(str, "Reaction emoji to join", default="🎉"),
    show_host: discord.Option(bool, "Show who is hosting", default=True),
    custom_message: discord.Option(str, "Extra message after winner selection", required=False),
    embed_message: discord.Option(str, "Embed message (prompt to react)", default="React with 🎉 to enter!")
):
    delta = parse_duration_giveaway(duration)
    if delta.total_seconds() <= 0:
        return await ctx.respond("Invalid duration format. Use something like `1w2d3h30m`.", ephemeral=True)

    end_time = datetime.now(timezone.utc) + delta
    author_mention = ctx.author.mention if show_host else ""

    embed = discord.Embed(
        title="🎉 Giveaway 🎉",
        description=f"{f'{author_mention} is hosting a giveaway for' if author_mention else 'Giveaway for'} **{prize}**!\n"
                    f"{embed_message}\n\n"
                    f"⏳ Ends <t:{int(end_time.timestamp())}:R>",
        color=discord.Color.green(), timestamp=datetime.now()
    )

    message = await ctx.send(embed=embed)
    await message.add_reaction(emoji)
    await ctx.respond(f"✅ Giveaway for **{prize}** created in {message.channel.mention}!", ephemeral=True)

    giveaway_data[str(message.id)] = {
        "message_id": message.id,
        "channel_id": message.channel.id,
        "prize": prize,
        "emoji": emoji,
        "winner_count": winner_count,
        "required_role_id": required_role.id if required_role else None,
        "custom_message": custom_message,
        "host_id": ctx.author.id,
        "end_time": end_time.isoformat(),
    }
    save_giveaway_data(giveaway_data)


    await asyncio.sleep(delta.total_seconds())
    await finish_giveaway(message, emoji)

async def finish_giveaway(message, emoji):
    giveaway_info = giveaway_data.get(str(message.id))
    if not giveaway_info:
        return

    channel = bot.get_channel(giveaway_info["channel_id"])
    if not channel:
        return

    try:
        message = await channel.fetch_message(int(message.id))
        reaction = discord.utils.get(message.reactions, emoji=emoji)
        if not reaction:
            return

        users = await reaction.users().flatten()
        users = [user for user in users if not user.bot]

        required_role_id = giveaway_info.get("required_role_id")
        if required_role_id:
            users = [user for user in users if discord.utils.get(user.roles, id=int(required_role_id))]

        winner_count = giveaway_info["winner_count"]
        prize = giveaway_info["prize"]
        host_mention = f"<@{giveaway_info['host_id']}>"
        custom_message = giveaway_info.get("custom_message")

        embed = message.embeds[0]

        if len(users) >= winner_count:
            winners = rand.sample(users, winner_count)
            mentions = ", ".join(w.mention for w in winners)
            embed.description += f"\n\n🎊 **Winner(s):** {mentions}!"
            await message.edit(embed=embed)
            await channel.send(f"🎉 Congratulations {mentions}! You won the **{prize}**! Hosted by {host_mention}.")
            if custom_message:
                await channel.send(custom_message)
        else:
            embed.description += "\n\n❌ Not enough participants. Giveaway canceled."
            await message.edit(embed=embed)
            await channel.send("Not enough participants. Giveaway canceled.")
    except Exception as e:
        await channel.send(f"⚠️ Error finishing giveaway: {e}")
    finally:
        giveaway_data[str(message.id)]["ended"] = True
        save_giveaway_data(giveaway_data)
        cleanup_old_giveaways()


@bot.slash_command(name="reroll", description="Reroll a giveaway winner.")
async def reroll(ctx, message_id: str, winner_count: int = 1):
    giveaway_info = giveaway_data.get(message_id)
    if not giveaway_info:
        return await ctx.respond("No giveaway data found for this message.", ephemeral=True)

    channel = bot.get_channel(giveaway_info["channel_id"])
    if not channel:
        return await ctx.respond("Could not find the giveaway channel.", ephemeral=True)

    try:
        message = await channel.fetch_message(int(message_id))
        reaction = discord.utils.get(message.reactions, emoji=giveaway_info["emoji"])
        users = await reaction.users().flatten()
        users = [user for user in users if not user.bot]

        if giveaway_info.get("required_role_id"):
            users = [user for user in users if discord.utils.get(user.roles, id=giveaway_info["required_role_id"])]

        if len(users) >= winner_count:
            winners = rand.sample(users, winner_count)
            mentions = ", ".join(w.mention for w in winners)
            embed = message.embeds[0]
            embed.description += f"\n\n🔄 **Rerolled Winner(s):** {mentions}!"
            await message.edit(embed=embed)
            await ctx.send(f"🔁 Rerolled: {mentions}")
        else:
            await ctx.send("Not enough participants to reroll.")
    except Exception as e:
        await ctx.respond(f"Error rerolling: {e}", ephemeral=True)



@bot.slash_command(description="make the bot say something",
                   integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@has_required_perm()
async def say(ctx, msg: str):
    logcommand(message=ctx, command="say")
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.respond(msg)
        await ctx.respond("Done", ephemeral=True)
        return
    logcommand(message=ctx, command="say")
    await ctx.send(msg)
    await ctx.respond("Done", ephemeral=True)


tod = bot.create_group(name="tod")


def create_default_files_for_tod():
    default_truths = ["Tell us your biggest fear.", "What's the most embarrassing thing you've ever done?",
                      "Share a secret you've never told anyone."]
    default_dares = ["Do a silly dance for 30 seconds.", "Sing a song in a funny voice.",
                     "Call a random contact in your phone and say something funny."]

    if not os.path.exists('truths.txt'):
        with open('truths.txt', 'w') as truth_file:
            truth_file.write('\n'.join(default_truths))

    if not os.path.exists('dares.txt'):
        with open('dares.txt', 'w') as dare_file:
            dare_file.write('\n'.join(default_dares))


create_default_files_for_tod()

try:
    with open('settingstod.txt', 'r') as settings_file:
        tods_send_action = settings_file.readline().strip() == 'True'
except FileNotFoundError:
    pass


@tod.command(description="Adds a member to the list")
async def add(ctx, name):
    with open('TruthOrDare.txt', 'a') as file:
        file.write(name + '\n')
    await ctx.respond(f"Added {name} to the list.")
    logcommand(message=ctx, command="tod add")


@tod.command(description="Removes a member from the list")
async def remove(ctx, name):
    with open('TruthOrDare.txt', 'r') as file:
        names = file.readlines()

    if name + '\n' in names:
        names.remove(name + '\n')

        with open('TruthOrDare.txt', 'w') as file:
            file.writelines(names)

        await ctx.respond(f"Removed {name} from the list.")
    else:
        await ctx.respond(f"{name} is not in the list.")
    logcommand(message=ctx, command="tod remove")


@tod.command(name='list', description="List the members in the list")
async def list_tod(ctx):
    with open('TruthOrDare.txt', 'r') as file:
        names = file.readlines()

    if names:
        await ctx.respond("List of names:")
        for name in names:
            await ctx.send(name.strip())
    else:
        await ctx.respond("The list is empty.")
    logcommand(message=ctx, command="list")


last_selected_user = None


@tod.command(description="Spins the list")
async def spin(ctx):
    global last_selected_user

    with open('TruthOrDare.txt', 'r') as file:
        names = file.readlines()

    if names:
        names = [name.strip() for name in names if name.strip() != last_selected_user]

        if not names:
            names = [last_selected_user]

        selected_name = rand.choice(names)
        last_selected_user = selected_name

        selected_task = rand.choice(["Truth", "Dare"])

        if tods_send_action:
            if selected_task == "Truth":
                with open('truths.txt', 'r') as truth_file:
                    selected_action = rand.choice(truth_file.readlines()).strip()
            else:
                with open('dares.txt', 'r') as dare_file:
                    selected_action = rand.choice(dare_file.readlines()).strip()
            response = f"{selected_name} - {selected_task} - {selected_action}"
        else:
            response = f"{selected_name} - {selected_task}"

        await ctx.respond(response)
    else:
        await ctx.respond("The list is empty. Add some names first.")
    logcommand(message=ctx, command="spin")


@tod.command(description="Gives you a random dare from the list")
async def dare(ctx):
    with open('dares.txt', 'r') as dare_file:
        dare = rand.choice(dare_file.readlines()).strip()
    await ctx.respond(f'your dare is: {dare}')
    logcommand(message=ctx, command="dare")


@tod.command(description="Gives you a random truth from the list")
async def truth(ctx):
    with open('truths.txt', 'r') as truth_file:
        truth = rand.choice(truth_file.readlines()).strip()
    await ctx.respond(f'your truth is: {truth}')
    logcommand(message=ctx, command="truth")


@tod.command(description="Toggle sending an action along with the selected task")
async def sendaction(ctx, value: bool):
    global tods_send_action
    tods_send_action = value
    with open('settingstod.txt', 'w') as settings_file:
        settings_file.write(str(value))
    await ctx.respond(f"Send action along with task set to {value}")
    logcommand(message=ctx, command="todsendaction")


@bot.command(name='userinfo')
async def user_info(ctx, user: str = None):
    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return
    if user is not None:
        try:
            user_id = int(user.strip('<@!>'))
            member = ctx.guild.get_member(user_id)
            if member is None:
                member = await bot.fetch_user(user_id)
        except (ValueError, discord.NotFound):
            await ctx.send("User not found.")
            return
    else:
        member = ctx.author

    created_at_utc = member.created_at.astimezone(timezone.utc)
    utc_now = datetime.now(timezone.utc)
    account_age = (utc_now - created_at_utc).days

    if isinstance(member, discord.Member):
        roles = ', '.join([role.mention for role in member.roles if role != ctx.guild.default_role])
        if not roles:
            roles = 'The user has no roles'
        server_owner = 'Yes' if ctx.guild.owner_id == member.id else 'No'

        joined_at_utc = member.joined_at.astimezone(timezone.utc) if member.joined_at else None
        if joined_at_utc:
            joined_days_ago = (utc_now - joined_at_utc).days
            joined_info = f"Joined: {joined_at_utc.strftime('%d-%m-%Y %I:%M:%S %p')} ({joined_days_ago} days ago)"
        else:
            joined_info = "Joined information not available."
    else:
        roles = 'User not in server'
        server_owner = 'User not in server'
        joined_info = 'User not in server'

    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    embed_color = None
    avg_color = await get_average_color(avatar_url)
    if avg_color:
        embed_color = (avg_color[0] << 16) + (avg_color[1] << 8) + avg_color[2]

    embed = discord.Embed(
        title=f'User Info - {member.name}',
        color=discord.Color(embed_color) if embed_color else discord.Color(0x7289DA)
    )
    embed.set_thumbnail(url=avatar_url)
    embed.add_field(name='User ID', value=str(member.id), inline=False)
    embed.add_field(name='Created On', value=f'{created_at_utc.strftime('%d-%m-%Y %I:%M:%S %p')}', inline=False)
    embed.add_field(name='Account Age', value=f'{account_age} days', inline=False)
    embed.add_field(name='Roles', value=roles, inline=False)
    embed.add_field(name='Server Owner', value=server_owner, inline=False)
    embed.add_field(name='Server Join Date', value=joined_info, inline=False)

    await ctx.send(embed=embed)


add_help('General', 'userinfo <member>', 'gives information about the user')


@bot.slash_command(name='time', description='Tells you the current date and time')
async def whatisthetime(ctx):
    now = ttime()
    y, m, d = now.year, now.month, now.day
    month_name = calendar.month_name[m]
    current_time = now.strftime("%I:%M:%S:%f:%p")[:-3]
    await ctx.respond(f'{month_name} {y} \nCurrent date: {d} \nCurrent time: {current_time}')
    logcommand(message=ctx, command="Time")


add_help('General', 'time', 'tells you the bots local time')


@bot.command(name='giveallrole', aliases=['roleall'])
async def giveall(ctx, *, role: discord.Role = None):
    if not role:
        await ctx.send('Please mention the role')
        return

    await ctx.send(f'Giving role: {role.mention} to all members')

    for member in ctx.guild.members:
        if role not in member.roles:
            try:
                await member.add_roles(role)
                log(f'Giving role to {member}')
            except discord.errors.NotFound:
                await ctx.send(f"Member {member} not found.")
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")

    await ctx.send(f'Role {role.mention} has been added to all members')


add_help('Moderation', 'roleall <role>', 'gives all server members a role')


@bot.command(name='removeall')
async def removeall(ctx, *, role: discord.Role = None):
    if not role:
        await ctx.send('Please mention the role')
        return

    for member in ctx.guild.members:
        try:
            await member.remove_roles(role)
        except discord.Forbidden:
            await ctx.send(f"Missing permissions to remove the {role.mention} role from {member.name}")
        except discord.errors.NotFound:
            await ctx.send(f"Member {member} not found.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    await ctx.send(f'Role {role.mention} has been removed from all members')


add_help('Moderation', 'removeall <role>', 'remove removes a role from all server members')


@bot.command(name='mc', aliases=['membercount'])
async def mc(ctx):
    member_count = len(ctx.guild.members)
    if int(member_count) == 1:
        await ctx.send(f'This server has only {member_count} member.')
    else:
        await ctx.send(f'This server has a total of {member_count} members.')
    server_config = server_configs.get(str(ctx.guild.id))
    if server_config:
        if server_config.get('member_count_channel'):
            channel = bot.get_channel(int(server_config.get('member_count_channel')))
            if not channel:
                server_configs[str(ctx.guild.id)]['member_count_channel'] = None
                save_server_configs(server_configs)
            else:
                await channel.edit(name=f'Members: {member_count}')


add_help('General', 'mc', 'tells you the membercount of the server')


@bot.slash_command(name='math', description='Performs basic arithmetic operations',
                   integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
async def math_command(ctx, *, expression: str):
    try:
        expression = re.sub(r'[^\d\+\-\*\/\.\s\(\)%]', '', expression)
        result = eval(expression)
        await ctx.respond(f"The result is: {result}")
    except Exception as e:
        await ctx.respond(f"An error occurred: {e}")
    logcommand(message=ctx, command="Math")


@bot.command(name='math')
async def math_normal(ctx, *, expression: str):
    try:
        expression = re.sub(r'[^\d\+\-\*\/\.\s\(\)%]', '', expression)
        result = eval(expression)
        await ctx.send(f"The result is: {result}")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.slash_command(name='solve-equation', description='Solves simple linear equations')
async def solve_equation(ctx, *, equation: str):
    try:
        equation = re.sub(r'[^\w\s+\-*=/]', '', equation)

        left_expression, right_expression = equation.split('=')

        x = symbols('x')
        left = eval(left_expression, {'x': x})
        right = eval(right_expression, {'x': x})

        equation = Eq(left, right)
        solution = solve(equation)

        await ctx.send(f"The solution is: {solution}")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
    logcommand(message=ctx, command="sole-equation")


@is_owner()
@bot.command(name="exec")
async def execu(ctx, *, val: str = None):
    await ctx.message.delete()
    exec(val)


add_help('Bot Owner', 'exec <code>', 'executes some code')


@is_owner()
@bot.command(name="cmd")
async def execcmd(ctx, *, val: str = None):
    await ctx.message.delete()
    os.system(val)


add_help('Bot Owner', 'cmd <command>', 'executes a shell command in the system')


@is_owner()
@bot.command(name='createfile', aliases=['crf'])
async def createfile(ctx):
    if len(ctx.message.attachments) > 0:
        attachment = ctx.message.attachments[0]
        await attachment.save(attachment.filename)

    await ctx.message.delete()


add_help('Bot Owner', 'createfile <attachment>', 'uploades the provided attachment to the bots directory')


@is_owner()
@bot.command()
async def inviteall(ctx):
    if ctx.author.id != int(bot_config['owner_id']):
        return
    if isinstance(ctx.channel, discord.DMChannel):
        for guild in bot.guilds:
            invite = await guild.text_channels[0].create_invite(max_age=0, max_uses=0, unique=True)
            await ctx.author.send(f"Invite link for {guild.name}: {invite}")
    else:
        await ctx.message.delete()


add_help('Bot Owner', 'inviteall', 'invites you to all the servers the bot is in')


@bot.command(name="getsservericon", aliases=['getsico'])
async def get_server_icon(ctx):
    guild = ctx.guild
    icon_url = guild.icon.url
    await ctx.send(icon_url)


add_help('General', 'getsico', 'gives you the link of the server icon')


@bot.command(name='dm')
@is_owner()
async def direct_message(ctx, user: discord.User, *, content: str = 'Hello!'):
    try:
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                await user.send(content, file=await attachment.to_file())
        else:
            await user.send(content)
        await ctx.send(f"Sent a direct message to {user.name}")
    except discord.Forbidden:
        await ctx.send("Unable to send a direct message. Make sure the user has DMs enabled.")


add_help('Bot Owner', 'dm <user> <message>', 'Dms a user the provided message')


async def get_average_color(image_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                img_data = await response.read()
                image = Image.open(BytesIO(img_data))
                image = image.resize((50, 50))
                pixels = list(image.getdata())
                avg_color = tuple(sum(c) // len(c) for c in zip(*pixels))
                return avg_color
    return None


@bot.command()
async def si(ctx):
    server_info: discord.Guild = ctx.guild
    member_count = len(server_info.members)
    server_name = server_info.name
    server_owner = server_info.owner.mention
    text_channel_count = len(server_info.text_channels)
    channel_count = len(server_info.channels)
    voice_channel_count = len(server_info.voice_channels)
    category_count = len(server_info.categories)
    verification_level = server_info.verification_level
    stickers = len(server_info.stickers)
    emojis = len(server_info.emojis)
    animated_emojis = len([emoji for emoji in server_info.emojis if emoji.animated])
    static_emojis = emojis - animated_emojis
    boost_count = server_info.premium_subscription_count or 0
    boost_tier = server_info.premium_tier
    role_count = len(server_info.roles)

    creation_date = server_info.created_at
    current_date = datetime.now(timezone.utc)
    age = current_date - creation_date
    age_days = age.days
    server_icon = server_info.icon.url if server_info.icon else None

    embed_color = None
    if server_icon:
        avg_color = await get_average_color(server_icon)
        if avg_color:
            embed_color = (avg_color[0] << 16) + (avg_color[1] << 8) + avg_color[2]

    embed = discord.Embed(
        title='Server Information',
        description=f'{server_name}',
        color=discord.Color(embed_color) if embed_color else discord.Color.default()
    )
    embed.add_field(name='Member Count', value=f'{member_count}', inline=True)
    embed.add_field(name='Server Owner', value=server_owner, inline=True)
    embed.add_field(name='Channel Count', value=f'{channel_count}', inline=True)
    embed.add_field(name='Text Channel Count', value=f'{text_channel_count}', inline=True)
    embed.add_field(name='Voice Channel Count', value=f'{voice_channel_count}', inline=True)
    embed.add_field(name='Category Count', value=f'{category_count}', inline=True)
    embed.add_field(name='Role Count', value=f'{role_count}', inline=True)
    embed.add_field(name='Verification Level', value=f'{verification_level}', inline=True)
    embed.add_field(name='Stickers', value=f'{stickers}/{server_info.sticker_limit}', inline=True)
    embed.add_field(name='Static Emojis', value=f'{static_emojis}/{server_info.emoji_limit}', inline=True)
    embed.add_field(name='Animated Emojis', value=f'{animated_emojis}/{server_info.emoji_limit}', inline=True)
    embed.add_field(name='Boost Level', value=f'{boost_tier}', inline=True)
    embed.add_field(name='Boost Count', value=f'{boost_count}', inline=True)
    embed.set_footer(
        text=f'Date Created: {creation_date.strftime("%d-%m-%Y %I:%M:%S %p")} | Age: {age_days} days | ID: {server_info.id}')
    if server_icon:
        embed.set_thumbnail(url=server_icon)

    await ctx.send(embed=embed)


add_help('General', 'si', 'gives you server information')


async def setupmute(ctx, channel: discord.abc.GuildChannel):
    guild = ctx.guild
    bot_top_role = guild.get_member(ctx.bot.user.id).top_role
    mute_role = discord.utils.get(guild.roles, name="Muted")
    if mute_role is None:
        await ctx.send('Creating muted role...')
        permissions = discord.Permissions(send_messages=False, speak=False)
        mute_role = await guild.create_role(name="Muted", permissions=permissions)
        await mute_role.edit(position=bot_top_role.position - 3)
    if mute_role in channel.overwrites and channel.overwrites[mute_role].send_messages is False and channel.overwrites[
        mute_role].speak is False:
        await ctx.send(f'Muted role is already set up for {channel.mention}.')
        return mute_role
    await ctx.send(f'Setting up muted permissions for {channel.mention}...')
    try:
        if isinstance(channel, discord.TextChannel):
            await channel.set_permissions(mute_role, send_messages=False)
        elif isinstance(channel, discord.VoiceChannel):
            await channel.set_permissions(mute_role, speak=False)
    except Exception as e:
        logw(e)

    return mute_role


@has_required_perm()
@bot.command(name='setupmute')
async def setup_mute_command(ctx, channel=None):
    if not channel:
        channel = str(ctx.channel.id)
    if channel == 'all':
        for channel in ctx.guild.channels:
            await setupmute(ctx, channel)
    else:
        channel = ctx.guild.get_channel(int(channel.strip('<#>')))
        await setupmute(ctx, channel)


add_help('Utils', 'setupmute', 'sets up the mute role')


@is_owner()
@bot.command()
async def oauth(ctx):
    client_id = bot.user.id
    await ctx.send(f'https://discord.com/oauth2/authorize?client_id={client_id}&permissions=8&scope=bot')


add_help('Bot Owner', 'oauth', 'gives you the authorization link of the bot')


@has_required_perm()
@bot.command(name='createvote', aliases=['cv'])
async def create_vote(ctx, *options):
    if not options:
        await ctx.send("Please provide options for the vote.")
        return
    if len(options) > 10:
        await ctx.send("You can only provide up to 10 options.")
        return
    vote_message = f"Vote initiated by {ctx.author.mention}:\n"
    for i, option in enumerate(options, 1):
        vote_message += f"{i}. {option}\n"
    vote_message += "\nReact with the corresponding number to vote!"
    vote = await ctx.send(vote_message)
    for i in range(1, len(options) + 1):
        await vote.add_reaction(f"{i}\N{COMBINING ENCLOSING KEYCAP}")


add_help('Utils', 'createvote <options>', 'creates a vote between options')


@has_required_perm()
@bot.command(name="roles")
async def rolelist(ctx, user: discord.Member = None):
    if user is not None:
        roles = user.roles[1:]
        if not roles:
            await ctx.send(f"{user.display_name} has no roles.")
            return
        role_list = "\n - ".join([role.mention for role in reversed(roles)])
        embed = discord.Embed(title=f"**Roles of {user.display_name}**", description=role_list,
                              color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        role_list = ''
        for role in reversed(ctx.guild.roles):
            if role.name != "@everyone":
                role_list += '\n - ' + role.mention
        if role_list == '':
            embed = discord.Embed(title="There are no roles in this server", color=discord.Color.red())
        else:
            embed = discord.Embed(title="**List of all the roles in the server**", description=role_list,
                                  color=discord.Color.green())
        await ctx.send(embed=embed)


add_help('Utils', 'roles [member]', 'lists all roles in server or the roles of a user')


ticket_ids = {}
if not os.path.exists('ticket_numbers.json'):
    with open('ticket_numbers.json', 'w') as f:
        json.dump({}, f)

with open('ticket_numbers.json', 'r') as f:
    ticket_ids = json.load(f)


def save_ticket_data():
    with open('ticket_numbers.json', 'w') as f:
        json.dump(ticket_ids, f)


when_ticket_create_functions = []


def when_ticket_create(function):
    when_ticket_create_functions.append(function)
    return function

async def handle_ticket_creation(interaction, bot, profile=None, data=None):
    guild = interaction.guild
    guild_id = str(guild.id)
    user_id = str(interaction.user.id)
    server_configs = load_server_configs()

    if guild_id not in ticket_ids:
        ticket_ids[guild_id] = {'counter': 1, 'users': {}}
    guild_data = ticket_ids[guild_id]

    # ❌ Prevent duplicate ticket
    if user_id in guild_data['users']:
        channel_id = guild_data['users'][user_id]
        channel = interaction.guild.get_channel(channel_id)
        if channel is None or (channel.category and channel.category.name == "Archived Tickets"):
            del guild_data['users'][user_id]
        else:
            try:
                await interaction.response.send_message("You already have an open ticket.", ephemeral=True)
            except discord.errors.NotFound:
                await interaction.followup.send("You already have an open ticket.", ephemeral=True)
            return

    # ✅ Load default config
    base_config = server_configs.get(guild_id, {}).copy()

    profile_data = None
    # ✅ Overlay profile config if exists
    if profile:
        profile_data = base_config.get("ticket_profiles", {}).get(profile)
        if profile_data is None:
            await interaction.response.send_message(f"⚠️ Ticket profile `{profile}` not found.", ephemeral=True)
            return
        base_config.update(profile_data)

    config = base_config.copy()
    if profile_data:
        config.update(profile_data)

    category_id = int(config.get('ticket_category', 0))
    category = discord.utils.get(guild.categories, id=category_id)
    if not category:
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category(name="Tickets")

    if len(category.channels) >= 50:
        overflow_id = config.get('ticket_overflow_category')
        category = discord.utils.get(guild.categories, id=int(overflow_id)) if overflow_id else None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    try:
        ticket_number = guild_data['counter']
        show_id = config.get("show_ticket_number", True)
        if show_id:
            channel_name = f'ticket-{ticket_number}-{interaction.user.name}'
        else:
            channel_name = f'ticket-{interaction.user.name}'

        channel = await category.create_text_channel(channel_name, overwrites=overwrites) if category else await guild.create_text_channel(channel_name, overwrites=overwrites)

        for f in when_ticket_create_functions:
            if inspect.iscoroutinefunction(f):
                await f(ticket_number, interaction.user, channel)
            else:
                f(ticket_number, interaction.user, channel)

        guild_data['users'][user_id] = channel.id
        guild_data['counter'] += 1
        save_ticket_data()

        ticket_message = f"Ticket opened by <@{interaction.user.id}>. A staff member will assist you shortly."
        embed = None

        if config.get('ticket_message'):
            message = config['ticket_message']
            message, embed_key = check_for_embed(message)
            ticket_message = replace_placeholders(message, interaction.user)

            embed_config = server_configs.get(guild_id, {}).get('embeds', {})
            if embed_key and embed_key in embed_config:
                embed = get_embed(embed_key, interaction.user)

        await channel.send(ticket_message, embed=embed)

        if config.get('ticket_handler'):
            await channel.send(f'<@&{config["ticket_handler"]}>')

        if data:
            embed = discord.Embed(title="Collected Info", color=discord.Color.blue())
            for k, v in data.items():
                embed.add_field(name=k.replace('_', ' ').title(), value=v or "None", inline=False)
            await channel.send(embed=embed)

        confirmation = f"Your ticket has been created at {channel.mention}. A staff member will assist you shortly."
        try:
            await interaction.response.send_message(confirmation, ephemeral=True)
        except discord.errors.NotFound:
            await interaction.followup.send(confirmation, ephemeral=True)

        view = CloseTicketRequestView(bot)
        await channel.send("Click the button below to close this ticket.", view=view)

    except discord.HTTPException as e:
        try:
            await interaction.response.send_message(
                "An error occurred while creating the ticket channel. Please try again later.", ephemeral=True)
        except discord.errors.NotFound:
            await interaction.followup.send(
                "An error occurred while creating the ticket channel. Please try again later.", ephemeral=True)
        loge(f"HTTPException while creating ticket channel: {e}")





def get_oldest_channel(category):
    return min(category.text_channels, key=lambda c: c.created_at, default=None)


async def handle_ticket_close_request(interaction, bot):
    guild_id = str(interaction.guild.id)

    if not interaction.channel.name.startswith('ticket-'):
        await interaction.response.send_message('This command can only be used in a ticket channel.', ephemeral=True)
        return

    if interaction.user.guild_permissions.administrator:
        await handle_ticket_closure(interaction, bot)
        return

    try:
        await interaction.response.send_message(
            "Your request to close the ticket has been sent to moderators.", ephemeral=True)
        view = CloseTicketView(interaction)
        await interaction.channel.send(
            f'{interaction.user.mention} has requested to close this ticket.', view=view)
        await interaction.message.delete()
    except discord.errors.NotFound:
        pass


async def handle_ticket_closure(interaction, bot):
    try:
        guild = interaction.guild
        guild_id = str(interaction.guild.id)
        user_id = None
        for user, channel_id in ticket_ids[guild_id]['users'].items():
            if interaction.channel.id == channel_id:
                user_id = str(user)
                break

        if not interaction.channel.name.startswith('ticket-'):
            await interaction.response.send_message('This command can only be used in a ticket channel.',
                                                    ephemeral=True)
            return

        # Only allow admins to close
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to close the ticket.", ephemeral=True)
            return

        await interaction.response.send_message('Archiving ticket...')
        await interaction.channel.send(f"{interaction.user.mention} has closed this ticket.")
        ticket_ids[guild_id]['users'].pop(user_id, None)
        save_ticket_data()

        config = server_configs.get(guild_id, {}).copy()

        archive_category_id = int(config.get('ticket_archive_category', 0))
        archive_category = discord.utils.get(guild.categories, id=archive_category_id)
        if not archive_category:
            archive_category = discord.utils.get(guild.categories, name="Archived Tickets")
            if not archive_category:
                archive_category = await guild.create_category(name="Archived Tickets")


        if len(archive_category.channels) >= 50:
            oldest_channel = get_oldest_channel(archive_category)
            if oldest_channel:
                await oldest_channel.delete()
                await interaction.channel.send(f"Deleted oldest archived ticket: {oldest_channel.name}")

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        await interaction.channel.edit(category=archive_category, overwrites=overwrites)
        await interaction.channel.send("Ticket archived successfully.")

        transcript_path = await transcribe_ticket(interaction.channel)
        user = interaction.guild.get_member(int(user_id))
        if user and server_configs.get(str(interaction.guild.id), {}).get('send_ticket_transcripts', False):
            try:
                with open(transcript_path, "rb") as file:
                    await user.send("Here is the transcript of your ticket:",
                                    file=discord.File(file, filename=os.path.basename(transcript_path)))
                await interaction.channel.send(f"Transcript has been sent to {user.mention}.")
            except discord.Forbidden:
                await interaction.channel.send(f"Could not DM {user.mention} the transcript. Please enable DMs.")

        if server_configs.get(str(interaction.guild.id), {}).get('ticket_transcripts_channel', None):
            try:
                channel = interaction.guild.get_channel(
                    int(server_configs[str(interaction.guild.id)]['ticket_transcripts_channel']))
                if channel:
                    with open(transcript_path, "rb") as file:
                        await channel.send(f"Transcript for ticket {interaction.channel.name}",
                                           file=discord.File(file, filename=os.path.basename(transcript_path)))
            except Exception as e:
                loge(e)

        view = DeleteTicketView(bot)
        await interaction.channel.send("Click the button below to delete this ticket.", view=view)

    except Exception as e:
        loge(f"Error while closing ticket: {e}")
        try:
            await interaction.followup.send("An error occurred while archiving the ticket. Please try again later.")
        except discord.errors.NotFound:
            pass


async def handle_ticket_deletion(interaction):
    if not interaction.channel.name.startswith('ticket-'):
        try:
            await interaction.response.send_message('This command can only be used in a ticket channel.',
                                                    ephemeral=True)
        except discord.errors.NotFound:
            await interaction.followup.send('This command can only be used in a ticket channel.', ephemeral=True)
        return

    try:
        await interaction.channel.delete()
    except Exception as e:
        logerr(f"Error while deleting ticket: {e}")
        try:
            await interaction.followup.send("An error occurred while deleting the ticket. Please try again later.")
        except discord.errors.NotFound:
            pass


async def transcribe_ticket(channel):
    guild_folder = f'transcripts/{sanitize_filename(channel.guild.name)}'
    if not os.path.exists(guild_folder):
        os.makedirs(guild_folder)

    participants = set()
    messages_data = []

    transcript = [f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcript - #{channel.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #36393f; color: white; padding: 20px; }}
        .message {{ display: flex; align-items: flex-start; margin-bottom: 10px; }}
        .avatar {{ width: 40px; height: 40px; border-radius: 50%; margin-right: 10px; }}
        .content {{ background: #40444b; padding: 10px; border-radius: 8px; max-width: 80%; }}
        .timestamp {{ font-size: 12px; color: #b9bbbe; margin-left: 5px; }}
        .mention {{ color: #7289da; background: rgba(114, 137, 218, 0.1); padding: 2px 4px; border-radius: 4px; }}
        .mention.role {{ color: #faa61a; }}
        .mention.channel {{ color: #44b07b; }}
    </style>
</head>
<body>
    <h2>Transcript for #{channel.name}</h2>
    <p>Channel ID: {channel.id}</p>
    <p>Created at: {channel.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <hr>
    """]

    async for message in channel.history(oldest_first=True):
        timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
        content = format_mentions(message)

        participants.add((message.author.id, message.author.name))
        messages_data.append({
            "author_id": message.author.id,
            "author_name": message.author.name,
            "timestamp": timestamp,
            "content": message.content
        })

        transcript.append(f"""
<div class="message">
    <img class="avatar" src="{avatar_url}" alt="Avatar">
    <div>
        <strong>{message.author.name}</strong> <span class="timestamp">{timestamp}</span>
        <div class="content">{content}</div>
    </div>
</div>
        """)

    # Embed metadata as JSON (invisible but extractable)
    metadata = {
        "channel": {
            "id": channel.id,
            "name": channel.name,
            "created_at": channel.created_at.isoformat()
        },
        "guild": {
            "id": channel.guild.id,
            "name": channel.guild.name
        },
        "participants": [{"id": pid, "name": name} for pid, name in participants],
        "total_messages": len(messages_data)
    }

    transcript.append(f"""
<script type="application/json" id="transcript-metadata">
{json.dumps(metadata, indent=4)}
</script>
    """)

    transcript.append("</body></html>")

    filename = f"{channel.name}-{channel.id}.html"
    file_path = os.path.join(guild_folder, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(transcript))

    return file_path


def format_mentions(message):
    content = message.content
    for user in message.mentions:
        content = content.replace(f"<@{user.id}>", f'<span class="mention">@{user.name}</span>')
    for role in message.role_mentions:
        content = content.replace(f"<@&{role.id}>", f'<span class="mention role">@{role.name}</span>')
    for channel in message.channel_mentions:
        content = content.replace(f"<#{channel.id}>", f'<span class="mention channel">#{channel.name}</span>')
    return content


async def send_close_request(user, ticket_channel):
    close_request_channel = ticket_channel
    if not close_request_channel:
        loge("Close request channel not found.")
        return

    embed = discord.Embed(
        title=f"Close Request from {user.name}#{user.discriminator}",
        description=f"User {user.mention} has requested closure of their ticket in {ticket_channel.mention}.",
        color=discord.Color.blurple()
    )
    await close_request_channel.send(embed=embed)


ticket_commands = bot.create_group(name='ticket')


@ticket_commands.command(name='setup-ticket-system', description='Sets up the ticket system in a specified channel.')
@has_required_perm()
async def setup_ticket_system(
        ctx,
        message: str = None,
        emoji: str = "🎟️",
        button_message: str = "Create Ticket",
        button_color: str = "blue",
        profile: str = None
):
    button_color_map = {
        "blue": discord.ButtonStyle.blurple,
        "red": discord.ButtonStyle.red,
        "green": discord.ButtonStyle.green,
        "grey": discord.ButtonStyle.grey
    }

    channel = ctx.channel
    if message == 'none':
        message = None
    elif message is None:
        message = "Click the button below to create a ticket."

    button_style = button_color_map.get(button_color.lower(), discord.ButtonStyle.primary)

    guild_id = ctx.guild.id if ctx.guild else 0
    view = CreateTicketView(ctx.bot, button_message=button_message, emoji=emoji, button_style=button_style,
                            profile=profile, guild_id=guild_id)

    await channel.send(message, view=view)
    await ctx.respond(content=f'Ticket system setup in {channel.mention}', ephemeral=True)
    logcommand(message=ctx, command="setup-ticket-system")


@ticket_commands.command(name="create-profile", description="Create a new ticket profile for this server.")
@has_required_perm()
async def create_profile(
    ctx,
    profile: str,
    category: discord.CategoryChannel = None,
    handler: discord.Role = None,
    message: str = None,
    overflow: discord.CategoryChannel = None,
    show_id: bool = None
):
    guild_id = str(ctx.guild.id)
    profiles = server_configs.setdefault(guild_id, {}).setdefault("ticket_profiles", {})

    if profile in profiles:
        await ctx.respond(f"⚠️ Profile `{profile}` already exists.", ephemeral=True)
        return

    profile_data = {}
    if category: profile_data["ticket_category"] = category.id
    if overflow: profile_data["ticket_overflow_category"] = overflow.id
    if handler: profile_data["ticket_handler"] = handler.id
    if message: profile_data["ticket_message"] = message
    if show_id != None: profile_data["show_ticket_number"] = show_id

    profiles[profile] = profile_data

    save_server_configs(server_configs)
    await ctx.respond(f"✅ Ticket profile `{profile}` created successfully.", ephemeral=True)


@ticket_commands.command(name="edit-profile", description="Edit an existing ticket profile.")
@has_required_perm()
async def edit_profile(
    ctx,
    profile: str,
    category: discord.CategoryChannel = None,
    handler: discord.Role = None,
    message: str = None,
    overflow: discord.CategoryChannel = None,
    show_id: bool = None
):
    guild_id = str(ctx.guild.id)
    profiles = server_configs.setdefault(guild_id, {}).setdefault("ticket_profiles", {})

    if profile not in profiles:
        await ctx.respond(f"⚠️ Profile `{profile}` does not exist.", ephemeral=True)
        return

    data = profiles[profile]
    if category: data["ticket_category"] = category.id
    if overflow: data["ticket_overflow_category"] = overflow.id
    if handler: data["ticket_handler"] = handler.id
    if message: data["ticket_message"] = message
    if show_id != None: data["show_ticket_number"] = show_id

    profiles[profile] = data
    save_server_configs(server_configs)

    await ctx.respond(f"✅ Ticket profile `{profile}` updated.", ephemeral=True)


@ticket_commands.command(name="delete-profile", description="Delete a ticket profile from this server.")
@has_required_perm()
async def delete_profile(ctx, profile: str):
    guild_id = str(ctx.guild.id)
    profiles = server_configs.setdefault(guild_id, {}).setdefault("ticket_profiles", {})

    if profile not in profiles:
        await ctx.respond(f"⚠️ Profile `{profile}` does not exist.", ephemeral=True)
        return

    del profiles[profile]
    save_server_configs(server_configs)
    await ctx.respond(f"✅ Profile `{profile}` has been deleted.", ephemeral=True)


@ticket_commands.command(name="list-profiles", description="List all ticket profiles for this server.")
@has_required_perm()
async def list_profiles(ctx):
    guild_id = str(ctx.guild.id)
    profiles = server_configs.get(guild_id, {}).get("ticket_profiles", {})

    if not profiles:
        await ctx.respond("⚠️ No ticket profiles found for this server.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎫 Ticket Profiles",
        description=f"List of configured ticket profiles in **{ctx.guild.name}**:",
        color=discord.Color.blurple()
    )

    for name, data in profiles.items():
        category = ctx.guild.get_channel(data.get("ticket_category")) if data.get("ticket_category") else None
        overflow = ctx.guild.get_channel(data.get("ticket_overflow_category")) if data.get("ticket_overflow_category") else None
        handler = ctx.guild.get_role(data.get("ticket_handler")) if data.get("ticket_handler") else None
        message = data.get("ticket_message", "*(No message set)*")
        show_id = data.get("show_ticket_number", True)

        embed.add_field(
            name=f"🔹 {name}",
            value=(
                f"**Category:** {category.mention if category else 'Not set'}\n"
                f"**Overflow:** {overflow.mention if overflow else 'Not set'}\n"
                f"**Handler Role:** {handler.mention if handler else 'Not set'}\n"
                f"**Message:** {message[:150] + '...' if len(message) > 150 else message}"
                f"**Show Ticket Number:** {show_id}\n"
            ),
            inline=False
        )

    await ctx.respond(embed=embed, ephemeral=True)


@ticket_commands.command(name="set-modal-field", description="Add or update a modal input field for a ticket profile.")
@has_required_perm()
async def set_modal_field(
        ctx,
        profile: str,
        label: str,
        required: bool = True,
        placeholder: str = None,
        style: str = "short",
        custom_id: str = None
):
    guild_id = str(ctx.guild.id)
    # Use the global server_configs variable (already loaded in memory)
    global server_configs  # ensure we modify the global variable
    # Get or create server config
    server_config = server_configs.setdefault(guild_id, {})
    profiles = server_config.setdefault("ticket_profiles", {})
    profile_data = profiles.setdefault(profile, {})

    # Ensure the modal field list exists
    modal_fields = profile_data.setdefault("ticket_modal_fields", [])

    # Normalize custom_id
    custom_id = custom_id or label.lower().replace(" ", "_")

    # Update the field if it exists; if not, add it
    for i, field in enumerate(modal_fields):
        if field.get("custom_id") == custom_id:
            modal_fields[i] = {
                "label": label,
                "custom_id": custom_id,
                "placeholder": placeholder,
                "style": style if style in ["short", "paragraph"] else "short",
                "required": required
            }
            break
    else:
        # Add new field
        modal_fields.append({
            "label": label,
            "custom_id": custom_id,
            "placeholder": placeholder,
            "style": style if style in ["short", "paragraph"] else "short",
            "required": required
        })

    # Save the updated global configuration
    save_server_configs(server_configs)
    await ctx.respond(f"✅ Field `{label}` added/updated for profile `{profile}`.", ephemeral=True)


@ticket_commands.command(
    name="delete-modal-field",
    description="Delete a modal input field from a ticket profile."
)
@has_required_perm()
async def delete_modal_field(ctx, profile: str, field_label: str):
    guild_id = str(ctx.guild.id)
    global server_configs  # use the global variable

    profiles = server_configs.get(guild_id, {}).get("ticket_profiles", {})
    profile_data = profiles.get(profile)

    if profile_data is None:
        await ctx.respond(f"⚠️ Profile `{profile}` does not exist.", ephemeral=True)
        return

    modal_fields = profile_data.get("ticket_modal_fields", [])

    # Remove the field with a matching label (case-insensitive)
    updated_fields = [
        f for f in modal_fields
        if f.get("label", "").lower() != field_label.lower()
    ]

    if len(modal_fields) == len(updated_fields):
        await ctx.respond(f"⚠️ No modal field with label `{field_label}` found in profile `{profile}`.", ephemeral=True)
        return

    profile_data["ticket_modal_fields"] = updated_fields

    # Save the updated configuration
    save_server_configs(server_configs)

    remaining = ", ".join(f"`{f['label']}`" for f in updated_fields) or "*No remaining fields*"
    await ctx.respond(
        f"✅ Removed field with label `{field_label}` from profile `{profile}`.\n"
        f"📝 Remaining fields: {remaining}",
        ephemeral=True
    )


@ticket_commands.command(name="list-modal-fields", description="List modal fields for a ticket profile.")
@has_required_perm()
async def list_modal_fields(ctx, profile: str):
    guild_id = str(ctx.guild.id)
    configs = load_server_configs()
    profiles = configs.get(guild_id, {}).get("ticket_profiles", {})
    profile_data = profiles.get(profile, {})

    fields = profile_data.get("ticket_modal_fields", [])
    if not fields:
        await ctx.respond(f"⚠️ No modal fields found in profile `{profile}`.", ephemeral=True)
        return

    content = "\n".join(
        f"- **{f['label']}** (custom_id: `{f['custom_id']}`, style: {f['style']}, required: {f['required']})"
        for f in fields
    )
    await ctx.respond(f"📝 Modal fields for `{profile}`:\n{content}", ephemeral=True)


@ticket_commands.command(name="view-profile", description="View the details of a ticket profile.")
@has_required_perm()
async def view_profile(ctx, profile: str):
    guild_id = str(ctx.guild.id)
    configs = load_server_configs()
    profiles = configs.get(guild_id, {}).get("ticket_profiles", {})
    data = profiles.get(profile)

    if not data:
        await ctx.respond(f"⚠️ Profile `{profile}` not found.", ephemeral=True)
        return

    embed = discord.Embed(title=f"Ticket Profile: {profile}", color=discord.Color.blue())

    for key, value in data.items():
        if key == "ticket_modal_fields":
            field_lines = [
                f"• **{f['label']}** (`{f.get('custom_id')}`)\n"
                f"   Style: `{f.get('style', 'short')}`, Required: `{f.get('required', True)}`\n"
                f"   Placeholder: `{f.get('placeholder', '-')}`"
                for f in value
            ]
            embed.add_field(name="Modal Fields", value="\n".join(field_lines) or "None", inline=False)
        else:
            embed.add_field(name=key.replace("_", " ").title(), value=str(value), inline=False)

    await ctx.respond(embed=embed, ephemeral=True)


@ticket_commands.command(name='set-ticket-handler', description='Sets the role to ping in tickets')
@has_required_perm()
async def setup_ticket_ping(ctx, role: discord.Role):
    server_id = str(ctx.guild.id)
    if not role:
        await ctx.respond("No role selected please select a role", ephemeral=True)
        return
    if server_id not in server_configs:
        server_configs[server_id] = {}
    server_configs[server_id]['ticket_handler'] = role.id
    save_server_configs(server_configs)
    await ctx.respond("Ticket handler defined successfully", ephemeral=True)
    logcommand(message=ctx, command="setup-ticket-handler")


@ticket_commands.command(name='send-ticket-transcripts',
                         description='toggles weather to send ticket transcripts to users or not')
@has_required_perm()
async def setup_ticket_transcript(ctx, arg: bool):
    server_id = str(ctx.guild.id)
    server_configs.setdefault(server_id, {})['send_ticket_transcripts'] = arg
    save_server_configs(server_configs)
    await ctx.respond(f"Sending ticket transcripts to users is now {arg}", ephemeral=True)
    logcommand(message=ctx, command="send-ticket-transcripts")


@ticket_commands.command(name='set-ticket-transcripts-channel',
                         description='toggles weather to send ticket transcripts to users or not')
@has_required_perm()
async def setup_ticket_transcript_channel(ctx, channel: discord.TextChannel):
    server_id = str(ctx.guild.id)
    server_configs.setdefault(server_id, {})['ticket_transcripts_channel'] = channel.id
    save_server_configs(server_configs)
    await ctx.respond(f"Set {channel.mention} as transcripts channel", ephemeral=True)
    logcommand(message=ctx, command="set-ticket-transcripts-channel")


@ticket_commands.command(name='set-ticket-category', description='Sets the category where tickets will be made')
@has_required_perm()
async def setup_ticket_category(ctx, category: discord.CategoryChannel):
    server_id = str(ctx.guild.id)
    server_configs.setdefault(server_id, {})['ticket_category'] = category.id
    save_server_configs(server_configs)
    await ctx.respond(f"Set {category.name} as tickets category", ephemeral=True)
    logcommand(message=ctx, command="set-ticket-category")


@ticket_commands.command(name='set-ticket-archive-category', description='Sets the category where tickets will be archived')
@has_required_perm()
async def setup_ticket_archive_category(ctx, category: discord.CategoryChannel):
    server_id = str(ctx.guild.id)
    server_configs.setdefault(server_id, {})['ticket_archive_category'] = category.id
    save_server_configs(server_configs)
    await ctx.respond(f"Set {category.name} as ticket archive category", ephemeral=True)
    logcommand(message=ctx, command="set-ticket-archive-category")


@ticket_commands.command(name='set-overflow-category',
                         description='Sets the overflow category where tickets will be made if main category is filled')
@has_required_perm()
async def setup_overflow_category(ctx, category: discord.CategoryChannel):
    server_id = str(ctx.guild.id)
    server_configs.setdefault(server_id, {})['ticket_overflow_category'] = category.id
    save_server_configs(server_configs)
    await ctx.respond(f"Set {category.name} as overflow tickets category", ephemeral=True)
    logcommand(message=ctx, command="set-overflow-category")


@ticket_commands.command(name='set-ticket-message', description='Sets the message sent in tickets')
@has_required_perm()
async def setup_ticket_message(ctx, message: str):
    server_id = str(ctx.guild.id)
    if server_id not in server_configs:
        server_configs[server_id] = {}
    server_configs[server_id]['ticket_message'] = message
    save_server_configs(server_configs)
    await ctx.respond("Ticket message defined successfully", ephemeral=True)
    logcommand(message=ctx, command="setup-ticket-message")


@ticket_commands.command(name='send-close-request', description='Send a close request button in the current channel.')
async def send_close_request(ctx):
    view = CloseTicketView(ctx)
    await ctx.channel.send(f"Ticket closure request by {ctx.user.mention}", view=view)
    await ctx.respond("Close request button sent.", ephemeral=True)
    logcommand(message=ctx, command="send-close-request")


@ticket_commands.command(name='add', description='Add a user to the current ticket.')
@has_required_perm()
async def ticket_add(ctx: discord.ApplicationContext, user: discord.Member):
    if not ctx.channel.name.startswith('ticket-'):
        await ctx.respond('This command can only be used in a ticket channel.', ephemeral=True)
        return

    overwrite = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    await ctx.channel.set_permissions(user, overwrite=overwrite)
    await ctx.respond(f"{user.mention} has been added to the ticket.", ephemeral=True)
    await ctx.channel.send(f"{user.mention} has been added to the ticket by an administrator.")
    logcommand(message=ctx, command="ticket add")


@ticket_commands.command(name='remove', description='Add a user to the current ticket.')
@has_required_perm()
async def ticket_remove(ctx: discord.ApplicationContext, user: discord.Member):
    if not ctx.channel.name.startswith('ticket-'):
        await ctx.respond('This command can only be used in a ticket channel.', ephemeral=True)
        return

    overwrite = discord.PermissionOverwrite(read_messages=False, send_messages=False, view_channel=False)
    await ctx.channel.set_permissions(user, overwrite=overwrite)
    await ctx.respond(f"{user.mention} has been removed from the ticket.", ephemeral=True)
    await ctx.channel.send(f"{user.mention} has been removed from the ticket by an administrator.")
    logcommand(message=ctx, command="ticket remove")


@ticket_commands.command(name='delete-all')
@has_required_perm()
async def ticket_force_delete_all(ctx):

    guild = ctx.guild
    archive_category_id = int(server_configs.get(str(guild.id), {}).get('ticket_archive_category', 0))
    archive_category = discord.utils.get(guild.categories, id=archive_category_id)
    if not archive_category:
        archive_category = discord.utils.get(guild.categories, name="Archived Tickets")
        if not archive_category:
            archive_category = await guild.create_category(name="Archived Tickets")

    if not archive_category.channels:
        await ctx.respond('No tickets found!')
        return

    await ctx.respond('Deleting all tickets')

    for channel in archive_category.channels:
        try:
            await channel.delete()
        except discord.errors.HTTPException as e:
            loge(e)
        except Exception as e:
            log(e.args)

    await ctx.respond('Tickets deleted successfully.')


@ticket_commands.command(name='show-ticket-number',
                         description='toggles weather to show ticket number in channel name or not')
@has_required_perm()
async def setup_ticket_number(ctx, arg: bool):
    server_id = str(ctx.guild.id)
    server_configs.setdefault(server_id, {})['show_ticket_number'] = arg
    save_server_configs(server_configs)
    await ctx.respond(f"Now Showing Ticket Numbers" if arg else "Now Hiding Ticket Number", ephemeral=True)
    logcommand(message=ctx, command="show-ticket-number")


afk_file = 'afk_users.json'

if os.path.exists(afk_file):
    with open(afk_file, 'r') as f:
        afk_users = json.load(f)
else:
    afk_users = {}


@bot.command()
async def afk(ctx, *, message="AFK"):
    afk_users[str(ctx.author.id)] = {
        "message": message,
        "time": ttime().isoformat(),
        "mentions": []
    }
    with open(afk_file, 'w') as f:
        json.dump(afk_users, f, indent=4)
    await ctx.send(f"{ctx.author.mention} is now AFK: {message}")


add_help('General', 'afk [reason]', 'Sets you as afk until you send another message')


@bot.command()
@has_required_perm()
async def hide(ctx, role: discord.Role = None):
    try:
        role = role or ctx.guild.default_role  # default to @everyone
        channel = ctx.channel
        await channel.set_permissions(role, view_channel=False)
        confirmation_msg = await ctx.send(f'{ctx.author.mention}, {channel.mention} has been hidden for {role.mention}.')
        await confirmation_msg.delete(delay=5)
    except discord.Forbidden:
        await ctx.send("I don't have permission to modify channel permissions.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"Failed to hide the channel: {e}", delete_after=5)

add_help('Utils', 'hide [role]', 'Hides the channel for the specified role (defaults to @everyone).')


@bot.command()
@has_required_perm()
async def unhide(ctx, role: discord.Role = None):
    try:
        role = role or ctx.guild.default_role  # default to @everyone
        channel = ctx.channel
        await channel.set_permissions(role, view_channel=True)
        confirmation_msg = await ctx.send(f'{ctx.author.mention}, {channel.mention} has been unhidden for {role.mention}.')
        await confirmation_msg.delete(delay=5)
    except discord.Forbidden:
        await ctx.send("I don't have permission to modify channel permissions.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"Failed to unhide the channel: {e}", delete_after=5)

add_help('Utils', 'unhide [role]', 'Unhides the channel for the specified role (defaults to @everyone).')



@bot.command(name='ch')
@has_required_perm()
async def manage_channel(ctx, action: str, *args):
    if action in ['create', 'vcreate']:
        if len(args) < 1:
            await ctx.send(
                f"Usage: {bot_prefix}ch:{action}:<channel_name>[:<channel_category>][:<force_create_category>]")
            return

        channel_name = args[0]
        channel_category = args[1] if len(args) > 1 else None
        force_create_category = len(args) > 2

        if channel_category:
            category = discord.utils.get(ctx.guild.categories, name=channel_category)

            if category and not force_create_category:
                if action == 'create':
                    await ctx.guild.create_text_channel(channel_name, category=category)
                elif action == 'vcreate':
                    await ctx.guild.create_voice_channel(channel_name, category=category)
                await ctx.send(f'Channel {channel_name} created in existing category {channel_category}.')
            else:
                if category is None or force_create_category:
                    category = await ctx.guild.create_category(channel_category)
                    await ctx.send(f'New category {channel_category} created.')

                if action == 'create':
                    await ctx.guild.create_text_channel(channel_name, category=category)
                elif action == 'vcreate':
                    await ctx.guild.create_voice_channel(channel_name, category=category)
                await ctx.send(f'Channel {channel_name} created in category {channel_category}.')
        else:
            if action == 'create':
                await ctx.guild.create_text_channel(channel_name)
            elif action == 'vcreate':
                await ctx.guild.create_voice_channel(channel_name)
            await ctx.send(f'Channel {channel_name} created without a category.')

    elif action == 'rename':
        if len(args) != 1:
            await ctx.send("Usage: !ch:rename:<new_name>")
            return

        new_name = args[0]
        channel = ctx.channel

        await channel.edit(name=new_name)
        await ctx.send(f'Channel renamed to {new_name}.')

    elif action == 'delete':

        channel = ctx.channel

        await channel.delete()

    elif action == 'deleteall':

        for channel in ctx.guild.channels:
            try:
                await channel.delete()
            except Exception as e:
                logw(e)

    else:
        await ctx.send("Unknown action. Use 'create', 'vcreate', 'rename', 'delete', or 'deleteall'.")


add_help('Utils', 'ch <action>', "Channel actions: 'create', 'vcreate', 'rename', 'delete' or 'deleteall'.")


@bot.command(name='cat')
@has_required_perm()
async def manage_category(ctx, action: str, *args):
    if action == 'create':
        if len(args) < 1:
            await ctx.send(f"Usage: {bot_prefix}cat:create:<category_name>")
            return

        category_name = args[0]
        existing = discord.utils.get(ctx.guild.categories, name=category_name)
        if existing:
            await ctx.send(f"⚠️ Category `{category_name}` already exists.")
            return

        await ctx.guild.create_category(category_name)
        await ctx.send(f"✅ Category `{category_name}` created successfully.")

    elif action == 'rename':
        if len(args) != 1:
            await ctx.send(f"Usage: {bot_prefix}cat:rename:<new_name>")
            return

        new_name = args[0]
        category = ctx.channel.category
        if not category:
            await ctx.send("⚠️ This command must be used inside a channel within a category.")
            return

        await category.edit(name=new_name)
        await ctx.send(f"✅ Category renamed to `{new_name}`.")

    elif action == 'delete':
        category = ctx.channel.category
        if not category:
            await ctx.send("⚠️ This command must be used inside a channel within a category.")
            return

        await category.delete()
        await ctx.send(f"🗑️ Category `{category.name}` has been deleted.")

    elif action == 'deleteall':
        deleted = 0
        for category in ctx.guild.categories:
            try:
                await category.delete()
                deleted += 1
            except Exception as e:
                logw(e)

        await ctx.send(f"🧹 Deleted {deleted} categories.")

    else:
        await ctx.send("❓ Unknown action. Use `create`, `rename`, `delete`, or `deleteall`.")



add_help('Utils', 'cat <action>', "Catrgory actions: 'create', 'rename', 'delete' or 'deleteall'.")


translator = Translator()


@bot.command(name='trans')
async def translate(ctx, *, text: str = None):
    dest = 'en'
    if ctx.author.id in user_language_settings:
        target_lang = user_language_settings[ctx.author.id]
        if target_lang != 'none':
            dest = target_lang
    if text:
        try:
            translated = await translator.translate(text, dest=dest)
            if translated and translated.text:
                await ctx.send(translated.text)
            else:
                await ctx.send('Translation failed. Please try again.')
        except Exception as e:
            await ctx.send(f'Error: {str(e)}')
    elif ctx.message.reference:
        try:
            referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            text_to_translate = referenced_message.content
            translated = await translator.translate(text_to_translate, dest=dest)
            if translated and translated.text:
                await ctx.send(f'Translated: {translated.text}')
            else:
                await ctx.send('Translation failed. Please try again.')
        except Exception as e:
            await ctx.send(f'Error: {str(e)}')
    else:
        await ctx.send(f'Please provide text to translate or reply to a message with `{bot.command_prefix}trans`.')


add_help('General', 'trans [text]', 'translates given text or reference message')

user_language_settings = {}


@bot.command(name='translang')
async def set_translation_language(ctx: discord.ApplicationContext, language: str = None, user: discord.User = None):
    userid = user.id if user else ctx.author.id
    if language.lower() in ['none', 'off', 'null']:
        if userid in user_language_settings:
            del user_language_settings[userid]
        await ctx.send("Default translation language disabled.")
    else:
        language_code = language.lower()
        if language_code in SUPPORTED_LANGUAGES:
            user_language_settings[userid] = language_code
            await ctx.send(
                f"Default translation language set to '{SUPPORTED_LANGUAGES[language_code]}' for user <@{userid}>")
        else:
            await ctx.send(f"Invalid language. Please choose from supported languages or 'none'.")


add_help('General', 'translang <language code/off> [user]',
         'Enables automatic translation and to a language for yourself or a user')


@bot.command(name='supported_languages', aliases=['langs', 'languages', 'translangs'])
async def show_supported_languages(ctx):
    languages_list = "\n".join([f"`{lang_code}` - {lang_name}" for lang_code, lang_name in SUPPORTED_LANGUAGES.items()])
    await ctx.send(f"Supported Languages:\n{languages_list}")


add_help('General', 'languages', 'lists all available languages for translation and their language code')


@is_owner()
@bot.command()
async def update(ctx):
    url = api + "/get_release"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(__file__, 'w', encoding='utf-8') as script_file:
                script_file.write(response.text)
            await ctx.send("Update successful! Please restart the bot...")
        else:
            await ctx.send(f"Failed to update. Status code: {response.status_code}")
    except Exception as e:
        await ctx.send(f"Failed to update. Error: {e}")


add_help('Bot Owner', 'update', 'Updates the bot to the latest version')

if '-dev-' in current_version:
    @is_owner()
    @bot.command()
    async def pullupdate(ctx):
        url = api + "/get_updated_script"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(__file__, 'w', encoding='utf-8') as script_file:
                    script_file.write(response.text)
                await ctx.send("Update successful! Please restart the bot...")
            else:
                await ctx.send(f"Failed to update. Status code: {response.status_code}")
        except Exception as e:
            await ctx.send(f"Failed to update. Error: {e}")


    add_help('DEV', 'pullupdate', 'pulls the latest development version of the bot')

    if bot_config['plugins']:
        @is_owner()
        @bot.command()
        async def getplugin(ctx: discord.ApplicationContext, plugin: str = ''):
            url = api + f"/get_plugin/{plugin}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(f'plugins/{plugin}.py', 'w', encoding='utf-8') as script_file:
                        script_file.write(response.text)
                    await ctx.send("Plugin downloaded, please restart bot")
                else:
                    await ctx.send(f"Failed to download plugin. Status code: {response.status_code}")
            except Exception as e:
                await ctx.send(f"Failed to download. Error: {e}")


        add_help('DEV', 'getplugin <plugin>', 'downloads a plugin from the official in progress plugins list')

if bot_config['plugins']:

    def paginate_list_plugins(title, items, per_page=10):
        pages = []
        for i in range(0, len(items), per_page):
            chunk = items[i:i + per_page]
            embed = discord.Embed(
                title=title,
                color=discord.Color.blurple()
            )

            embed.description = "\n".join(
                f"- **{index + 1}.** **{item}**"
                for index, item in enumerate(chunk, start=i)
            )
            embed.set_footer(text=f"Page {i // per_page + 1} • Total Plugins: {len(items)}")
            pages.append(embed)
        return pages


    @is_owner()
    @bot.command(name='downloadplugin')
    async def download_plugin(ctx, plugin_name: str = None):
        if plugin_name:
            url = f"{api}/get_plugin_release/{current_version}/{plugin_name}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(f'plugins/{plugin_name}.py', 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    await ctx.send(embed=discord.Embed(
                        title="✅ Plugin Downloaded",
                        description=f"Plugin `{plugin_name}` downloaded. Please restart the bot.",
                        color=discord.Color.green()
                    ))
                else:
                    await ctx.send(f"Failed to download plugin. Status code: {response.status_code}")
            except Exception as e:
                await ctx.send(f"Failed to download. Error: {e}")
        else:
            plugin_list = requests.get(f'{api}/get_plugins_list/{current_version}').json()
            embeds = paginate_list_plugins("Available Plugins", [p[:-3] for p in plugin_list])
            if embeds:
                await pages.Paginator(pages=embeds).send(ctx)
            else:
                await ctx.send("No plugins available.")


    add_help('Bot Owner', 'downloadplugin [plugin]', 'Downloads or lists available plugins.')


    @is_owner()
    @bot.command(name='rmplugin')
    async def rmplugin(ctx, plugin: str):
        plugin_path = f'plugins/{plugin}.py'
        if not os.path.exists(plugin_path):
            return await ctx.send(f"❌ Plugin `{plugin}` not found.")
        try:
            os.remove(plugin_path)
            await ctx.send(embed=discord.Embed(
                title="🗑️ Plugin Removed",
                description=f"Plugin `{plugin}` removed successfully. Please restart the bot.",
                color=discord.Color.red()
            ))
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


    add_help('Bot Owner', 'rmplugin <plugin>', 'Removes a plugin.')


    @is_owner()
    @bot.command(name='disableplugin')
    async def disable_plugin(ctx, plugin_name):
        path = os.path.join('plugins', f'{plugin_name}.py')
        if not os.path.exists(path):
            return await ctx.send(f"❌ Plugin `{plugin_name}` not found or already disabled.")
        try:
            os.rename(path, path + ".disabled")
            await ctx.send(embed=discord.Embed(
                title="🛑 Plugin Disabled",
                description=f"Plugin `{plugin_name}` has been disabled. Please restart the bot.",
                color=discord.Color.orange()
            ))
        except Exception as e:
            await ctx.send(f"Error: {e}")


    add_help('Bot Owner', 'disableplugin <plugin>', 'Disables a plugin.')


    @is_owner()
    @bot.command(name='enableplugin')
    async def enable_plugin(ctx, plugin_name):
        path = os.path.join('plugins', f'{plugin_name}.py.disabled')
        if not os.path.exists(path):
            return await ctx.send(f"❌ Plugin `{plugin_name}` not found or already enabled.")
        try:
            os.rename(path, path.replace(".disabled", ""))
            await ctx.send(embed=discord.Embed(
                title="✅ Plugin Enabled",
                description=f"Plugin `{plugin_name}` has been enabled. Please restart the bot.",
                color=discord.Color.green()
            ))
        except Exception as e:
            await ctx.send(f"Error: {e}")


    add_help('Bot Owner', 'enableplugin <plugin>', 'Enables a previously disabled plugin.')


    @is_owner()
    @bot.command(name='plugins')
    async def plugin_list(ctx, filter: str = 'enabled'):
        if not bot_config.get("plugins", False):
            return await ctx.send("⚠️ Plugin system is disabled.")

        all_plugins = os.listdir('plugins')
        enabled = [p[:-3] for p in all_plugins if p.endswith('.py')]
        disabled = [p[:-3].replace('.py', '') for p in all_plugins if p.endswith('.py.disabled')]

        if filter == 'enabled':
            result = enabled
            title = "✅ Enabled Plugins"
        elif filter == 'disabled':
            result = disabled
            title = "🛑 Disabled Plugins"
        elif filter == 'all':
            result = [f"{p} (enabled)" for p in enabled] + [f"{p} (disabled)" for p in disabled]
            title = "📦 All Plugins"
        else:
            return await ctx.send("Invalid filter. Use `enabled`, `disabled`, or `all`.")

        embeds = paginate_list_plugins(title, result)
        if embeds:
            await pages.Paginator(pages=embeds).send(ctx)
        else:
            await ctx.send("No plugins found.")


    add_help('Bot Owner', 'plugins [enabled|disabled|all]', 'Shows plugins with optional filter.')

@bot.command(name='autoroleadd')
@has_required_perm()
async def autoroleadd(ctx, role: discord.Role):
    guild_id = str(ctx.guild.id)
    if guild_id not in server_roles:
        server_roles[guild_id] = []
    if role.id not in server_roles[guild_id]:
        server_roles[guild_id].append(role.id)
        save_roles()
        await ctx.send(f'Role {role.mention} added to auto-roles for this server.')
    else:
        await ctx.send(f'Role {role.mention} is already in the auto-roles list.')


add_help('Utils', 'autoroleadd <role>', 'adds a role to auto role list')


@bot.command(name='autoroleremove')
@has_required_perm()
async def autoroleremove(ctx, role: discord.Role):
    guild_id = str(ctx.guild.id)
    if guild_id in server_roles and role.id in server_roles[guild_id]:
        server_roles[guild_id].remove(role.id)
        save_roles()
        await ctx.send(f'Role {role.mention} removed from auto-roles for this server.')
    else:
        await ctx.send(f'Role {role.mention} is not in the auto-roles list.')


add_help('Utils', 'autoroleremove <role>', 'removes a role from the auto role list')


@bot.command(name='autoroles')
@has_required_perm()
async def autoroles(ctx):
    guild_id = str(ctx.guild.id)
    if guild_id in server_roles and server_roles[guild_id]:
        roles_list = []
        for role_id in server_roles[guild_id]:
            role_object: discord.Role = get(ctx.guild.roles, id=role_id)
            if role_object:
                roles_list.append(role_object.name)
            else:
                server_roles[guild_id].remove(role_id)
                roles_list.append(f"`Role ID {role_id} (deleted)`")

        roles_display = "\n".join(roles_list)
        await ctx.send(f"Auto-roles for this server:\n{roles_display}")
    else:
        await ctx.send("There are no auto-roles configured for this server.")


add_help('Utils', 'autoroles', 'lists all the autoroles for the server ')


@bot.command('buttons')
@has_required_perm()
async def buttons_(ctx, *, arg: str):
    arg = arg.split(' ')
    if arg[0] == 'list':
        msg = '# Registered Buttons are:-\n'
        for item in button_configurations:
            button = item['custom_id']
            msg += f'{button}\n'
        await ctx.send(msg)
    elif arg[0] == 'send':
        if arg[1] in button_views:
            await ctx.send(view=button_views[arg[1]])
        else:
            await ctx.send('Given button not registered')
    elif arg[0] == 'combine' and arg[1] == 'send':
        buttons_to_combine = arg[2:]
        combined_view = View()
        for button_id in buttons_to_combine:
            if button_id in button_views:
                for child in button_views[button_id].children:
                    if isinstance(child, Button):
                        combined_view.add_item(child)
            else:
                await ctx.send(f'Button with id {button_id} not registered')
                return
        await ctx.send(view=combined_view)
    elif arg[0] == 'create':
        label = arg[1]
        if arg[2] == 'red':
            style = discord.ButtonStyle.red
        elif arg[2] == 'blue':
            style = discord.ButtonStyle.blurple
        elif arg[2] == 'green':
            style = discord.ButtonStyle.green
        elif arg[2] == 'gray':
            style = discord.ButtonStyle.gray
        custom_id = arg[3]
        callback = default_callback
        emoji = arg[4]
        view = create_button_view(label, style, custom_id, callback, emoji)
        await ctx.send(view=view)
    else:
        await ctx.send('Invalid command or arguments')


DATA_FILE = 'guild_vcs_data.json'
PERSONAL_VC_FILE = 'personal_vcs_data.json'

guild_vcs = {}
personal_vcs = {}

def load_vc_data():
    global guild_vcs
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            guild_vcs = json.load(f)
    else:
        guild_vcs = {}

def save_vc_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(guild_vcs, f, indent=4)

def load_personal_vcs():
    global personal_vcs
    if os.path.exists(PERSONAL_VC_FILE):
        with open(PERSONAL_VC_FILE, 'r') as f:
            raw = json.load(f)
            for user_id, (guild_id, channel_id) in raw.items():
                guild = bot.get_guild(int(guild_id))
                if guild:
                    channel = guild.get_channel(int(channel_id))
                    if channel:
                        personal_vcs[int(user_id)] = channel
    else:
        personal_vcs = {}

def save_personal_vcs():
    data = {
        str(user_id): [str(vc.guild.id), str(vc.id)]
        for user_id, vc in personal_vcs.items()
        if vc and vc.guild
    }
    with open(PERSONAL_VC_FILE, 'w') as f:
        json.dump(data, f, indent=4)


@bot.command(name="setupvc")
@has_required_perm()
async def setupvc(ctx, user_limit: int = 0, channel_id: int = None):
    guild_id = str(ctx.guild.id)

    if channel_id:
        join_to_create_channel = ctx.guild.get_channel(channel_id)
        if not join_to_create_channel or not isinstance(join_to_create_channel, discord.VoiceChannel):
            return await ctx.send("❌ Invalid channel ID or the channel is not a voice channel.")
    else:
        join_to_create_channel = await ctx.guild.create_voice_channel('Join to Create VC')

    if guild_id not in guild_vcs:
        guild_vcs[guild_id] = {}

    guild_vcs[guild_id][str(join_to_create_channel.id)] = {"user_limit": user_limit}
    save_vc_data()

    await ctx.send(
        f"'Join to Create VC' is set: {join_to_create_channel.mention}. "
        f"Private VCs will have a user limit of {user_limit if user_limit > 0 else 'unlimited'}.")

add_help('Utils', 'setupvc [limit] [channel_id]', 'Join-to-create VC setup with optional user limit and channel ID')


@has_required_perm()
@bot.command('join')
async def join_vc(ctx: discord.ApplicationContext, vc: discord.VoiceChannel = None):
    if not vc:
        user = ctx.author
        if user.voice and user.voice.channel:
            await user.voice.channel.connect()
        else:
            await ctx.send('You are not connected to a voice channel!')
    else:
        try:
            await vc.connect()
        except Exception as e:
            await ctx.send(f'An error occurred: {e}')


add_help('Utils', 'join', 'makes the bot join vc')


@has_required_perm()
@bot.command('discon')
async def disconnect_vc(ctx: discord.ApplicationContext, user: discord.Member = None):
    if not user:
        client = ctx.guild.voice_client
        if client:
            await client.disconnect()
    elif user.voice:
        channel = user.voice.channel.name
        await user.move_to(None)
        await ctx.send(f' disconnected {user.display_name} from {channel}')
    else:
        await ctx.send(f'{user.display_name} is not connected to a voice channel')


add_help('Utils', 'discon [user]', 'disconnects the bot if it has joined the vc or a user')


@has_required_perm()
@bot.group()
async def embed(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"Invalid embed command, use the embed help command to view embed")


add_help('Utils', 'embed [help]', 'To show embed help menu')


@has_required_perm()
@embed.command(name='create', aliases=['mk'])
async def create_embed(ctx, name: str = None, *, content: str = None):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    if not name:
        return await ctx.send('Please provide a name')
    if name in embeds:
        await ctx.send(f"An embed with the name `{name}` already exists. Use `/embed edit` to modify it.")
        return

    if not content:
        content = f'This embed was created by {ctx.author.mention}'

    embed_dict = {
        "title": "",
        "description": content,
        "color": 0,
        "fields": [],
        "footer": "",
        "image": "",
        "thumbnail": ""
    }
    server_configs.setdefault(str(ctx.guild.id), {}).setdefault('embeds', {})[name] = embed_dict
    save_server_configs(server_configs)
    embed = get_embed(name, ctx.author)
    await ctx.send(f"Embed `{name}` has been created.", embed=embed)


@has_required_perm()
@embed.command(name='edit')
async def edit_embed(ctx, name: str = None, field: str = None, *, value: str = None):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    if not name or not field or not value:
        return await ctx.send("Please provide name field and value")

    if name not in embeds:
        await ctx.send(f"No embed found with the name `{name}`. Use `.embed create` to create it first.")
        return

    if field not in ["title", "description", "footer"]:
        await ctx.send("You can only edit `title`, `description`, or `footer` with this command.")
        return

    server_configs.setdefault(str(ctx.guild.id), {}).setdefault('embeds', {})[name][field] = value
    save_server_configs(server_configs)
    embed = get_embed(name, ctx.author)
    await ctx.send(f"Embed `{name}` has been updated: {field} set to `{value}`.", embed=embed)


@has_required_perm()
@embed.command(name='addfield')
async def add_field(ctx, name: str, title: str, value: str, inline: bool = False):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    if name not in embeds:
        await ctx.send(f"No embed found with the name `{name}`.")
        return

    server_configs.setdefault(str(ctx.guild.id), {}).setdefault('embeds', {})[name]["fields"].append(
        {"name": title, "value": value, "inline": inline})
    save_server_configs(server_configs)
    embed = get_embed(name, ctx.author)
    await ctx.send(f"Field added to embed `{name}`.", embed=embed)


@has_required_perm()
@embed.command(name='delfield')
async def delete_field(ctx, name: str, index: int):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    if name not in embeds:
        await ctx.send(f"No embed found with the name `{name}`.")
        return

    try:
        server_configs.setdefault(str(ctx.guild.id), {}).setdefault('embeds', {})[name]["fields"].pop(index)
        save_server_configs(server_configs)
        embed = get_embed(name, ctx.author)
        await ctx.send(f"Field `{embeds['name']}` has been removed from embed `{name}`.", embed=embed)
    except IndexError:
        await ctx.send("Invalid field index. Please check the embed and try again.")


@has_required_perm()
@embed.command(name='editfield')
async def edit_field(ctx, name: str, index: int, field_type: str, *, content: str):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    index += 1
    if name not in embeds:
        await ctx.send(f"No embed found with the name `{name}`.")
        return
    try:
        field = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})[name]["fields"][index]
        if field_type.lower() == "title":
            field["name"] = content
        elif field_type.lower() == "description":
            field["value"] = content
        elif field_type.lower() == "inline":
            if content.lower() in ["true", "false"]:
                field["inline"] = content.lower() == "true"
                await ctx.send(
                    f"Field at index `{index}` in embed `{name}` has been updated with inline set to `{field['inline']}`.")
                return
        else:
            await ctx.send("Invalid field type. Please choose either 'title', 'description', or 'inline'.")
            return
        save_server_configs(server_configs)
        embed = get_embed(name, ctx.author)
        await ctx.send(f"Field at index `{index}` in embed `{name}` has been updated (field type: `{field_type}`).",
                       embed=embed)
    except IndexError:
        await ctx.send("Invalid field index. Please check the embed and try again.")


@has_required_perm()
@embed.command(name='setcolor')
async def set_color_embed(ctx, name: str, color: str):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    if name not in embeds:
        await ctx.send(f"No embed found with the name `{name}`.")
        return

    try:
        if color.startswith("#"):
            color = color[1:]
        server_configs.setdefault(str(ctx.guild.id), {}).setdefault('embeds', {})[name]["color"] = int(color, 16)
        save_server_configs(server_configs)
        embed = get_embed(name, ctx.author)
        await ctx.send(f"Color updated for embed `{name}`.", embed=embed)
    except ValueError:
        await ctx.send("Invalid color code. Please provide a valid hexadecimal color (e.g., #3498db).")


@has_required_perm()
@embed.command(name='setimage')
async def set_image_embed(ctx, name: str, image: str = ""):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    if name not in embeds:
        await ctx.send(f"No embed found with the name `{name}`.")
        return

    try:
        if image in ['none', 'null']:
            image = ""
        server_configs.setdefault(str(ctx.guild.id), {}).setdefault('embeds', {})[name]["image"] = image
        save_server_configs(server_configs)
        embed = get_embed(name, ctx.author)
        await ctx.send(f"Image updated for embed `{name}`.", embed=embed)
    except ValueError:
        await ctx.send("Invalid color code. Please provide a valid hexadecimal color (e.g., #3498db).")


@has_required_perm()
@embed.command(name='setthumbnail')
async def set_thumbnail_embed(ctx, name: str, thumbnail: str = ""):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    if name not in embeds:
        await ctx.send(f"No embed found with the name `{name}`.")
        return

    try:
        if thumbnail in ['none', 'null']:
            thumbnail = ""
        server_configs.setdefault(str(ctx.guild.id), {}).setdefault('embeds', {})[name]["thumbnail"] = thumbnail
        save_server_configs(server_configs)
        embed = get_embed(name, ctx.author)
        await ctx.send(f"Thmbnail updated for embed `{name}`.", embed=embed)
    except ValueError:
        await ctx.send("Invalid color code. Please provide a valid hexadecimal color (e.g., #3498db).")


@has_required_perm()
@embed.command(name='delete', aliases=['del'])
async def delete_embed(ctx, name: str):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    if name not in embeds:
        await ctx.send(f"No embed found with the name `{name}`.")
        return

    del server_configs.setdefault(str(ctx.guild.id), {}).setdefault('embeds', {})[name]
    save_server_configs(server_configs)
    await ctx.send(f"Embed `{name}` has been deleted.")


@has_required_perm()
@embed.command(name='send')
async def send_embed(ctx, *, name: str):
    embed = get_embed(name, ctx.author)
    target_channel = ctx.channel
    await target_channel.send(embed=embed)


@has_required_perm()
@embed.command(name='list')
async def list_embeds(ctx):
    embeds = server_configs.get(str(ctx.guild.id), {}).get('embeds', {})
    try:
        embed_list = ', '.join(embeds) if embeds else "No embeds available."

        await ctx.send(f"Here are the available embeds:\n{embed_list}")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@has_required_perm()
@embed.command(name='export')
async def export_embed(ctx, name):
    guild_id = str(ctx.guild.id)
    embeds = server_configs.get(guild_id, {}).get('embeds', {})

    if name in embeds:
        embed_data = json.dumps(embeds[name], indent=4)
        if len(embed_data) > 2000:
            buffer = BytesIO(embed_data.encode())
            buffer.seek(0)
            await ctx.send(file=File(buffer, filename=f"{name}.json"))
        else:
            await ctx.send(f"```json\n{embed_data}```")
    else:
        await ctx.send('Embed not found ❌')


@has_required_perm()
@embed.command(name='import')
async def import_embed(ctx, name, *, embed_json=None):
    global server_configs
    guild_id = str(ctx.guild.id)

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith('.json'):
            try:
                file_data = await attachment.read()
                embed_obj = json.loads(file_data.decode())
            except Exception as e:
                return await ctx.send(f'Failed to parse attached JSON file ❌\n`{e}`')
        else:
            return await ctx.send('Only `.json` files are supported as attachments ❌')
    elif embed_json:
        try:
            embed_obj = json.loads(embed_json)
        except Exception as e:
            return await ctx.send(f'Failed to parse JSON string ❌\n`{e}`')
    else:
        return await ctx.send('No embed data provided ❌')

    try:
        server_configs.setdefault(guild_id, {}).setdefault('embeds', {})[name] = embed_obj
        save_server_configs(server_configs)
        await ctx.send('Embed imported successfully! ✅')
    except Exception as e:
        await ctx.send(f'An Unexpected Error Occurred ❌\n`{e}`')


@has_required_perm()
@embed.command(name='help')
async def embed_help(ctx):
    help_embed = discord.Embed(
        title="📘 Embed Command Help",
        description="Here are the available embed subcommands:",
        color=0x3498db
    )

    help_embed.add_field(
        name=f"`{bot.command_prefix}embed create <name> [content]`",
        value="Create a new embed with optional content.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed edit <name> <field> <value>`",
        value="Edit the `title`, `description`, or `footer` of an embed.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed addfield <name> <title> <value> [inline]`",
        value="Add a field to an embed.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed delfield <name> <index>`",
        value="Delete a field at the given index from an embed.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed editfield <name> <index> <title|description|inline> <content>`",
        value="Edit a specific field in an embed.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed setcolor <name> <hex>`",
        value="Set the color of an embed (e.g., `#3498db`).",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed setimage <name> <url|none>`",
        value="Set or remove the image of an embed.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed setthumbnail <name> <url|none>`",
        value="Set or remove the thumbnail of an embed.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed delete <name>`",
        value="Delete an existing embed.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed send <name>`",
        value="Send an embed in the current channel.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed list`",
        value="List all stored embed names.",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed export <name>`",
        value="Export an embed as JSON (inline or file if too long).",
        inline=False
    )
    help_embed.add_field(
        name=f"`{bot.command_prefix}embed import <name> [json or .json file]`",
        value="Import an embed from a JSON string or attached `.json` file.",
        inline=False
    )

    help_embed.set_footer(text=f"Use {bot.command_prefix}embed <subcommand> for managing embeds.")

    await ctx.send(embed=help_embed)


@has_required_perm()
@bot.command(name='setwelcomechannel')
async def def_welcome_channel(ctx, channel: discord.TextChannel = None):
    global server_configs
    server_id = str(ctx.guild.id)
    if server_id not in server_configs:
        server_configs[server_id] = {}
    server_configs[server_id]['welcome_channel_id'] = channel.id if channel else ctx.channel.id
    save_server_configs(server_configs)
    await ctx.channel.send('Welcome channel defined successfully')


add_help('Utils', 'setwelcomechannel <channel>', 'defines the welcome message channel of a server')


@has_required_perm()
@bot.command(name='rmwelcomechannel')
async def rm_welcome_channel(ctx):
    server_id = str(ctx.guild.id)

    if server_id not in server_configs:
        server_configs[server_id] = {}

    if 'welcome_channel_id' not in server_configs[server_id]:
        await ctx.send('No welcome channel defined')
        return
    server_configs[server_id].pop('welcome_channel_id')
    save_server_configs(server_configs)
    await ctx.send('Welcome channel removed successfully')


add_help('Utils', 'rmwelcomechannel', 'removes the defined welcome message channel')


@has_required_perm()
@bot.command(name='setwelcomemessage')
async def def_welcome_embed(ctx, *, message: str = None):
    server_id = str(ctx.guild.id)
    if server_id not in server_configs:
        server_configs[server_id] = {}

    server_configs[str(ctx.guild.id)]['welcome_message'] = message
    save_server_configs(server_configs)

    await ctx.channel.send('Welcome embed defined successfully')


add_help('Utils', 'setwelcomemessage <message>', 'sets the welcome message for the server')


@has_required_perm()
@bot.command(name='setleavechannel')
async def def_leave_channel(ctx, channel: discord.TextChannel = None):
    global server_configs
    server_id = str(ctx.guild.id)
    if server_id not in server_configs:
        server_configs[server_id] = {}
    server_configs[server_id]['leave_channel_id'] = channel.id if channel else ctx.channel.id
    save_server_configs(server_configs)
    await ctx.channel.send('Leave channel defined successfully')


add_help('Utils', 'setleavechannel <channel>', 'defines the leave message channel of a server')


@has_required_perm()
@bot.command(name='rmleavechannel')
async def rm_leave_channel(ctx):
    server_id = str(ctx.guild.id)

    if server_id not in server_configs:
        server_configs[server_id] = {}

    if 'leave_channel_id' not in server_configs[server_id]:
        await ctx.send('No Leave channel defined')
        return
    server_configs[server_id].pop('leave_channel_id')
    save_server_configs(server_configs)
    await ctx.send('Leave channel removed successfully')


add_help('Utils', 'rmleavechannel', 'removes the defined leave message channel')


@has_required_perm()
@bot.command(name='setleavemessage')
async def def_leave_embed(ctx, *, message: str = None):
    server_id = str(ctx.guild.id)
    if server_id not in server_configs:
        server_configs[server_id] = {}

    server_configs[str(ctx.guild.id)]['leave_message'] = message
    save_server_configs(server_configs)

    await ctx.channel.send('Leave embed defined successfully')


add_help('Utils', 'setleavemessage <message>', 'sets the leave message for the server')


@has_required_perm()
@bot.command(name='setmembercountchannel')
async def def_member_count_channel(ctx, channel: discord.abc.GuildChannel = None):
    server_id = str(ctx.guild.id)
    if server_id not in server_configs:
        server_configs[server_id] = {}
    if not channel:
        channel = ctx.channel

    server_configs[str(ctx.guild.id)]['member_count_channel'] = int(channel.id) if channel else None
    save_server_configs(server_configs)

    await ctx.channel.send('Member Count Channel defined successfully')


add_help('Utils', 'setmembercountchannel <channel>', 'removes the defined welcome message channel')


@bot.group()
async def antinuke(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Please use antinuke help command to see available commands')


add_help('Moderation', 'antinuke [help]', 'To see antinuke options')


@antinuke.command(name='enable')
async def enable_antinuke(ctx):
    if not is_trusted(ctx.guild, ctx.author):
        return await ctx.send('You are not authorized to use this command!')
    if not server_configs.get(str(ctx.guild.id)):
        server_configs[str(ctx.guild.id)] = {}
    server_configs[str(ctx.guild.id)]['antinuke'] = True
    save_server_configs(server_configs)
    await ctx.send("Antinuke enabled for this server")


@antinuke.command(name='disable')
async def disable_antinuke(ctx):
    if not is_trusted(ctx.guild, ctx.author):
        return await ctx.send('You are not authorized to use this command!')
    if not server_configs.get(str(ctx.guild.id)):
        server_configs[str(ctx.guild.id)] = {}
    server_configs[str(ctx.guild.id)]['antinuke'] = False
    save_server_configs(server_configs)
    await ctx.send("Antinuke disabled for this server")


@antinuke.command(name='setlogschannel')
async def set_logs_channel_antinuke(ctx, channel: discord.TextChannel = None):
    if not is_trusted(ctx.guild, ctx.author):
        return await ctx.send('You are not authorized to use this command!')
    if not channel:
        channel = ctx.channel

    if not server_configs.get(str(ctx.guild.id)):
        server_configs[str(ctx.guild.id)] = {}
    server_configs[str(ctx.guild.id)]['antinuke_logs_channel'] = channel.id
    save_server_configs(server_configs)
    await ctx.send("Antinuke logs channel defined successfully")


@antinuke.command(name='rmlogschannel')
async def rm_logs_channel_antinuke(ctx):
    if not is_trusted(ctx.guild, ctx.author):
        return await ctx.send('You are not authorized to use this command!')
    if not server_configs.get(str(ctx.guild.id)):
        server_configs[str(ctx.guild.id)] = {}
    if server_configs[str(ctx.guild.id)].get('antinuke_logs_channel'):
        server_configs[str(ctx.guild.id)].pop('antinuke_logs_channel')
    save_server_configs(server_configs)
    await ctx.send("Antinuke logs channel removed successfully")


@antinuke.command(name='whitelist')
async def whitelist_antinuke(ctx, subcommand: str = None, user: discord.User = None):
    if not is_trusted(ctx.guild, ctx.author):
        return await ctx.send('You are not authorized to use this command!')
    guild_id = str(ctx.guild.id)
    if not server_configs.get(str(ctx.guild.id)):
        server_configs[str(ctx.guild.id)] = {}
    if not subcommand and not user:
        return await ctx.send("**Current whitelist:**\n" + "\n - ".join(
            f"- <@{user_id}>" for user_id in server_configs[guild_id]['antinuke_whitelist']))

    if not subcommand or not user:
        return await ctx.send("Please provide a subcommand add or remove and a user")
    if subcommand == 'add':
        if not server_configs[guild_id].get('antinuke_whitelist'):
            server_configs[guild_id]['antinuke_whitelist'] = []
        if not user.id in server_configs[guild_id]['antinuke_whitelist']:
            server_configs[guild_id]['antinuke_whitelist'].append(user.id)
        save_server_configs(server_configs)
        await ctx.send("User added to whitelist successfully")
    if subcommand == 'remove':
        if not server_configs[guild_id].get('antinuke_whitelist'):
            server_configs[guild_id]['antinuke_whitelist'] = []
        if user.id in server_configs[guild_id]['antinuke_whitelist']:
            server_configs[guild_id]['antinuke_whitelist'].remove(user.id)
        save_server_configs(server_configs)
        await ctx.send("User removed from whitelist successfully")


@antinuke.command(name='trust')
async def trust_antinuke(ctx, subcommand: str = None, user: discord.User = None):
    if not is_trusted(ctx.guild, ctx.author):
        return await ctx.send('You are not authorized to use this command!')
    guild_id = str(ctx.guild.id)
    if not server_configs.get(str(ctx.guild.id)):
        server_configs[str(ctx.guild.id)] = {}
    if not subcommand and not user:
        return await ctx.send("**Current trust list:**\n" + "\n - ".join(
            f"- <@{user_id}>" for user_id in server_configs[guild_id]['antinuke_trustlist']))
    if not subcommand or not user:
        return await ctx.send("Please provide a subcommand add or remove and a user")
    if subcommand == 'add':
        if not server_configs[guild_id].get('antinuke_trustlist'):
            server_configs[guild_id]['antinuke_trustlist'] = []
        if not user.id in server_configs[guild_id]['antinuke_trustlist']:
            server_configs[guild_id]['antinuke_trustlist'].append(user.id)
        save_server_configs(server_configs)
        await ctx.send("User added to trust list successfully")
    if subcommand == 'remove':
        if not server_configs[guild_id].get('antinuke_trustlist'):
            server_configs[guild_id]['antinuke_trustlist'] = []
        if user.id in server_configs[guild_id]['antinuke_trustlist']:
            server_configs[guild_id]['antinuke_trustlist'].remove(user.id)
        save_server_configs(server_configs)
        await ctx.send("User removed from trust list successfully")


@antinuke.command(name='help')
async def antinuke_help(ctx):
    prefix = bot.command_prefix
    embed = discord.Embed(
        title="🛡️ Antinuke Help",
        description="List of available antinuke subcommands:",
        color=discord.Color.dark_red()
    )
    embed.add_field(name=f"{prefix}antinuke enable", value="Enable antinuke protection", inline=False)
    embed.add_field(name=f"{prefix}antinuke disable", value="Disable antinuke protection", inline=False)
    embed.add_field(name=f"{prefix}antinuke setlogschannel [#channel]",
                    value="Set the logs channel (defaults to current channel if not given)", inline=False)
    embed.add_field(name=f"{prefix}antinuke rmlogschannel", value="Remove the antinuke logs channel", inline=False)
    embed.add_field(name=f"{prefix}antinuke whitelist add/remove @user",
                    value="Add or remove a user from the whitelist", inline=False)
    embed.add_field(name=f"{prefix}antinuke whitelist", value="View current whitelist", inline=False)
    embed.add_field(name=f"{prefix}antinuke trust add/remove @user", value="Add or remove a user from the trust list",
                    inline=False)
    embed.add_field(name=f"{prefix}antinuke trust", value="View current trust list", inline=False)

    embed.set_footer(text="Only trusted users can use these commands.")
    await ctx.send(embed=embed)


@bot.command(name='authorization')
@has_owner_perm()
async def authorization_server(ctx, subcommand: str = None, user: discord.User = None):
    guild_id = str(ctx.guild.id)
    if not server_configs.get(str(ctx.guild.id)):
        server_configs[str(ctx.guild.id)] = {}
    if not subcommand and not user:
        return await ctx.send("**Current authorized list:**\n" + "\n - ".join(
            f"- <@{user_id}>" for user_id in server_configs[guild_id]['authorized_users']))
    if not subcommand or not user:
        return await ctx.send("Please provide a subcommand add or remove and a user")
    if subcommand == 'add':
        if not server_configs[guild_id].get('authorized_users'):
            server_configs[guild_id]['authorized_users'] = []
        if not user.id in server_configs[guild_id]['authorized_users']:
            server_configs[guild_id]['authorized_users'].append(user.id)
        save_server_configs(server_configs)
        await ctx.send("User added to authorized list successfully")
    if subcommand == 'remove':
        if not server_configs[guild_id].get('authorized_users'):
            server_configs[guild_id]['authorized_users'] = []
        if user.id in server_configs[guild_id]['authorized_users']:
            server_configs[guild_id]['authorized_users'].remove(user.id)
        save_server_configs(server_configs)
        await ctx.send("User removed from authorized list successfully")


add_help('Server Owner', 'authorization <add/remove> <user>',
         'Authorizes users for Moderation level command permissions')


@bot.command(name='owner')
@has_owner_perm()
async def ownerization_server(ctx, subcommand: str = None, user: discord.User = None):
    guild_id = str(ctx.guild.id)
    if not server_configs.get(str(ctx.guild.id)):
        server_configs[str(ctx.guild.id)] = {}
    if not subcommand and not user:
        return await ctx.send("**Current owner list:**\n" + "\n - ".join(
            f"- <@{user_id}>" for user_id in server_configs[guild_id]['owners']))
    if not subcommand or not user:
        return await ctx.send("Please provide a subcommand add or remove and a user")
    if subcommand == 'add':
        if not server_configs[guild_id].get('owners'):
            server_configs[guild_id]['owners'] = []
        if not user.id in server_configs[guild_id]['owners']:
            server_configs[guild_id]['owners'].append(user.id)
        save_server_configs(server_configs)
        await ctx.send("User added to authorized list successfully")
    if subcommand == 'remove':
        if not server_configs[guild_id].get('owners'):
            server_configs[guild_id]['owners'] = []
        if user.id in server_configs[guild_id]['owners']:
            server_configs[guild_id]['owners'].remove(user.id)
        save_server_configs(server_configs)
        await ctx.send("User removed from authorized list successfully")


add_help('Server Owner', 'owner <add/remove> <user>', 'Authorizes users for Server owner level command permissions')


@bot.command(name='bypass')
@is_owner()
async def bypass_bot(ctx, subcommand: str = None, user: discord.User = None, status: str = "True"):
    guild_id = str(ctx.guild.id)

    if not subcommand:
        bypass_list = "\n".join(
            f"- <@{user_id}>: Default: `{info.get('default', False)}` | {', '.join([f'{gid}: {state}' for gid, state in info.get('servers', {}).items()])}"
            for user_id, info in bypassusers.items()
        )
        return await ctx.send(f"**Current bypass list:**\n{bypass_list}" if bypass_list else "No users in bypass list.")

    if not user:
        return await ctx.send("Please provide a user.")

    user_id = str(user.id)
    status_bool = status.lower() == "true"

    if user_id not in bypassusers:
        bypassusers[user_id] = {"default": False, "servers": {}}

    if subcommand == 'setdefault':
        bypassusers[user_id]["default"] = status_bool
        save_bypass_users(bypassusers)
        await ctx.send(f"Set default bypass for <@{user_id}> to `{status_bool}`.")

    elif subcommand == 'setserver':
        bypassusers[user_id]["servers"][guild_id] = status_bool
        save_bypass_users(bypassusers)
        await ctx.send(f"Set server bypass for <@{user_id}> in `{ctx.guild.name}` to `{status_bool}`.")

    elif subcommand == 'remove':
        if user_id in bypassusers:
            if guild_id in bypassusers[user_id]["servers"]:
                del bypassusers[user_id]["servers"][guild_id]
                save_bypass_users(bypassusers)
                await ctx.send(f"Removed server override for <@{user_id}> in `{ctx.guild.name}`.")
            else:
                await ctx.send("No server override found for that user.")
        else:
            await ctx.send("User not in bypass list.")
    else:
        await ctx.send("Invalid subcommand. Use `setdefault`, `setserver`, or `remove`.")


add_help(
    'Bot Owner',
    'bypass [setdefault/setserver/remove] <user> [status: True/False]',
    'Manages global and per-server bypass permissions.\n- `setdefault` sets global bypass status for a user.\n- `setserver` sets or overrides bypass for the current server.\n- `remove` deletes the server-specific override.\nNo subcommand shows the full bypass list.'
)


timers_file = "timers.json"


def load_timers():
    try:
        with open(timers_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_timers(timers):
    with open(timers_file, "w") as f:
        f.write(json.dumps(timers))


@bot.group(name='timer', invoke_without_command=True)
async def timers_group(ctx):
    embed = discord.Embed(title="Timer Commands",
                          description=f"Use `{bot_prefix}timer add`, `{bot_prefix}timer list`, or `{bot_prefix}timer delete`.",
                          color=discord.Color.blurple())
    await ctx.send(embed=embed)


add_help('General', 'timer <set/list/delete> [1h/m/s/d/w]', 'sets a timer and notifes you when the timer ends')


@timers_group.command(name="add", aliases=['set'])
async def timer_add(ctx, duration: str, *, note: str = "No note provided"):
    timers = load_timers()
    try:
        channel_id = str(ctx.channel.id)
        user_id = str(ctx.author.id)
        delta = parse_duration(duration)
        if delta is None:
            await ctx.send(embed=discord.Embed(
                description="❌ Invalid duration format! Use `1h2m3s`, `10s`, etc.",
                color=discord.Color.red()))
            return

        end_time = datetime.now(timezone.utc) + delta

        if user_id not in timers:
            timers[user_id] = {}

        timers[user_id][end_time.isoformat()] = {
            "channel_id": channel_id,
            "note": note
        }

        save_timers(timers)
        embed = discord.Embed(
            description=f"✅ Timer set for `{duration}` with note:\n`{note}`\nWill end <t:{int(end_time.timestamp())}:R>",
            color=discord.Color.green())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(embed=discord.Embed(
            description=f"❌ An error occurred: {e}",
            color=discord.Color.red()))


@timers_group.command(name="list")
async def timer_list(ctx):
    timers = load_timers()
    user_id = str(ctx.author.id)
    if user_id not in timers or not timers[user_id]:
        await ctx.send(embed=discord.Embed(
            description="You have no active timers.",
            color=discord.Color.blurple()))
        return

    embed = discord.Embed(title="Your Active Timers", color=discord.Color.blurple())
    for i, (end_time, info) in enumerate(timers[user_id].items()):
        remaining = datetime.fromisoformat(end_time) - datetime.now(timezone.utc)
        if remaining.total_seconds() > 0:
            embed.add_field(
                name=f"#{i + 1} - Ends in {str(remaining).split('.')[0]}",
                value=f"Channel: <#{info['channel_id']}>\nNote: `{info['note']}`",
                inline=False
            )

    await ctx.send(embed=embed)



@timers_group.command(name="delete", aliases=['remove'])
async def timer_delete(ctx, timer_id: int = None):
    timers = load_timers()
    user_id = str(ctx.author.id)

    if user_id not in timers or not timers[user_id]:
        await ctx.send(embed=discord.Embed(
            description="❌ You have no active timers.",
            color=discord.Color.red()))
        return

    user_timers = list(timers[user_id].items())

    if timer_id is None:
        embed = discord.Embed(
            title="⏳ Your Active Timers",
            description="\n".join(
                [f"`{i + 1}`: Ends at `{end_time}`, Note: `{info['note']}`"
                 for i, (end_time, info) in enumerate(user_timers)]
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Use {bot_prefix}timer delete <ID> to delete a specific timer.")
        await ctx.send(embed=embed)
        return

    if timer_id < 1 or timer_id > len(user_timers):
        await ctx.send(embed=discord.Embed(
            description="❌ Invalid timer ID.",
            color=discord.Color.red()))
        return

    end_time, _ = user_timers[timer_id - 1]
    del timers[user_id][end_time]
    if not timers[user_id]:
        del timers[user_id]

    save_timers(timers)
    await ctx.send(embed=discord.Embed(
        description=f"✅ Timer ending at `{end_time}` deleted!",
        color=discord.Color.green()))



@tasks.loop(seconds=1)
async def check_timers():
    timers = load_timers()
    now = datetime.now(timezone.utc)
    expired = []

    for user_id, user_timers in timers.items():
        for end_time, info in list(user_timers.items()):
            try:
                end_time_obj = datetime.fromisoformat(end_time)
                if end_time_obj <= now:
                    expired.append((user_id, end_time, info))
            except ValueError as e:
                loge(f"Skipping invalid timer: {end_time}. Error: {e}")

    for user_id, end_time, info in expired:
        channel = bot.get_channel(int(info['channel_id']))  # Fix here: access info['channel_id']
        if channel:
            embed = discord.Embed(
                title="⏰ Timer Expired",
                description=f"<@{user_id}>, your timer has ended!\n**Note:** {info['note']}",
                color=discord.Color.orange())
            await channel.send(f'<@{user_id}>', embed=embed)
        del timers[user_id][end_time]
        if not timers[user_id]:
            del timers[user_id]

    if expired:
        save_timers(timers)



@bot.group(invoke_without_command=True)
async def bannedwords(ctx):
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(
            title="Invalid Command",
            description="Please use a valid subcommand, se bannedwords help command to see all commands",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)


@bannedwords.command(name="add")
async def banned_words_add(ctx, *, word):
    if not word:
        embed = discord.Embed(
            title="Error",
            description="You need to specify a word to add to the banned words list.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    guild_id = str(ctx.guild.id)
    if word in server_configs.get(guild_id, {}).get("bannable_words", []):
        embed = discord.Embed(
            title="Word Already Exists",
            description=f'"{word}" is already in the banned words list.',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    server_configs.setdefault(guild_id, {}).setdefault("bannable_words", []).append(word)
    save_server_configs(server_configs)
    embed = discord.Embed(
        title="Word Added",
        description=f'"{word}" has been added to the banned words list.',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bannedwords.command(name="remove")
async def banned_words_remove(ctx, *, word):
    if not word:
        embed = discord.Embed(
            title="Error",
            description="You need to specify a word to remove from the banned words list.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    guild_id = str(ctx.guild.id)
    if word not in server_configs.get(guild_id, {}).get("bannable_words", []):
        embed = discord.Embed(
            title="Word Not Found",
            description=f'"{word}" is not in the banned words list.',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    server_configs[guild_id]["bannable_words"].remove(word)
    save_server_configs(server_configs)
    embed = discord.Embed(
        title="Word Removed",
        description=f'"{word}" has been removed from the banned words list.',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bannedwords.command(name="list")
async def banned_words_list(ctx):
    guild_id = str(ctx.guild.id)
    words = server_configs.get(guild_id, {}).get("bannable_words", [])
    embed = discord.Embed(
        title="Banned Words List",
        description="No banned words set." if not words else "\n- ".join(words),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)


@bannedwords.command(name="action")
async def banned_words_action(ctx, threshold: int, action: str, duration: str, *, message: str = None):
    if action not in ["warn", "mute", "ban"]:
        embed = discord.Embed(
            title="❌ Invalid Action",
            description="Valid actions: `warn`, `mute`, `ban`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    parsed_duration = parse_duration(duration)
    if not parsed_duration:
        embed = discord.Embed(
            title="❌ Invalid Duration",
            description="Use format: `1w2d3h4m5s` (weeks, days, hours, minutes, seconds).",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    duration_seconds = int(parsed_duration.total_seconds())

    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault("action_settings", {})[str(threshold)] = {
        "action": action,
        "timeframe": duration_seconds
    }
    save_server_configs(server_configs)

    if message:
        server_configs[guild_id]["action_settings"][str(threshold)]["message"] = message

    embed = discord.Embed(
        title="✅ Action Set",
        description=f"**Threshold:** {threshold} violations\n"
                    f"**Action:** {action.capitalize()}\n"
                    f"**Timeframe:** {duration} ({duration_seconds} seconds)\n"
                    f"**Custom Message:** {message if message else 'None'}",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bannedwords.command(name="help")
async def bannedwords_help(ctx):
    prefix = ctx.prefix
    embed = discord.Embed(
        title="📕 BannedWords Help",
        description="List of available bannedwords subcommands:",
        color=discord.Color.blurple()
    )
    embed.add_field(
        name=f"{prefix}bannedwords add <word/*word/word*/...>",
        value="Add a word (supports wildcards and regex patterns) to the banned words list.",
        inline=False
    )
    embed.add_field(
        name=f"{prefix}bannedwords remove <word>",
        value="Remove a word from the banned words list.",
        inline=False
    )
    embed.add_field(
        name=f"{prefix}bannedwords list",
        value="List all words currently in the banned words list.",
        inline=False
    )
    embed.add_field(
        name=f"{prefix}bannedwords action <threshold> <warn/mute/ban> <duration> [message]",
        value="Set an action to trigger when a user hits the banned word threshold within the given timeframe.\n"
              "Example: `3 mute 1h` mutes after 3 violations in 1 hour.",
        inline=False
    )
    embed.set_footer(text="Example duration format: 1w2d3h4m5s")

    await ctx.send(embed=embed)


add_help('Moderation', 'bannedwords [help]', 'help command to see banned words options')


@has_required_perm()
@bot.group(name='chatcooldown', invoke_without_command=True)
async def chatcooldown(ctx):
    await ctx.send(
        'Please use a valid subcommand: add, remove, window <message window in seconds>, cooldownmax <in seconds>, cooldownmin <in seconds>, threshold <amount>, minimumtheshold')


add_help('Moderation', 'chatcooldown [help]', 'to see chat cooldown options')


@has_required_perm()
@chatcooldown.command(name='add')
async def chatcooldown_add(ctx):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault('cooldown_channels', []).append(ctx.channel.id)
    save_server_configs(server_configs)
    await ctx.send('Channel added successfully')


@has_required_perm()
@chatcooldown.command(name='remove')
async def chatcooldown_remove(ctx):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault('cooldown_channels', [])

    if ctx.channel.id in server_configs[guild_id]['cooldown_channels']:
        server_configs[guild_id]['cooldown_channels'].remove(ctx.channel.id)
        save_server_configs(server_configs)
        await ctx.send("Cooldown removed from this channel.")
    else:
        await ctx.send("This channel is not in the cooldown list.")


@has_required_perm()
@chatcooldown.command(name='window')
async def chatcooldown_window(ctx, window: int = 10):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault('cooldown_message_window', window)
    save_server_configs(server_configs)
    await ctx.send(f'Message window set to {window} seconds')


@has_required_perm()
@chatcooldown.command(name='threshold')
async def chatcooldown_threshold(ctx, threshold: int = 10):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault('cooldown_message_threshold', threshold)
    save_server_configs(server_configs)
    await ctx.send(f'Message threshold set to {threshold} messages within message window to trigger max cooldown')


@has_required_perm()
@chatcooldown.command(name='minimumthreshold')
async def chatcooldown_minimumthreshold(ctx, threshold: int = 10):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault('cooldown_minimum_threshold', threshold)
    save_server_configs(server_configs)
    await ctx.send(f'Minimum threshold set to {threshold} messages within message window to trigger max cooldown')


@has_required_perm()
@chatcooldown.command(name='cooldownmax')
async def chatcooldown_cooldownmax(ctx, cooldown: int = 5):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault('cooldown_max', cooldown)
    save_server_configs(server_configs)
    await ctx.send(f'Max cooldown set to {cooldown} seconds')


@has_required_perm()
@chatcooldown.command(name='cooldownmin')
async def chatcooldown_cooldownmin(ctx, cooldown: int = 0):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault('cooldown_min', cooldown)
    save_server_configs(server_configs)
    await ctx.send(f'Minimum cooldown set to {cooldown} seconds')


@chatcooldown.command(name='help')
async def chatcooldown_help(ctx):
    embed = discord.Embed(
        title="Chat Cooldown Command Help",
        description="Manage dynamic chat cooldowns based on activity.\n\n**Available Subcommands:**",
        color=discord.Color.green()
    )

    embed.add_field(
        name="add",
        value="Adds the current channel to the active cooldown list.",
        inline=False
    )
    embed.add_field(
        name="remove",
        value="Removes the current channel from the cooldown list.",
        inline=False
    )
    embed.add_field(
        name="window <seconds>",
        value="Sets the time window in seconds to count messages.",
        inline=False
    )
    embed.add_field(
        name="threshold <amount>",
        value="Sets message threshold to trigger max cooldown.",
        inline=False
    )
    embed.add_field(
        name="minimumthreshold <amount>",
        value="Sets the **minimum** message threshold to trigger cooldown adjustment.",
        inline=False
    )
    embed.add_field(
        name="cooldownmax <seconds>",
        value="Sets the **maximum** cooldown duration.",
        inline=False
    )
    embed.add_field(
        name="cooldownmin <seconds>",
        value="Sets the **minimum** cooldown duration.",
        inline=False
    )

    await ctx.send(embed=embed)


@has_required_perm()
@bot.group('levelrewards', invoke_without_command=True)
async def levelrewards(ctx):
    await ctx.send(
        'Please use valid subcommand enable/disable, add <message amount> <role>, remove <message count>, exclude')


add_help('Utils', 'levelrewards', 'command to setup levelrewards in the server')


@has_required_perm()
@levelrewards.command(name='enable')
async def level_rewards_enable(ctx):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault("level_rewards_config", {})["enabled"] = True
    save_server_configs(server_configs)
    await ctx.send("Level rewards enabled.")


@has_required_perm()
@levelrewards.command(name='disable')
async def level_rewards_disable(ctx):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault("level_rewards_config", {})["enabled"] = False
    save_server_configs(server_configs)
    await ctx.send("Level rewards disabled.")


@has_required_perm()
@levelrewards.command(name='add')
async def level_rewards_add(ctx, message_count: str = "10", role: discord.Role = None):
    if not role:
        return await ctx.send("Please mention a valid role.")

    guild_id = str(ctx.guild.id)
    config = server_configs.setdefault(guild_id, {}).setdefault("level_rewards_config", {})
    config.setdefault("roles", {})[message_count] = role.id

    save_server_configs(server_configs)
    await ctx.send(f'Level reward added! Members will receive {role.mention} at **{message_count}** messages.')


@has_required_perm()
@levelrewards.command(name='remove')
async def level_rewards_remove(ctx, message_count: str = None):
    if message_count is None:
        return await ctx.send("Please provide the message count to remove.")

    guild_id = str(ctx.guild.id)
    config = server_configs.get(guild_id, {}).get("level_rewards_config", {})
    reward_roles = config.get("roles", {})

    if message_count not in reward_roles:
        return await ctx.send(f"No level reward configured at {message_count} messages.")

    del reward_roles[message_count]
    save_server_configs(server_configs)

    await ctx.send(f"Removed level reward for **{message_count}** messages.")


@has_required_perm()
@levelrewards.command(name='exclude')
async def level_rewards_exclude(ctx):
    guild_id = str(ctx.guild.id)
    config = server_configs.setdefault(guild_id, {}).setdefault("level_rewards_config", {})
    excluded = config.setdefault("excluded_channels", [])

    if ctx.channel.id in excluded:
        excluded.remove(ctx.channel.id)
        await ctx.send(f"{ctx.channel.mention} has been re-included in level rewards.")
    else:
        excluded.append(ctx.channel.id)
        await ctx.send(f"{ctx.channel.mention} has been excluded from level rewards.")

    save_server_configs(server_configs)



@bot.command(name='levels')
async def levels(ctx):
    guild_id = str(ctx.guild.id)
    config = server_configs.get(guild_id, {}).get("level_rewards_config", {})
    reward_roles = config.get("roles", {})

    if not reward_roles:
        return await ctx.send("No level rewards configured for this server.")

    embed = discord.Embed(title="Level Rewards", color=discord.Color.blue())
    for message_count, role_id in sorted(reward_roles.items(), key=lambda x: int(x[0])):
        role = ctx.guild.get_role(role_id)
        if role:
            embed.add_field(name=f"{message_count} Messages", value=role.mention, inline=False)

    await ctx.send(embed=embed)

add_help('General', 'levels', 'Lists all the available level rewards in the server')


@bot.command(name='level')
async def level(ctx, user: discord.Member = None):
    guild_id = str(ctx.guild.id)
    user = user or ctx.author
    user_id = str(user.id)

    config = server_configs.get(guild_id, {}).get('level_rewards_config', {})

    if not config.get('enabled', False):
        return await ctx.send('Level rewards are not enabled in this server.')

    user_messages = server_configs.get(guild_id, {}).get('user_messages', {}).get(user_id, 0)

    embed = discord.Embed(
        title=f"{user.display_name}'s Level",
        color=discord.Color.green()
    )
    embed.add_field(name="Total Messages", value=str(user_messages), inline=False)

    reward_roles = config.get('roles', {})

    if reward_roles:
        thresholds = sorted(int(lvl) for lvl in reward_roles)
        current_level = max((lvl for lvl in thresholds if lvl <= user_messages), default=0)
        next_level = next((lvl for lvl in thresholds if lvl > user_messages), None)

        if str(current_level) in reward_roles:
            current_role = ctx.guild.get_role(reward_roles[str(current_level)])
            if current_role:
                embed.add_field(
                    name="Current Reward",
                    value=f"{current_role.mention} (Reached at {current_level} messages)",
                    inline=False
                )

        if next_level is not None and str(next_level) in reward_roles:
            next_role = ctx.guild.get_role(reward_roles[str(next_level)])
            if next_role:
                embed.add_field(
                    name="Next Reward",
                    value=f"{next_role.mention} at {next_level} messages!",
                    inline=False
                )

    await ctx.send(embed=embed)



add_help('General', 'level', 'know your current level, if level rewards are setup in the server')


@has_required_perm()
@bot.command(name='reactionrole')
async def setup_reactionrole(ctx, emoji: str = None, role: discord.Role = None, message_reference: str = None):
    reaction_roles = server_configs.get(str(ctx.guild.id), {}).get('reaction_roles', {})
    try:
        if ctx.message.reference:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        else:
            match = re.search(r'/(\d+)/(\d+)/(\d+)', message_reference)
            if not match:
                await ctx.send("Invalid message reference. Please reply to a message or provide a valid link.")
                return
            guild_id, channel_id, message_id = map(int, match.groups())
            channel = bot.get_channel(channel_id)
            if not channel:
                await ctx.send("Couldn't find the channel. Make sure the bot has access.")
                return
            message = await channel.fetch_message(message_id)
        if not emoji or not role:
            await ctx.send("Usage: Reply to a message OR use a link, then specify an emoji and a role mention.")
            return
        if str(message.id) not in reaction_roles:
            reaction_roles[str(message.id)] = {}
        server_configs.setdefault(str(ctx.guild.id), {}).setdefault('reaction_roles', {}).setdefault(str(message.id),
                                                                                                     {})[
            emoji] = role.id
        save_server_configs(server_configs)
        await message.add_reaction(emoji)
        await ctx.send(f"Reaction role set: {emoji} → {role.name} on message {message.jump_url}")
    except Exception as e:
        await ctx.send(f"Error: {e}")


add_help('Utils', 'reactionrole <emoji> <role mention> <message link or message reply>', 'sets up a reaction role')


@bot.command()
@has_required_perm()
async def lockdown(ctx):
    guild_id = ctx.guild.id if ctx.guild else 0
    if guild_id not in server_configs:
        server_configs[guild_id] = {'unlocked_state': {}}

    for channel in ctx.guild.channels:
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        server_configs[guild_id]['unlocked_state'][channel.id] = {
            'view_channel': overwrite.view_channel,
            'send_messages': overwrite.send_messages
        }
        overwrite.view_channel = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    save_server_configs(server_configs)

    await ctx.send(f":lock: All channels have been locked down.")


add_help('Moderation', 'lockdown', 'Performs a serverwide lockdown locking all channels')


@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlockdown(ctx):
    guild_id = ctx.guild.id if ctx.guild else 0
    if guild_id in server_configs and 'unlocked_state' in server_configs[guild_id]:
        for channel in ctx.guild.channels:
            if channel.id in server_configs[guild_id]['unlocked_state']:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                prev_perms = server_configs[guild_id]['unlocked_state'][channel.id]
                overwrite.view_channel = prev_perms['view_channel']
                overwrite.send_messages = prev_perms['send_messages']
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        del server_configs[guild_id]['unlocked_state']
        save_server_configs(server_configs)
        await ctx.send(f":unlock: All channels have been restored to their previous state.")
    else:
        await ctx.send(":x: No saved state found to restore.")


add_help('Moderation', 'unlockdown', 'restores the server perms to original state before lockdown')


@bot.command(name='tag', aliases=['t'])
async def tag_command(ctx, tag='None'):
    guild_id = str(ctx.guild.id)
    if tag:
        if tag in server_configs.get(guild_id, {}).get('tags', {}):
            await ctx.send(server_configs[guild_id]['tags'][tag])
        else:
            await ctx.send('No tags found')


add_help('General', 'tag <tag>', 'sends a predefined message')


@has_required_perm()
@bot.command(name='tags')
async def tags_command(ctx, action=None, tag=None, *, content=None):
    guild_id = str(ctx.guild.id)
    if action and action in ['list', 'show']:
        tags = ', '.join(server_configs[guild_id]['tags'].keys())
        return await ctx.send(f'Available tags: {tags}' if tags else 'No tags available.')
    if not action or not tag or not content:
        return await ctx.send('Please provide an action, tag and depending on action content')
    if tag in server_configs.get(guild_id, {}).get('tags', {}):
        if action in ['add', 'append']:
            await ctx.send('Tag already exists')
        elif tag in ['remove', 'del']:
            del server_configs[guild_id]['tags'][tag]
            save_server_configs(server_configs)
            await ctx.send(f'Tag `{tag}` removed!')
    elif action in ['add', 'append']:
        server_configs.setdefault(guild_id, {}).setdefault('tags', {})[tag] = content
        save_server_configs(server_configs)
        await ctx.send('Tag added successfully')
    else:
        await ctx.send('invalid command')


add_help('Utils', 'tags <add/remove/list> [content]', 'commands to set tags')


@has_required_perm()
@bot.command(name='setvoicelogs')
async def setlogschannel(ctx, channel: discord.TextChannel = None):
    if not channel:
        channel = ctx.channel

    server_configs.setdefault(str(ctx.guild.id), {})['voice_logs_channel'] = channel.id
    save_server_configs(server_configs)
    await ctx.send('Voice logs channel defined successfully')


add_help('Logging', 'setvoicelogs [channel mention]', 'Sets the voice logs channel for the server')


@has_required_perm()
@bot.command(name='rmvoicelogs')
async def rmlogschannel(ctx):
    server_configs.setdefault(str(ctx.guild.id), {})['voice_logs_channel'] = 0
    save_server_configs(server_configs)
    await ctx.send('Voice logs channel undefined successfully')


add_help('Logging', 'rmvoicelogs', 'undefines the voice logs channel for the server')


@has_required_perm()
@bot.command(name='settextlogs')
async def settextchannel(ctx, channel: discord.TextChannel = None):
    if not channel:
        channel = ctx.channel

    server_configs.setdefault(str(ctx.guild.id), {})['message_logs_channel'] = channel.id
    save_server_configs(server_configs)
    await ctx.send('Text logs channel defined successfully')


add_help('Logging', 'settextlogs [channel mention]', 'Sets the text logs channel for the server')


@has_required_perm()
@bot.command(name='rmtextlogs')
async def rmtextchannel(ctx):
    server_configs.setdefault(str(ctx.guild.id), {})['message_logs_channel'] = 0
    save_server_configs(server_configs)
    await ctx.send('Text logs channel undefined successfully')


add_help('Logging', 'rmtextlogs', 'undefines the text logs channel for the server')


@has_required_perm()
@bot.command(name='setmemberlogs')
async def setmemberlogs(ctx, channel: discord.TextChannel = None):
    if not channel:
        channel = ctx.channel

    server_configs.setdefault(str(ctx.guild.id), {})['member_logs_channel'] = channel.id
    save_server_configs(server_configs)
    await ctx.send('Member logs channel defined successfully')


add_help('Logging', 'setmemberlogs [channel mention]', 'Sets the member logs channel for the server')


@has_required_perm()
@bot.command(name='rmmemberlogs')
async def rmmemberlogs(ctx):
    server_configs.setdefault(str(ctx.guild.id), {})['member_logs_channel'] = 0
    save_server_configs(server_configs)
    await ctx.send('Member logs channel undefined successfully')


add_help('Logging', 'rmmemberlogs', 'undefines the member logs channel for the server')


@when_member_join
async def member_log_engine_join(member):
    guild_id = str(member.guild.id)
    config = server_configs.setdefault(guild_id, {})
    channel_id = config.get('member_logs_channel')

    if channel_id and channel_id != 0:
        channel = member.guild.get_channel(int(channel_id))
        if channel:
            await channel.send(f"📥 Member joined: `{member}`")

            embed = discord.Embed(
                title="Member Joined",
                color=0x2ecc71,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Username", value=f"{member}", inline=True)
            embed.add_field(name="User ID", value=f"{member.id}", inline=True)
            embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            inline=False)

            await channel.send(embed=embed)


@when_member_leave
async def member_log_engine_leave(member):
    guild_id = str(member.guild.id)
    config = server_configs.setdefault(guild_id, {})
    channel_id = config.get('member_logs_channel')

    if channel_id and channel_id != 0:
        channel = member.guild.get_channel(int(channel_id))
        if channel:
            await channel.send(f"📤 Member left: `{member}`")

            embed = discord.Embed(
                title="Member Left",
                color=0xe74c3c,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Username", value=f"{member}", inline=True)
            embed.add_field(name="User ID", value=f"{member.id}", inline=True)
            if member.joined_at:
                embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                inline=False)

            await channel.send(embed=embed)


# @bot.group(name='analytics', invoke_without_command=True)
async def analytics_group(ctx):
    await ctx.send('Please use subbcommand enable or disable')


# @analytics_group.command(name='enable')
async def enable_analytics(ctx):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {}).setdefault("analytics", True)
    server_configs[guild_id].setdefault("data", {})
    save_server_configs(server_configs)
    await ctx.send("Analytics enabled for this server!")


# @analytics_group.command(name='disable')
async def disable_analytics(ctx):
    guild_id = str(ctx.guild.id)
    if guild_id in server_configs:
        server_configs[guild_id]["analytics"] = False
        save_server_configs(server_configs)
        await ctx.send("Analytics disabled for this server.")
    else:
        await ctx.send("Analytics is not enabled.")


# @analytics_group.command(name='role')
async def role_distribution(ctx):
    role_counts = {role.name: len(role.members) for role in ctx.guild.roles if role.name != "@everyone"}
    embed = discord.Embed(title="Role Distribution", color=discord.Color.blue())
    for role, count in role_counts.items():
        embed.add_field(name=role, value=str(count), inline=False)
    await ctx.send(embed=embed)


# @analytics_group.command(name='chart')
async def analytics_chart(ctx, timeframe="day"):
    guild_id = str(ctx.guild.id)
    if not server_configs.get(guild_id, {}).get("analytics", False):
        return await ctx.send("Analytics is not enabled for this server.")

    data = server_configs[guild_id]["data"]
    tz = pytz.utc
    now = datetime.now(tz)

    if timeframe == "minute":
        source = "messages_per_minute"
        date_format = "%Y-%m-%d %H:%M"
        start_time = now - timedelta(minutes=60)
    elif timeframe == "hour":
        source = "messages_per_minute"
        date_format = "%Y-%m-%d %H:%M"
        start_time = now - timedelta(hours=24)
    elif timeframe == "day":
        source = "messages"
        date_format = "%Y-%m-%d"
        start_time = now - timedelta(days=7)
    elif timeframe == "week":
        source = "messages"
        date_format = "%Y-%m-%d"
        start_time = now - timedelta(weeks=4)
    else:
        await ctx.send("Invalid timeframe! Use minute, hour, day, or week.")
        return

    filtered_data = {
        datetime.strptime(date, date_format).replace(tzinfo=tz): count
        for date, count in data.get(source, {}).items()
        if datetime.strptime(date, date_format).replace(tzinfo=tz) >= start_time
    }

    if not filtered_data:
        await ctx.send("No data available for the selected timeframe.")
        return

    dates = list(filtered_data.keys())
    counts = list(filtered_data.values())

    def format_large_numbers(val, _):
        if val >= 1_000_000:
            return f"{val / 1_000_000:.1f}M"
        elif val >= 1_000:
            return f"{val / 1_000:.1f}K"
        return str(int(val))

    background_color = "#1a1a1a"

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=background_color)
    ax.set_facecolor(background_color)
    x = np.linspace(0, 1, len(dates))
    ax.fill_between(dates, counts, color=plt.cm.coolwarm(0.4), alpha=0.3)
    line, = ax.plot(dates, counts, marker="o", linestyle="-", color="cyan", linewidth=2.5)
    line.set_path_effects([pe.Stroke(linewidth=4, foreground='black'), pe.Normal()])
    ax.set_xlabel("Time", fontsize=12, color="white")
    ax.set_ylabel("Messages", fontsize=12, color="white")
    ax.set_title(f"📊 Message Analytics ({timeframe})", fontsize=14, color="white", fontweight="bold")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_large_numbers))
    ax.tick_params(axis="x", colors="white", rotation=30)
    ax.tick_params(axis="y", colors="white")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
    ax.grid(color="gray", linestyle="--", linewidth=0.5)
    plt.savefig("analytics_chart.png", facecolor=background_color)
    plt.close()
    embed = discord.Embed(title=f"📊 Analytics Chart ({timeframe})", color=discord.Color.blue())
    embed.set_image(url="attachment://analytics_chart.png")
    await ctx.send(embed=embed, file=discord.File("analytics_chart.png"))


@has_required_perm()
@bot.command()
async def linkbutton(ctx, link: str, *, label: str = "Click Here"):
    if not link.startswith(("http://", "https://")):
        await ctx.send("Please provide a valid URL starting with http:// or https://")
        return

    view = discord.ui.View()
    button = discord.ui.Button(label=label, url=link, style=discord.ButtonStyle.link)
    view.add_item(button)

    await ctx.send(view=view)


add_help('Utils', 'linkbutton <link> [label]', 'gives a link button for the provided link')

ROLE_DATA_FILE = "stored_roles.json"

role_data = {}
if os.path.exists(ROLE_DATA_FILE):
    with open(ROLE_DATA_FILE, "r") as f:
        role_data = json.load(f)


def save_role_data():
    with open(ROLE_DATA_FILE, "w") as f:
        json.dump(role_data, f, indent=4)


@bot.command(name='userroledata')
@has_required_perm()
async def user_role_data(ctx, action):
    guild_id = str(ctx.guild.id)
    if action == 'enable':
        server_configs.setdefault(guild_id, {})['userroledata'] = True
        save_server_configs(server_configs)
        await ctx.send('Now storing user role data')
    elif action == 'disable':
        server_configs.setdefault(guild_id, {})['userroledata'] = False
        save_server_configs(server_configs)
        await ctx.send('Now not storing user role data')
    else:
        await ctx.send('Unknown subcommand')


add_help('Utils', 'userroledata <enable/disable>',
         'Enables or disables the user role data feature, it stores role of all users and reassigns them incase they rejoin ')


@bot.command(name='clearuserroledata')
@has_required_perm()
async def clear_role_data(ctx, member: discord.Member):
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    if guild_id in role_data and user_id in role_data[guild_id]:
        del role_data[guild_id][user_id]
        save_role_data()
        await ctx.send(f"Cleared stored roles for {member.mention}")
    else:
        await ctx.send(f"No stored roles found for {member.mention}")


add_help('Utils', 'clearuserroledata <usermention>', 'clears user role data for a user')


@bot.command(name='listuserroledata')
@has_required_perm()
async def list_stored(ctx):
    guild_id = str(ctx.guild.id)

    if guild_id not in role_data or not role_data[guild_id]:
        await ctx.send("No users with stored roles.")
        return

    user_ids = list(role_data[guild_id].keys())
    per_page = 10
    pages = [user_ids[i:i + per_page] for i in range(0, len(user_ids), per_page)]
    total_pages = len(pages)
    current_page = 0

    def make_embed(page_index):
        embed = discord.Embed(
            title="Stored User Role Data",
            description="List of users who have stored roles.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Page {page_index + 1} of {total_pages}")

        for user_id in pages[page_index]:
            member = ctx.guild.get_member(int(user_id))
            name = member.mention if member else f"`{user_id}`"
            embed.add_field(name=name, value="Stored roles", inline=False)

        return embed

    message = await ctx.send(embed=make_embed(current_page))
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return (
                user == ctx.author
                and reaction.message.id == message.id
                and str(reaction.emoji) in ["⬅️", "➡️"]
        )

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "➡️":
                if current_page < total_pages - 1:
                    current_page += 1
                    await message.edit(embed=make_embed(current_page))
            elif str(reaction.emoji) == "⬅️":
                if current_page > 0:
                    current_page -= 1
                    await message.edit(embed=make_embed(current_page))

            await message.remove_reaction(reaction, user)

        except asyncio.TimeoutError:
            await message.clear_reactions()
            break


add_help('Utils', 'listuserroledata', 'Lists all stored user role data')


@when_member_join
async def roledata_join(member):
    guild_id = str(member.guild.id)
    user_id = str(member.id)

    if server_configs.get(guild_id, {}).get('userroledata', False) and guild_id in role_data and user_id in role_data[
        guild_id]:
        role_ids = role_data[guild_id][user_id]
        roles_to_assign = []

        for role_id in role_ids:
            role = member.guild.get_role(role_id)
            if role:
                roles_to_assign.append(role)

        try:
            await member.add_roles(*roles_to_assign, reason="Restoring previous roles")
        except discord.Forbidden:
            loge(f"Missing permissions to assign roles to {member.name}")
        except Exception as e:
            loge(f"Error assigning roles to {member.name}: {e}")


@when_member_leave
async def roledata_leave(member):
    guild_id = str(member.guild.id)
    user_id = str(member.id)

    if server_configs.get(guild_id, {}).get('userroledata', False):
        if guild_id not in role_data:
            role_data[guild_id] = {}

        role_ids = [role.id for role in member.roles if role.name != "@everyone"]
        role_data[guild_id][user_id] = role_ids
        save_role_data()


tts_queues = defaultdict(deque)
tts_playing_flags = defaultdict(lambda: False)


def text_to_speech_sync(text, filename):
    """Synchronous TTS generation using gTTS"""
    try:
        # Remove existing file
        if os.path.exists(filename):
            os.remove(filename)

        # Generate and save audio
        tts = gTTS(text=text, lang='en')
        tts.save(filename)

        return True
    except Exception as e:
        loge(f"TTS Generation Error: {e}")
        return False


async def text_to_speech_async(text, filename=TTS_VOICE_FILE):
    """Async wrapper for TTS generation using gTTS"""
    loop = asyncio.get_event_loop()

    success = await loop.run_in_executor(
        None,
        text_to_speech_sync,
        text,
        filename
    )

    if success and os.path.exists(filename):
        file_size = os.path.getsize(filename)
        return file_size > 100

    return False


async def play_tts_queue(guild: discord.Guild, channel: discord.TextChannel):
    guild_id = str(guild.id)
    voice_client = guild.voice_client

    while tts_queues[guild_id]:
        tts_playing_flags[guild_id] = True
        tts_text = tts_queues[guild_id].popleft()

        success = await text_to_speech_async(tts_text)
        if not success:
            await channel.send("❌ Failed to generate or play audio.")
            continue

        if not voice_client or not voice_client.is_connected():
            await channel.send("❌ Failed to generate or play audio.")
            break

        if not os.path.exists(FFMPEG_PATH):
            await channel.send("❌ FFmpeg not found!")
            continue

        audio_source = discord.FFmpegPCMAudio(
            TTS_VOICE_FILE,
            executable=FFMPEG_PATH
        )

        done_event = asyncio.Event()

        def after_playing(error):
            if error:
                asyncio.create_task(channel.send(f"❌ Playback error: {error}"))
                logerr(f"TTS Playback Error: {error}")
            done_event.set()

        voice_client.play(audio_source, after=after_playing)
        await done_event.wait()
        await asyncio.sleep(0.3)

    tts_playing_flags[guild_id] = False


@bot.command()
async def tts(ctx, *, message=None):
    if not message:
        await ctx.send("❌ Please provide text to speak!")
        return

    if not ctx.voice_client:
        await ctx.send(f"❌ I'm not in a voice channel. Use `{bot.command_prefix}join` first.")
        return

    if vcinuse_flags[str(ctx.guild.id)]:
        await ctx.send("❌ Voice channel is currently in use. TTS is temporarily disabled.")
        return

    user: discord.User = ctx.author
    tts_text = f"{user.display_name} says: {message}"
    tts_queues[str(ctx.guild.id)].append(tts_text)

    await ctx.send(f"✅ Queued TTS: {message[:100]}{'...' if len(message) > 100 else ''}")

    if not tts_playing_flags[str(ctx.guild.id)]:
        await play_tts_queue(ctx.guild, ctx.channel)


add_help('General', 'tts <message>',
         'Text To Speach given message to the vc the bot has joined. join it using the bot join command')


@bot.command('ttschannel')
async def toggle_tts_channel(ctx):
    guild_id = str(ctx.guild.id)
    channel_id = ctx.channel.id
    if channel_id in server_configs.get(guild_id, {}).get('tts_channels', []):
        server_configs[guild_id]['tts_channels'].remove(channel_id)
        save_server_configs(server_configs)
        await ctx.send('TTS disabled for this channel')
    else:
        server_configs.setdefault(guild_id, {}).setdefault('tts_channels', []).append(channel_id)
        save_server_configs(server_configs)
        await ctx.send('TTS enabled for this channel')


add_help('Moderation', 'ttschannel', 'toggles the current channel for auto tts')


@bot.command('ttsdisable')
async def toggle_tts_enable_disable(ctx):
    guild_id = str(ctx.guild.id)
    channel_id = ctx.channel.id
    if server_configs.get(guild_id, {}).get('disable_tts', False):
        server_configs[guild_id]['disable_tts'] = False
        save_server_configs(server_configs)
        await ctx.send('TTS enabled for this server')
    else:
        server_configs.setdefault(guild_id, {})['disable_tts'] = True
        save_server_configs(server_configs)
        await ctx.send('TTS disabled for this server')


add_help('Moderation', 'ttsdisable', 'toggles tts globally for server')


@when_message
async def tts_auto_engine(message):
    if message.author.bot:
        return

    if message.guild is None:
        return

    ch_id = message.channel.id
    guild = message.guild
    guild_id = str(guild.id)

    if vcinuse_flags[guild_id]:
        return

    special_characters = string.punctuation

    if (not server_configs.get(guild_id, {}).get('disable_tts', False)
        and not message.content[:1] in special_characters) and message.guild.voice_client is not None:

        if ch_id in server_configs.get(guild_id, {}).get('tts_channels', []):
            user: discord.User = message.author
            tts_text = f"{user.display_name} says: {message.content}"
            tts_queues[guild_id].append(tts_text)

            if not tts_playing_flags[guild_id]:
                await play_tts_queue(guild, message.channel)


@has_required_perm()
@bot.command(name='excludelogging')
async def excludelogging(ctx, type: str = "text"):
    if not type or type not in exclude_log_types:
        await ctx.send(f"Invalid or no Log Type, valid log types: {', '.join(exclude_log_types)}")
        return
    server = str(ctx.guild.id)
    channel = ctx.channel.id
    if not channel in server_configs.get(server, {}).get('excluded', {}).get(type, []):
        server_configs.setdefault(server, {}).setdefault('logging_excluded', {}).setdefault(type, []).append(channel)
        save_server_configs(server_configs)
        await ctx.send(f'Channel excluded from {type} logging')
        return
    server_configs.setdefault(server, {}).setdefault('logging_excluded', {}).setdefault(type, []).remove(channel)
    save_server_configs(server_configs)
    await ctx.send(f'Channel un-excluded from {type} logging')


add_help('Logging', 'excludelogging <type>', 'excludes that channel for that type of logging')


SUGGESTIONS_FILE = "suggestions.json"
suggestion_data = {}

def load_suggestions():
    global suggestion_data
    if os.path.exists(SUGGESTIONS_FILE):
        with open(SUGGESTIONS_FILE, "r") as f:
            suggestion_data = json.load(f)

def save_suggestions():
    with open(SUGGESTIONS_FILE, "w") as f:
        json.dump(suggestion_data, f, indent=4)

load_suggestions()


class SuggestionView(discord.ui.View):
    def __init__(self, message_id, author_id):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.author_id = author_id

    async def update_votes(self, interaction: discord.Interaction, is_upvote: bool):
        msg_id = str(self.message_id)
        data = suggestion_data.get(msg_id)
        if not data:
            await interaction.response.send_message("Suggestion not found.", ephemeral=True)
            return

        user_id = interaction.user.id
        if is_upvote:
            if user_id in data["votes"]["down"]:
                data["votes"]["down"].remove(user_id)
            if user_id not in data["votes"]["up"]:
                data["votes"]["up"].append(user_id)
        else:
            if user_id in data["votes"]["up"]:
                data["votes"]["up"].remove(user_id)
            if user_id not in data["votes"]["down"]:
                data["votes"]["down"].append(user_id)

        save_suggestions()

        msg = await interaction.channel.fetch_message(int(self.message_id))
        embed = msg.embeds[0]
        embed.set_field_at(1, name="Votes", value=f"✅ {len(data['votes']['up'])} | ❌ {len(data['votes']['down'])}", inline=True)
        await msg.edit(embed=embed, view=self)

        await interaction.response.send_message("✅ Vote counted!", ephemeral=True)

    @discord.ui.button(label="✅", style=discord.ButtonStyle.success, custom_id="vote_up")
    async def vote_up(self, button, interaction: discord.Interaction):
        await self.update_votes(interaction, is_upvote=True)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger, custom_id="vote_down")
    async def vote_down(self, button, interaction: discord.Interaction):
        await self.update_votes(interaction, is_upvote=False)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.primary, custom_id="approve_button", row=1)
    async def approve(self, button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("🚫 You don't have permission.", ephemeral=True)
            return

        msg_id = str(self.message_id)
        data = suggestion_data.get(msg_id)
        if not data or data["status"] == "approved":
            await interaction.response.send_message("Already approved or not found.", ephemeral=True)
            return

        data["status"] = "approved"
        save_suggestions()

        msg = await interaction.channel.fetch_message(int(msg_id))
        embed = msg.embeds[0]
        embed.color = discord.Color.green()
        embed.set_field_at(0, name="Status", value="✅ Approved", inline=True)
        await msg.edit(embed=embed, view=self)

        await interaction.response.send_message("👍 Suggestion approved.", ephemeral=True)

    @discord.ui.button(label="Disapprove", style=discord.ButtonStyle.danger, custom_id="disapprove_button", row=1)
    async def disapprove(self, button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("🚫 You don't have permission.", ephemeral=True)
            return

        msg_id = str(self.message_id)
        data = suggestion_data.get(msg_id)
        if not data or data["status"] == "disapproved":
            await interaction.response.send_message("Already disapproved or not found.", ephemeral=True)
            return

        data["status"] = "disapproved"
        save_suggestions()

        msg = await interaction.channel.fetch_message(int(msg_id))
        embed = msg.embeds[0]
        embed.color = discord.Color.red()
        embed.set_field_at(0, name="Status", value="❌ Disapproved", inline=True)
        await msg.edit(embed=embed, view=self)

        await interaction.response.send_message("👎 Suggestion disapproved.", ephemeral=True)

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.secondary, custom_id="delete_button", row=1)
    async def delete_suggestion(self, button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("🚫 You don't have permission.", ephemeral=True)
            return

        msg_id = str(self.message_id)
        data = suggestion_data.get(msg_id)
        if not data:
            await interaction.response.send_message("❌ Suggestion not found in memory.", ephemeral=True)
            return

        try:
            await interaction.message.delete()
            suggestion_data.pop(msg_id, None)
            save_suggestions()
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Failed to delete: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("🗑️ Suggestion deleted.", ephemeral=True)

@when_bot_ready
async def suggestion_view_persistent ():
    for msg_id, data in suggestion_data.items():
        view = SuggestionView(message_id=int(msg_id), author_id=data["user_id"])
        bot.add_view(view, message_id=int(msg_id))


@bot.slash_command(name="suggest", description="Submit a suggestion")
async def suggest(ctx: discord.ApplicationContext, suggestion: discord.Option(str, "Your suggestion")):
    guild_id = str(ctx.guild.id)
    config = server_configs.get(guild_id, {})

    if not config.get("suggestions_enabled"):
        await ctx.respond("❌ Suggestions are disabled.", ephemeral=True)
        return

    channel_id = config.get("suggestions_channel")
    if not channel_id:
        await ctx.respond("❌ Suggestions channel not set.", ephemeral=True)
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.respond("⚠️ Suggestions channel is invalid.", ephemeral=True)
        return

    await ctx.defer(ephemeral=True)

    embed = discord.Embed(
        title="📬 New Suggestion",
        description=f"> {suggestion}",
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Suggested by {ctx.user.name}", icon_url=ctx.user.display_avatar.url)
    embed.add_field(name="Status", value="🕐 Pending", inline=True)
    embed.add_field(name="Votes", value="✅ 0 | ❌ 0", inline=True)

    view = SuggestionView(message_id=0, author_id=ctx.user.id)
    msg = await channel.send(embed=embed, view=view)
    view.message_id = msg.id
    await msg.edit(view=view)

    suggestion_data[str(msg.id)] = {
        "guild_id": guild_id,
        "channel_id": channel_id,
        "message_id": msg.id,
        "user_id": ctx.user.id,
        "suggestion": suggestion,
        "status": "pending",
        "votes": {"up": [], "down": []}
    }
    save_suggestions()

    await ctx.followup.send("✅ Your suggestion has been posted!", ephemeral=True)

suggestion_config = bot.create_group(name="suggestionconfig", description="Configure suggestions")


@suggestion_config.command(name="channel", description="Set the channel for suggestions")
@has_required_perm()
async def set_suggestion_channel(ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "Target channel")):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {})
    server_configs[guild_id]["suggestions_channel"] = channel.id
    save_server_configs(server_configs)
    save_suggestions()
    await ctx.respond(f"✅ Suggestions channel set to {channel.mention}.", ephemeral=True)

@suggestion_config.command(name="enable", description="Enable the suggestion system")
@has_required_perm()
async def enable_suggestions(ctx: discord.ApplicationContext):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {})
    server_configs[guild_id]["suggestions_enabled"] = True
    save_server_configs(server_configs)
    save_suggestions()
    await ctx.respond("✅ Suggestions have been enabled.", ephemeral=True)

@suggestion_config.command(name="disable", description="Disable the suggestion system")
@has_required_perm()
async def disable_suggestions(ctx: discord.ApplicationContext):
    guild_id = str(ctx.guild.id)
    server_configs.setdefault(guild_id, {})
    server_configs[guild_id]["suggestions_enabled"] = False
    save_server_configs(server_configs)
    save_suggestions()
    await ctx.respond("❌ Suggestions have been disabled.", ephemeral=True)


@bot.group(name="invitetracker", invoke_without_command=True, aliases=['it'])
async def invitetracker(ctx):
    await ctx.send("Use subcommands: `count <Code>`, `whoinvited <member>`.", delete_after=10)


async def get_invite_uses(guild, invite_code):
    invites = await guild.invites()
    matched_invite = next((inv for inv in invites if inv.code == invite_code), None)

    if matched_invite:
        return matched_invite.uses
    else:
        return None


@invitetracker.command(name="count",aliases=['c'])
async def invite_count(ctx, invite_code: str):
    uses = await get_invite_uses(ctx.guild, invite_code)

    if uses is not None:
        embed = Embed(
            title="Invite Usage Count",
            description=f"Invite `{invite_code}` has been used **{uses} times**.",
            color=discord.Color.green()
        )
    else:
        embed = Embed(
            title="Error",
            description=f"❌ Invite `{invite_code}` not found in this server.",
            color=discord.Color.red()
        )

    await ctx.send(embed=embed)


@invitetracker.command(name="invitedcount", aliases=['ic'])
async def invited_count(ctx, member: discord.Member):
    guild_id = str(ctx.guild.id)
    join_info = server_configs.get(guild_id, {}).get("invite_joins", {})

    count = sum(1 for info in join_info.values() if info['inviter_id'] == str(member.id))

    embed = Embed(
        title="Invite Count",
        description=f"**{member}** has invited **{count} members** to this server.",
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed)


@invitetracker.command(name="invitedlist", aliases=['icl'])
async def invited_list(ctx, member: discord.Member):
    guild_id = str(ctx.guild.id)
    join_info = server_configs.get(guild_id, {}).get("invite_joins", {})

    def paginate(items, page_size=10):
        for i in range(0, len(items), page_size):
            yield items[i: i + page_size]

    invited_users = [
        f"<@{user_id}>"
        for user_id, info in join_info.items()
        if info['inviter_id'] == str(member.id)
    ]

    if not invited_users:
        embed = discord.Embed(
            title="Invited Users",
            description=f"⚠️ {member} has not invited any members.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    pages = list(paginate(invited_users, page_size=10))
    total_pages = len(pages)
    current_page = 0

    embed = discord.Embed(
        title=f"Invited Users by {member}",
        description="\n".join(pages[current_page]),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Page {current_page + 1}/{total_pages}")

    message = await ctx.send(embed=embed)

    if total_pages == 1:
        return

    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return (
            reaction.message.id == message.id and
            user != bot.user and
            str(reaction.emoji) in ["⬅️", "➡️"]
        )

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)

            if str(reaction.emoji) == "➡️" and current_page < total_pages - 1:
                current_page += 1
            elif str(reaction.emoji) == "⬅️" and current_page > 0:
                current_page -= 1
            else:
                await message.remove_reaction(reaction, user)
                continue

            new_embed = discord.Embed(
                title=f"Invited Users by {member}",
                description="\n".join(pages[current_page]),
                color=discord.Color.blue()
            )
            new_embed.set_footer(text=f"Page {current_page + 1}/{total_pages}")

            await message.edit(embed=new_embed)
            await message.remove_reaction(reaction, user)

        except Exception:
            break  # Timeout after 60 seconds of inactivity




@invitetracker.command(name="whoinvited", aliases=['wi'])
async def whoused(ctx, member: discord.Member):
    guild_id = str(ctx.guild.id)
    member_id = str(member.id)

    join_info = server_configs.get(guild_id, {}).get("invite_joins", {}).get(member_id)

    if join_info:
        embed = Embed(
            title="Invite Usage Info",
            description=(
                f"**Member:** {member}\n"
                f"**Invite Code:** `{join_info['invite_code']}`\n"
                f"**Inviter:** <@{join_info['inviter_id']}> (`{join_info['inviter_name']}`)"
            ),
            color=discord.Color.green()
        )
    else:
        embed = Embed(
            title="Info",
            description=f"⚠️ No invite usage record found for {member}.",
            color=discord.Color.orange()
        )

    await ctx.send(embed=embed)


@invitetracker.command(name="help", aliases=['h'])
async def invitetracker_help(ctx):
    embed = Embed(
        title="Invite Tracker Help",
        color=discord.Color.blue()
    )

    embed.add_field(
        name=f"{bot.command_prefix}invitetracker count <invite_code>",
        value="📊 Get the usage count of a specific invite code.",
        inline=False
    )
    embed.add_field(
        name=f"{bot.command_prefix}invitetracker whoinvited <member>",
        value="🧐 Show which invite code was used by a specific member.",
        inline=False
    )
    embed.add_field(
        name=f"{bot.command_prefix}invitetracker invitedcount <member>",
        value="📋 Show how many members a user has invited.",
        inline=False
    )
    embed.add_field(
        name=f"{bot.command_prefix}invitetracker invitedlist <member>",
        value="📋 Show the list of members invited by a user.",
        inline=False
    )
    embed.add_field(
        name=f"{bot.command_prefix}invitetracker help",
        value="❔ Show this help message.",
        inline=False
    )

    await ctx.send(embed=embed)
add_help('Utils', 'invitetracker [help]', 'Invite Tracker Commands')


@when_member_join
async def track_invite_engine(member):
    guild = member.guild
    guild_id = str(guild.id)

    invites_before = bot.cached_invites.get(guild.id, [])
    invites_after = await guild.invites()

    used_invite = None
    for after_inv in invites_after:
        before_inv = discord.utils.get(invites_before, code=after_inv.code)

        if before_inv:
            if after_inv.uses > before_inv.uses:
                used_invite = after_inv
                break
        else:
            if after_inv.uses > 0:
                used_invite = after_inv
                break

    bot.cached_invites[guild.id] = invites_after

    if used_invite:
        inviter = used_invite.inviter
        invite_code = used_invite.code
        print(f"✅ {member} joined using invite {invite_code} by {inviter}")

        server_configs.setdefault(guild_id, {})
        join_info = server_configs[guild_id].setdefault("invite_joins", {})
        join_info[str(member.id)] = {
            "invite_code": invite_code,
            "inviter_id": str(inviter.id),
            "inviter_name": str(inviter),
        }
        save_server_configs(server_configs)

    else:
        print(f"ℹ️ {member} joined, but no invite usage increment detected.")


@when_member_leave
async def invite_track_remove_engine(member):
    guild_id = str(member.guild.id)
    member_id = str(member.id)

    if "invite_joins" in server_configs.get(guild_id, {}):
        if member_id in server_configs[guild_id]["invite_joins"]:
            del server_configs[guild_id]["invite_joins"][member_id]
            save_server_configs(server_configs)
            print(f"ℹ️ Removed join record for {member} because they left the server.")


bot.remove_command('help')


@bot.command(name='help', aliases=['h'])
async def help(ctx, *, category: str = None):
    def create_embed_pages(commands, category_name=None):
        pages = []
        current_embed = discord.Embed(
            title=f"{category_name} Commands" if category_name else "Help Menu",
            color=discord.Color.blue()
        )
        current_embed.set_footer(text="Use ⬅️ and ➡️ to navigate.")
        description = ""
        for cmd, desc in commands.items():
            command_text = f"- __**{bot_prefix}{cmd}**__\n→ {desc}\n\n"

            if len(description) + len(command_text) > 1024:
                current_embed.description = description
                pages.append(current_embed)
                current_embed = discord.Embed(
                    title=f"{category_name} Commands" if category_name else "Help Menu",
                    color=discord.Color.blue()
                )
                current_embed.set_footer(text="Use ⬅️ and ➡️ to navigate.")
                description = command_text
            else:
                description += command_text
        current_embed.description = description
        pages.append(current_embed)
        return pages

    if category:
        lower_category = category.lower()
        lower_helps = {key.lower(): value for key, value in helps.items()}
        if lower_category in lower_helps:
            commands = lower_helps[lower_category]
            pages = create_embed_pages(commands, category.title())
        else:
            embed = discord.Embed(
                title="Category Not Found",
                description=f"Category '{category}' not found.\nUse `{bot_prefix}help` to see all available categories.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
    else:
        embed = discord.Embed(
            title="Help Menu",
            description=(
                    "**Basics:**\n"
                    "`<>` = required, `[]` = optional\n\n"
                    f"Use `{bot_prefix}help <category>` to view commands in a category.\n\n"
                    "**Available Categories:**\n" +
                    "\n".join(f"- {key}" for key in helps.keys())
            ),
            color=discord.Color.green()
        )
        pages = [embed]

    current_page = 0
    message = await ctx.send(embed=pages[current_page])

    if len(pages) > 1:
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

        def check(reaction, user):
            return (
                    user == ctx.author and
                    str(reaction.emoji) in ["⬅️", "➡️"] and
                    reaction.message.id == message.id
            )

        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
                await message.remove_reaction(reaction.emoji, user)

                if str(reaction.emoji) == "⬅️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=pages[current_page])
                elif str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                    current_page += 1
                    await message.edit(embed=pages[current_page])
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break


async def default_callback(interaction):
    await interaction.respond(f'Pressed Button: {interaction.data["custom_id"]}')


def check_for_updates():
    try:
        state = "Latest"
        devbuild = False
        latest_release = str(requests.get(f'{api}/get_latest').json()["latest_version"]).strip('V')
        current_version_number = current_version.strip('V')

        if '-dev-' in current_version_number:
            current_version_number = current_version_number.split('-')[0]
            devbuild = True

        if float(latest_release) > float(current_version_number):
            outdated = True
            state = "Outdated"
            logw(f'New version {latest_release} available!')
        else:
            outdated = False
        if devbuild:
            state = state + " Development Build"

        message = f"Running Current Version: {current_version} {state}"
        if outdated:
            message = message + f'\nNew version {latest_release} available!'
        return message
    except Exception as e:
        logw(f'Failed to check for updates due to an unexpected error: {e}')
        return f'Failed to check for updates due to an unexpected error: {e}'


if bot_config['check_for_updates']:
    log(check_for_updates())


def log_to_file(message, date_string, log_dir):
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, 'log.txt')
    with open(log_file_path, 'a', encoding='utf-8') as file:
        file.write(message + '\n')


def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)


try:
    with open("responses.json", "r") as f:
        responses = json.load(f)
except FileNotFoundError:
    responses = {}
    with open("responses.json", "w") as f:
        json.dump(responses, f)


async def check_message(message, keywords, caps):
    content = message.content if caps else message.content.lower()
    pattern = r'<@![0-9]+>|' + '|'.join(re.escape(keyword) for keyword in keywords)
    matches = re.findall(pattern, content)

    return len(matches) == len(keywords)


async def process_responses(message, responses):
    for key, response_data in responses.items():
        keywords = response_data['keywords']
        response = replace_placeholders(response_data['response'], message.author)
        caps = response_data.get('caps', False)

        if response_data.get('type', 'any') == "all":
            if await check_message(message, keywords, caps):
                await message.channel.send(response)
                break
        else:
            if any((keyword in message.content) if caps else (keyword.lower() in message.content.lower()) for keyword in
                   keywords):
                await message.channel.send(response)
                break


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    reaction_roles = server_configs.get(str(payload.guild_id), {}).get('reaction_roles', {})
    if str(payload.message_id) in reaction_roles:
        guild = bot.get_guild(payload.guild_id)
        role_id = reaction_roles[str(payload.message_id)].get(str(payload.emoji))
        if role_id:
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return
    reaction_roles = server_configs.get(str(payload.guild_id), {}).get('reaction_roles', {})
    if str(payload.message_id) in reaction_roles:
        guild = bot.get_guild(payload.guild_id)
        role_id = reaction_roles[str(payload.message_id)].get(str(payload.emoji))
        if role_id:
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.remove_roles(role)


when_voice_state_update_functions = []


def when_voice_state_update(function):
    when_voice_state_update_functions.append(function)
    return function


@bot.event
async def on_voice_state_update(member: discord.Member, before, after):
    for f in when_voice_state_update_functions:
        if inspect.iscoroutinefunction(f):
            await f(member, before, after)
        else:
            f(member, before, after)

    global guild_vcs, personal_vcs
    guild_id = str(member.guild.id)

    if server_configs.get(guild_id, {}).get("analytics", False):
        tz = pytz.utc
        now = datetime.now(tz)
        time_key = now.strftime("%Y-%m-%d %H:%M")

        server_configs.setdefault(guild_id, {}).setdefault("data", {}).setdefault("voice", {}).setdefault(
            str(member.id), 0)

        if before.channel is None and after.channel is not None:
            server_configs[guild_id]["data"]["voice"][str(member.id)] = now.timestamp()

        elif before.channel is not None and after.channel is None:
            join_time = server_configs[guild_id]["data"]["voice"].get(str(member.id), now.timestamp())
            total_time = now.timestamp() - join_time

            server_configs[guild_id]["data"].setdefault("voice_time", {}).setdefault(str(member.id), 0)
            server_configs[guild_id]["data"]["voice_time"][str(member.id)] += total_time  # Total VC time

            server_configs[guild_id]["data"].setdefault("voice_time_per_minute", {}).setdefault(time_key, 0)
            server_configs[guild_id]["data"]["voice_time_per_minute"][time_key] += total_time  # Minute tracking

            save_server_configs(server_configs)

    if bot_config['log']:
        date_string = ttime().strftime('%Y-%m-%d')
        time_string = ttime().strftime('%H-%M-%S')
        log_dir = os.path.join('Logs', date_string, sanitize_filename(member.guild.name), 'Voice States')

        if before.channel != after.channel:
            if before.channel is None:
                log_message = f'{member.guild.name} > {time_string} > {member.name} joined {after.channel.name}'
            elif after.channel is None:
                log_message = f'{member.guild.name} > {time_string} > {member.name} left {before.channel.name}'
            else:
                log_message = f'{member.guild.name} > {time_string} > {member.name} moved from {before.channel.name} to {after.channel.name}'
            log_to_file(log_message, date_string, log_dir)

    LOG_CHANNEL_ID = server_configs.get(guild_id, {}).get('voice_logs_channel', 0)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    log_type = 'voice'
    channel = before.channel.id if before.channel else after.channel.id
    server = guild_id
    if channel in server_configs.get(server, {}).get('logging_excluded', {}).get(log_type, []):
        return
    if log_channel:
        embed = discord.Embed(title="Voice State Update", color=discord.Color.blue())
        embed.set_author(name=member, icon_url=member.avatar.url)

        if before.channel != after.channel:
            if before.channel is None:
                embed.add_field(name="Voice Status", value=f"Joined {after.channel.mention}", inline=False)
            elif after.channel is None:
                embed.add_field(name="Voice Status", value=f"Left {before.channel.mention}", inline=False)
            else:
                embed.add_field(name="Voice Status",
                                value=f"Moved from {before.channel.mention} to {after.channel.mention}", inline=False)

        if before.self_mute != after.self_mute:
            embed.add_field(name="Mute", value="Muted" if after.self_mute else "Unmuted", inline=False)

        if before.self_deaf != after.self_deaf:
            embed.add_field(name="Deaf", value="Deafened" if after.self_deaf else "Undeafened", inline=False)

        if before.mute != after.mute:
            embed.add_field(name="Server Mute", value="Muted" if after.mute else "Unmuted", inline=False)

        if before.deaf != after.deaf:
            embed.add_field(name="Server Deaf", value="Deafened" if after.deaf else "Undeafened", inline=False)

        if before.self_stream != after.self_stream:
            embed.add_field(name="Stream", value="Started Streaming" if after.self_stream else "Stopped Streaming",
                            inline=False)

        if before.self_video != after.self_video:
            embed.add_field(name="Video", value="Enabled Video" if after.self_video else "Disabled Video", inline=False)

        if before.suppress != after.suppress:
            embed.add_field(name="Priority Speaker", value="Enabled" if after.suppress else "Disabled", inline=False)

        if before.requested_to_speak_at != after.requested_to_speak_at:
            embed.add_field(
                name="Request to Speak",
                value="Requested to Speak" if after.requested_to_speak_at else "Request Withdrawn",
                inline=False
            )

        if before.afk != after.afk:
            embed.add_field(name="AFK Status", value="Moved to AFK" if after.afk else "Left AFK", inline=False)

        embed.timestamp = discord.utils.utcnow()
        await log_channel.send(embed=embed)

    if guild_id in guild_vcs:
        if after.channel and str(after.channel.id) in guild_vcs[guild_id]:
            join_to_create_id = str(after.channel.id)

            if member.id in personal_vcs and personal_vcs[member.id].guild.id == int(guild_id):
                await member.move_to(personal_vcs[member.id])
                return

            user_limit = guild_vcs[guild_id][join_to_create_id]["user_limit"]

            if user_limit == 1:
                overwrites = {
                    member.guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
                    member: discord.PermissionOverwrite(view_channel=True, connect=True)
                }
            else:
                overwrites = {
                    member.guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True),
                    member: discord.PermissionOverwrite(view_channel=True, connect=True)
                }

            category = after.channel.category
            vc = await member.guild.create_voice_channel(f"{member.display_name}'s Room", overwrites=overwrites,
                                                         category=category,
                                                         user_limit=user_limit if user_limit > 0 else None)

            await member.move_to(vc)

            personal_vcs[member.id] = vc
            save_personal_vcs()

        if before.channel and before.channel.id in [vc.id for vc in personal_vcs.values()]:
            if len(before.channel.members) == 0:
                owner_id = [user_id for user_id, vc in personal_vcs.items() if vc.id == before.channel.id]
                if owner_id:
                    await before.channel.delete()
                    del personal_vcs[owner_id[0]]
                    save_personal_vcs()

        for join_to_create_id in list(guild_vcs[guild_id].keys()):
            if not bot.get_channel(int(join_to_create_id)):
                del guild_vcs[guild_id][join_to_create_id]
                save_vc_data()


@bot.event
async def on_message_edit(before, after):
    guild_id = str(before.guild.id) if before.guild else 0
    if before.content == after.content:
        return
    LOG_CHANNEL_ID = server_configs.get(guild_id, {}).get('message_logs_channel', 0)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    log_type = 'text'
    channel = before.channel.id
    server = guild_id
    if channel in server_configs.get(server, {}).get('logging_excluded', {}).get(log_type, []):
        return
    if log_channel:
        embed = discord.Embed(title="Message Edited", color=discord.Color.gold())
        embed.set_author(name=before.author, icon_url=before.author.avatar.url)
        embed.add_field(name="Before", value=before.content or "None", inline=False)
        embed.add_field(name="After", value=after.content or "None", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.timestamp = before.created_at
        await log_channel.send(embed=embed)


@bot.event
async def on_message_delete(message):
    guild_id = str(message.guild.id) if message.guild else 0
    LOG_CHANNEL_ID = server_configs.get(guild_id, {}).get('message_logs_channel', 0)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    log_type = 'text'
    channel = message.channel.id
    server = guild_id
    if channel in server_configs.get(server, {}).get('logging_excluded', {}).get(log_type, []):
        return
    if log_channel:
        embed = discord.Embed(title="Message Deleted", color=discord.Color.red())
        embed.set_author(name=message.author, icon_url=message.author.avatar.url)
        embed.add_field(name="Content", value=message.content or "None", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.timestamp = message.created_at
        await log_channel.send(embed=embed)


@bot.event
async def on_bulk_message_delete(messages):
    guild_id = str(messages[0].guild.id)
    LOG_CHANNEL_ID = server_configs.get(guild_id, {}).get('message_logs_channel', 0)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    log_type = 'text'
    channel = messages[0].channel.id
    server = guild_id
    if channel in server_configs.get(server, {}).get('logging_excluded', {}).get(log_type, []):
        return
    if log_channel and messages:
        first_message = messages[0]
        embed = discord.Embed(
            title="Bulk Messages Deleted",
            color=discord.Color.red(),
            description=f"{len(messages)} messages were deleted in {first_message.channel.mention}"
        )
        embed.timestamp = discord.utils.utcnow()
        await log_channel.send(embed=embed)


@bot.event
async def on_member_update(before, after):
    if bot_config['log']:
        date_string = ttime().strftime('%Y-%m-%d')
        time_string = ttime().strftime('%H-%M-%S')
        log_dir = os.path.join('Logs', date_string, sanitize_filename(after.guild.name), 'Member Updates')

        if before.roles != after.roles:
            removed_roles = [role for role in before.roles if role not in after.roles]
            added_roles = [role for role in after.roles if role not in before.roles]

            log_message = f'{after.guild.name} > {time_string} > {after.name} roles updated. '

            if removed_roles:
                log_message += f"Removed roles: {', '.join([role.name for role in removed_roles])}. "
            if added_roles:
                log_message += f"Added roles: {', '.join([role.name for role in added_roles])}. "
            if not (added_roles or removed_roles):
                log_message += "No changes in roles."
            log_to_file(log_message, date_string, log_dir)
        if before.name != after.name:
            log_message = f'{after.guild.name} > {time_string} > Username updated. Before: {before.name}, After: {after.name}'
            log_to_file(log_message, date_string, log_dir)


user_violations = defaultdict(list)


def contains_banned_word(message, guild_id):
    bannable_words = server_configs.get(str(guild_id), {}).get("bannable_words", [])
    words = message.split()

    for pattern in bannable_words:
        if pattern.startswith("*") and pattern.endswith("*"):
            regex = re.compile(re.escape(pattern.strip("*")), re.IGNORECASE)
        elif pattern.startswith("*"):
            regex = re.compile(re.escape(pattern.strip("*")) + r"$", re.IGNORECASE)
        elif pattern.endswith("*"):
            regex = re.compile(r"^" + re.escape(pattern.strip("*")), re.IGNORECASE)
        else:
            regex = re.compile(rf"\b{re.escape(pattern)}\b", re.IGNORECASE)
        if any(regex.search(word) for word in words):
            return True

    return False


async def take_action(user, guild, violations, current_time):
    guild_id = str(guild.id)

    for action_key, action_config in server_configs.get(guild_id, {}).get("action_settings", {}).items():
        threshold = int(action_key)
        timeframe = action_config.get("timeframe", 60)

        valid_violations = [t for t in user_violations[user.id] if t > current_time - timeframe]
        if len(valid_violations) >= threshold:
            action = action_config["action"]
            if action == "warn":
                msg = replace_placeholders(action_config.get("message", "You have been warned for using banned words."),
                                           user)
                try:
                    await user.send(msg)
                except:
                    pass
            elif action == "mute":
                mute_role = discord.utils.get(guild.roles, name="Muted")
                if mute_role:
                    await user.add_roles(mute_role)
            elif action == "ban":
                await guild.ban(user, reason="Repeated use of banned words.")
            break


message_log = {}


@when_message
async def func_chat_cooldown(message):
    if isinstance(message.channel, discord.DMChannel):
        return
    guild_id = str(message.channel.guild.id)
    TRACKED_CHANNELS = server_configs.get(guild_id, {}).get('cooldown_channels', [])
    MESSAGE_WINDOW = server_configs.get(guild_id, {}).get('cooldown_message_window', 10)
    MESSAGE_THRESHOLD = server_configs.get(guild_id, {}).get('cooldown_message_threshold', 10)
    MINIMUM_THRESHOLD = server_configs.get(guild_id, {}).get('cooldown_minimum_threshold', 2)
    MAX_SLOWMODE = server_configs.get(guild_id, {}).get('cooldown_max', 5)
    MIN_SLOWMODE = server_configs.get(guild_id, {}).get('cooldown_min', 0)

    if message.author.bot or message.channel.id not in TRACKED_CHANNELS:
        return

    channel = message.channel
    now = ttime()

    if channel.id not in message_log:
        message_log[channel.id] = deque()

    log = message_log[channel.id]
    log.append(now)

    while log and (now - log[0]).total_seconds() > MESSAGE_WINDOW:
        log.popleft()

    message_count = len(log)
    if message_count >= MESSAGE_THRESHOLD:
        cooldown = min(MAX_SLOWMODE, message_count // 2)
    elif message_count < MINIMUM_THRESHOLD:
        return
    else:
        cooldown = MIN_SLOWMODE

    return await channel.edit(slowmode_delay=cooldown)


@when_message
async def level_rewards_engine(message):
    if message.author.bot or isinstance(message.channel, discord.DMChannel):
        return

    guild_id = str(message.guild.id)
    user_id = str(message.author.id)

    server_config = server_configs.setdefault(guild_id, {})
    level_config = server_config.get('level_rewards_config', {})

    if not level_config.get('enabled', False):
        return

    if message.channel.id in level_config.get('excluded_channels', []):
        return

    server_config.setdefault('user_messages', {})
    server_config['user_messages'][user_id] = server_config['user_messages'].get(user_id, 0) + 1
    save_server_configs(server_configs)

    message_count = server_config['user_messages'][user_id]
    reward_roles = {int(k): v for k, v in level_config.get('roles', {}).items()}

    if message_count in reward_roles:
        role = message.guild.get_role(reward_roles[message_count])
        if role:
            await message.author.add_roles(role, reason="Level reward reached")
            await message.channel.send(
                f'🎉 Congrats {message.author.mention}, you have been given the **{role.name}** role!'
            )


@bot.event
async def on_message(message: discord.Message):
    await bot.process_commands(message)
    for f in when_message_functions:
        if inspect.iscoroutinefunction(f):
            await f(message)
        else:
            f(message)

    guild_id = str(message.guild.id) if message.guild else 0
    if server_configs.get(guild_id, {}).get("analytics", False):
        tz = pytz.utc
        now = datetime.now(tz)
        date_key = now.strftime("%Y-%m-%d")
        time_key = now.strftime("%Y-%m-%d %H:%M")
        server_configs.setdefault(guild_id, {}).setdefault("data", {}).setdefault("messages", {}).setdefault(date_key,
                                                                                                             0)
        server_configs[guild_id]["data"]["messages"][date_key] += 1

        server_configs[guild_id]["data"].setdefault("messages_ per_minute", {}).setdefault(time_key, 0)
        server_configs[guild_id]["data"]["messages_per_minute"][time_key] += 1

        server_configs[guild_id]["data"].setdefault("active_users", {}).setdefault(str(message.author.id), 0)
        server_configs[guild_id]["data"]["active_users"][str(message.author.id)] += 1

        save_server_configs(server_configs)

    guild_id = str(message.guild.id if message.guild else None)
    violation_timeframe = server_configs.get(guild_id, {}).get("violation_timeframe", 60)

    if contains_banned_word(message.content, guild_id):
        ctx = await bot.get_context(message)
        if ctx.valid:
            return

        await message.delete()
        embed = discord.Embed(
            title="Banned Word Detected",
            description=f"{message.author.mention}, your message contained a banned word!",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)

        current_time = message.created_at.timestamp()
        user_violations[message.author.id].append(current_time)

        user_violations[message.author.id] = [t for t in user_violations[message.author.id] if
                                              t > current_time - violation_timeframe]

        await take_action(message.author, message.guild, len(user_violations[message.author.id]), current_time)

    if not message.content.startswith(bot_config['prefix']):
        if message.author.id in user_language_settings:
            target_lang = user_language_settings[message.author.id]
            if target_lang != 'none':
                try:
                    translated = await translator.translate(message.content, dest=target_lang)
                    await message.reply(f"[Translated to {SUPPORTED_LANGUAGES[target_lang]}]: {translated.text}")
                except Exception as e:
                    await message.channel.send(f"Translation failed: {str(e)}")

    user_id_str = str(message.author.id)
    if not message.content.startswith(f'{bot.command_prefix}afk'):
        if user_id_str in afk_users:
            afk_data = afk_users.pop(user_id_str)
            with open(afk_file, 'w') as f:
                json.dump(afk_users, f, indent=4)

            afk_start_time = datetime.fromisoformat(afk_data['time'])
            afk_duration = ttime() - afk_start_time

            def format_timedelta(td):
                seconds = int(td.total_seconds())
                periods = [
                    ('day', 60 * 60 * 24),
                    ('hour', 60 * 60),
                    ('minute', 60),
                    ('second', 1)
                ]
                parts = []
                for period_name, period_seconds in periods:
                    if seconds > period_seconds or period_name == 'second':
                        period_value, seconds = divmod(seconds, period_seconds)
                        if period_value == 1:
                            parts.append(f"{period_value} {period_name}")
                        elif period_value > 1:
                            parts.append(f"{period_value} {period_name}s")
                return ", ".join(parts)

            afk_duration_str = format_timedelta(afk_duration)
            mention_count = len(afk_data['mentions'])

            mention_details = "\n".join([
                f"{mention['author']} in {mention['channel']}" for mention in afk_data['mentions']
            ]) if mention_count > 0 else "No mentions."

            await message.channel.send(
                f"{message.author.mention} is no longer AFK. You were AFK for {afk_duration_str}.\n"
                f"You were mentioned {mention_count} times:\n{mention_details}"
            )

        if message.mentions:
            if message.author.id != bot.user.id:
                for mention in message.mentions:
                    if str(mention.id) in afk_users:
                        afk_message = afk_users[str(mention.id)]["message"]
                        afk_users[str(mention.id)]["mentions"].append({
                            "author": str(message.author),
                            "channel": f'[{str(message.channel)}]({message.jump_url})'
                        })
                        with open(afk_file, 'w') as f:
                            json.dump(afk_users, f, indent=4)
                        await message.channel.send(f"{mention.name} is AFK: {afk_message}")

    await process_responses(message, responses)

    if bot_config['log']:
        date_string = ttime().strftime('%Y-%m-%d')
        time_string = ttime().strftime('%H-%M-%S')

        if message.content is None:
            msg = ''
        else:
            msg = message.content

        if isinstance(message.channel, discord.DMChannel):
            author_name = sanitize_filename(message.author.name)
            log_dir = os.path.join('Logs', date_string, 'DMs', author_name)
            log_message = f"[DM] {message.author} > {time_string}: {msg}"
        else:
            server_name = sanitize_filename(message.guild.name)
            channel_name = sanitize_filename(message.channel.name)
            log_dir = os.path.join('Logs', date_string, server_name, channel_name)
            log_message = f'{server_name} > #{channel_name} > {time_string} > {message.author.name}: {msg}'

        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, 'log.txt')

        with open(log_file_path, 'a', encoding='utf-8') as file:
            file.write(log_message + '\n')

            for attachment in message.attachments:
                file_ext = attachment.filename.split('.')[-1].lower()
                if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov', 'mp3', 'wav', 'zip', 'rar', 'ico',
                                'txt']:
                    attachment_dir = os.path.join(log_dir, 'attachments')
                    os.makedirs(attachment_dir, exist_ok=True)
                    file_name = f'{time_string}_{sanitize_filename(message.author.name)}_{sanitize_filename(attachment.filename)}'
                    file_path = os.path.join(attachment_dir, file_name)
                    await attachment.save(file_path)
                    file.write(f'{attachment.url} > {file_path}\n')

            for embed in message.embeds:
                embed_log_message = "\nEmbed:"
                embed_log_message += f"\nTitle: {embed.title if embed.title else ''}"
                embed_log_message += f"\nDescription: {embed.description if embed.description else ''}"
                for field in embed.fields:
                    embed_log_message += f"\nField - Name: {field.name if field.name else ''}, Value: {field.value if field.value else ''}"
                embed_log_message += "\n"
                file.write(embed_log_message)

            if message.attachments or message.embeds:
                file.write('\n')


@bot.event
async def on_rate_limit(retry_after: float):
    if retry_after > 5 * 60:
        logc(f"⚠️ Global rate limit hit! ({retry_after:.2f} seconds.) Shutting down bot!!")
        await bot.close()
    else:
        loge(f"Rate limited! Retrying in {retry_after:.2f} seconds.")
        await asyncio.sleep(retry_after)


async def example_call_back(interaction):
    await interaction.respond(f'Hello! {interaction.user.mention}, this is an example button!')


async def example_select_menu_callback(interaction: discord.Interaction):
    selected_values = interaction.data['values']
    await interaction.response.send_message(f"You selected: {', '.join(selected_values)}")


async def example_modal_callback(interaction: discord.Interaction, modal: ui.Modal):
    input_1 = modal.children[0].value
    input_2 = modal.children[1].value
    await interaction.response.send_message(f"Received: Input 1 = {input_1}, Input 2 = {input_2}")


eg_button = {
    'label': 'example',
    'style': discord.ButtonStyle.danger,
    'custom_id': 'example',
    'callback': example_call_back,
    'emoji': '🥳'
}
button_configurations.append(eg_button)


@bot.command()
async def example_select_view(ctx: commands.Context):
    options = [
        SelectOption(label="Option 1", value="1"),
        SelectOption(label="Option 2", value="2")
    ]

    view = create_select_view(placeholder="Choose an option", options=options, custom_id="select_menu_1",
                              callback=example_select_menu_callback)
    await ctx.send("Please choose an option:", view=view)


@bot.command()
async def example_modal(ctx: discord.ApplicationContext):
    inputs = [
        discord.ui.InputText(label="Input 1", placeholder="Enter something...", custom_id="input_1"),
        discord.ui.InputText(label="Input 2", placeholder="Enter something else...", custom_id="input_2")
    ]

    modal = create_modal_view(title="Your Modal Title", inputs=inputs, custom_id="modal_1",
                              callback=example_modal_callback)

    await ctx.send_modal(modal)


def register_on_ready_extension(name, data):
    if not os.path.isfile(f'{plugins_folder}/on_ready_{name}.ext'):
        with open(f'{plugins_folder}/on_ready_{name}.ext', 'w') as f:
            f.write(data)


def register_on_message_extension(name, data):
    if not os.path.isfile(f'{plugins_folder}/on_message_{name}.ext'):
        with open(f'{plugins_folder}/on_message_{name}.ext', 'w') as f:
            f.write(data)




plugin_ = {}

if __name__ == '__main__' and bot_config['plugins']:
    if not os.path.exists('plugins'):
        os.mkdir('plugins')

    plugin_dirs = ['plugins']
    if os.path.exists('dev-plugins'):
        plugin_dirs.append('dev-plugins')

    for folder in plugin_dirs:
        plugin_files = [
            f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f)) and f.endswith('.py')
        ]

        for plugin_file in plugin_files:
            plugin_name = plugin_file[:-3]  # Strip .py
            plugin_path = os.path.join(folder, plugin_file)

            with open(plugin_path, encoding='utf-8') as f:
                try:
                    lines = f.readlines()
                    filtered_code = '\n'.join(
                        line for line in lines if not line.strip().startswith('from main import')
                    )

                    # Create a shared but isolated namespace using a copy of globals
                    plugin_namespace = globals().copy()
                    plugin_namespace.update({
                        '__name__': plugin_name,
                        'plugin_': plugin_,
                        'main': globals()
                    })

                    exec(compile(filtered_code, plugin_path, 'exec'), plugin_namespace)

                    # Store the plugin's namespace in plugin_
                    plugin_[plugin_name] = plugin_namespace

                    log(f'Successfully loaded plugin: {plugin_file}')
                except Exception as e:
                    logerr(f'Error loading plugin: {plugin_file}\n{e}')




@bot.event
async def on_ready():
    check_timers.start()
    for f in when_bot_ready_functions:
        if inspect.iscoroutinefunction(f):
            await f()
        else:
            f()

    bot.cached_invites = {}
    for guild in bot.guilds:
        bot.cached_invites[guild.id] = await guild.invites()

    for button_config in button_configurations:
        button_views[button_config['custom_id']] = create_button_view(
            label=button_config['label'],
            style=button_config['style'],
            custom_id=button_config['custom_id'],
            callback=button_config['callback'],
            emoji=button_config['emoji'] if 'emoji' in button_config else None,
            disabled=button_config['disabled'] if 'disabled' in button_config else False
        )

        bot.add_view(button_views[button_config['custom_id']])


    bot.add_view(CreateTicketView(bot))
    bot.add_view(CloseTicketView(bot))
    bot.add_view(CloseTicketRequestView(bot))
    bot.add_view(DeleteTicketView(bot))

    for guild_id, config in server_configs.items():
        profiles = config.get("ticket_profiles", {})
        for profile in profiles:
            view = CreateTicketView(bot, profile=profile)
            bot.add_view(view)

    load_vc_data()
    load_personal_vcs()


    log(f'Logged in as {bot.user} (ID: {bot.user.id})')

    if not bot.guilds:
        client_id = bot.user.id
        logw(
            f'Bot not in any servers \nOAuth link: https://discord.com/oauth2/authorize?client_id={client_id}&permissions=8&scope=bot')

    log('Starting Post Startup Setup')
    for guild in bot.guilds:
        bot_top_role = guild.get_member(bot.user.id).top_role
        if not any(role.name == "Muted" for role in guild.roles):
            log(f"Creating 'Muted' role in guild {guild}")
            permissions = discord.Permissions(send_messages=False, speak=False)
            mute_role = await guild.create_role(name="Muted", permissions=permissions)
            try:
                if mute_role.position >= bot_top_role.position:
                    raise discord.HTTPException(None, "Role hierarchy issue")
                await mute_role.edit(position=bot_top_role.position - 1)
            except discord.HTTPException as e:
                logw(f"Failed to move 'Muted' role in {guild.name}: {e}")
                log("Retrying hierarchy adjustment...")
                bot_controlled_roles = [role for role in guild.roles if role.managed]
                for role in bot_controlled_roles:
                    if role.position >= bot_top_role.position:
                        await role.edit(position=bot_top_role.position - 1)
            for channel in guild.channels:
                log(f"Setting 'Muted' permissions in guild {guild} channel {channel}")
                try:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False)
                except Exception as e:
                    logw(e)
        if not server_configs.get(str(guild.id)):
            server_configs[str(guild.id)] = {}

        server_config = server_configs.get(str(guild.id))
        if server_config:
            if server_config.get('member_count_channel'):
                channel = bot.get_channel(int(server_config.get('member_count_channel')))
                if not channel:
                    server_configs[str(guild.id)]['member_count_channel'] = None
                    save_server_configs(server_configs)
                else:
                    member_count = len(channel.guild.members)
                    await channel.edit(name=f'Members: {member_count}')

    await bot.sync_commands()

    log('Post Startup Finished!')


when_bot_join_guild_functions = []


def when_bot_join_guild(function):
    when_bot_join_guild_functions.append(function)
    return function


@bot.event
async def on_guild_join(guild):
    for function in when_bot_join_guild_functions:
        function(guild)

    bot_top_role = guild.get_member(bot.user.id).top_role
    if not any(role.name == "Muted" for role in guild.roles):
        log(f"Creating 'Muted' role in guild {guild}")
        permissions = discord.Permissions(send_messages=False, speak=False)
        mute_role = await guild.create_role(name="Muted", permissions=permissions)
        try:
            if mute_role.position >= bot_top_role.position:
                raise discord.HTTPException(None, "Role hierarchy issue")
            await mute_role.edit(position=bot_top_role.position - 1)
        except discord.HTTPException as e:
            logw(f"Failed to move 'Muted' role in {guild.name}: {e}")
            log("Retrying hierarchy adjustment...")
            bot_controlled_roles = [role for role in guild.roles if role.managed]
            for role in bot_controlled_roles:
                if role.position >= bot_top_role.position:
                    await role.edit(position=bot_top_role.position - 1)
        for channel in guild.channels:
            log(f"Setting 'Muted' permissions in guild {guild} channel {channel}")
            try:
                await channel.set_permissions(mute_role, send_messages=False, speak=False)
            except Exception as e:
                logw(e)
    if not server_configs.get(str(guild.id)):
        server_configs[str(guild.id)] = {}


def create_restart_script():
    try:
        filename = os.path.abspath(sys.argv[0])
        script_content = f"""\
import os
import sys
import time
import subprocess

def restart_bot(script_name):
    \"\"\"Restart the bot using subprocess with error handling\"\"\"
    python_exec = sys.executable
    if not os.path.exists(python_exec):
        print(f"[ERROR] Python executable not found: {{python_exec}}")
        return
    try:
        print(f"[INFO] Restarting {{script_name}} with {{python_exec}}...")
        subprocess.run([python_exec, script_name])
    except Exception as e:
        print(f"[ERROR] Failed to restart: {{e}}")

if __name__ == "__main__":
    print("[INFO] Waiting before restart...")
    time.sleep(2)
    target_script = os.environ.get("MAIN_SCRIPT", {repr(filename)})
    restart_bot(target_script)
"""
        with open("restart_script.py", "w", encoding="utf-8") as f:
            f.write(script_content)
        log("Restart script created successfully.")
    except Exception as e:
        logerr(f"Could not create restart script: {e}")


def retry_after_message(t):
    waiting = True
    time_remaining = t
    while waiting:
        time_remaining -= 1
        if time_remaining < 0:
            waiting = False
        if time_remaining > 60:
            timestring = f'{time_remaining / 60:.2f} Minutes'
        else:
            timestring = f'{time_remaining} Seconds'
        log(f'Retrying in {timestring}')
        time.sleep(1)

bot_exit_code = 0

async def save_state_and_exit(exit_code: int = 0, already_exiting=False):
    global is_exiting, bot_exit_code
    if is_exiting:
        return
    is_exiting = True
    bot_exit_code = exit_code
    log(f"Bot is shutting down with exit code {exit_code}...")
    for f in when_bot_shutdown_functions:
        if inspect.iscoroutinefunction(f):
            await f()
        else:
            f()
    await bot.close()
    if not already_exiting:
        sys.exit(exit_code)


async def restart_bot():
    logger.info("Bot is restarting...")
    subprocess.Popen([sys.executable, "restart_script.py"])
    await save_state_and_exit()


def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}. Exiting gracefully...")

    async def _safe_shutdown():
        try:
            await save_state_and_exit()
        except SystemExit:
            pass
        except Exception as e:
            logerr(f"Error during shutdown: {e}")

    asyncio.create_task(_safe_shutdown())

atexit.register(lambda: suppress_system_exit())

def suppress_system_exit():
    global is_exiting
    if not is_exiting:
        try:
            asyncio.run(save_state_and_exit(already_exiting=True))
        except SystemExit:
            pass
        except Exception as e:
            logerr(f"Atexit shutdown failed: {e}")


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def countdown(retry_after):
    for remaining in range(int(retry_after), 0, -1):
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02}:{minutes:02}:{seconds:02}"  # Format as HH:MM:SS

        logger.warning(f"Retrying in {time_str} (HH:MM:SS)...")
        await asyncio.sleep(1)


def run_bot():
    create_restart_script()
    while not is_exiting:
        try:
            bot.loop.run_until_complete(bot.start(bot_config['bot_token']))
            logger.info('Bot Closed!')
        except discord.HTTPException as e:
            if e.status == 429:
                retry_after = float(e.response.headers.get('Retry-After', 5))
                logger.warning(f'Rate limited! Waiting for {retry_after} seconds...')
                asyncio.run(countdown(retry_after))
            else:
                logger.error(f'An error occurred: {e}')
        except Exception as e:
            logger.error(f'An unexpected error occurred: {e}')
            break

    exit_code = bot_exit_code
    log(f"Exiting main loop with code {exit_code}...")
    os._exit(exit_code)


if __name__ == '__main__':
    try:
        run_bot()
    except SystemExit:
        pass
    except Exception as e:
        logerr(f"Unhandled exception: {e}")

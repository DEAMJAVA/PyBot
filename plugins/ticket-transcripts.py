from flask import Flask, render_template_string, send_from_directory, abort, session, redirect, request
from functools import wraps
import requests
import os
import re
import html
import json
from threading import Thread

# === Plugin-specific variables ===
TT_PLUGIN_NAME = "tickettranscripts"
TT_TRANSCRIPTS_DIR = os.path.abspath("transcripts")
TT_TEMPLATE_DIR = os.path.abspath("templates")
TT_CONFIG_FILE = os.path.abspath("plugins/TicketTranscripts/transcriptconfig.json")

# === Load configuration ===
os.makedirs(os.path.dirname(TT_CONFIG_FILE), exist_ok=True)

# Default config structure
TT_default_config = {
    "port": 25494,
    "require_auth": False,
    "auth": {
        "enabled": False,
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "redirect_uri": "http://localhost:25494/callback",
    },
    "restrict_to_participants": False
}

if not os.path.exists(TT_CONFIG_FILE):
    with open(TT_CONFIG_FILE, "w") as f:
        json.dump(TT_default_config, f, indent=4)

# Load config
with open(TT_CONFIG_FILE, "r") as f:
    TT_config = json.load(f)

# Extract config variables
TT_PORT = TT_config.get("port", 25494)
TT_REQUIRE_AUTH = TT_config.get("require_auth", False)
TT_RESTRICT_TO_PARTICIPANTS = TT_config.get("restrict_to_participants", False)

# OAuth2 config
TT_AUTH_CONFIG = TT_config.get("auth", {})
TT_AUTH_ENABLED = TT_AUTH_CONFIG.get("enabled", False)
TT_CLIENT_ID = TT_AUTH_CONFIG.get("client_id", "")
TT_CLIENT_SECRET = TT_AUTH_CONFIG.get("client_secret", "")
TT_REDIRECT_URI = TT_AUTH_CONFIG.get("redirect_uri", "")

# === Ensure directories ===
os.makedirs(TT_TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(TT_TEMPLATE_DIR, exist_ok=True)

# === Default templates ===
TT_default_templates = {
    "TT_index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Servers</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #2c2f33;
            color: #ffffff;
            margin: 0;
            padding: 0;
        }

        header {
            background-color: #23272a;
            text-align: center;
            padding: 30px 20px;
            border-bottom: 2px solid #202225;
        }

        header h1 {
            margin: 0;
            font-size: 28px;
        }

        .container {
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
        }

        .search-container {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }

        .search-container input {
            width: 100%;
            max-width: 400px;
            padding: 12px 16px;
            border-radius: 8px;
            border: none;
            background-color: #40444b;
            color: white;
            font-size: 16px;
            transition: box-shadow 0.2s;
        }

        .search-container input:focus {
            outline: none;
            box-shadow: 0 0 8px rgba(114, 137, 218, 0.6);
        }

        h2 {
            text-align: center;
            font-weight: 500;
            margin-bottom: 20px;
            color: #ccc;
        }

        .server-list {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
            padding: 0;
        }

        .server-list li {
            list-style: none;
        }

        .server-list a {
            display: inline-block;
            background-color: #7289da;
            color: white;
            padding: 14px 26px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 500;
            text-decoration: none;
            transition: background-color 0.3s, transform 0.2s;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        }

        .server-list a:hover {
            background-color: #5b6eae;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <header>
        <h1>Available Servers</h1>
        {% if not session.get('user_id') %}
        <div style="margin-top: 10px;">
          <a href="/login" style="
              display: inline-block;
              padding: 10px 18px;
              background-color: #5865f2;
              color: white;
              border-radius: 8px;
              text-decoration: none;
              font-weight: 500;
              font-size: 15px;
              transition: background-color 0.2s ease;
          " onmouseover="this.style.backgroundColor='#4752c4'" onmouseout="this.style.backgroundColor='#5865f2'">
            🔐 Login with Discord
          </a>
        </div>
        {% else %}
        <div style="margin-top: 10px;">
          <span style="color: #ccc;">✅ Logged in as <strong>{{ session['username'] }}</strong></span>
          <a href="/logout" style="
              display: inline-block;
              margin-left: 12px;
              padding: 6px 12px;
              background-color: #ff5c5c;
              color: white;
              border-radius: 6px;
              text-decoration: none;
              font-weight: 500;
              font-size: 14px;
              transition: background-color 0.2s ease;
          " onmouseover="this.style.backgroundColor='#e04848'" onmouseout="this.style.backgroundColor='#ff5c5c'">Logout</a>
        </div>
        {% endif %}
    </header>

    <div class="container">
        <div class="search-container">
            <input type="text" id="serverSearch" placeholder="Search for a server..." oninput="searchServers()">
        </div>

        <h2>Select a Server</h2>
        <ul class="server-list" id="serverList">
        {% for server in servers %}
            <li><a href="/{{ server }}/" class="server-item">🌐 {{ server }}</a></li>
        {% endfor %}
        </ul>
    </div>

    <script>
        function searchServers() {
            const searchQuery = document.getElementById("serverSearch").value.toLowerCase();
            const servers = document.querySelectorAll(".server-item");
            servers.forEach(server => {
                const serverName = server.textContent.toLowerCase();
                server.parentElement.style.display = serverName.includes(searchQuery) ? "block" : "none";
            });
        }
    </script>
</body>
</html>
''',

    "TT_server.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>{{ server }} Transcripts</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #2c2f33;
            color: #fff;
            margin: 0;
            padding: 0;
        }

        header {
            background-color: #23272a;
            padding: 30px 20px;
            text-align: center;
            border-bottom: 2px solid #202225;
        }

        header h1 {
            margin: 0;
            font-size: 28px;
            color: #ffffff;
        }

        .container {
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
        }

        .search-container {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }

        .search-container input {
            width: 100%;
            max-width: 400px;
            padding: 12px 16px;
            border-radius: 8px;
            border: none;
            background-color: #40444b;
            color: white;
            font-size: 16px;
            transition: box-shadow 0.2s;
        }

        .search-container input:focus {
            outline: none;
            box-shadow: 0 0 8px rgba(88, 101, 242, 0.6);
        }

        h2 {
            text-align: center;
            font-weight: 500;
            margin-bottom: 20px;
            color: #ccc;
        }

        .transcript-list {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
            padding: 0;
        }

        .transcript-list li {
            list-style: none;
        }

        .transcript-list a {
            display: inline-block;
            background-color: #5865f2;
            color: white;
            padding: 14px 26px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 500;
            text-decoration: none;
            transition: background 0.3s, transform 0.2s;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        }

        .transcript-list a:hover {
            background-color: #4752c4;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <header>
        <h1>{{ server }} Transcripts</h1>
        {% if not session.get('user_id') %}
        <div style="margin-top: 10px;">
          <a href="/login" style="
              display: inline-block;
              padding: 10px 18px;
              background-color: #5865f2;
              color: white;
              border-radius: 8px;
              text-decoration: none;
              font-weight: 500;
              font-size: 15px;
              transition: background-color 0.2s ease;
          " onmouseover="this.style.backgroundColor='#4752c4'" onmouseout="this.style.backgroundColor='#5865f2'">
            🔐 Login with Discord
          </a>
        </div>
        {% else %}
        <div style="margin-top: 10px;">
          <span style="color: #ccc;">✅ Logged in as <strong>{{ session['username'] }}</strong></span>
          <a href="/logout" style="
              display: inline-block;
              margin-left: 12px;
              padding: 6px 12px;
              background-color: #ff5c5c;
              color: white;
              border-radius: 6px;
              text-decoration: none;
              font-weight: 500;
              font-size: 14px;
              transition: background-color 0.2s ease;
          " onmouseover="this.style.backgroundColor='#e04848'" onmouseout="this.style.backgroundColor='#ff5c5c'">Logout</a>
        </div>
        {% endif %}
    </header>

    <div class="container">
        <div class="search-container">
            <input type="text" id="transcriptSearch" placeholder="Search for a transcript..." oninput="searchTranscripts()">
        </div>

        <h2>Select a Transcript</h2>
        <ul class="transcript-list" id="transcriptList">
        {% for transcript in transcripts %}
            {% set parts = transcript.split('-') %}
            {% set ticket_part = parts[0] ~ '-' ~ parts[1] %}
            {% set username_part = parts[2] %}
            <li>
                <a href="/{{ server }}/{{ transcript }}" class="transcript-item">
                    🎫 {{ ticket_part }} &mdash; 👤 {{ username_part }}
                </a>
            </li>
        {% endfor %}
        </ul>
    </div>

    <script>
        function searchTranscripts() {
            const query = document.getElementById("transcriptSearch").value.toLowerCase();
            const items = document.querySelectorAll(".transcript-item");
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.parentElement.style.display = text.includes(query) ? "block" : "none";
            });
        }
    </script>
</body>
</html>'''
}

def login_required_if_enabled(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if TT_REQUIRE_AUTH and TT_AUTH_ENABLED:
            if 'user_id' not in session:
                return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def extract_transcript_metadata(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            html_text = f.read()

        match = re.search(
            r'<script type="application/json" id="transcript-metadata">\s*(.*?)\s*</script>',
            html_text,
            re.DOTALL
        )
        if not match:
            return None
        metadata_raw = match.group(1)
        return json.loads(metadata_raw)
    except Exception as e:
        print("Error extracting metadata JSON:", e)
        return None

def extract_participant_ids_from_transcript(path):
    try:

        metadata = extract_transcript_metadata(path)
        if not metadata:
            return None

        participant_ids = [str(p['id']) for p in metadata.get("participants", [])]
        return participant_ids
    except Exception as e:
        print("Error parsing participant IDs:", e)
        return None


def is_user_authorized_to_view(file_path):
    if not (TT_AUTH_ENABLED and TT_REQUIRE_AUTH and TT_RESTRICT_TO_PARTICIPANTS):
        return True

    if TT_REQUIRE_AUTH and 'user_id' not in session:
        return False

    user_id = int(session['user_id'])

    metadata = extract_transcript_metadata(file_path)
    if not metadata:
        return False

    guild_id = str(metadata.get("guild", {}).get("id", 0))
    if not guild_id:
        return False

    guild = bot.get_guild(int(guild_id))
    if not guild:
        return False

    member = guild.get_member(user_id)
    if not member:
        return False

    author_id = user_id

    # Ensure server config exists
    if not server_configs.get(guild_id):
        server_configs[guild_id] = {'owners': [], 'authorized_users': []}
        save_server_configs(server_configs)

    if not server_configs[guild_id].get('owners'):
        server_configs[guild_id]['owners'] = []
        save_server_configs(server_configs)

    if is_user_bypassed(author_id, guild_id):
        return True

    if str(author_id) == bot_config.get('owner_id'):
        return True

    if author_id == guild.owner_id or author_id in server_configs[guild_id]['owners'] or author_id in server_configs[guild_id]['authorized_users'] or str(author_id) == creator_id:
        return True

    if member.guild_permissions.administrator:
        return True

    if TT_RESTRICT_TO_PARTICIPANTS:
        for participant in metadata.get("participants", []):
            if int(participant.get("id", 0)) == user_id:
                return True

    return False



# === Write default templates if missing ===
for name, content in TT_default_templates.items():
    path = os.path.join(TT_TEMPLATE_DIR, name)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

# === Flask app instance (scoped) ===
TT_app = Flask(f"{TT_PLUGIN_NAME}_flask")
TT_app.secret_key = os.urandom(24)

@TT_app.route('/')
@login_required_if_enabled
def TT_index():
    servers = [d for d in os.listdir(TT_TRANSCRIPTS_DIR) if os.path.isdir(os.path.join(TT_TRANSCRIPTS_DIR, d))]
    with open(os.path.join(TT_TEMPLATE_DIR, 'TT_index.html'), encoding='utf-8') as f:
        return render_template_string(f.read(), servers=servers)

@TT_app.route('/<server>/')
@login_required_if_enabled
def TT_list_transcripts(server):
    server_path = os.path.join(TT_TRANSCRIPTS_DIR, server)
    if not os.path.exists(server_path):
        abort(404)
    transcripts = [f for f in os.listdir(server_path) if f.endswith(".html")]
    with open(os.path.join(TT_TEMPLATE_DIR, 'TT_server.html'), encoding='utf-8') as f:
        return render_template_string(f.read(), server=server, transcripts=transcripts)


@TT_app.route('/<server>/<transcript>')
def TT_view_transcript(server, transcript):
    if not transcript.endswith(".html"):
        abort(404)

    server_path = os.path.join(TT_TRANSCRIPTS_DIR, server)
    file_path = os.path.join(server_path, transcript)
    if not os.path.exists(file_path):
        abort(404)

    if not is_user_authorized_to_view(file_path):
        if TT_AUTH_ENABLED:
            if 'user_id' not in session:
                return redirect('/login')
        return "You are not authorized to view this transcript.", 403

    return send_from_directory(server_path, transcript)



@TT_app.route('/login')
def TT_login():
    if not TT_AUTH_ENABLED:
        return redirect('/')
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={TT_CLIENT_ID}"
        f"&redirect_uri={TT_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
    )
    return redirect(discord_auth_url)

@TT_app.route('/callback')
def TT_callback():
    if not TT_AUTH_ENABLED:
        return redirect('/')
    code = request.args.get("code")
    data = {
        'client_id': TT_CLIENT_ID,
        'client_secret': TT_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': TT_REDIRECT_URI,
        'scope': 'identify'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    tokens = r.json()

    user_res = requests.get("https://discord.com/api/users/@me", headers={
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    user_res.raise_for_status()
    user = user_res.json()
    session['user_id'] = user['id']
    session['username'] = user['username']
    return redirect('/')

@TT_app.route('/logout')
def TT_logout():
    session.clear()
    return redirect('/')

# === Async-safe startup function ===
def run_TT_webserver():
    TT_app.run(host='0.0.0.0', port=TT_PORT, debug=False)
threading.Thread(target=run_TT_webserver, daemon=True).start()

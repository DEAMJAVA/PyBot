import threading

import discord
from flask import Flask, request, render_template, session
import requests
import os
import json
import pymysqlhelper

from main import logc, bot, add_help, bot_config, when_member_join, is_owner, is_owner_check, has_owner_perm_check

oauth_CONFIG_FILE = 'plugins/oauth/config.json'

oauth_CONFIG = {
        'database': {
            'type': 'sqlite',
            'types_comment....': 'This is to help set database. Supported sqlite and mysql',
            'username': 'changeme',
            'password': 'changeme',
            'database': 'oauth.db',
            'host': 'changeme',
            'port': 3306
        },
        'bot': {
            'client_id': 'changeme',
            'client_secret': 'changeme',
            'redirect_uri': 'changeme',
            'scopes': "identify email guilds.join guilds applications.commands",
            'host': '0.0.0.0',
            'port': 80,
            'proxy': False
        }
    }

if not os.path.exists(oauth_CONFIG_FILE):
    os.makedirs(os.path.dirname(oauth_CONFIG_FILE), exist_ok=True)
    with open(oauth_CONFIG_FILE, 'w') as f:
        json.dump(oauth_CONFIG, f, indent=2)
else:
    with open(oauth_CONFIG_FILE, 'r') as f:
        oauth_CONFIG = json.load(f)


oauth_SERVERs_CONFIG_FILE = 'plugins/oauth/servers_config.json'

oauth_SERVERS_CONFIG = {}

if not os.path.exists(oauth_SERVERs_CONFIG_FILE):
    os.makedirs(os.path.dirname(oauth_SERVERs_CONFIG_FILE), exist_ok=True)
    with open(oauth_SERVERs_CONFIG_FILE, 'w') as f:
        json.dump(oauth_SERVERS_CONFIG, f, indent=2)
else:
    with open(oauth_SERVERs_CONFIG_FILE, 'r') as f:
        oauth_SERVERS_CONFIG = json.load(f)

def save_oauth_server_config(config):
    with open(oauth_SERVERs_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


if not os.path.exists('templates/index.html'):
    os.makedirs('templates', exist_ok=True)
    with open('templates/index.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Login with Discord</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white flex items-center justify-center h-screen">
  <div class="text-center">
    <h1 class="text-4xl font-bold mb-4">Welcome to the Discord OAuth Portal</h1>
    <p class="mb-8 text-gray-300">Click below to authenticate with your Discord account.</p>
    <a href="https://discord.com/api/oauth2/authorize?client_id={{ client_id }}&redirect_uri={{ redirect_uri }}&response_type=code&scope={{ scopes }}&integration_type=1"
       class="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-full transition">
      Login with Discord
    </a>
  </div>
</body>
</html>
""")


if not os.path.exists('templates/callback.html'):
    os.makedirs('templates', exist_ok=True)
    with open('templates/callback.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OAuth Callback</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white flex items-center justify-center min-h-screen p-8">
  <div class="bg-gray-800 rounded-2xl shadow-lg p-6 w-full max-w-xl">
    {% if error %}
      <h2 class="text-2xl font-bold text-red-500 mb-4">Error</h2>
      <p>{{ error }}</p>
    {% else %}
      <h2 class="text-2xl font-bold text-green-400 mb-4">Welcome, {{ username }}</h2>
      <p><strong>User ID:</strong> {{ user_id }}</p>
      <p><strong>Email:</strong> {{ email }}</p>
      <p class="mt-4"><strong>Access Token:</strong> <code class="bg-gray-700 px-2 py-1 rounded text-sm">{{ access_token }}</code></p>
      <p class="mt-2"><strong>Refresh Token:</strong> <code class="bg-gray-700 px-2 py-1 rounded text-sm">{{ refresh_token }}</code></p>
    {% endif %}
  </div>
</body>
</html>

""")








if oauth_CONFIG['database']['type'] == 'sqlite':
    oauth_db = pymysqlhelper.LocalDatabase(oauth_CONFIG['database']['database'])
elif oauth_CONFIG['database']['type'] == 'mysql':
    oauth_db = pymysqlhelper.Database(username=oauth_CONFIG['database']['username'],
                                      password=oauth_CONFIG['database']['password'],
                                      database=oauth_CONFIG['database']['database'],
                                      host=oauth_CONFIG['database']['host'],
                                      port=oauth_CONFIG['database']['port'])
else:
    logc('Invalid DatabaseType')

if not 'access_tokens' in oauth_db.list_tables():
    oauth_db.define_table('access_tokens', user_id=pymysqlhelper.BigInteger, username=pymysqlhelper.Text,
                          email=pymysqlhelper.Text, access_token=pymysqlhelper.Text, refresh_token=pymysqlhelper.Text)

app = Flask(__name__)
app.secret_key = os.urandom(24)

if oauth_CONFIG['bot']['proxy']:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

CLIENT_ID = oauth_CONFIG['bot']['client_id']
CLIENT_SECRET = oauth_CONFIG['bot']['client_secret']
REDIRECT_URI = oauth_CONFIG['bot']['redirect_uri'] + '/callback'
SCOPES = oauth_CONFIG['bot']['scopes']

DISCORD_API_BASE_URL = "https://discord.com/api/v10"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_OAUTH_URL = "https://discord.com/api/oauth2/authorize"


def add_user(access_token, BOT_TOKEN, GUILD_ID, debug=False):
    def log_debug(message, data=None):
        if debug:
            print("[DEBUG]", message)
            if data is not None:
                print("        ", data)

    # Step 1: Get user info
    user_response = requests.get(
        f"{DISCORD_API_BASE_URL}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    log_debug("User info request sent.", {"status_code": user_response.status_code})

    if user_response.status_code != 200:
        log_debug("Failed to fetch user info", user_response.text)
        return {"success": False, "error": "Invalid access token"}

    user_data = user_response.json()
    user_id = user_data['id']
    log_debug("User info retrieved", user_data)

    # Step 2: Add user to guild
    join_payload = {"access_token": access_token}
    join_headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    join_url = f"{DISCORD_API_BASE_URL}/guilds/{GUILD_ID}/members/{user_id}"
    log_debug("Sending PUT to add user to guild", {"url": join_url, "payload": join_payload})

    join_response = requests.put(join_url, headers=join_headers, json=join_payload)
    log_debug("Guild join response", {"status_code": join_response.status_code, "response": join_response.text})

    if join_response.status_code in [201, 204]:
        return {"success": True, "user_id": user_id}
    else:
        error_message = join_response.text
        log_debug("Failed to add user to guild", error_message)
        return {"success": False, "error": error_message}


def validate_access_token(access_token, debug=False):
    def log_debug(message, data=None):
        if debug:
            print("[DEBUG]", message)
            if data is not None:
                print("        ", data)

    url = f"{DISCORD_API_BASE_URL}/users/@me"
    headers = {"Authorization": f"Bearer {access_token}"}

    log_debug("Sending access token validation request", {"url": url, "headers": headers})

    response = requests.get(url, headers=headers)

    log_debug("Validation response", {"status_code": response.status_code, "response": response.text})

    return response.status_code == 200


def refresh_access_token(refresh_token, CLIENT_ID, CLIENT_SECRET, debug=False):
    def log_debug(message, data=None):
        if debug:
            print("[DEBUG]", message)
            if data is not None:
                print("        ", data)

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'scope': 'identify email guilds guilds.join'
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    url = f"{DISCORD_API_BASE_URL}/oauth2/token"
    log_debug("Sending refresh token request", {"url": url, "data": data})

    response = requests.post(url, data=data, headers=headers)

    log_debug("Refresh response", {"status_code": response.status_code, "response": response.text})

    if response.status_code == 200:
        token_data = response.json()
        new_access_token = token_data["access_token"]
        new_refresh_token = token_data["refresh_token"]
        log_debug("Token refreshed successfully", {"access_token": new_access_token, "refresh_token": new_refresh_token})
        return new_access_token, new_refresh_token
    else:
        log_debug("Failed to refresh token", response.text)
        return None, None


@app.route("/")
def index():
    server_id = request.args.get("server_id")
    session['server_id'] = server_id
    return render_template("index.html", client_id=CLIENT_ID, redirect_uri=REDIRECT_URI, scopes=SCOPES)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    server_id = session.pop('server_id', None)  # get it and remove from session

    if not code:
        return render_template('callback.html', error="No code provided!")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
    if response.status_code != 200:
        return render_template('callback.html', error="Failed to fetch token")

    token_data = response.json()

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    user_info = requests.get(
        f"{DISCORD_API_BASE_URL}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    user_id = user_info["id"]
    username = f"{user_info['username']}#{user_info['discriminator']}"
    email = user_info.get("email", "Not available")

    if not oauth_db.search('access_tokens', user_id=user_id):
        oauth_db.insert('access_tokens', user_id=user_id, username=username, email=email, access_token=access_token,
                        refresh_token=refresh_token)
    else:
        oauth_db.update('access_tokens', {'user_id': user_id},
                        {'email': email, 'access_token': access_token, 'refresh_token': refresh_token, 'username': username})

    autojoin = oauth_SERVERS_CONFIG.get('autojoin', [])
    autojoinunique = oauth_SERVERS_CONFIG.get('autojoinunique', [])


    if server_id and int(server_id) in autojoinunique:
        add_user(access_token, bot_config['bot_token'], server_id)
    else:
        for server in autojoin:
            add_user(access_token, bot_config['bot_token'], server)

    return render_template(
        'callback.html',
        user=user_info,
        user_id=user_id,
        username=username,
        email=email,
        access_token=access_token,
        refresh_token=refresh_token
    )



def run_oauth_webserver():
    app.run(host=oauth_CONFIG['bot']['host'], port=oauth_CONFIG['bot']['port'])
threading.Thread(target=run_oauth_webserver, daemon=True).start()


@when_member_join
async def check_user(member: discord.Member):
    known_users = oauth_db.distinct_values('access_tokens', 'user_id')
    if member.guild.id in oauth_SERVERS_CONFIG.setdefault('autojoin', []) and (member.id not in known_users):
        await member.kick(reason='UnAuthorized')


@is_owner()
@bot.command(name='jm')
async def join_member(ctx, user):
    user = oauth_db.get('access_tokens', user_id=user)
    if not user:
        user = oauth_db.get('access_tokens', email=user)
    if not user:
        await ctx.send('User not found! ❌')
        return
    access_token = user['access_token']
    if not validate_access_token(user.get('access_token')):
        access_token, new_refresh_token = refresh_access_token(
            user.get('refresh_token'),
            oauth_CONFIG['bot']['client_id'],
            oauth_CONFIG['bot']['client_secret']
        )

        oauth_db.update('access_tokens',
                        {'user_id': user['user_id']},
                        {'access_token': access_token, 'refresh_token':new_refresh_token})
    result = add_user(access_token, bot_config['bot_token'], ctx.guild.id)
    if result.get('success'):
        await ctx.send(f'User <@{user['user_id']}> added successfully! ✅')
    else:
        await ctx.send('Something went wrong! ❌')

add_help('Oauth', 'jm <userid>', 'joins a member to the server if the user has authorized to the bot')


@is_owner()
@bot.command(name='jmall')
async def join_member(ctx):
    for user in oauth_db.search('access_tokens'):
        access_token = user['access_token']
        if not validate_access_token(user.get('access_token')):
            access_token, new_refresh_token = refresh_access_token(
                user.get('refresh_token'),
                oauth_CONFIG['bot']['client_id'],
                oauth_CONFIG['bot']['client_secret']
            )
            oauth_db.update('access_tokens',
                            {'user_id': user['user_id']},
                            {'access_token': access_token, 'refresh_token': new_refresh_token})
        add_user(access_token, bot_config['bot_token'], ctx.guild.id)
    await ctx.send(f'All know users added successfully! ✅')
add_help('Oauth', 'jmall', 'joins all authorized member who have authorized the bot to the server')


@bot.command(name='auth')
async def oath_auth(ctx, *, args: str):
    arg = args.split()
    if not arg:
        await ctx.send("Please specify a subcommand: `enable`, `disable`, `clean`, `autojoin`, `autojoinunique`, `validate` or `validateall`.")
        return
    guild: discord.Guild = ctx.guild
    know_users = oauth_db.distinct_values('access_tokens', 'user_id')
    subcommand = arg[0].lower()

    if subcommand == 'enable':
        if not has_owner_perm_check(ctx):
            await ctx.send('Only server owner can use this command')
            return
        oauth_SERVERS_CONFIG.setdefault(str(guild.id), {})['enabled'] = True
        save_oauth_server_config(oauth_SERVERS_CONFIG)
        await ctx.send("OAuth system enabled for this server.")
    elif subcommand == 'disable':
        if not has_owner_perm_check(ctx):
            await ctx.send('Only server owner can use this command')
            return
        oauth_SERVERS_CONFIG.setdefault(str(guild.id), {})['enabled'] = False
        save_oauth_server_config(oauth_SERVERS_CONFIG)
        await ctx.send("OAuth system disabled for this server.")
    elif subcommand == 'clean':
        if not has_owner_perm_check(ctx):
            await ctx.send('Only server owner can use this command')
            return
        removed = 0
        for user in guild.members:
            if not user.bot and (user.id not in know_users):
                try:
                    await user.kick(reason='UnAuthorized')
                    removed += 1
                except discord.Forbidden:
                    await ctx.send(f"Missing permissions to kick {user}")
        await ctx.send(f'Removed {removed} unauthorized users.')
    elif subcommand == 'autojoin':
        if not is_owner_check(ctx):
            await ctx.send('Only bot owner can use this command')
            return
        print(is_owner_check(ctx))
        if len(arg) < 2:
            await ctx.send('Please specify `enable` or `disable` for autojoin.')
            return
        autojoin = oauth_SERVERS_CONFIG.setdefault('autojoin', [])
        action = arg[1].lower()
        if action == 'enable':
            if guild.id not in autojoin:
                autojoin.append(guild.id)
                save_oauth_server_config(oauth_SERVERS_CONFIG)
                await ctx.send("Autojoin enabled for this server.")
            else:
                await ctx.send("Autojoin is already enabled.")
        elif action == 'disable':
            if guild.id in autojoin:
                autojoin.remove(guild.id)
                save_oauth_server_config(oauth_SERVERS_CONFIG)
                await ctx.send("Autojoin disabled for this server.")
            else:
                await ctx.send("Autojoin was not enabled.")
        else:
            await ctx.send("Invalid autojoin action. Use `enable` or `disable`.")

    elif subcommand == 'validate':
        if not is_owner_check(ctx):
            await ctx.send('Only bot owner can use this command')
            return
        if len(arg) < 2:
            await ctx.send('Please specify a user to validate')
            return
        user = oauth_db.get('access_tokens', user_id=arg[1]) or oauth_db.get('access_tokens', email=arg[1])
        if not user:
            await ctx.send('User not found')
            return

        if validate_access_token(user['access_token']):
            await ctx.send('User token is valid ✅')
            return

        new_access_token, new_refresh_token = refresh_access_token(
            user['refresh_token'],
            CLIENT_ID,
            CLIENT_SECRET
        )
        if new_access_token and new_refresh_token:
            oauth_db.update(
                'access_tokens',
                {'user_id': user['user_id']},
                {
                    'access_token': new_access_token,
                    'refresh_token': new_refresh_token
                }
            )
            await ctx.send(f"Access token was invalid but successfully refreshed 🔁\nNew token saved.")
        else:
            oauth_db.delete('access_tokens', user_id=user['user_id'])
            await ctx.send(
                'Access token was invalid and could not be refreshed. User likely deauthorized the app, so record was removed ❌')


    elif subcommand == 'validateall':
        if not is_owner_check(ctx):
            await ctx.send('Only bot owner can use this command')
            return
        users = oauth_db.search('access_tokens')
        if not users:
            await ctx.send("No users found in the database.")
            return
        valid_count = 0
        refreshed_count = 0
        removed_count = 0
        for user in users:
            user_id = user['user_id']
            if validate_access_token(user['access_token']):
                valid_count += 1
                continue
            new_access_token, new_refresh_token = refresh_access_token(
                user['refresh_token'],
                CLIENT_ID,
                CLIENT_SECRET
            )
            if new_access_token and new_refresh_token:
                oauth_db.update(
                    'access_tokens',
                    {'user_id': user_id},
                    {
                        'access_token': new_access_token,
                        'refresh_token': new_refresh_token
                    }
                )
                refreshed_count += 1
            else:
                oauth_db.delete('access_tokens', user_id=user_id)
                removed_count += 1
        await ctx.send(
            f"✅ Valid tokens: {valid_count}\n"
            f"🔁 Refreshed tokens: {refreshed_count}\n"
            f"❌ Removed (deauthed) users: {removed_count}"
        )

    elif subcommand == 'autojoinunique':
        if not has_owner_perm_check(ctx):
            await ctx.send('Only server owner can use this command')
            return
        if len(arg) < 2:
            await ctx.send('Please specify `enable` or `disable` for autojoinunique.')
            return
        autojoinunique = oauth_SERVERS_CONFIG.setdefault('autojoinunique', [])
        action = arg[1].lower()
        if action == 'enable':
            if guild.id not in autojoinunique:
                autojoinunique.append(guild.id)
                save_oauth_server_config(oauth_SERVERS_CONFIG)
                await ctx.send("Unique Autojoin enabled for this server.")
                await ctx.send(f"Unique Auth Link for this server is: `{oauth_CONFIG['bot']['redirect_uri']}/?server_id={ctx.guild.id}`")
            else:
                await ctx.send("Unique Autojoin is already enabled.")
                await ctx.send(
                    f"Unique Auth Link for this server is: `{oauth_CONFIG['bot']['redirect_uri']}/?server_id={ctx.guild.id}`")
        elif action == 'disable':
            if guild.id in autojoinunique:
                autojoinunique.remove(guild.id)
                save_oauth_server_config(oauth_SERVERS_CONFIG)
                await ctx.send("Unique Autojoin disabled for this server.")
            else:
                await ctx.send("Unique Autojoin was not enabled.")
        else:
            await ctx.send("Invalid autojoinunique action. Use `enable` or `disable`.")

    elif subcommand == 'help':
        embed = discord.Embed(
            title="📘 OAuth Command Help",
            description="Manage the OAuth system for your server. Only bot owner or server owner can use some commands.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="`auth enable` / `auth disable`",
            value="Enable or disable OAuth system for this server (owner only).",
            inline=False
        )
        embed.add_field(
            name="`auth clean`",
            value="Kick all unauthorized members (those who haven’t authorized the bot).",
            inline=False
        )
        embed.add_field(
            name="`auth autojoin enable/disable`",
            value="Enable/disable autojoining of new authorized users (bot owner only).",
            inline=False
        )
        embed.add_field(
            name="`auth autojoinunique enable/disable`",
            value="Enable/disable autojoining with a unique OAuth link per server (owner only).",
            inline=False
        )
        embed.add_field(
            name="`auth validate <user_id/email>`",
            value="Check if a user's access token is valid and refresh it if possible (bot owner only).",
            inline=False
        )
        embed.add_field(
            name="`auth validateall`",
            value="Validate and refresh all users in the database (bot owner only).",
            inline=False
        )
        embed.set_footer(text="Use the subcommands wisely. Some are restricted to bot or server owners.")
        await ctx.send(embed=embed)
        return



    else:
        await ctx.send(f"Unknown subcommand `{subcommand}`.")
add_help('Oauth', 'auth [help]', 'shows the help message for the auth command')





import discord
import subprocess
import os
import asyncio

from main import bot, add_help

CONFIG_FILE = 'plugins/scripts.txt'
bot_processes = {}
intents = discord.Intents.default()

MAIN_BOT_PATH = os.path.abspath(__file__)


def read_config_file(config_file):
    if not os.path.exists(config_file):
        log(f"Config file '{config_file}' does not exist. Creating a new one...")
        open(config_file, 'w').close()

    scripts = {}
    with open(config_file, 'r') as f:
        for line in f:
            if line.strip() and not line.strip().startswith('#'):
                parts = line.strip().split(' | ')

                script_path = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else script_path
                default_state = parts[2].strip() if len(parts) > 2 else "start"
                python_executable = parts[3].strip() if len(parts) > 3 else "python"
                args = parts[4].strip().split() if len(parts) > 4 else []

                scripts[name] = {
                    'path': script_path,
                    'state': default_state,
                    'python': python_executable,
                    'args': args
                }
    return scripts

configs = read_config_file(CONFIG_FILE)

async def start_bot(identifier, config):
    bot_path = os.path.abspath(config['path'])

    if bot_path == MAIN_BOT_PATH:
        return "Cannot start the main bot from itself!"

    if identifier in bot_processes:
        return f"Bot '{identifier}' is already running."

    try:
        log(f"Starting bot: {bot_path}")
        process = subprocess.Popen(
            [config['python'], bot_path] + config['args'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=os.path.dirname(bot_path)
        )
        bot_processes[identifier] = process

        asyncio.create_task(read_bot_output(identifier, process))

        return f"Started bot '{identifier}'."
    except Exception as e:
        return f"Failed to start bot '{identifier}': {str(e)}"


async def stop_bot(identifier):
    if identifier not in bot_processes:
        return f"Bot '{identifier}' is not running."

    process = bot_processes[identifier]
    process.terminate()
    process.wait()
    del bot_processes[identifier]

    return f"Stopped bot '{identifier}'."


async def restart_bot(identifier):
    configs = read_config_file(CONFIG_FILE)
    if identifier not in configs:
        return f"Bot '{identifier}' not found in {CONFIG_FILE}."

    await stop_bot(identifier)
    return await start_bot(identifier, configs[identifier])


async def read_bot_output(identifier, process):
    try:
        while True:
            output = await asyncio.to_thread(process.stdout.readline)
            if output:
                log(f"[{identifier}]: {output.strip()}")
            if process.poll() is not None:
                break
            await asyncio.sleep(0.1)

        leftover = process.stdout.read()
        if leftover:
            log(f"[{identifier}]: {leftover.strip()}")
    except Exception as e:
        logerr(f"Error reading output from bot '{identifier}': {str(e)}")


@bot.group(name='script', invoke_without_command=True)
async def bot_controller(ctx):
    await ctx.send('Please use a proper sub command: `start`, `stop`, `restart`, `list`')

add_help('Script Controller', 'bot <start/stop/restart/list> [script]', 'Script controller commands')


@bot_controller.command()
async def start(ctx, identifier: str):
    if identifier not in configs:
        await ctx.send(f"Bot '{identifier}' not found in {CONFIG_FILE}.")
    else:
        response = await start_bot(identifier, configs[identifier])
        await ctx.send(response)


@bot_controller.command()
async def stop(ctx, identifier: str):
    response = await stop_bot(identifier)
    await ctx.send(response)


@bot_controller.command(name='restart')
async def restart_(ctx, identifier: str):
    response = await restart_bot(identifier)
    await ctx.send(response)


@bot_controller.command(name='list')
async def list_bots(ctx):
    configs = read_config_file(CONFIG_FILE)
    if not configs:
        await ctx.send(f"No bots found in `{CONFIG_FILE}`.")
    else:
        message = '\n'.join(
            [f"{name}: {config['path']} | {config['python']} {' '.join(config['args'])}" for name, config in configs.items()]
        )
        await ctx.send(f"Configured Bots:\n```{message}```")

@when_bot_ready
async def autostart_bots():
    configs = read_config_file(CONFIG_FILE)
    for identifier, config in configs.items():
        if config['state'].lower() == "start":
            log(f"[AutoStart] Starting {identifier}...")
            result = await start_bot(identifier, config)
            log(f"[AutoStart] {result}")


@when_bot_shutdown
async def shutdown_all_bots():
    log("Shutting down all bots...")
    for identifier, process in list(bot_processes.items()):
        log(f"Stopping bot '{identifier}'...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        del bot_processes[identifier]
    log("All bots have been stopped.")

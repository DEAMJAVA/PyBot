import json
import os.path

import aiohttp
import discord
import asyncio

from main import bot, when_message, add_help

ai_config = {
    "open_router_key": "Change me",
    "agenda" : "You are a helpful assistant on Discord.",
    "model": "deepseek/deepseek-r1-0528:free",
    "context_message_limit": 20,
    "servers": {}
}

ai_config_path = 'plugins/AI/config.json'
if not os.path.exists(ai_config_path):
    os.makedirs(os.path.dirname(ai_config_path), exist_ok=True)
    with open(ai_config_path, 'w') as f:
        json.dump(ai_config, f)
else:
    with open(ai_config_path, 'r') as f:
        ai_config = json.load(f)

def save_ai_config(config):
    with open(ai_config_path, 'w') as f:
        json.dump(config, f)



async def ask_ai(prompt, context=None, return_all_choices=False):
    import asyncio
    import aiohttp

    try:
        headers = {
            "Authorization": f"Bearer {ai_config['open_router_key']}",
            "Content-Type": "application/json",
        }

        messages = [{"role": "system", "content": ai_config['agenda']}]
        if context:
            if not all(isinstance(c, dict) and "role" in c and "content" in c for c in context):
                return "❌ Invalid context format"
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": ai_config['model'],
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
            "n": 3 if return_all_choices else 1
        }

        timeout = aiohttp.ClientTimeout(total=120)  # 15 second timeout

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=data
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    return f"❌ Error from OpenRouter: {response.status} {text}"

                result = await response.json()

                choices = result.get("choices", [])
                if not choices:
                    return "❌ OpenRouter returned no completions."

                if return_all_choices:
                    return "\n\n".join(f"**Choice {i+1}:**\n{c['message']['content'].strip()}"
                                       for i, c in enumerate(choices))

                return choices[0]['message']['content'].strip()

    except asyncio.TimeoutError:
        return "❌ Request to OpenRouter timed out."
    except aiohttp.ClientError as e:
        return f"❌ AIOHTTP Client error: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"




@bot.command(name="ai")
async def ask_ai_command(ctx, *, question: str):
    message = await ctx.send("💬 Thinking...")
    answer = await ask_ai(question)
    await message.edit(answer)
add_help('AI', 'ai <prompt>', 'ask an ai something.')

@bot.command(name="setaichannel")
async def set_ai_channel(ctx):
    ai_config['servers'][str(ctx.guild.id)] = ctx.channel.id
    save_ai_config(ai_config)
    await ctx.send('AI Channel defined successfully ✅')
add_help('AI', 'setaichannel', 'sets the channel as AI channel, any messages sent in the channel the ai would reply to automatically')

@when_message
async def on_message_gpt(message):
    if message.author.bot:
        return
    if message.content.startswith(bot.command_prefix):
        return
    if not message.guild:
        return

    AI_CHANNEL_ID = ai_config.get('servers', {}).get(str(message.guild.id), None)


    if AI_CHANNEL_ID and message.channel.id == AI_CHANNEL_ID:
        channel: discord.TextChannel = message.channel
        async with channel.typing():
            history = [msg async for msg in channel.history(limit=ai_config['context_message_limit'], oldest_first=False)]

            context = []
            for msg in reversed(history):
                if msg.id == message.id:
                    continue
                role = "assistant" if msg.author.bot else "user"

                context.append({"role": role, "content": msg.content})

            reply = await ask_ai(message.content, context=context)

            for chunk in split_message(reply):
                await channel.send(chunk)


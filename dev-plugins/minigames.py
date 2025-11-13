import asyncio

import discord

from main import when_bot_ready, plugin_, bot, add_help
import random

Economy = False
ensure_user = lambda _: None
load_data = lambda _: None
save_data = lambda _: None
Coin = None

max_round_memory = 15

@when_bot_ready
def on_ready():
    global Economy, ensure_user, load_data, save_data, Coin
    Economy = 'credits' in plugin_.keys()
    if Economy:
        credits_ = plugin_['credits']
        ensure_user = credits_['ensure_user']
        load_data = credits_['load_data']
        save_data = credits_['save_data']
        Coin = credits_['coin']

def handle_economy(user: str, amount: int):
    if not Economy:
        return
    user = str(user)
    data = load_data()
    data = ensure_user(data, user)
    data[user]['balance'] += amount
    save_data(data)

ALL_COLORS = ["🔴", "🟢", "🔵", "🟡", "🟣", "🟠", "⚪", "⚫"]
user_games = {}

MEMORY_DISPLAY_TIME = 3
BUTTON_INPUT_TIME = 15

class MemoryView(discord.ui.View):
    def __init__(self, sequence, user_id, round_number):
        super().__init__(timeout=30)
        self.sequence = sequence
        self.user_input = []
        self.user_id = user_id
        self.round = round_number

        for emoji in sorted(set(sequence)):
            self.add_item(ColorButton(emoji))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("🚫 This isn't your game!", ephemeral=True)
            return False
        return True

class ColorButton(discord.ui.Button):
    def __init__(self, emoji):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        view: MemoryView = self.view
        view.user_input.append(self.emoji.name)

        index = len(view.user_input) - 1
        if view.user_input[index] != view.sequence[index]:
            handle_economy(view.user_id, round(user_games.get(view.user_id).get('bet') * (view.round/10)))
            embed = discord.Embed(
                title="❌ Incorrect!",
                description=f"You failed at **Round {view.round}**.\nUse `{bot.command_prefix}memory` to try again."
                f"You won {round(user_games.get(view.user_id).get('bet') * (view.round/10))} {Coin}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            user_games.pop(view.user_id, None)
            view.stop()
            return

        if len(view.user_input) == len(view.sequence):
            if max_round_memory > 0 and view.round == max_round_memory:
                amount = round(user_games.get(view.user_id, {}).get('bet', 100) * (view.round / 10))
                handle_economy(view.user_id, amount)
                embed = discord.Embed(
                    title="🎉 You Win!",
                    description=f"You completed **all {max_round_memory} rounds**!\nYou're a memory master! 🧠"
                                f"\nYou Won {amount} {Coin}",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                user_games.pop(view.user_id, None)
                view.stop()
                return
            else:
                embed = discord.Embed(
                    title=f"✅ Round {view.round} Complete!",
                    description="Get ready for the next round...",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=None)
                view.stop()
                await asyncio.sleep(1.5)
                await next_round(interaction, view.user_id, view.round + 1)
                return

        await interaction.response.defer()

@bot.command()
async def memory(ctx):
    bet = 100
    round_number = 1
    color_pool = ALL_COLORS[:2]
    sequence = [random.choice(color_pool)]

    user_games[ctx.author.id] = {
        "round": round_number,
        "sequence": sequence,
        "bet": bet
    }

    embed = discord.Embed(
        title="🧠 Memorize This!",
        description=f"**Round {round_number}**\nMemorize this sequence:\n**{' '.join(sequence)}**",
        color=discord.Color.blurple()
    ).set_footer(text=f"You have {MEMORY_DISPLAY_TIME} seconds to memorize it.")

    message = await ctx.send(embed=embed)
    await asyncio.sleep(MEMORY_DISPLAY_TIME)

    hidden_embed = discord.Embed(
        title=f"🧠 Memory Game - Round {round_number}",
        description="Click the buttons in the correct order!",
        color=discord.Color.blurple()
    ).set_footer(text=f"You have {BUTTON_INPUT_TIME} seconds to complete this round.")

    view = MemoryView(sequence, ctx.author.id, round_number)
    await message.edit(embed=hidden_embed, view=view)

    try:
        await asyncio.wait_for(view.wait(), timeout=BUTTON_INPUT_TIME)
        if not view.is_finished():
            amount = round(bet * (round_number / 10))
            handle_economy(ctx.author.id, amount)
            await message.edit(
                embed=discord.Embed(
                    title="❌ Time's Up!",
                    description=f"You didn't complete Round {round_number} in time.\nUse `{bot.command_prefix}memory` to try again."
                                f"\nYou won {amount} {Coin}",
                    color=discord.Color.red()
                ),
                view=None
            )
            user_games.pop(ctx.author.id, None)
    except asyncio.TimeoutError:
        amount = round(bet * (round_number / 10))
        handle_economy(ctx.author.id, amount)
        await message.edit(
            embed=discord.Embed(
                title="⏰ Time's Up!",
                description=f"You took too long to respond in **Round {round_number}**.\nUse `{bot.command_prefix}memory` to restart."
                            f"\nYou won {amount} {Coin}",
                color=discord.Color.red()
            ),
            view=None
        )
        view.stop()
        user_games.pop(ctx.author.id, None)
add_help('Economy', 'memory', 'Test your memory and play the memory sequence game and earn rewards!')

async def next_round(interaction: discord.Interaction, user_id: int, round_number: int):
    await asyncio.sleep(2)

    color_pool = ALL_COLORS[:min(2 + round_number - 1, 8)]
    sequence = [random.choice(color_pool) for _ in range(round_number)]
    bet = user_games.get(user_id, {}).get("bet", 100)

    user_games[user_id] = {
        "round": round_number,
        "sequence": sequence,
        "bet": bet
    }

    show_embed = discord.Embed(
        title=f"🧠 Memorize Round {round_number}!",
        description=f"Memorize this sequence:\n**{' '.join(sequence)}**",
        color=discord.Color.blurple()
    ).set_footer(text=f"You have {MEMORY_DISPLAY_TIME} seconds to memorize it.")

    show_msg = await interaction.followup.send(embed=show_embed)
    await asyncio.sleep(MEMORY_DISPLAY_TIME)

    hide_embed = discord.Embed(
        title=f"🧠 Memory Game - Round {round_number}",
        description="Click the buttons in the correct order!",
        color=discord.Color.blurple()
    ).set_footer(text=f"You have {BUTTON_INPUT_TIME} seconds to complete this round.")

    view = MemoryView(sequence, user_id, round_number)
    await show_msg.edit(embed=hide_embed, view=view)

    try:
        await asyncio.wait_for(view.wait(), timeout=BUTTON_INPUT_TIME)

        if not view.is_finished():
            amount = round(bet * (round_number / 10))
            handle_economy(user_id, amount)
            await show_msg.edit(
                embed=discord.Embed(
                    title="❌ Time's Up!",
                    description=f"You didn't complete Round {round_number} in time.\nUse `{bot.command_prefix}memory` to try again."
                                f"\nYou won {amount} {Coin}",
                    color=discord.Color.red()
                ),
                view=None
            )
            user_games.pop(user_id, None)

    except asyncio.TimeoutError:
        amount = round(bet * (round_number / 10))
        handle_economy(user_id, amount)
        await show_msg.edit(
            embed=discord.Embed(
                title="⏰ Time's Up!",
                description=f"You took too long to respond in **Round {round_number}**.\nUse `{bot.command_prefix}memory` to restart."
                            f"\nYou won {amount}",
                color=discord.Color.red()
            ),
            view=None
        )
        view.stop()
        user_games.pop(user_id, None)



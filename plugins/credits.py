import json
import os
import random
import time
import hashlib
from discord import Interaction

from main import add_help

user_cooldowns = {}
mines_games = {}

ECONOMY_FILE = "plugins/credits/economy.json"
ConfigFile = 'plugins/credits/config.json'

def load_config():
    os.makedirs(os.path.dirname(ConfigFile), exist_ok=True)
    if not os.path.exists(ConfigFile):
        with open(ConfigFile, 'w') as f:
            config = {
                'COINFLIP_COOLDOWN': 10,
                'DAILY_REWARDS': [250, 500, 200, 100, 150, 1000, 60, 20, 20, 25, 25, 2000, 10000],
                'DAILY_COOLDOWN': 24 * 60 * 60,
                'COIN': 'Credits',
                'Secret': 0
            }
            json.dump(config, f, indent=4, ensure_ascii=False)
    with open(ConfigFile, "r") as f:
        return json.load(f)

config = load_config()

COINFLIP_COOLDOWN = config.get('COINFLIP_COOLDOWN')
coin = config.get('COIN')
DAILY_COOLDOWN = config.get('DAILY_COOLDOWN')
DAILY_REWARDS = config.get('DAILY_REWARDS')


def load_data():
    os.makedirs(os.path.dirname(ECONOMY_FILE), exist_ok=True)
    if not os.path.exists(ECONOMY_FILE):
        with open(ECONOMY_FILE, "w") as f:
            json.dump({}, f)
    with open(ECONOMY_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(ECONOMY_FILE, "w") as f:
        json.dump(data, f, indent=4)


def ensure_user(data, user_id):
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"balance": 100}
    return data


class ConfirmResetView(View):
    def __init__(self, ctx):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.message = None

    @discord.ui.button(label="✅ Confirm Reset", style=discord.ButtonStyle.danger)
    async def confirm(self, button: Button, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not authorized to confirm this.", ephemeral=True)

        save_data({})
        await interaction.response.edit_message(
            content="💥 Economy reset! All data wiped.",
            view=None
        )
        self.stop()

    async def on_timeout(self):
        if self.message:
            await self.message.edit(content="❌ Reset cancelled (timed out).", view=None)


class BlackjackView(discord.ui.View):
    def __init__(self, ctx, bet, player_hand, dealer_hand, data):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.bet = bet
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.data = data
        self.user_id = str(ctx.author.id)
        self.message = None

    def hand_value(self, hand):
        value = sum(card[1] for card in hand)
        aces = sum(1 for card in hand if card[0] == 'A')
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def format_hand(self, hand):
        return ' '.join(card[0] for card in hand)

    async def update_embed(self, interaction):
        embed = discord.Embed(
            title="🃏 Blackjack",
            description=f"**Your Hand:** {self.format_hand(self.player_hand)} (Value: {self.hand_value(self.player_hand)})\n"
                        f"**Dealer's Hand:** {self.dealer_hand[0][0]} 🂠",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, button, interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This game isn't yours.", ephemeral=True)

        self.player_hand.append(draw_card())
        value = self.hand_value(self.player_hand)

        if value > 21:
            # Bust
            self.data[self.user_id]["balance"] -= self.bet
            save_data(self.data)
            embed = discord.Embed(
                title="💥 Bust!",
                description=f"Your hand: {self.format_hand(self.player_hand)} (Value: {value})\nYou lost {self.bet} {coin}.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()
        else:
            await self.update_embed(interaction)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red)
    async def stand(self, button, interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This game isn't yours.", ephemeral=True)

        # Dealer logic
        dealer_value = self.hand_value(self.dealer_hand)
        while dealer_value < 17:
            self.dealer_hand.append(draw_card())
            dealer_value = self.hand_value(self.dealer_hand)

        player_value = self.hand_value(self.player_hand)
        embed = discord.Embed(title="🎴 Final Results", color=discord.Color.green())

        dealer_display = self.format_hand(self.dealer_hand)
        result = ""

        if dealer_value > 21 or player_value > dealer_value:
            result = f"🎉 You won {self.bet} {coin}!"
            self.data[self.user_id]["balance"] += self.bet
        elif player_value < dealer_value:
            result = f"😢 You lost {self.bet} {coin}."
            self.data[self.user_id]["balance"] -= self.bet
        else:
            result = f"🤝 It's a draw. You keep your {self.bet} {coin}."

        embed.description = (
            f"**Your Hand:** {self.format_hand(self.player_hand)} (Value: {player_value})\n"
            f"**Dealer's Hand:** {dealer_display} (Value: {dealer_value})\n\n"
            f"**{result}**"
        )

        save_data(self.data)
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    async def on_timeout(self):
        if self.message:
            embed = discord.Embed(
                title="⏰ Timed Out",
                description="You took too long. Game ended.",
                color=discord.Color.dark_grey()
            )
            await self.message.edit(embed=embed, view=None)

class MinesButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(label="⬜", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        if user_id not in mines_games:
            await interaction.response.send_message("❌ No active game found.", ephemeral=True)
            return

        game = mines_games[user_id]
        if interaction.user.id != game['player'].id:
            await interaction.response.send_message("❌ This is not your game.", ephemeral=True)
            return

        coord = (self.x, self.y)
        if coord in game['clicked']:
            await interaction.response.send_message("🔁 Already clicked!", ephemeral=True)
            return

        game['clicked'].add(coord)
        self.disabled = True

        if coord in game['mines']:
            self.label = "💣"
            self.style = discord.ButtonStyle.danger

            # Handle loss
            embed = discord.Embed(
                title="💥 Boom! You hit a mine.",
                description=f"**You lost {game['bet']} {coin}.**",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Seed: `{game.get('seed', 'unknown')}`")

            await interaction.response.edit_message(embed=embed, view=None)
            del mines_games[user_id]

            data = load_data()
            data = ensure_user(data, interaction.user.id)
            data[user_id]["balance"] -= game['bet']
            save_data(data)
            return

        else:
            self.label = "✅"
            self.style = discord.ButtonStyle.success

        if len(game['clicked']) == 25 - game['mine_count']:
            clicked = len(game['clicked'])
            mine_count = game['mine_count']
            max_tiles = 25 - mine_count
            progress = clicked / max_tiles
            risk_factor = 1 + (mine_count / 8)  # Slightly higher scaling

            # Slightly less aggressive exponent, base boost
            multiplier = round(1 + (progress ** 1.6) * risk_factor + (clicked * 0.03), 2)
            reward = int((game['bet'] * multiplier))

            data = load_data()
            data = ensure_user(data, interaction.user.id)
            data[user_id]["balance"] += reward - game['bet']
            save_data(data)

            embed = discord.Embed(
                title="🎉 You cleared the board!",
                description=f"**You won {reward} {coin} (x{multiplier})!**",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Seed: `{game.get('seed', 'unknown')}`")

            await interaction.response.edit_message(embed=embed, view=None)
            del mines_games[user_id]

        else:
            await interaction.response.edit_message(view=game['view'])


class MinesView(discord.ui.View):
    def __init__(self, user, game, bet):
        super().__init__(timeout=None)
        self.user = user
        self.game = game
        self.bet = bet

        for y in range(5):
            for x in range(5):
                self.add_item(MinesButton(x, y))



def draw_card():
    ranks = {
        'A': 11, '2': 2, '3': 3, '4': 4, '5': 5,
        '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 10, 'Q': 10, 'K': 10
    }
    card = random.choice(list(ranks.items()))
    return card

@bot.command(name='setbalance', aliases=['setbal'])
@is_owner()
async def set_balance(ctx, member: discord.Member = None, amount: int = None):
    if not member or amount is None:
        return await ctx.send(f"Usage: `{bot.command_prefix}setbalance @user <amount>`")
    if amount < 0:
        return await ctx.send("Balance cannot be negative.")

    data = load_data()
    data = ensure_user(data, member.id)
    data[str(member.id)]["balance"] = amount
    save_data(data)

    embed = discord.Embed(
        title="🔧 Balance Set",
        description=f"{member.display_name}'s balance is now {amount} {coin}.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)
add_help('Economy', 'setbal <@user> <amount> (BOT OWNER)', 'Sets a user\'s balance to a specific amount')


@bot.command(name='addbalance', aliases=['addbal'])
@is_owner()
async def add_balance(ctx, member: discord.Member = None, amount: int = None):
    if not member or amount is None:
        return await ctx.send(f"Usage: `{bot.command_prefix}addbalance @user <amount>`")

    data = load_data()
    data = ensure_user(data, member.id)
    data[str(member.id)]["balance"] += amount
    save_data(data)

    embed = discord.Embed(
        title="💹 Balance Increased",
        description=f"Added {amount} {coin} to {member.display_name}.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
add_help('Economy', 'addbal <@user> <amount> (BOT OWNER)', 'Adds a specified amount to a user\'s balance')


@bot.command(name='predictmines')
@is_owner()
async def predict_mines(ctx, seed: int = None, mine_count: int = None):

    if seed is not None and mine_count is not None:
        if not (1 <= mine_count < 25):
            return await ctx.send("❌ Mine count must be between 1 and 24.")
        clicked = set()
        title = f"Prediction for Seed `{seed}`"
    else:
        return await ctx.send("Incorrect Usage")

    mines = generate_mines(mine_count, seed)

    # Build 5x5 grid
    grid = ""
    for y in range(5):
        for x in range(5):
            coord = (x, y)
            if coord in clicked:
                emoji = "✅" if coord not in mines else "💥"
            elif coord in mines:
                emoji = "💣"
            else:
                emoji = "🟩"
            grid += emoji + " "
        grid += "\n"

    embed = discord.Embed(
        title=f"🧩 {title}",
        description=grid,
        color=discord.Color.teal()
    )
    embed.set_footer(text=f"Seed: {seed} | Mines: {mine_count}")
    await ctx.send(embed=embed)
add_help('Economy', 'predictmines <seed> <mines> (BOT OWNER)', 'Reveal mine positions from a seed and mine count — for debugging or verification')


@bot.command(name='reseteco')
@is_owner()
async def reset_economy(ctx):
    view = ConfirmResetView(ctx)
    msg = await ctx.send("⚠️ Are you sure you want to **reset the entire economy**?", view=view)
    view.message = msg
add_help('Economy', 'reseteco', '**WIPES ECONOMY DATA**!!')


@bot.command(name='balance', aliases=['bal'])
async def balance(ctx, member: discord.Member = None):
    user = member or ctx.author
    data = load_data()
    data = ensure_user(data, user.id)
    save_data(data)
    embed = discord.Embed(
        title=f"{user.display_name}'s Balance",
        description=f"💰 {data[str(user.id)]['balance']} {coin}",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
add_help('Economy', 'balance [@user]', 'Shows the users balance')

@bot.command(name='give', aliases=['transfer'])
async def give(ctx, member: discord.Member = None, amount: int = None):
    if member is None or amount is None:
        return await ctx.send(f"Usage: `{bot.command_prefix}give @user <amount>`")

    if member == ctx.author:
        return await ctx.send(f"You can't give {coin} to yourself.")
    if amount <= 0:
        return await ctx.send("Amount must be positive.")

    data = load_data()
    data = ensure_user(data, ctx.author.id)
    data = ensure_user(data, member.id)

    if data[str(ctx.author.id)]["balance"] < amount:
        return await ctx.send(f"You don't have enough {coin}!")

    data[str(ctx.author.id)]["balance"] -= amount
    data[str(member.id)]["balance"] += amount
    save_data(data)

    embed = discord.Embed(
        title="💸 Transfer Complete",
        description=f"{ctx.author.display_name} gave {amount} {coin} to {member.display_name}.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
add_help('Economy', 'give <@user> <amount>', f'Gives the user a sum of {coin} from your account')

@bot.command(name='daily')
async def daily(ctx):
    data = load_data()
    user_id = str(ctx.author.id)
    user = ensure_user(data, user_id).get(user_id)

    now = int(time.time())
    last_claim = user.get("last_daily", 0)
    DAILY_REWARD = random.choice(DAILY_REWARDS)
    remaining = DAILY_COOLDOWN - (now - last_claim)
    if remaining > 0:
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(
            title="⏳ Daily Already Claimed",
            description=(
                f"{ctx.author.mention}, you already claimed your daily reward.\n"
                f"Come back in **{hours}h {minutes}m {seconds}s**!"
            ),
            color=discord.Color.orange()
        )
        return await ctx.send(embed=embed)

    user["balance"] += DAILY_REWARD
    user["last_daily"] = now
    save_data(data)

    embed = discord.Embed(
        title="✅ Daily Claimed",
        description=f"{ctx.author.mention}, you received {DAILY_REWARD} {coin}!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
add_help('Economy', 'daily', 'Claim daily rewards')

# Casino Commands
@bot.command(name='slot')
async def slot(ctx, bet: int = 100):
    if bet is None:
        return await ctx.send(f"Usage: `{bot.command_prefix}slot <bet>`")

    data = load_data()
    data = ensure_user(data, ctx.author.id)

    if bet <= 0:
        return await ctx.send("Bet must be a positive amount.")
    if data[str(ctx.author.id)]["balance"] < bet:
        return await ctx.send(f"You don't have enough {coin}!")

    symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    slot_display = " | ".join(result)

    match_count = len(set(result))
    winnings = 0

    if match_count == 1:
        winnings = bet * 5
        result_msg = f"🎉 **JACKPOT!** You won {winnings} {coin}!"
        data[str(ctx.author.id)]["balance"] += winnings
    elif match_count == 2:
        winnings = int(bet * 1.5)
        result_msg = f"✨ Two matched! You won {winnings} {coin}!"
        data[str(ctx.author.id)]["balance"] += winnings
    else:
        data[str(ctx.author.id)]["balance"] -= bet
        result_msg = f"😢 No match. You lost {bet} {coin}."

    save_data(data)

    embed = discord.Embed(title="🎰 Slot Machine", description=slot_display, color=discord.Color.purple())
    embed.add_field(name="Result", value=result_msg, inline=False)
    await ctx.send(embed=embed)
add_help('Economy', 'slot [bet]', 'Spin the 🎰 slot machine and match symbols to win up to 5x your bet!')


@bot.command(name='coinflip', aliases=['cf'])
async def coinflip(ctx, bet: int = 100, choice: str = 't'):
    user_id = str(ctx.author.id)

    # Cooldown Check
    now = time.time()
    if user_id in user_cooldowns and now - user_cooldowns[user_id] < COINFLIP_COOLDOWN:
        remaining = int(COINFLIP_COOLDOWN - (now - user_cooldowns[user_id]))
        return await ctx.send(f"🕒 You're on cooldown! Try again in `{remaining}s`.", delete_after=remaining)

    if bet is None:
        return await ctx.send(f"Usage: `{bot.command_prefix}coinflip <bet> [heads/tails]`")

    choice = choice.lower()
    if choice in ['h', 'head']:
        choice = 'heads'
    elif choice in ['t', 'tail']:
        choice = 'tails'
    elif choice not in ['heads', 'tails']:
        return await ctx.send("Invalid choice. Choose `heads` or `tails`")

    data = load_data()
    data = ensure_user(data, ctx.author.id)

    if bet <= 0:
        return await ctx.send("❌ Bet must be a positive number.")
    if data[user_id]["balance"] < bet:
        return await ctx.send(f"❌ You don't have enough {coin}.")


    # Initial Flip Embed
    flip_embed = discord.Embed(
        title="🪙 Flipping the Coin...",
        description=f"You bet {bet} Credits on **{choice.capitalize()}**.\nFlipping...",
        color=discord.Color.blurple()
    )
    message = await ctx.send(embed=flip_embed)

    # Simulate delay
    await asyncio.sleep(2.5)

    flip = random.choice(["heads", "tails"])
    won = (flip == choice)

    result_embed = discord.Embed(
        title="🪙 Coin Flip Result",
        color=discord.Color.green() if won else discord.Color.red()
    )
    result_embed.add_field(name="You chose", value=choice.capitalize(), inline=True)
    result_embed.add_field(name="Coin landed on", value=flip.capitalize(), inline=True)

    if won:
        data[user_id]["balance"] += bet
        result_embed.add_field(name="Result", value=f"🎉 You won {bet} {coin}!", inline=False)
    else:
        data[user_id]["balance"] -= bet
        result_embed.add_field(name="Result", value=f"😢 You lost {bet} {coin}!", inline=False)

    save_data(data)

    # Update cooldown
    user_cooldowns[user_id] = now

    # Edit the original message with result
    await message.edit(embed=result_embed)
add_help('Economy', 'coinflip [bet] [heads/tails]', 'Bet on heads or tails — flip the coin and win 2x your bet if you guess right!')


@bot.command(name='blackjack', aliases=['bj'])
async def blackjack(ctx, bet: int = 100):
    user_id = str(ctx.author.id)

    data = load_data()
    data = ensure_user(data, ctx.author.id)

    if bet <= 0:
        return await ctx.send("❌ Bet must be a positive number.")
    if data[user_id]["balance"] < bet:
        return await ctx.send("❌ You don't have enough funds for this bet.")

    player_hand = [draw_card(), draw_card()]
    dealer_hand = [draw_card(), draw_card()]

    view = BlackjackView(ctx, bet, player_hand, dealer_hand, data)
    embed = discord.Embed(
        title="🃏 Blackjack",
        description=f"**Your Hand:** {view.format_hand(player_hand)} (Value: {view.hand_value(player_hand)})\n"
                    f"**Dealer's Hand:** {dealer_hand[0][0]} 🂠",
        color=discord.Color.blurple()
    )
    msg = await ctx.send(embed=embed, view=view)
    view.message = msg
add_help('Economy', 'blackjack [bet]', 'Play a game of 21! Beat the dealer without going over to win your bet.')


@bot.command(name='leaderboard', aliases=['lb'])
async def leaderboard(ctx, scope: str = "global"):
    data = load_data()
    scope = scope.lower()

    if not data:
        return await ctx.send("❌ No economy data available.")

    leaderboard_data = []

    if scope == "server":
        for member in ctx.guild.members:
            if not member.bot and str(member.id) in data:
                leaderboard_data.append((member, data[str(member.id)]['balance']))
    else:
        for user_id, user_data in data.items():
            member = await bot.fetch_user(int(user_id))
            leaderboard_data.append((member, user_data['balance']))

    if not leaderboard_data:
        return await ctx.send("❌ No users found with economy data in this scope.")

    # Sort by balance descending
    leaderboard_data.sort(key=lambda x: x[1], reverse=True)
    top = leaderboard_data[:10]

    # Create embed
    title_scope = "Server" if scope == "server" else "Global"
    embed = discord.Embed(
        title=f"🏆 {title_scope} Leaderboard - Top 10",
        color=discord.Color.gold()
    )

    for idx, (user, bal) in enumerate(top, start=1):
        embed.add_field(
            name=f"{idx}. {user.name}",
            value=f"{bal} {coin}",
            inline=False
        )

    await ctx.send(embed=embed)
add_help('Economy', 'leaderboard [server/global]', 'Shows the leaderboard')


def generate_mines(count, seed=None):
    """
    Returns a set of (x, y) tuples representing mine positions.
    If a seed is provided, the mine positions will be reproducible.
    """
    rng = random.Random(seed + config['Secret'])
    all_coords = [(x, y) for x in range(5) for y in range(5)]
    return set(rng.sample(all_coords, count))


def generate_seed():
    """
    Generates a pseudo-random 10-digit numeric seed using current time and randomness.
    This can be used to recreate games with generate_mines().
    """
    base = f"{time.time()}_{random.randint(0, 999999)}"
    seed_hash = hashlib.sha256(base.encode()).hexdigest()
    seed_int = int(seed_hash[:10], 16)
    return seed_int


@bot.command(name="mines")
async def play_mines(ctx, bet: int = 100, mine_count: int = 5):
    if bet is None or bet <= 0:
        return await ctx.send("Usage: `!mines <bet> [mine_count=5]`")

    if not (1 <= mine_count < 25):
        return await ctx.send("Mine count must be between 1 and 24.")

    user_id = str(ctx.author.id)
    data = load_data()
    data = ensure_user(data, ctx.author.id)
    seed = generate_seed()

    if data[user_id]["balance"] < bet:
        return await ctx.send("❌ You don't have enough funds for this bet.")

    view = MinesView(ctx.author, bet, mine_count)
    embed = discord.Embed(
        title="🧨 Mines Game Started!",
        description="Click tiles to avoid mines.\nReact with 💸 to cash out.\n",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Seed: `{seed}`")
    msg = await ctx.send(embed=embed, view=view)

    # Save game state
    mines_games[user_id] = {
        "player": ctx.author,
        "bet": bet,
        "mine_count": mine_count,
        "mines": generate_mines(mine_count, seed),
        "clicked": set(),
        "view": view,
        "message": msg,
        "seed": seed
    }

    await msg.add_reaction("💸")

    def check(reaction, user):
        return (
            user.id == ctx.author.id and
            reaction.message.id == msg.id and
            str(reaction.emoji) == "💸"
        )

    while user_id in mines_games:
        try:
            reaction, user = await bot.wait_for("reaction_add", check=check)
        except Exception:
            break

        if user_id not in mines_games:
            break

        game = mines_games[user_id]
        opened = len(game['clicked'])

        if opened == 0:
            await ctx.send("❌ You haven't opened any tiles yet.")
            continue

        mine_count = game['mine_count']
        max_tiles = 25 - mine_count
        progress = opened / max_tiles
        risk_factor = 1 + (mine_count / 8)

        multiplier = round(1 + (progress ** 1.6) * risk_factor + (opened * 0.03), 2)
        reward = int((game['bet'] * multiplier))

        data = load_data()
        data = ensure_user(data, user_id)
        data[user_id]["balance"] += reward - game['bet']
        save_data(data)

        end_embed = discord.Embed(
            title="💸 Cashed Out!",
            description=(
                f"✅ Tiles opened: `{opened}`\n"
                f"💰 You won {reward} {coin} (x{multiplier})!"
            ),
            color=discord.Color.green()
        )
        await msg.edit(embed=end_embed, view=None)
        del mines_games[user_id]
        break
add_help('Economy', 'mines [bet] [amount]', 'Pick safe tiles to multiply your winnings — but hit a mine and lose it all!')


@bot.command(name='dice', aliases=['dicegame', 'roll'])
async def dice_game(ctx, bet: int = 100, choice: int = 1):
    user_id = str(ctx.author.id)

    if not 1 <= choice <= 6:
        return await ctx.send("❌ Invalid number. Choose a number between 1 and 6.")

    if bet <= 0:
        return await ctx.send("❌ Bet must be a positive number.")

    data = load_data()
    data = ensure_user(data, ctx.author.id)

    if data[user_id]["balance"] < bet:
        return await ctx.send(f"❌ You don't have enough {coin}.")

    # Initial Embed
    roll_embed = discord.Embed(
        title="🎲 Rolling the Dice...",
        description=f"You bet {bet} {coin} on number **{choice}**.\nRolling...",
        color=discord.Color.blurple()
    )
    message = await ctx.send(embed=roll_embed)

    await asyncio.sleep(2.5)

    rolled = random.randint(1, 6)
    won = (rolled == choice)

    result_embed = discord.Embed(
        title="🎲 Dice Roll Result",
        color=discord.Color.green() if won else discord.Color.red()
    )
    result_embed.add_field(name="You chose", value=str(choice), inline=True)
    result_embed.add_field(name="Dice rolled", value=str(rolled), inline=True)

    if won:
        winnings = bet * 16
        data[user_id]["balance"] += winnings
        result_embed.add_field(name="Result", value=f"🎉 You guessed right and won {winnings} {coin}!", inline=False)
    else:
        data[user_id]["balance"] -= bet
        result_embed.add_field(name="Result", value=f"😢 You lost {bet} {coin}!", inline=False)

    save_data(data)

    await message.edit(embed=result_embed)

add_help('Economy', 'dice [bet] [1-6]', 'Roll a dice. Guess the number (1-6) and win 5x if correct!')


@bot.command(name='crash')
async def crash_game(ctx, bet: int = 100):
    user_id = str(ctx.author.id)

    if bet <= 0:
        return await ctx.send("❌ Bet must be a positive number.")

    data = load_data()
    data = ensure_user(data, ctx.author.id)

    if data[user_id]["balance"] < bet:
        return await ctx.send(f"❌ You don't have enough {coin}.")

    data[user_id]["balance"] -= bet
    save_data(data)

    crash_point = round(random.uniform(1.5, 5.0), 2)
    multiplier = 1.00
    cashout_multiplier = None
    game_ended = False

    class CrashView(View):
        def __init__(self):
            super().__init__(timeout=None)
            self.value = None

        @discord.ui.button(label="💸 Cash Out", style=discord.ButtonStyle.green)
        async def cashout(self, button: Button, interaction: Interaction):
            nonlocal game_ended, cashout_multiplier
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("This isn’t your game!", ephemeral=True)

            if game_ended:
                return

            game_ended = True
            cashout_multiplier = multiplier
            self.stop()
            await interaction.response.defer()

    view = CrashView()

    embed = discord.Embed(
        title="🚀 Crash Game Started",
        description=f"Bet: **{bet} {coin}**\nMultiplier: **{multiplier:.2f}x**\nChoose an action below.",
        color=discord.Color.blurple()
    )
    message = await ctx.send(embed=embed, view=view)

    try:
        while multiplier < crash_point and not game_ended:
            await asyncio.sleep(1.5)
            multiplier += round(random.uniform(0.10, 0.35), 2)
            multiplier = round(multiplier, 2)
            embed.description = f"Bet: **{bet} {coin}**\nMultiplier: **{multiplier:.2f}x**\nChoose an action below."
            await message.edit(embed=embed, view=view)

        view.stop()
        await message.edit(view=None)

        result_embed = discord.Embed(title="💥 Crash Game Result")

        if cashout_multiplier:
            winnings = int(bet * cashout_multiplier)
            data[user_id]["balance"] += winnings
            result_embed.color = discord.Color.green()
            result_embed.description = (
                f"✅ You cashed out at **{cashout_multiplier:.2f}x**!\n"
                f"💰 You won **{winnings} {coin}**!"
            )
        else:
            result_embed.color = discord.Color.red()
            result_embed.description = (
                f"💥 It crashed at **{crash_point:.2f}x** before you cashed out.\n"
                f"😢 You lost **{bet} {coin}**."
            )

        save_data(data)
        await message.edit(embed=result_embed)

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")
add_help('Economy', 'crash [bet]', 'Test your luck! Watch the multiplier rise and click Cash Out before it crashes to win big!')


@bot.command(name='roulette', aliases=['rlt'])
async def roulette_game(ctx, bet: int = 100):
    user_id = str(ctx.author.id)

    if bet <= 0:
        return await ctx.send("❌ Bet must be a positive number.")

    data = load_data()
    data = ensure_user(data, ctx.author.id)

    if data[user_id]["balance"] < bet:
        return await ctx.send(f"❌ You don't have enough {coin}.")

    class RouletteView(View):
        def __init__(self):
            super().__init__(timeout=30)
            self.choice = None

        @discord.ui.button(label="🔴 Red", style=discord.ButtonStyle.danger)
        async def red(self, button: Button, interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("This is not your game!", ephemeral=True)
            self.choice = "red"
            self.stop()
            await interaction.response.defer()

        @discord.ui.button(label="⚫ Black", style=discord.ButtonStyle.secondary)
        async def black(self, button: Button, interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("This is not your game!", ephemeral=True)
            self.choice = "black"
            self.stop()
            await interaction.response.defer()

        @discord.ui.button(label="🟢 Green", style=discord.ButtonStyle.success)
        async def green(self, button: Button, interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("This is not your game!", ephemeral=True)
            self.choice = "green"
            self.stop()
            await interaction.response.defer()

    view = RouletteView()

    embed = discord.Embed(
        title="🎰 Roulette Game",
        description=f"Bet: **{bet} {coin}**\nPick a color to bet on:",
        color=discord.Color.blurple()
    )
    message = await ctx.send(embed=embed, view=view)

    embed.set_footer('The wheel spins!')
    await view.wait()
    await message.edit(view=None, embed=embed)

    if view.choice is None:
        return await ctx.send("⏳ Game timed out. No color selected.")

    # Deduct bet
    data[user_id]["balance"] -= bet
    save_data(data)

    # Spin the wheel
    await asyncio.sleep(2.0)
    roll = random.randint(0, 14)  # 0 = green, 1-7 = red, 8-14 = black
    if roll == 0:
        result_color = "green"
        emoji = "🟢"
    elif 1 <= roll <= 7:
        result_color = "red"
        emoji = "🔴"
    else:
        result_color = "black"
        emoji = "⚫"

    # Determine win
    won = (view.choice == result_color)
    winnings = 0
    if won:
        if result_color == "green":
            winnings = bet * 25
        else:
            winnings = bet * 2
        data[user_id]["balance"] += winnings
        result_text = f"🎉 You won **{winnings} {coin}**!"
        color = discord.Color.green()
    else:
        result_text = f"😢 You lost **{bet} {coin}**."
        color = discord.Color.red()

    save_data(data)

    result_embed = discord.Embed(
        title="🎯 Roulette Result",
        description=(
            f"You chose: **{view.choice.capitalize()}**\n"
            f"Wheel landed on: {emoji} **{result_color.capitalize()}**\n\n"
            f"{result_text}"
        ),
        color=color
    )
    await message.edit(embed=result_embed)
add_help('Economy', 'roulette [bet]', 'Bet on 🔴 Red, ⚫ Black, or 🟢 Green and spin the wheel — win up to 25x your bet!')



@bot.command(name="race")
async def horse_race(ctx, bet: int = 100):
    user_id = str(ctx.author.id)

    if bet <= 0:
        return await ctx.send("❌ Bet must be a positive number.")

    data = load_data()
    data = ensure_user(data, ctx.author.id)

    if data[user_id]["balance"] < bet:
        return await ctx.send(f"❌ You don't have enough {coin}.")

    horses = ["🐎", "🦄", "🐢", "🐇"]  # Add more if you like
    finish_line = 10
    user_choice = None

    # Step 1: Pick your racer
    class PickHorseView(View):
        def __init__(self):
            super().__init__(timeout=30)

        @discord.ui.button(label="🐎", style=discord.ButtonStyle.primary)
        async def horse1(self, button: Button, interaction: Interaction):
            nonlocal user_choice
            if interaction.user != ctx.author:
                return await interaction.response.send_message("This isn’t your race!", ephemeral=True)
            user_choice = "🐎"
            self.stop()
            await interaction.response.defer()

        @discord.ui.button(label="🦄", style=discord.ButtonStyle.primary)
        async def horse2(self, button: Button, interaction: Interaction):
            nonlocal user_choice
            if interaction.user != ctx.author:
                return await interaction.response.send_message("This isn’t your race!", ephemeral=True)
            user_choice = "🦄"
            self.stop()
            await interaction.response.defer()

        @discord.ui.button(label="🐢", style=discord.ButtonStyle.primary)
        async def horse3(self, button: Button, interaction: Interaction):
            nonlocal user_choice
            if interaction.user != ctx.author:
                return await interaction.response.send_message("This isn’t your race!", ephemeral=True)
            user_choice = "🐢"
            self.stop()
            await interaction.response.defer()

        @discord.ui.button(label="🐇", style=discord.ButtonStyle.primary)
        async def horse4(self, button: Button, interaction: Interaction):
            nonlocal user_choice
            if interaction.user != ctx.author:
                return await interaction.response.send_message("This isn’t your race!", ephemeral=True)
            user_choice = "🐇"
            self.stop()
            await interaction.response.defer()

    pick_view = PickHorseView()

    embed = discord.Embed(
        title="🏁 Emoji Race",
        description="Pick your racer by clicking a button below!\nWinner earns 15x your bet!",
        color=discord.Color.blurple()
    )
    pick_msg = await ctx.send(embed=embed, view=pick_view)

    await pick_view.wait()
    await pick_msg.edit(view=None)

    if not user_choice:
        return await ctx.send("⏳ You didn't choose a racer in time!")

    # Deduct bet
    data[user_id]["balance"] -= bet
    save_data(data)

    # Step 2: Start race
    positions = {emoji: 0 for emoji in horses}

    race_msg = await ctx.send("🏁 Race is starting...")

    winner = None
    while not winner:
        await asyncio.sleep(1)
        advancing = random.choice(horses)
        positions[advancing] += 1

        race_text = ""
        for horse in horses:
            progress = "‣" * positions[horse] + " " * (finish_line - positions[horse])
            race_text += f"{horse} | {progress}🏁\n"

        await race_msg.edit(content=f"**🏇 Emoji Race!**\n\n{race_text}")

        for horse in horses:
            if positions[horse] >= finish_line:
                winner = horse
                break

    # Step 3: Results
    result_embed = discord.Embed(
        title="🎉 Race Finished!",
        description=f"🏁 **Winner:** {winner}\nYour pick: {user_choice}",
        color=discord.Color.green() if winner == user_choice else discord.Color.red()
    )

    if winner == user_choice:
        winnings = bet * 15
        data[user_id]["balance"] += winnings
        result_embed.add_field(name="Result", value=f"🎉 You won **{winnings} {coin}**!")
    else:
        result_embed.add_field(name="Result", value=f"😢 You lost **{bet} {coin}**.")

    save_data(data)

    await ctx.send(embed=result_embed)
add_help('Economy', 'race [bet]', 'Pick your racer 🐎🦄🐢🐇 and watch the emoji race live — win 15x if your pick finishes first!')

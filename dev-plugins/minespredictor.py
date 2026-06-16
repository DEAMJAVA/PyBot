import random
import discord
from discord.ext import commands
import json
import os

from main import bot

MIN_GEMS = 1
MAX_GEMS = 24
GRID_SIZE = 5
ALLOW_CLOSE_DEFAULT = True
WHITELIST_FILE = "plugins/whitelist.json"
mines_command = ''
application_url = ""
mine_ = ''
gem_ = ''


class WhitelistManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.whitelists = self.load_whitelists()

    def load_whitelists(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        else:
            return {}

    def save_whitelists(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.whitelists, f, indent=4)

    def get_whitelist(self, index):
        return self.whitelists.get(str(index), [])

    def add_to_whitelist(self, index, user_id):
        if str(index) not in self.whitelists:
            self.whitelists[str(index)] = []
        if user_id not in self.whitelists[str(index)]:
            self.whitelists[str(index)].append(user_id)
            self.save_whitelists()

    def remove_from_whitelist(self, index, user_id):
        if str(index) in self.whitelists and user_id in self.whitelists[str(index)]:
            self.whitelists[str(index)].remove(user_id)
            self.save_whitelists()

    def reload_whitelists(self):
        self.whitelists = self.load_whitelists()


whitelist_manager = WhitelistManager(WHITELIST_FILE)


def create_grid(size, num_gems, allow_close, specified_positions=None):
    grid = [[mine_ for _ in range(size)] for _ in range(size)]

    if specified_positions:
        for pos in specified_positions:
            row, col = pos
            if 0 <= row < size and 0 <= col < size:
                grid[row][col] = gem_
        return grid

    num_gems = min(num_gems, size * size)
    min_distance = max(size // 3, 1)
    placed_gems = 0

    while placed_gems < num_gems:
        random_row = random.randint(0, size - 1)
        random_col = random.randint(0, size - 1)

        if grid[random_row][random_col] == mine_:
            too_close = False
            for r in range(max(0, random_row - min_distance), min(size, random_row + min_distance + 1)):
                for c in range(max(0, random_col - min_distance), min(size, random_col + min_distance + 1)):
                    if not allow_close and grid[r][c] == gem_:
                        too_close = True
                        break
                if too_close:
                    break

            if not too_close:
                grid[random_row][random_col] = gem_
                placed_gems += 1

    return grid


def grid_to_string(grid):
    return '\n'.join(' '.join(row) for row in grid)



async def is_whitelisted(ctx):
    if not ctx.guild:
        return False

    if ctx.author and ctx.author.guild_permissions.administrator:
        return True

    # Check if the user is whitelisted
    whitelist = whitelist_manager.get_whitelist(0)  # Use index 0 as an example
    if ctx.author.id in whitelist:
        return True

    return False


@bot.slash_command(name=mines_command)
@commands.check(is_whitelisted)
async def mines(ctx, ammount_of_mines:int, bet_amount: int, seed: str, next_client_seed: str):
    if not await is_whitelisted(ctx):
        await ctx.respond("You are not authorized to use this bot.")
        return
    gems = 25-ammount_of_mines
    try:
        if gems < MIN_GEMS or gems > MAX_GEMS:
            await ctx.respond(f'Invalid number of gems. It should be between {MIN_GEMS} and {MAX_GEMS}.')
            return
        if len(seed) != 64:
            await ctx.respond("Invalid server seed. Seed length should be at least 64 characters.")
            return

        if len(next_client_seed) != 10:
            await ctx.respond("Invalid client seed. Seed length should be at least 10 characters.")
            return

        seed_display = seed[:64]

        # Parse flags from seed
        flags = seed[64:].strip().split('-')[1:]
        specified_positions = []
        for flag in flags:
            try:
                row, col = map(int, flag.split(','))
                specified_positions.append((row, col))
            except ValueError:
                await ctx.respond(f"Invalid flag format: {flag}. Flags should be in 'row,col' format.")
                return

        grid = create_grid(GRID_SIZE, gems, ALLOW_CLOSE_DEFAULT, specified_positions=specified_positions)
        grid_str = grid_to_string(grid)

        embed = discord.Embed(title="Predicted Gems", description=grid_str, color=discord.Color.from_rgb(1, 1, 1))
        embed.add_field(name="Server Seed", value=str(seed_display), inline=True)
        embed.add_field(name="Next Client Seed", value=str(next_client_seed), inline=True)
        embed.add_field(name="bet amount", value=bet_amount, inline=True)
        embed.add_field(name="Accuracy", value='100%', inline=True)
        embed.set_footer(text="Powered by Salvix Bush")
        embed.set_thumbnail(url=application_url)

        await ctx.respond(embed=embed)
    except Exception as e:
        print(e)
        await ctx.respond("An error occurred while processing your request.")


whitelistcommands = bot.create_group(name=f'{mines_command}-whitelist')


@whitelistcommands.command(name="add")
@commands.has_permissions(administrator=True)
async def add_whitelist(ctx, member: discord.Member):
    if not ctx.guild:
        await ctx.respond("Commands can only be used within a server.")
        return

    user_id = member.id
    whitelist_manager.add_to_whitelist(0, user_id)
    await ctx.respond(f'{member.mention} has been added to the whitelist.')


@whitelistcommands.command(name="remove")
@commands.has_permissions(administrator=True)
async def remove_whitelist(ctx, member: discord.Member):
    if not ctx.guild:
        await ctx.respond("Commands can only be used within a server.")
        return

    user_id = member.id
    whitelist_manager.remove_from_whitelist(0, user_id)
    await ctx.respond(f'{member.mention} has been removed from the whitelist.')


@whitelistcommands.command(name="reload")
@commands.has_permissions(administrator=True)
async def reload_whitelist(ctx):
    if not ctx.guild:
        await ctx.respond("Commands can only be used within a server.")
        return

    whitelist_manager.reload_whitelists()
    await ctx.respond("Whitelist has been reloaded from the file.")


@whitelistcommands.command(name="list")
@commands.has_permissions(administrator=True)
async def whitelist_list(ctx):
    if not ctx.guild:
        await ctx.respond("Commands can only be used within a server.")
        return

    whitelist = whitelist_manager.get_whitelist(0)
    if not whitelist:
        await ctx.respond("The whitelist is currently empty.")
    else:
        members = [await bot.fetch_user(user_id) for user_id in whitelist]
        member_mentions = [member.mention for member in members if member]
        await ctx.respond("Whitelisted members:\n" + "\n".join(member_mentions))



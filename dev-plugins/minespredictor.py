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
mines_command = 'mines'
application_url = "data:image/jpeg;base64,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"
mine_ = 'M'
gem_ = 'G'


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


        seed_display = seed[:64]

        flags = seed[64:].strip().split('-')[1:]
        specified_positions = []


        if len(seed_display) != 64:
            await ctx.respond("Invalid server seed. Seed length should be at least 64 characters.")
            return

        if len(next_client_seed) != 10:
            await ctx.respond("Invalid client seed. Seed length should be at least 10 characters.")
            return

        if not (1 <= ammount_of_mines <= 24):
            await ctx.respond("Mine count must be between 1 and 24.")
            return

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



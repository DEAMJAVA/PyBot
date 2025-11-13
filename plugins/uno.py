import discord
from discord.ui import View, Button, Select
from discord import Interaction, SelectOption, ButtonStyle
from discord.ext import commands
import random
import string
import asyncio

from main import add_help

games = {}  # code: GameSession

COLORS = ['Red', 'Green', 'Blue', 'Yellow']
VALUES = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'Skip', 'Reverse', 'Draw Two']
WILD_CARDS = ['Wild', 'Wild Draw Four']


class GameSession:
    def __init__(self, host_id, player_limit, starting_cards: int = 7, wild_cards=4, player_time_out=0):
        self.code = self.generate_code()
        self.host_id = host_id
        self.player_limit = max(2, min(player_limit, 10))
        self.players = [host_id]
        self.started = False
        self.finished = False

        self.deck = []
        self.hands = {}  # user_id: [cards]
        self.current_color = None
        self.current_value = None
        self.turn_index = 0
        self.direction = 1  # 1 for forward, -1 for backward
        self.discard_pile = []
        self.draw_penalty = 0  # For stacking draw cards
        self.skip_next = False  # For skip cards

        self.message = None  # Discord message to update
        self.view = None  # GameView instance
        self.game_log = []  # Store recent game events

        self.called_uno = set()
        self.starting_cards = max(1, min(starting_cards, 20))
        self.wild_cards = wild_cards
        self.player_time_out = player_time_out if player_time_out > 0 else None
        self.stopped = False

        # Add timeout tracking
        self.turn_start_time = None
        self.timeout_task = None

    def generate_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            if code not in games:
                return code

    def is_full(self):
        return len(self.players) >= self.player_limit

    def start_game(self):
        """Initialize the game with proper UNO rules"""
        self.deck = self.generate_deck()
        self.hands = {pid: [] for pid in self.players}

        # Deal cards to each player
        for _ in range(self.starting_cards):
            for pid in self.players:
                if self.deck:
                    self.hands[pid].append(self.deck.pop())

        # Find a valid starting card (no wild cards or action cards for simplicity)
        while self.deck:
            top = self.deck.pop()
            if top[0] != 'Black' and top[1] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                break
            # Put it back and shuffle
            self.deck.insert(random.randint(0, len(self.deck)), top)

        if not self.deck:
            # Fallback if no valid starting card found
            top = ('Red', '1')

        self.discard_pile.append(top)
        self.current_color, self.current_value = top
        self.started = True

        # Start timeout tracking for first turn
        self._start_turn_timeout()

    def generate_deck(self):
        """Generate a proper UNO deck"""
        deck = []

        # Regular cards
        for color in COLORS:
            # One 0 per color
            deck.append((color, '0'))
            # Two of each 1-9 and action cards per color
            for value in VALUES[1:]:
                deck.append((color, value))
                deck.append((color, value))

        # Wild cards - 4 of each
        for _ in range(self.wild_cards):
            deck.append(('Black', 'Wild'))
            deck.append(('Black', 'Wild Draw Four'))

        random.shuffle(deck)
        return deck

    def get_current_player(self):
        if not self.players:
            return None
        return self.players[self.turn_index % len(self.players)]

    def _cancel_turn_timeout(self):
        """Cancel the timeout task if it's active."""
        if self.timeout_task and not self.timeout_task.done():
            self.timeout_task.cancel()
        self.timeout_task = None

    def _start_turn_timeout(self):
        """Start timeout tracking for the current turn."""
        if self.player_time_out is None or self.finished or self.stopped:
            return

        # Cancel any existing timeout
        self._cancel_turn_timeout()

        self.turn_start_time = time.time()
        self.timeout_task = asyncio.create_task(self._handle_turn_timeout())

    async def _handle_turn_timeout(self):
        """Handles the turn timeout and auto-advances the turn."""
        try:
            await asyncio.sleep(self.player_time_out)
        except asyncio.CancelledError:
            return  # Timeout was cancelled, exit gracefully

        # Check if game is still active
        if self.finished or not self.players or self.stopped:
            return

        current_player = self.get_current_player()
        if current_player is None:
            return

        # Cancel the current timeout task to prevent conflicts
        self.timeout_task = None


        # Handle timeout - auto-draw a card or skip turn
        if self.draw_penalty > 0:
            # If there's a draw penalty, force the player to draw
            drawn_cards = self._draw_cards_internal(current_player, self.draw_penalty)
            self.draw_penalty = 0
            self.add_game_event(f"<@{current_player}> timed out and drew {len(drawn_cards)} penalty cards!")
        else:
            # Auto-draw one card for the player
            drawn_cards = self._draw_cards_internal(current_player, 1)
            if drawn_cards:
                self.add_game_event(f"<@{current_player}> timed out and drew a card!")

        # Check for winner after drawing
        winner = self.check_winner()
        if winner:
            try:
                await self.update_message()
            except Exception as e:
                pass
            return

        # Move to next turn (this will start a new timeout)
        self.next_turn()

        # Update the message with timeout to prevent hanging
        try:
            await asyncio.wait_for(self.update_message(), timeout=5.0)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            pass

    def next_turn(self):
        """Advance to the next player considering direction"""
        # Clean up uno calls for players who no longer have 1 card
        self.called_uno = {uid for uid in self.called_uno if len(self.hands.get(uid, [])) == 1}

        # Cancel current timeout before changing turns
        self._cancel_turn_timeout()

        if self.skip_next:
            # Skip the next player
            self.turn_index = (self.turn_index + (self.direction * 2)) % len(self.players)
            self.skip_next = False
        else:
            self.turn_index = (self.turn_index + self.direction) % len(self.players)


        # Start timeout for new turn
        self._start_turn_timeout()

    def reverse_direction(self):
        """Reverse the play direction"""
        self.direction *= -1

    def can_play_card(self, card):
        """Check if a card can be played according to UNO rules"""
        # If there's a draw penalty active, only stacking the same penalty card is allowed
        if self.draw_penalty > 0:
            # Can only play Draw Two if penalty is from Draw Two
            if self.current_value == 'Draw Two' and card[1] == 'Draw Two':
                return True
            # Can only play Wild Draw Four if penalty is from Wild Draw Four
            elif self.current_value == 'Wild Draw Four' and card[1] == 'Wild Draw Four':
                return True
            return False  # All other cards blocked while draw penalty active

        # If no draw penalty, follow standard rules
        if card[0] == 'Black':  # Wild cards can always be played
            return True

        return (card[0] == self.current_color or card[1] == self.current_value)

    def get_playable_cards(self, user_id):
        """Get all playable cards for a user"""
        if user_id not in self.hands:
            return []

        playable = []
        for card in self.hands[user_id]:
            if self.can_play_card(card):
                playable.append(card)
        return playable

    def play_card(self, user_id, card):
        """Play a card and handle its effects"""
        if card not in self.hands[user_id]:
            return False, "You don't have this card!"

        if not self.can_play_card(card):
            return False, "This card cannot be played!"

        # Remove card from hand
        self.hands[user_id].remove(card)
        self.discard_pile.append(card)

        color, value = card

        # Always update value first (even for wilds)
        self.current_value = value

        if color == 'Black':
            # Don't update color yet, wait for user to select it
            if value == 'Wild Draw Four':
                self.draw_penalty += 4
                self.add_game_event(f"<@{user_id}> played Wild Draw Four! (+4 penalty)")
            else:
                self.add_game_event(f"<@{user_id}> played Wild card!")
            # Color will be updated separately via ColorButton
        else:
            self.current_color = color
            if value == 'Skip':
                self.skip_next = True
                self.add_game_event(f"<@{user_id}> played {color} Skip! Next player skipped.")
            elif value == 'Reverse':
                self.reverse_direction()
                if len(self.players) == 2:
                    self.skip_next = True
                    self.add_game_event(f"<@{user_id}> played {color} Reverse! Turn skipped.")
                else:
                    self.add_game_event(f"<@{user_id}> played {color} Reverse! Direction changed.")
            elif value == 'Draw Two':
                self.draw_penalty += 2
                self.add_game_event(f"<@{user_id}> played {color} Draw Two! (+2 penalty)")
            else:
                self.add_game_event(f"<@{user_id}> played {color} {value}")

        # Reset the timeout for the current turn after a card is played
        self._start_turn_timeout()
        return True, "Card played successfully!"

    def _draw_cards_internal(self, user_id, count):
        """Internal method to draw cards without restarting timeout"""
        if user_id not in self.hands:
            return []

        cards_drawn = []
        for _ in range(count):
            if not self.deck:
                # Reshuffle discard pile if deck is empty
                if len(self.discard_pile) > 1:
                    top_card = self.discard_pile.pop()
                    self.deck = self.discard_pile[:]
                    self.discard_pile = [top_card]
                    random.shuffle(self.deck)
                    self.add_game_event("Deck reshuffled from discard pile!")
                else:
                    break  # No more cards available

            if self.deck:
                card = self.deck.pop()
                self.hands[user_id].append(card)
                cards_drawn.append(card)

        return cards_drawn

    def draw_cards(self, user_id, count):
        """Draw cards for a player"""
        cards_drawn = self._draw_cards_internal(user_id, count)

        if cards_drawn:
            card_count = len(cards_drawn)
            if count > 1:  # Penalty draw
                self.add_game_event(f"<@{user_id}> drew {card_count} penalty cards")
            else:  # Regular draw
                self.add_game_event(f"<@{user_id}> drew a card")

        # Reset timeout after drawing (only for manual draws, not timeouts)
        self._start_turn_timeout()
        return cards_drawn

    def check_winner(self):
        """Check if there's a winner"""
        for user_id in self.players:
            if len(self.hands[user_id]) == 0:
                self.finished = True
                # Cancel timeout when game finishes
                self._cancel_turn_timeout()
                return user_id
        return None

    def stop_game(self, reason=None):
        """Forcefully stop the game."""
        self.finished = True
        self.stopped = True

        # Cancel timeout when game stops
        self._cancel_turn_timeout()

        # Stop any existing view
        if self.view:
            self.view.stop()

        if reason:
            self.add_game_event(f"🚫 Game stopped: {reason}")
        else:
            self.add_game_event("🚫 Game stopped by host.")

    def add_game_event(self, event):
        """Add an event to the game log"""
        self.game_log.append(event)
        # Keep only the last 5 events to avoid message being too long
        if len(self.game_log) > 5:
            self.game_log.pop(0)

    def get_game_state_message(self):
        """Get the current game state message"""
        if self.finished:
            if self.stopped:
                return "🚫 **Game stopped**.\nThanks for playing UNO."
            winner = self.check_winner()
            return f"🎉 Game Over! <@{winner}> wins the game! 🎉\nThanks for playing UNO."

        current_player = self.get_current_player()
        penalty_text = ""

        if self.draw_penalty > 0:
            if self.current_value == 'Draw Two':
                penalty_text = f" ⚠️ **DRAW {self.draw_penalty} PENALTY** - Play Draw Two to stack or draw cards!"
            elif self.current_value == 'Wild Draw Four':
                penalty_text = f" ⚠️ **DRAW {self.draw_penalty} PENALTY** - Play Wild Draw Four to stack or draw cards!"
            else:
                penalty_text = f" ⚠️ **DRAW {self.draw_penalty} PENALTY** - Must draw cards!"

        # Add timeout info
        timeout_text = ""
        if self.player_time_out and self.turn_start_time:
            elapsed = time.time() - self.turn_start_time
            remaining = max(0, self.player_time_out - elapsed)
            if remaining > 0:
                timeout_text = f" ⏱️ {remaining:.0f}s remaining"

        # Build the main game state
        message = (f"**UNO Game - Code: {self.code}**\n"
                   f"Top card: **{self.current_color} {self.current_value}**{penalty_text}\n"
                   f"It's <@{current_player}>'s turn!{timeout_text}\n"
                   f"Direction: {'→' if self.direction == 1 else '←'}")

        # Add recent events if any
        if self.game_log:
            message += "\n\n**Recent Events:**\n"
            for event in self.game_log[-3:]:  # Show last 3 events
                message += f"• {event}\n"

        # Add player hand counts
        message += "\n**Players:**\n"
        for i, player_id in enumerate(self.players):
            hand_count = len(self.hands.get(player_id, []))
            turn_indicator = "👉 " if i == self.turn_index else "   "
            message += f"{turn_indicator}<@{player_id}>: {hand_count} cards\n"

        return message

    async def update_message(self):
        """Update the game message"""
        if not self.message or self.finished:
            return

        try:
            # Get the current game state message
            content = self.get_game_state_message()

            # Create new view only if game is still active
            if not self.finished and not self.stopped:
                try:
                    # Cancel any existing view timeouts before creating new one
                    if self.view:
                        self.view.stop()

                    self.view = GameView(self)
                    await self.message.edit(content=content, view=self.view)
                except Exception as view_error:
                    # Fallback: update without view
                    await self.message.edit(content=content, view=None)
            else:
                # Game finished, no view needed
                await self.message.edit(content=content, view=None)

        except discord.NotFound:
            pass
            self.message = None
        except discord.HTTPException as e:
            pass
        except Exception as e:
            pass


class GameView(View):
    def __init__(self, session: GameSession):
        # Set timeout to None since we handle timeouts manually in GameSession
        super().__init__(timeout=None)
        self.session = session
        self.add_components()

    def add_components(self):
        """Add all components to the view"""
        self.clear_items()

        if self.session.finished:
            return

        self.add_item(ShowHandButton(self.session))
        self.add_item(UnoButton(self.session))
        self.add_item(CatchUnoButton(self.session))

        current_player = self.session.get_current_player()
        if current_player:
            self.add_item(DrawCardButton(self.session))

            playable_cards = self.session.get_playable_cards(current_player)
            if playable_cards:
                self.add_item(PlayCardSelect(self.session, playable_cards))

    async def on_timeout(self):
        if not self.session.finished:
            current_player = self.session.get_current_player()
            if current_player:
                self.session.add_game_event(f"<@{current_player}>'s turn timed out. Skipped!")
                self.session.skip_next = False
                self.session.next_turn()
                await self.session.update_message()


class UnoButton(Button):
    def __init__(self, session):
        super().__init__(label="🛎️ Call UNO!", style=ButtonStyle.success)
        self.session = session

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        if user_id not in self.session.players:
            return await interaction.response.send_message("You're not in this game.", ephemeral=True)

        hand = self.session.hands.get(user_id, [])
        if len(hand) != 1:
            return await interaction.response.send_message("You can only call UNO when you have exactly one card!", ephemeral=True)

        self.session.called_uno.add(user_id)
        self.session.add_game_event(f"<@{user_id}> called UNO!")
        await interaction.response.send_message("You called UNO! 🛎️", ephemeral=True)
        await self.session.update_message()


class CatchUnoButton(Button):
    def __init__(self, session):
        super().__init__(label="🚨 Catch UNO", style=ButtonStyle.danger)
        self.session = session

    async def callback(self, interaction: Interaction):
        catcher_id = interaction.user.id
        punished = []

        for pid in self.session.players:
            hand = self.session.hands.get(pid, [])
            if len(hand) == 1 and pid not in self.session.called_uno:
                self.session.draw_cards(pid, 2)
                self.session.add_game_event(f"<@{catcher_id}> caught <@{pid}> not calling UNO! +2 penalty.")
                punished.append(f"<@{pid}>")

        if not punished:
            return await interaction.response.send_message("No one to catch! Everyone called UNO or has more than 1 card.", ephemeral=True)

        await interaction.response.send_message(f"Caught: {', '.join(punished)}", ephemeral=True)
        await self.session.update_message()



class ShowHandButton(Button):
    def __init__(self, session):
        super().__init__(label="👀 Show Hand", style=ButtonStyle.secondary)
        self.session = session

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        if user_id not in self.session.players:
            return await interaction.response.send_message("You're not in this game.", ephemeral=True)

        hand = self.session.hands.get(user_id, [])
        if not hand:
            return await interaction.response.send_message("You have no cards.", ephemeral=True)

        # Group cards by color for better display
        hand_by_color = {}
        for card in hand:
            color = card[0]
            if color not in hand_by_color:
                hand_by_color[color] = []
            hand_by_color[color].append(card[1])

        hand_text = ""
        for color, values in hand_by_color.items():
            hand_text += f"**{color}:** {', '.join(values)}\n"

        playable_cards = self.session.get_playable_cards(user_id)
        playable_text = ""
        if playable_cards:
            playable_text = f"\n**Playable:** {', '.join([f'{c[0]} {c[1]}' for c in playable_cards])}"
        elif self.session.draw_penalty > 0:
            penalty_type = "Draw Two" if self.session.current_value == 'Draw Two' else "Wild Draw Four"
            playable_text = f"\n⚠️ **PENALTY ACTIVE**: You must play {penalty_type} to stack or draw {self.session.draw_penalty} cards!"

        await interaction.response.send_message(
            f"**Your hand ({len(hand)} cards):**\n{hand_text}{playable_text}",
            ephemeral=True
        )


class DrawCardButton(Button):
    def __init__(self, session):
        super().__init__(label="🎴 Draw Card", style=ButtonStyle.primary)
        self.session = session

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        current_player = self.session.get_current_player()

        if current_player != user_id:
            return await interaction.response.send_message("It's not your turn.", ephemeral=True)

        if user_id not in self.session.hands:
            return await interaction.response.send_message("You're not in the game.", ephemeral=True)

        # Check if there's a draw penalty and if player has valid cards to play
        if self.session.draw_penalty > 0:
            playable_cards = self.session.get_playable_cards(user_id)
            if not playable_cards:
                # Player must draw penalty cards
                draw_count = self.session.draw_penalty
                self.session.draw_penalty = 0  # Reset penalty after drawing

                cards_drawn = self.session.draw_cards(user_id, draw_count)

                if not cards_drawn:
                    return await interaction.response.send_message("No more cards in deck!", ephemeral=True)

                await interaction.response.send_message(
                    f"You drew the penalty: {draw_count} cards",
                    ephemeral=True
                )

                # End turn after drawing penalty
                self.session.next_turn()
                await self.session.update_message()
                return

        # Normal draw (1 card when no penalty)
        draw_count = 1
        cards_drawn = self.session.draw_cards(user_id, draw_count)

        if not cards_drawn:
            return await interaction.response.send_message("No more cards in deck!", ephemeral=True)

        await interaction.response.send_message(
            f"You drew a card",
            ephemeral=True
        )

        # End turn after drawing (unless they can play immediately)
        self.session.next_turn()
        await self.session.update_message()


class PlayCardSelect(Select):
    def __init__(self, session, playable_cards):
        self.session = session

        # Create unique options for each card
        options = []
        card_counts = {}

        for card in playable_cards:
            card_key = f"{card[0]} {card[1]}"
            card_counts[card_key] = card_counts.get(card_key, 0) + 1

            # Create unique value by adding count
            unique_value = f"{card[0]}|{card[1]}|{card_counts[card_key]}"
            display_label = f"{card_key}" + (f" ({card_counts[card_key]})" if card_counts[card_key] > 1 else "")

            options.append(SelectOption(
                label=display_label,
                value=unique_value,
                description=f"Play {card_key}"
            ))

        # Limit to 25 options (Discord limit)
        options = options[:25]

        super().__init__(
            placeholder="Choose a card to play",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        current_player = self.session.get_current_player()

        if user_id != current_player:
            return await interaction.response.send_message("Not your turn!", ephemeral=True)

        # Parse the selected card
        parts = self.values[0].split("|")
        if len(parts) < 2:
            return await interaction.response.send_message("Invalid card selection!", ephemeral=True)

        color, value = parts[0], parts[1]
        card = (color, value)

        # Attempt to play the card
        success, message = self.session.play_card(user_id, card)

        if not success:
            return await interaction.response.send_message(message, ephemeral=True)

        # Handle wild card color selection
        if color == 'Black':
            await interaction.response.send_message(
                "Choose a color for the wild card:",
                view=ColorSelectView(self.session, user_id),
                ephemeral=True
            )
            return

        # Regular card played - just acknowledge
        await interaction.response.send_message(
            f"You played {card[0]} {card[1]}!",
            ephemeral=True
        )

        # Check for winner
        winner = self.session.check_winner()
        if winner:
            self.session.finished = True
            self.session.add_game_event(f"🎉 <@{winner}> wins the game! 🎉")

            # Create final embed
            final_embed = discord.Embed(
                title="UNO - Game Over!",
                description=f"🎉 Winner: <@{winner}> 🎉",
                color=discord.Color.green()
            )
            final_embed.set_footer(text=f"Game Code: {self.session.code}")
            final_embed.add_field(name="Final Log", value="\n".join(self.session.game_log[-5:]), inline=False)

            try:
                await self.session.message.edit(embed=final_embed, view=None)  # Remove buttons
            except discord.NotFound:
                pass

            # Optional: Send followup message
            await interaction.followup.send(f"🎉 <@{winner}> has won the game!", ephemeral=False)

            if self.session.code in games:
                del games[self.session.code]
            return

        # Continue to next turn
        self.session.next_turn()
        await self.session.update_message()


class ColorSelectView(View):
    def __init__(self, session, player_id):
        super().__init__(timeout=session.player_time_out)
        self.session = session
        self.player_id = player_id
        self.color_chosen = False

        for color in COLORS:
            self.add_item(ColorButton(color, session, player_id, self))  # ✅ Pass view

    async def on_timeout(self):
        if not self.color_chosen:
            self.session.current_color = 'Red'
            self.session.add_game_event("No color selected in time. Defaulted to **Red**.")



class ColorButton(Button):
    def __init__(self, color, session, player_id, parent_view):
        color_emojis = {'Red': '🔴', 'Green': '🟢', 'Blue': '🔵', 'Yellow': '🟡'}
        super().__init__(
            label=color,
            emoji=color_emojis.get(color, '⚪'),
            style=ButtonStyle.secondary
        )
        self.color = color
        self.session = session
        self.player_id = player_id
        self.parent_view = parent_view  # 🔄 renamed from self.view

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.player_id:
            return await interaction.response.send_message(
                "Only the player who played the wild card can choose!",
                ephemeral=True
            )

        self.session.current_color = self.color
        self.parent_view.color_chosen = True

        # Force value to stay Wild or Wild Draw Four
        top_card = self.session.discard_pile[-1]
        self.session.current_value = top_card[1]

        self.session.add_game_event(f"<@{self.player_id}> chose **{self.color}** as the color.")
        await interaction.response.send_message(f"You chose {self.color}!", ephemeral=True)

        # Disable all color buttons
        for child in self.parent_view.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self.parent_view)
        except discord.NotFound:
            pass

        winner = self.session.check_winner()
        if winner:
            self.session.finished = True
            self.session.add_game_event(f"🎉 <@{winner}> wins the game! 🎉")

            final_embed = discord.Embed(
                title="UNO - Game Over!",
                description=f"🎉 Winner: <@{winner}> 🎉",
                color=discord.Color.green()
            )
            final_embed.set_footer(text=f"Game Code: {self.session.code}")
            final_embed.add_field(name="Final Log", value="\n".join(self.session.game_log[-5:]), inline=False)

            try:
                await self.session.message.edit(embed=final_embed, view=None)
            except discord.NotFound:
                pass

            await interaction.followup.send(f"🎉 <@{winner}> has won the game!", ephemeral=False)

            if self.session.code in games:
                del games[self.session.code]
            return

        self.session.next_turn()
        await self.session.update_message()



# Bot commands
@bot.group(name='uno', invoke_without_command=True, aliases=['u'])
async def uno(ctx):
    """UNO game commands"""
    embed = discord.Embed(title="UNO Commands", color=0x00ff00)
    embed.add_field(name="create [limit (Default: 4)] [Starting Cards (Default: 7)] [Wild Cards (Default: 4)] [Player Time Out (Default: 60, 0 for none)]", value="Create a new game (2-10 players)", inline=False)
    embed.add_field(name="join <code>", value="Join an existing game", inline=False)
    embed.add_field(name="leave", value="Leave your current game", inline=False)
    embed.add_field(name="list", value="Show active games", inline=False)
    embed.add_field(name="start [code]", value="Start the game (host only)", inline=False)
    embed.add_field(name="stop [code]", value="Stop the game (host only)", inline=False)
    await ctx.send(embed=embed)


@uno.command()
async def create(ctx, limit: int = 4, cards: int = 7, wild_cards:int = 4, player_time_out:int = 60):
    """Create a new UNO game"""
    if limit > 10 or limit < 2:
        return await ctx.send("❌ Player limit must be between 2 and 10.")

    if cards > 20 or cards < 1:
        return await ctx.send("❌ Starting Cards must be between 1 and 20.")

    # Check if user is already in a game
    for game in games.values():
        if ctx.author.id in game.players:
            return await ctx.send("❌ You're already in a game. Leave it first with `uno leave`.")

    session = GameSession(ctx.author.id, limit, cards, wild_cards, player_time_out)
    games[session.code] = session

    embed = discord.Embed(title="🎮 UNO Game Created!", color=0x00ff00)
    embed.add_field(name="Game Code", value=f"`{session.code}`", inline=True)
    embed.add_field(name="Player Limit", value=f"{limit}", inline=True)
    embed.add_field(name="Initial Cards", value=cards, inline=True)
    embed.add_field(name="Wild Cards", value=wild_cards, inline=True)
    embed.add_field(name="Player Timeout", value=player_time_out if player_time_out else "N/A", inline=True)
    embed.add_field(name="Join Command", value=f"`{bot.command_prefix}uno join {session.code}`", inline=False)

    await ctx.send(embed=embed)
add_help('General', 'uno', 'Uno game commands')


@uno.command()
async def join(ctx, code: str):
    """Join an UNO game"""
    code = code.upper()
    session = games.get(code)

    if not session:
        return await ctx.send("❌ Game not found.")

    if session.started:
        return await ctx.send("❌ This game has already started.")

    if ctx.author.id in session.players:
        return await ctx.send("❌ You are already in this game.")

    if session.is_full():
        return await ctx.send("❌ This game is full.")

    session.players.append(ctx.author.id)

    embed = discord.Embed(title="✅ Joined Game!", color=0x00ff00)
    embed.add_field(name="Game Code", value=f"`{code}`", inline=True)
    embed.add_field(name="Players", value=f"{len(session.players)}/{session.player_limit}", inline=True)

    player_list = [f"<@{pid}>" for pid in session.players]
    embed.add_field(name="Current Players", value=", ".join(player_list), inline=False)

    await ctx.send(f"{ctx.author.mention} joined the game!", embed=embed)


@uno.command()
async def leave(ctx):
    """Leave your current UNO game"""
    for code, session in list(games.items()):
        if ctx.author.id in session.players:
            if session.started and not session.finished:
                # Game is in progress
                session.players.remove(ctx.author.id)
                if len(session.players) < 2:
                    # End game if too few players
                    del games[code]
                    return await ctx.send("🛑 Game ended due to insufficient players.")
                else:
                    # Adjust turn index if necessary
                    if session.turn_index >= len(session.players):
                        session.turn_index = 0
                    await session.update_message()
                    return await ctx.send("✅ You left the game.")
            else:
                # Game not started yet
                session.players.remove(ctx.author.id)
                if ctx.author.id == session.host_id:
                    del games[code]
                    return await ctx.send("🛑 Game deleted because host left.")
                else:
                    return await ctx.send("✅ You left the game.")

    await ctx.send("❌ You're not in any game.")


@uno.command(name='list')
async def listgames(ctx):
    """List all active UNO games"""
    if not games:
        return await ctx.send("❌ No active games.")

    embed = discord.Embed(title="🎮 Active UNO Games", color=0x0099ff)

    for code, game in games.items():
        status = "🔴 In Progress" if game.started else "🟡 Waiting"
        if game.finished:
            status = "⚫ Finished"

        embed.add_field(
            name=f"Code: `{code}`",
            value=f"Players: {len(game.players)}/{game.player_limit}\nStatus: {status}",
            inline=True
        )

    await ctx.send(embed=embed)


@uno.command(name='start')
async def startgame(ctx, code: str = None):
    """Start an UNO game"""
    session = None

    if code:
        session = games.get(code.upper())
    else:
        # Auto-locate the game
        for s in games.values():
            if ctx.author.id in s.players:
                session = s
                break

    if not session:
        return await ctx.send("❌ Game not found or you're not in any game.")

    if session.started:
        return await ctx.send("❌ Game already started.")

    if ctx.author.id != session.host_id:
        return await ctx.send("❌ Only the host can start the game.")

    if len(session.players) < 2:
        return await ctx.send("❌ Need at least 2 players to start.")

    # Start the game
    session.start_game()
    session.add_game_event(f"Game started with {len(session.players)} players!")

    view = GameView(session)
    session.view = view

    message = await ctx.send(session.get_game_state_message(), view=view)
    session.message = message


@uno.command(name='stop')
async def stopgame(ctx, code: str = None):
    """Stop an UNO game"""
    session: GameSession = None

    if code:
        session = games.get(code.upper())
    else:
        # Auto-locate the game
        for s in games.values():
            if ctx.author.id in s.players:
                session = s
                break

    if not session:
        return await ctx.send("❌ Game not found or you're not in any game.")

    if ctx.author.id != session.host_id:
        return await ctx.send("❌ Only the host can stop the game.")


    session.stop_game()
    await session.update_message()

    del games[session.code]
    await ctx.send(f"🛑 Game `{session.code}` has been stopped.")



def parse_card(card_str):
    """Parses a card string like 'Red:5' or 'Black:Wild Draw Four' into a tuple."""
    if ':' not in card_str:
        return None

    color, value = card_str.split(':', 1)
    color = color.strip().capitalize()
    value = ' '.join(word.capitalize() for word in value.strip().split())

    if color not in COLORS and color != 'Black':
        return None
    if value not in VALUES and value not in WILD_CARDS:
        return None

    return (color, value)


@uno.command(name='sethand', aliases=['sh'])
@is_owner()
async def set_hand(ctx, member: discord.Member, *, cards_str: str):
    """[Admin/Test] Set the hand of a player in their current UNO game.
    Usage: !sethand @user Red:5, Blue:Reverse, Black:Wild Draw Four
    """
    session = None

    # Find the session the member is in
    for s in games.values():
        if member.id in s.players:
            session = s
            break

    if not session:
        return await ctx.send("❌ This user is not in any active game.")

    # Split and parse each card
    cards = [card.strip() for card in cards_str.split(',') if card.strip()]
    if not cards:
        return await ctx.send("❌ You must provide cards (e.g., Red:5, Black:Wild).")

    new_hand = []
    for card_str in cards:
        parsed = parse_card(card_str)
        if not parsed:
            return await ctx.send(f"❌ Invalid card: `{card_str}`. Use format Color:Value.")
        new_hand.append(parsed)

    # Set the player's hand
    session.hands[member.id] = new_hand

    await ctx.send(f"✅ Set hand for {member.mention} to: " +
                   ", ".join([f"`{c[0]} {c[1]}`" for c in new_hand]))

    await session.update_message()



@uno.command(name='givecard', aliases=['gc'])
@is_owner()
async def give_card(ctx, member: discord.Member, *,card_str: str):
    """[Admin/Test] Add a card to a player's hand."""
    session = None
    for s in games.values():
        if member.id in s.players:
            session = s
            break

    if not session:
        return await ctx.send("❌ This user is not in any active game.")

    card = parse_card(card_str)
    if not card:
        return await ctx.send(f"❌ Invalid card format: `{card_str}`. Use Color:Value.")

    session.hands.setdefault(member.id, []).append(card)

    await ctx.send(f"✅ Gave `{card[0]} {card[1]}` to {member.mention}.")
    await session.update_message()


@uno.command(name='removecard', aliases=['rc'])
@is_owner()
async def remove_card(ctx, member: discord.Member, *,card_str: str):
    """[Admin/Test] Remove a specific card from a player's hand."""
    session = None
    for s in games.values():
        if member.id in s.players:
            session = s
            break

    if not session:
        return await ctx.send("❌ This user is not in any active game.")

    card = parse_card(card_str)
    if not card:
        return await ctx.send(f"❌ Invalid card format: `{card_str}`. Use Color:Value.")

    try:
        session.hands[member.id].remove(card)
        await ctx.send(f"✅ Removed `{card[0]} {card[1]}` from {member.mention}'s hand.")
        await session.update_message()
    except ValueError:
        await ctx.send(f"❌ {member.mention} does not have `{card[0]} {card[1]}` in their hand.")

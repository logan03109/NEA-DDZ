"""Small command-line entry point for exercising the game engine.

Run from the project root with ``python -m engine.main``.  A graphical menu
can later import ``Game`` from here or create it directly without changing the
core rules modules.
"""

from __future__ import annotations

import sys
from pathlib import Path


# PyCharm can run this file directly, whereas ``python -m engine.main`` runs it
# as part of the ``engine`` package.  Add the project root only for direct
# execution so the imports below work in both cases.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from engine.cards import Card
    from engine.game import Game
    from engine.player import BotPlayer, Player
else:
    from .cards import Card
    from .game import Game
    from .player import BotPlayer, Player


def create_demo_game() -> Game:
    """Create and deal a round with one human player and two simple bots.

    This is a temporary development helper, not the final login or lobby flow.
    It gives the first player the landlord role so the engine is immediately
    ready for a test turn.
    """
    game = Game((Player("Player 1"), BotPlayer("Bot 1"), BotPlayer("Bot 2")))
    game.start_round()
    game.set_landlord(0)
    return game


def main() -> None:
    """Start a basic console game against two bots."""
    game = create_demo_game()
    print(f"Round started. {game.current_player.name} is the landlord.")
    print("Enter card indexes separated by commas, 'pass', 'hand', or 'quit'.")

    while game.state.value == "playing":
        player = game.current_player
        player_index = game.current_player_index

        if isinstance(player, BotPlayer):
            selection = player.choose_play(game.previous_play)
            if selection is None:
                game.pass_turn(player_index)
                print(f"{player.name} passes.")
            else:
                play = game.play_turn(player_index, selection)
                print(f"{player.name} plays: {_format_cards(play.cards)}")
            continue

        print(f"\nYour hand: {_format_indexed_hand(player.hand.cards)}")
        if game.previous_play is not None:
            print(f"Cards to beat: {_format_cards(game.previous_play.cards)}")
        else:
            print("You are leading this trick: play any valid combination.")

        command = input("Your move: ").strip().lower()
        if command == "quit":
            print("Game ended by player.")
            return
        if command == "hand":
            continue

        try:
            if command == "pass":
                game.pass_turn(player_index)
                print("You pass.")
            else:
                selected_cards = _cards_from_indexes(command, player.hand.cards)
                play = game.play_turn(player_index, selected_cards)
                print(f"You play: {_format_cards(play.cards)}")
        except ValueError as error:
            print(f"Invalid move: {error}")

    print(f"\n{game.winner.name} has played all their cards and wins the round.")


def _format_cards(cards: tuple[Card, ...] | list[Card]) -> str:
    """Return card labels in a compact form for console messages."""
    return ", ".join(str(card) for card in cards)


def _format_indexed_hand(cards: list[Card]) -> str:
    """Number a hand so a console player can select cards by index."""
    return " | ".join(f"{index}: {card}" for index, card in enumerate(cards))


def _cards_from_indexes(command: str, hand_cards: list[Card]) -> list[Card]:
    """Convert comma-separated hand indexes into the chosen card objects.

    For example, ``'0, 3, 4'`` selects the first, fourth, and fifth displayed
    cards.  Duplicate and out-of-range indexes are rejected before the game
    engine sees them.
    """
    try:
        indexes = [int(value.strip()) for value in command.split(",")]
    except ValueError as error:
        raise ValueError("Use comma-separated card indexes, for example 0, 3.") from error
    if not indexes or len(set(indexes)) != len(indexes):
        raise ValueError("Choose at least one different card index.")
    if any(index < 0 or index >= len(hand_cards) for index in indexes):
        raise ValueError("One or more selected card indexes do not exist.")
    return [hand_cards[index] for index in indexes]


if __name__ == "__main__":
    main()

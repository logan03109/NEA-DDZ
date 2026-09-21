"""Human and computer-controlled participants in a Dou Dizhu game."""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from .cards import Card
from .hand import Hand, Play


class PlayerRole(Enum):
    """The temporary team roles assigned after dealing each round."""

    LANDLORD = "landlord"
    TENANT = "tenant"


class Player:
    """A participant's current hand and persistent basic statistics.

    ``Game`` assigns a role and controls turns.  Interface code gives selected
    cards to :meth:`play_cards`; it must not remove cards directly from the
    hand.
    """

    def __init__(self, name: str) -> None:
        if not name.strip():
            raise ValueError("A player name cannot be empty.")
        self.name = name
        self.hand = Hand()
        self.role: PlayerRole | None = None
        self.points = 0
        self.games_won = 0
        self.games_played = 0

    def receive_cards(self, cards: Iterable[Card]) -> None:
        """Add dealt cards or the landlord's three centre cards to the hand."""
        self.hand.add_cards(cards)

    def play_cards(self, selected_cards: Iterable[Card]) -> Play:
        """Make a validated play from cards currently in this player's hand."""
        return self.hand.make_play(selected_cards)


class BotPlayer(Player):
    """A simple bot that chooses the first legal low-value play it can make.

    This deliberately basic strategy is useful for filling an empty lobby.  A
    stronger strategy can later override :meth:`choose_play` without changing
    ``Game``.
    """

    def choose_play(self, previous_play: Play | None) -> tuple[Card, ...] | None:
        """Return a legal card selection, or ``None`` when the bot should pass."""
        for card in self.hand.cards:
            candidate = Play.from_cards((card,))
            if previous_play is None or candidate.beats(previous_play):
                return (card,)
        return None

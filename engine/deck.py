"""Deck creation, shuffling, and dealing for a Dou Dizhu round."""

from __future__ import annotations

import random

from .cards import Card, create_standard_deck


class Deck:
    """A mutable 54-card deck used only while setting up a round.

    Typical use::

        deck = Deck()
        deck.shuffle()
        hands, centre_cards = deck.deal()

    ``Game.start_round`` will normally perform these steps, so screens and
    players should not need to deal cards themselves.
    """

    def __init__(self) -> None:
        self.cards: list[Card] = []
        self.reset()

    def reset(self) -> None:
        """Replace any remaining cards with a new, ordered full deck."""
        self.cards = create_standard_deck()

    def shuffle(self) -> None:
        """Randomly reorder the undealt cards in place."""
        random.shuffle(self.cards)

    def draw(self, amount: int = 1) -> list[Card]:
        """Remove and return cards from the top of the deck.

        This is useful for testing, while ``deal`` is the normal setup method.
        A request for more cards than remain is rejected to avoid silently
        producing an incomplete game.
        """
        if amount < 1:
            raise ValueError("The number of cards drawn must be at least one.")
        if amount > len(self.cards):
            raise ValueError("There are not enough cards left in the deck.")
        drawn = self.cards[:amount]
        del self.cards[:amount]
        return drawn

    def deal(self) -> tuple[list[list[Card]], list[Card]]:
        """Deal three 17-card hands and leave three centre cards.

        The returned hands are plain lists so ``Game`` can give each one to a
        ``Hand`` object.  Call this only after ``shuffle`` in a real game.
        """
        if len(self.cards) != 54:
            raise ValueError("A round can only be dealt from a complete deck.")

        hands = [self.draw(17) for _ in range(3)]
        centre_cards = self.draw(3)
        return hands, centre_cards

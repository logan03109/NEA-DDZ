"""Card values used by the Dou Dizhu game engine.

This module deliberately knows nothing about turns, players, or whether a
group of cards is a valid hand.  It only creates and compares individual
cards.  ``Deck`` will use :func:`create_standard_deck` to obtain the cards it
needs, while ``Hand`` will use the rank values when it validates combinations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


class Suit(Enum):
    """The four suits used by the 52 non-joker cards.

    Suits distinguish otherwise identical cards in a deck, but they have no
    strength in Dou Dizhu.  They should therefore never be used to decide
    which play beats another play.
    """

    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"


class Rank(IntEnum):
    """Card ranks in increasing Dou Dizhu strength.

    Dou Dizhu treats 2 as stronger than ace, and the two jokers as the two
    highest ranks.  Using ``IntEnum`` means normal numeric comparisons work:
    ``Rank.TWO > Rank.ACE`` is true.
    """

    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    TWO = 15
    SMALL_JOKER = 16
    BIG_JOKER = 17


_RANK_LABELS: dict[Rank, str] = {
    Rank.THREE: "3",
    Rank.FOUR: "4",
    Rank.FIVE: "5",
    Rank.SIX: "6",
    Rank.SEVEN: "7",
    Rank.EIGHT: "8",
    Rank.NINE: "9",
    Rank.TEN: "10",
    Rank.JACK: "J",
    Rank.QUEEN: "Q",
    Rank.KING: "K",
    Rank.ACE: "A",
    Rank.TWO: "2",
    Rank.SMALL_JOKER: "Small Joker",
    Rank.BIG_JOKER: "Big Joker",
}


@dataclass(frozen=True, slots=True)
class Card:
    """One immutable playing card.

    Create ordinary cards with both a rank and suit, for example
    ``Card(Rank.ACE, Suit.SPADES)``.  Joker cards have no suit, for example
    ``Card(Rank.BIG_JOKER)``.  Cards are immutable so a card cannot accidentally
    change identity while it is in a player's hand.
    """

    rank: Rank
    suit: Suit | None = None

    def __post_init__(self) -> None:
        """Reject invalid card combinations when a card is constructed."""
        is_joker = self.rank in {Rank.SMALL_JOKER, Rank.BIG_JOKER}
        if is_joker and self.suit is not None:
            raise ValueError("Jokers must not have a suit.")
        if not is_joker and self.suit is None:
            raise ValueError("Non-joker cards must have a suit.")

    @property
    def label(self) -> str:
        """Return a readable card name for labels, logs, and debugging.

        Example: an ace of spades returns ``'A of spades'`` and a joker returns
        ``'Big Joker'``.  The GUI may later use this value as its accessible
        text while showing a card image.
        """
        rank_label = _RANK_LABELS[self.rank]
        return rank_label if self.suit is None else f"{rank_label} of {self.suit.value}"

    @property
    def strength(self) -> int:
        """Return the rank strength used when sorting or comparing plays.

        Compare a card's ``strength`` rather than its suit.  Full hand rules
        belong in ``Play``/``Hand``; this is only the strength of one card.
        """
        return int(self.rank)

    def __str__(self) -> str:
        """Use the readable label when a card is printed."""
        return self.label


def create_standard_deck() -> list[Card]:
    """Create a new ordered 54-card Dou Dizhu deck.

    Each call returns fresh ``Card`` objects: ``Deck.reset()`` can safely call
    this function before shuffling, and tests can call it to get predictable
    unshuffled cards.  ``Deck.shuffle()`` will randomise the returned list.
    """
    ordinary_ranks = tuple(rank for rank in Rank if rank < Rank.SMALL_JOKER)
    cards = [Card(rank, suit) for rank in ordinary_ranks for suit in Suit]
    cards.extend((Card(Rank.SMALL_JOKER), Card(Rank.BIG_JOKER)))
    return cards

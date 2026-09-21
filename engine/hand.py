"""Player hands and the basic legal plays recognised by the game."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .cards import Card, Rank


class CombinationType(Enum):
    """The core Dou Dizhu combinations implemented in this first ruleset."""

    SINGLE = "single"
    PAIR = "pair"
    TRIPLE = "triple"
    TRIPLE_WITH_SINGLE = "triple with single"
    TRIPLE_WITH_PAIR = "triple with pair"
    STRAIGHT = "straight"
    CONSECUTIVE_PAIRS = "consecutive pairs"
    BOMB = "bomb"
    ROCKET = "rocket"


@dataclass(frozen=True, slots=True)
class Play:
    """A validated collection of cards played during one turn.

    Use :meth:`from_cards` rather than constructing this class directly.  It
    identifies the combination and raises ``ValueError`` if the cards are not
    a legal play.  ``Game`` then calls :meth:`beats` before accepting it.
    """

    cards: tuple[Card, ...]
    combination: CombinationType
    main_rank: Rank

    @classmethod
    def from_cards(cls, cards: Iterable[Card]) -> Play:
        """Validate cards and create the corresponding play.

        This supports singles, pairs, triples, triple attachments, straights,
        consecutive pairs, bombs, and the two-joker rocket.  Airplanes and
        four-with-two combinations can be added here later without changing
        the player or game classes.
        """
        selected = tuple(sorted(cards, key=lambda card: card.strength))
        if not selected:
            raise ValueError("At least one card must be selected.")

        counts = Counter(card.rank for card in selected)
        ranks = sorted(counts)
        length = len(selected)

        if length == 2 and set(ranks) == {Rank.SMALL_JOKER, Rank.BIG_JOKER}:
            return cls(selected, CombinationType.ROCKET, Rank.BIG_JOKER)
        if length == 1:
            return cls(selected, CombinationType.SINGLE, ranks[0])
        if length == 2 and len(counts) == 1:
            return cls(selected, CombinationType.PAIR, ranks[0])
        if length == 3 and len(counts) == 1:
            return cls(selected, CombinationType.TRIPLE, ranks[0])
        if length == 4 and len(counts) == 1:
            return cls(selected, CombinationType.BOMB, ranks[0])
        if length == 4 and sorted(counts.values()) == [1, 3]:
            return cls(selected, CombinationType.TRIPLE_WITH_SINGLE, _rank_with_count(counts, 3))
        if length == 5 and sorted(counts.values()) == [2, 3]:
            return cls(selected, CombinationType.TRIPLE_WITH_PAIR, _rank_with_count(counts, 3))
        if length >= 5 and _is_consecutive(ranks) and all(count == 1 for count in counts.values()):
            return cls(selected, CombinationType.STRAIGHT, ranks[-1])
        if length >= 6 and length % 2 == 0 and _is_consecutive(ranks) and all(
            count == 2 for count in counts.values()
        ):
            return cls(selected, CombinationType.CONSECUTIVE_PAIRS, ranks[-1])

        raise ValueError("The selected cards do not form a supported legal play.")

    def beats(self, previous_play: Play) -> bool:
        """Return whether this play can legally beat ``previous_play``.

        A rocket beats everything.  A bomb beats any non-bomb play; otherwise
        plays must be the same type and card count, with a stronger main rank.
        """
        if self.combination is CombinationType.ROCKET:
            return previous_play.combination is not CombinationType.ROCKET
        if previous_play.combination is CombinationType.ROCKET:
            return False
        if self.combination is CombinationType.BOMB:
            return previous_play.combination is not CombinationType.BOMB or self.main_rank > previous_play.main_rank
        if previous_play.combination is CombinationType.BOMB:
            return False
        return (
            self.combination is previous_play.combination
            and len(self.cards) == len(previous_play.cards)
            and self.main_rank > previous_play.main_rank
        )


class Hand:
    """The cards currently owned by one player.

    ``Player`` owns a ``Hand`` and asks it to validate and remove a selected
    play.  The UI should pass selected ``Card`` objects to ``make_play`` rather
    than editing ``cards`` itself.
    """

    def __init__(self, cards: Iterable[Card] = ()) -> None:
        self.cards = list(cards)
        self.sort()

    def sort(self) -> None:
        """Sort cards from weakest to strongest for consistent display."""
        self.cards.sort(key=lambda card: (card.strength, card.suit.value if card.suit else ""))

    def add_cards(self, cards: Iterable[Card]) -> None:
        """Add cards, then sort them for the player display."""
        self.cards.extend(cards)
        self.sort()

    def make_play(self, selected_cards: Iterable[Card]) -> Play:
        """Validate selected cards and remove them from this hand.

        The cards are removed only after validation succeeds.  ``Game`` checks
        whether the returned play beats the centre play before calling this
        method, so an invalid turn never changes a player's hand.
        """
        selected = tuple(selected_cards)
        if not _contains_all(self.cards, selected):
            raise ValueError("A player can only play cards currently in their hand.")
        play = Play.from_cards(selected)
        for card in selected:
            self.cards.remove(card)
        return play

    @property
    def is_empty(self) -> bool:
        """Return true when this player has played their final card."""
        return not self.cards


def _rank_with_count(counts: Counter[Rank], amount: int) -> Rank:
    """Return the only rank occurring ``amount`` times in a legal play."""
    return next(rank for rank, count in counts.items() if count == amount)


def _is_consecutive(ranks: list[Rank]) -> bool:
    """Return whether ranks form a sequence that does not include 2 or jokers."""
    return ranks[-1] < Rank.TWO and all(right == left + 1 for left, right in zip(ranks, ranks[1:]))


def _contains_all(hand_cards: list[Card], selected_cards: tuple[Card, ...]) -> bool:
    """Check selection membership while preserving duplicate-card correctness."""
    available = Counter(hand_cards)
    requested = Counter(selected_cards)
    return all(available[card] >= amount for card, amount in requested.items())

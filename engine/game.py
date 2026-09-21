"""Round state and turn rules for a three-player Dou Dizhu game."""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from .cards import Card
from .deck import Deck
from .hand import Play
from .player import Player, PlayerRole


class GameState(Enum):
    """The stages a game can be in."""

    SETUP = "setup"
    PLAYING = "playing"
    FINISHED = "finished"


class Game:
    """Coordinates dealing, landlord selection, turns, passes, and a winner.

    Create it with exactly three ``Player`` objects.  A controller or UI should
    call ``start_round``, choose a landlord with ``set_landlord``, then submit
    plays through ``play_turn`` or passes through ``pass_turn``.
    """

    def __init__(self, players: Iterable[Player]) -> None:
        self.players = list(players)
        if len(self.players) != 3:
            raise ValueError("Dou Dizhu requires exactly three players.")
        if len({player.name for player in self.players}) != 3:
            raise ValueError("Each player must have a unique name.")

        self.deck = Deck()
        self.centre_cards: list[Card] = []
        self.state = GameState.SETUP
        self.landlord_index: int | None = None
        self.current_player_index = 0
        self.previous_play: Play | None = None
        self.previous_player_index: int | None = None
        self.consecutive_passes = 0
        self.winner: Player | None = None

    @property
    def current_player(self) -> Player:
        """Return the only player allowed to act right now."""
        return self.players[self.current_player_index]

    def start_round(self) -> None:
        """Shuffle and deal a fresh round, ready for landlord selection."""
        self.deck.reset()
        self.deck.shuffle()
        hands, self.centre_cards = self.deck.deal()
        for player, cards in zip(self.players, hands):
            player.hand = player.hand.__class__(cards)
            player.role = None
        self.landlord_index = None
        self.current_player_index = 0
        self.previous_play = None
        self.previous_player_index = None
        self.consecutive_passes = 0
        self.winner = None
        self.state = GameState.SETUP

    def set_landlord(self, player_index: int) -> None:
        """Assign the landlord, give them the centre cards, and begin play.

        Bidding can be implemented in the UI later; once it decides a winner,
        it calls this method with that player's index.
        """
        if self.state is not GameState.SETUP or not self.centre_cards:
            raise ValueError("Deal a round before choosing the landlord.")
        if player_index not in range(len(self.players)):
            raise ValueError("The landlord index must identify one of the players.")

        self.landlord_index = player_index
        for index, player in enumerate(self.players):
            player.role = PlayerRole.LANDLORD if index == player_index else PlayerRole.TENANT
        self.players[player_index].receive_cards(self.centre_cards)
        self.current_player_index = player_index
        self.state = GameState.PLAYING

    def play_turn(self, player_index: int, selected_cards: Iterable[Card]) -> Play:
        """Play cards for the current player and advance to the next turn."""
        self._require_current_player(player_index)
        selected = tuple(selected_cards)
        play = Play.from_cards(selected)
        if self.previous_play is not None and not play.beats(self.previous_play):
            raise ValueError("This play does not beat the current centre play.")

        self.current_player.play_cards(selected)
        self.previous_play = play
        self.previous_player_index = player_index
        self.consecutive_passes = 0

        if self.current_player.hand.is_empty:
            self.winner = self.current_player
            self.state = GameState.FINISHED
            return play

        self._advance_turn()
        return play

    def pass_turn(self, player_index: int) -> None:
        """Pass the current turn; two passes return control to the last player."""
        self._require_current_player(player_index)
        if self.previous_play is None:
            raise ValueError("The opening player must make a play, not pass.")

        self.consecutive_passes += 1
        if self.consecutive_passes == 2:
            # The player who made the last accepted play begins a new trick.
            self.current_player_index = self.previous_player_index  # type: ignore[assignment]
            self.previous_play = None
            self.previous_player_index = None
            self.consecutive_passes = 0
        else:
            self._advance_turn()

    def _require_current_player(self, player_index: int) -> None:
        """Reject moves when setup has not finished or it is another player's turn."""
        if self.state is not GameState.PLAYING:
            raise ValueError("The game is not currently accepting turns.")
        if player_index != self.current_player_index:
            raise ValueError("It is not this player's turn.")

    def _advance_turn(self) -> None:
        """Move turn control clockwise through the three players."""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

from .deck import Card
from .rules_325 import (
    deal_first_batch,
    deal_remaining_batch,
    is_valid_move,
    resolve_trick,
    check_quota,
)

# Turn order for LEADING to the first trick and for play in general.
# trump_chooser leads first, then play passes to the right in this order.
PLAY_ORDER = ["trump_chooser", "third_player", "dealer"]


class GameState:
    """Holds everything about one hand of 3-2-5 in progress:
    whose cards are whose, what trump is, whose turn it is,
    what's been played this trick, and each player's trick count.
    """

    def __init__(self):
        # Deal the first 5 cards to each player, hold back the rest
        self.remaining_deck, self.hands = deal_first_batch()

        self.trump_suit = None          # not chosen yet
        self.phase = "choosing_trump"   # game starts paused here

        self.current_trick = []         # cards played so far this trick
        self.current_trick_players = [] # who played each of those cards
        self.current_leader = "trump_chooser"  # who leads the current trick

        self.tricks_won = {
            "dealer": 0,
            "trump_chooser": 0,
            "third_player": 0,
        }

    def choose_trump(self, suit: str):
        """Called once the trump_chooser announces their suit.
        Deals the remaining 5 cards to everyone and unlocks play.
        """
        if self.phase != "choosing_trump":
            raise ValueError("Trump has already been chosen for this hand.")

        self.trump_suit = suit
        self.hands = deal_remaining_batch(self.remaining_deck, self.hands)
        self.phase = "playing"

    def _turn_order_for_trick(self) -> list[str]:
        """Returns the 3 players in the order they play this trick,
        starting from whoever is set as current_leader.
        """
        start_index = PLAY_ORDER.index(self.current_leader)
        return PLAY_ORDER[start_index:] + PLAY_ORDER[:start_index]

    def whose_turn(self) -> str:
        """Returns the name of the player who needs to play next, or None
        if the current trick is full and waiting to be resolved."""
        order = self._turn_order_for_trick()
        if len(self.current_trick) >= len(order):
            return None
        return order[len(self.current_trick)]

    def play_card(self, player: str, card: Card):
        """Attempts to play a card for the given player.
        Raises an error if it's not their turn or the move is illegal.
        NOTE: this no longer auto-resolves the trick when it's full —
        call resolve_current_trick() separately once you're ready to
        (this lets the caller pause first, so all 3 cards are visible
        before the trick clears).
        """
        if self.phase != "playing":
            raise ValueError("Can't play a card right now — game isn't in the playing phase.")

        if player != self.whose_turn():
            raise ValueError(f"It's not {player}'s turn.")

        hand = self.hands[player]

        if not is_valid_move(hand, card, self.current_trick):
            raise ValueError(f"{card} is not a legal move for {player} right now.")

        hand.remove(card)
        self.current_trick.append(card)
        self.current_trick_players.append(player)

    def is_trick_full(self) -> bool:
        """True once all 3 players have played a card this trick."""
        return len(self.current_trick) == 3

    def resolve_current_trick(self):
        """Scores the completed trick, sets the winner as next leader,
        and resets for the next trick. Call this only after is_trick_full()
        is True."""
        winner = resolve_trick(self.current_trick, self.trump_suit, self.current_trick_players)
        self.tricks_won[winner] += 1

        self.current_leader = winner
        self.current_trick = []
        self.current_trick_players = []

        if all(len(h) == 0 for h in self.hands.values()):
            self.phase = "hand_complete"

    def quota_results(self) -> dict[str, bool]:
        """Returns whether each player met their quota, once the hand is over."""
        return {
            position: check_quota(self.tricks_won[position], position)
            for position in self.tricks_won
        }

    def summary(self) -> dict:
        """A snapshot of the current game state — useful for printing/testing,
        and later for sending to the frontend."""
        return {
            "phase": self.phase,
            "trump_suit": self.trump_suit,
            "hands": self.hands,
            "current_trick": self.current_trick,
            "current_leader": self.current_leader,
            "tricks_won": self.tricks_won,
        }
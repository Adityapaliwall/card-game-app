from .deck import Card
from .rules_325 import is_valid_move  # follow-suit logic is game-agnostic, reused as-is
from .chokri_rules import (
    deal_all_13, team_of, is_valid_bid, resolve_trick_52,
    calculate_round_score, check_game_over, BASE_BID
)

PLAYERS = ["1", "2", "3", "4"]


class ChokriGameState:
    """Manages one full Chokri game session: bidding, trump, trick-play,
    and running team scores across MULTIPLE hands (unlike 3-2-5, which
    is just one hand and done)."""

    def __init__(self, dealer="1"):
        self.players = PLAYERS
        self.dealer = dealer
        self.team_scores = {"team_A": 0, "team_B": 0}
        self._start_new_hand()

    def _start_new_hand(self):
        """Deals fresh cards and resets everything EXCEPT team_scores,
        which carries over between hands."""
        self.hands = deal_all_13(self.players)
        self.phase = "bidding"
        self.trump_suit = None
        self.current_trick = []
        self.current_trick_players = []
        self.current_leader = None
        self.tricks_won = {p: 0 for p in self.players}

        # Bidding starts with the player after the dealer
        dealer_index = self.players.index(self.dealer)
        bid_order = self.players[dealer_index + 1:] + self.players[:dealer_index + 1]
        self.active_bidders = bid_order  # a queue; shrinks as players pass
        self.current_bid = 0
        self.highest_bidder = None

    # ---------- Bidding ----------

    def whose_bid_turn(self):
        if self.phase != "bidding":
            return None
        return self.active_bidders[0]

    def submit_bid(self, player: str, bid: int = None, pass_turn: bool = False):
        if self.phase != "bidding":
            raise ValueError("Bidding isn't happening right now.")
        if player != self.active_bidders[0]:
            raise ValueError(f"It's not {player}'s turn to bid.")

        if pass_turn:
            if self.current_bid == 0:
                # Nobody has bid yet — the first bidder MUST bid the
                # base (or higher), they can't pass on nothing
                raise ValueError("You must bid at least the base of 7 — you can't pass yet.")
            self.active_bidders.pop(0)
        else:
            if not is_valid_bid(self.current_bid, bid):
                raise ValueError(f"Bid must be higher than {self.current_bid} and at most 13.")
            self.current_bid = bid
            self.highest_bidder = player
            # This player stays in the running — move them to the back
            # of the queue so bidding continues around the table
            self.active_bidders.append(self.active_bidders.pop(0))

        # Bidding ends once only one active bidder remains
        if len(self.active_bidders) == 1:
            self.highest_bidder = self.active_bidders[0]
            self.phase = "choosing_trump"

    # ---------- Trump ----------

    def choose_trump(self, player: str, suit: str):
        if self.phase != "choosing_trump":
            raise ValueError("Trump can't be chosen right now.")
        if player != self.highest_bidder:
            raise ValueError("Only the winning bidder chooses trump.")

        self.trump_suit = suit
        self.current_leader = self.highest_bidder
        self.phase = "playing"

    # ---------- Trick play ----------

    def _turn_order_for_trick(self):
        start_index = self.players.index(self.current_leader)
        return self.players[start_index:] + self.players[:start_index]

    def whose_turn(self):
        if self.phase != "playing":
            return None
        order = self._turn_order_for_trick()
        if len(self.current_trick) >= len(order):
            return None  # trick is full, waiting to be resolved
        return order[len(self.current_trick)]

    def play_card(self, player: str, card: Card):
        if self.phase != "playing":
            raise ValueError("Can't play a card right now.")
        if player != self.whose_turn():
            raise ValueError(f"It's not {player}'s turn.")

        hand = self.hands[player]
        if not is_valid_move(hand, card, self.current_trick):
            raise ValueError(f"{card} is not a legal move for {player} right now.")

        hand.remove(card)
        self.current_trick.append(card)
        self.current_trick_players.append(player)

    def is_trick_full(self) -> bool:
        return len(self.current_trick) == 4

    def resolve_current_trick(self):
        winner = resolve_trick_52(self.current_trick, self.trump_suit, self.current_trick_players)
        self.tricks_won[winner] += 1

        self.current_leader = winner
        self.current_trick = []
        self.current_trick_players = []

        if all(len(h) == 0 for h in self.hands.values()):
            self._finish_hand()

    # ---------- End of hand ----------

    def _finish_hand(self):
        """Applies your scoring rule and checks if the whole GAME is over."""
        bidding_team = team_of(self.highest_bidder)
        team_a_tricks = self.tricks_won["1"] + self.tricks_won["3"]
        team_b_tricks = self.tricks_won["2"] + self.tricks_won["4"]
        tricks_made = team_a_tricks if bidding_team == "team_A" else team_b_tricks

        result = calculate_round_score(bidding_team, self.current_bid, tricks_made)
        self.team_scores[result["team"]] += result["points"]

        self.last_round_result = {
            "bidding_team": bidding_team,
            "bid": self.current_bid,
            "tricks_made": tricks_made,
            "score_change": result,
        }

        loser = check_game_over(self.team_scores)
        if loser:
            self.phase = "game_over"
            self.losing_team = loser
        else:
            self.phase = "hand_complete"

    def start_next_hand(self):
        """Call this after a hand ends (and the game isn't over) to deal
        the next hand. Rotates the dealer to the next player."""
        if self.phase != "hand_complete":
            raise ValueError("Can't start a new hand right now.")

        current_dealer_index = self.players.index(self.dealer)
        self.dealer = self.players[(current_dealer_index + 1) % len(self.players)]
        self._start_new_hand()
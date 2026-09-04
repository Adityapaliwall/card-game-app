import random

# 3-2-5 uses a 30-card deck: ranks 8 through Ace in all four suits,
# plus the 7 of Hearts and the 7 of Spades (kept as extra low cards).
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]

# Rank strength, used later to compare cards (higher number = stronger card)
RANK_ORDER = {
    "7": 0,
    "8": 1,
    "9": 2,
    "10": 3,
    "Jack": 4,
    "Queen": 5,
    "King": 6,
    "Ace": 7,
}


class Card:
    """A single playing card, e.g. Card('Hearts', 'King')."""

    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank

    def strength(self) -> int:
        """Returns how strong this card's rank is, for comparing cards."""
        return RANK_ORDER[self.rank]

    def __repr__(self):
        # This controls how a Card looks when printed, e.g. "King of Hearts"
        return f"{self.rank} of {self.suit}"

    def __eq__(self, other):
        # Two cards are equal if they have the same suit and rank
        return self.suit == other.suit and self.rank == other.rank


def build_deck() -> list[Card]:
    """Builds the full 30-card 3-2-5 deck: 8 through Ace in every suit,
    plus the extra 7 of Hearts and 7 of Spades."""
    deck = []

    # Add ranks 8 through Ace for all four suits
    for suit in SUITS:
        for rank in RANKS[1:]:  # skip "7" here, we add the two special 7s below
            deck.append(Card(suit, rank))

    # Add the two special low cards
    deck.append(Card("Hearts", "7"))
    deck.append(Card("Spades", "7"))

    return deck


def shuffle_deck(deck: list[Card]) -> list[Card]:
    """Returns a shuffled copy of the deck (does not change the original list)."""
    shuffled = deck.copy()
    random.shuffle(shuffled)
    return shuffled
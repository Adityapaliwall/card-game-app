from .deck import Card

# Chokri uses the full standard 52-card deck (unlike 3-2-5's 30-card deck)
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]

# Rank strength — same idea as deck.py's RANK_ORDER, but covers 2 through Ace
RANK_ORDER_52 = {rank: index for index, rank in enumerate(RANKS)}


def build_full_deck() -> list[Card]:
    """Builds the standard 52-card deck: 2 through Ace, all four suits.
    Reuses the same Card class from deck.py — a card is a card, only
    the deck-building and ranking differ for Chokri."""
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append(Card(suit, rank))
    return deck


def card_strength_52(card: Card) -> int:
    """Returns this card's strength under 52-card ranking (2 is lowest,
    Ace is highest). We can't reuse Card.strength() from deck.py because
    that one is built for the 3-2-5 ranking (which starts at 7, not 2)."""
    return RANK_ORDER_52[card.rank]
import os
import sys
import numpy as np

# Ensure project root on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from resources.rule_definitions import Rule
from utils.players.aggregate_recommender import AggregateRecommender
from utils.matrix.game_state import Game


def _print_moves_dict(game: Game, moves_dict, limit=10):
    print("Recommendations (by optimiser):")
    for name in sorted(moves_dict.keys()):
        moves = moves_dict[name]
        print(f"- {name}: {len(moves)} move(s)")
        if not moves:
            continue
        for i, (adds, score) in enumerate(moves[:limit], start=1):
            word_positions = sorted(adds, key=lambda x: (x[1][0], x[1][1]))
            word = ''.join(ch.upper() for ch, _ in word_positions)
            positions = [(pos[0], pos[1]) for _, pos in word_positions]
            direction = (
                'Horizontal' if len(set(p[0] for p in positions)) == 1 else
                'Vertical' if len(set(p[1] for p in positions)) == 1 else
                'Mixed'
            )
            print(f"    {i}. {word} ({direction}) - Score: {score}")
            print(f"       Positions: {positions}")
            print(f"       Additions: {adds}")
        if len(moves) > limit:
            print(f"    ... and {len(moves) - limit} more moves")


def _collect_board_words(game: Game):
    """Collect all contiguous horizontal and vertical words (len>=2) currently on the board."""
    words = set()
    b = game.board
    # Horizontal scan
    for r in range(15):
        c = 0
        while c < 15:
            if b[r, c] == '':
                c += 1
                continue
            start = c
            while c < 15 and b[r, c] != '':
                c += 1
            word = ''.join(b[r, start:c])
            if len(word) >= 2:
                words.add(word.lower())
        
    # Vertical scan
    for c in range(15):
        r = 0
        while r < 15:
            if b[r, c] == '':
                r += 1
                continue
            start = r
            while r < 15 and b[r, c] != '':
                r += 1
            word = ''.join(b[start:r, c])
            if len(word) >= 2:
                words.add(word.lower())
    return sorted(words)


def _validate_board_words(rule: Rule, game: Game):
    """Validate all existing board words against the dictionary; return list of invalid ones."""
    existing = _collect_board_words(game)
    invalid = [w for w in existing if w not in rule.scrabble_dictionary]
    return existing, invalid


def _run_case(title, setup_board_fn, deck):
    print("=" * 100)
    print(title)
    print("=" * 100)
    rule = Rule('resources/twl06_scrabble_dic_american.txt')
    game = Game(rule)
    setup_board_fn(game)

    print(f"Deck: {deck}")
    print("\nBoard state:")
    game.print_board()
    existing, invalid = _validate_board_words(rule, game)
    if existing:
        print(f"\nExisting words detected: {existing}")
    if invalid:
        print(f"WARNING: Invalid pre-placed words detected: {invalid}")

    agg = AggregateRecommender(rule, game)
    try:
        rec = agg.recommend_next_move(deck)
    except Exception as e:
        print(f"Error during recommendation: {e}")
        return

    print("\n")
    _print_moves_dict(game, rec, limit=3)
    print("\n")


def test_agg_empty_board_opening():
    deck = list('AEINRST')
    def setup(game: Game):
        pass  # empty board
    _run_case("AGG TEST 1: Empty Board Opening (PrizeCells only)", setup, deck)


def test_agg_empty_board_no_moves():
    # Consonant-heavy deck likely yields no opening word
    deck = list('BCDFGHK')
    def setup(game: Game):
        pass
    _run_case("AGG TEST 2: Empty Board - Likely No Moves", setup, deck)


def test_agg_single_word_extension():
    deck = list('AEINRTS')
    def setup(game: Game):
        game.board[7, 6:10] = list('STAR')
    _run_case("AGG TEST 3: Non-Empty - Single Existing Word Extension", setup, deck)


def test_agg_crossword_opportunity():
    deck = list('RAINSET')
    def setup(game: Game):
        # Valid existing words: "TO" horizontal and "AT" vertical crossing the 'T', plus vertical "ION".
        # Place horizontal TO at (7,7)-(7,8).
        game.board[7, 7:9] = list('TO')
        # Place 'A' above 'T' to form vertical AT.
        game.board[6, 7] = 'A'
        # Create vertical ION using the O at (7,8): I at (6,8), O at (7,8), N at (8,8).
        game.board[6, 8] = 'I'
        game.board[8, 8] = 'N'
    _run_case("AGG TEST 4: Non-Empty - Crossword Opportunities (Valid words: TO, AT, ION)", setup, deck)


def test_agg_dense_channel():
    deck = list('TEARLNS')
    def setup(game: Game):
        # Use two long valid words as dense bands leaving corridor cells for new plays.
        # Row 6: CONSTRAINTS (11 letters) across columns 2..12.
        word1 = 'CONSTRAINTS'
        game.board[6, 2:13] = list(word1)
        # Row 8: PREDICTIONS (11 letters) across columns 2..12.
        word2 = 'PREDICTIONS'
        game.board[8, 2:13] = list(word2)
        # Provide anchor letters that form valid vertical words with surrounding letters.
        # At col4 (between N and E) place 'A' -> forms NAE (valid in TWL06).
        game.board[7, 4] = 'A'
        # At col8 (between A and T) place 'N' -> forms ANT (valid).
        game.board[7, 8] = 'N'
    _run_case("AGG TEST 5: Non-Empty - Dense Bands (CONSTRAINTS / PREDICTIONS) with Anchors", setup, deck)


def test_agg_no_moves_nonempty():
    deck = list('QZZZZQZ')
    def setup(game: Game):
        game.board[7, 6:10] = list('STAR')
    _run_case("AGG TEST 6: Non-Empty - Likely No Moves with Hard Deck", setup, deck)


def test_agg_wildcard_usage():
    deck = list('A-EINRT')
    def setup(game: Game):
        game.board[7, 6:10] = list('STAR')
        game.board[5:9, 12] = list('MEAN')
    _run_case("AGG TEST 7: Non-Empty - Wildcard Deck", setup, deck)


if __name__ == "__main__":
    # Run all tests when executed directly
    test_agg_empty_board_opening()
    test_agg_empty_board_no_moves()
    test_agg_single_word_extension()
    test_agg_crossword_opportunity()
    test_agg_dense_channel()
    test_agg_no_moves_nonempty()
    test_agg_wildcard_usage()

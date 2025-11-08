import os
import sys
import numpy as np

# Ensure project root is on sys.path when running this file directly
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from resources.rule_definitions import Rule
from utils.players.longest_word import OptimiserLength
from utils.players.prized_cells import OptimiserPrize
from utils.matrix.game_state import Game


PLAYERS = {
    'LongestWord': lambda rule, game: OptimiserLength(rule, game),
    'PrizeCells': lambda rule, game: OptimiserPrize(rule, game),
}


def _print_additions(game, additions_list, limit=10, prefix=""):
    if prefix:
        print(prefix)
    print(f"  Found {len(additions_list)} move(s):")
    for i, adds in enumerate(additions_list[:limit], 1):
        word_positions = sorted(adds, key=lambda x: (x[1][0], x[1][1]))
        word = ''.join(ch.upper() for ch, _ in word_positions)
        positions = [(pos[0], pos[1]) for _, pos in word_positions]
        try:
            score = game.score_calculator(adds)
            direction = (
                'Horizontal' if len(set(p[0] for p in positions)) == 1 else
                'Vertical' if len(set(p[1] for p in positions)) == 1 else
                'Mixed'
            )
            print(f"\n    Move {i}: {word} ({direction}) - Score: {score}")
            print(f"    Positions: {positions}")
            print(f"    Additions: {adds}")
        except Exception as e:
            print(f"\n    Move {i}: Error scoring - {e}")
    if len(additions_list) > limit:
        print(f"\n    ... and {len(additions_list) - limit} more moves")


def _run_players_on_case(title, setup_board_fn, deck):
    print("="*100)
    print(title)
    print("="*100)
    rule = Rule('resources/twl06_scrabble_dic_american.txt')

    # Prepare per-player games with identical boards
    games = {name: Game(rule) for name in PLAYERS}
    for name, game in games.items():
        setup_board_fn(game)

    # Print shared board and deck once (use one of the games)
    any_game = next(iter(games.values()))
    print(f"Deck: {deck}")
    print("\nBoard state:")
    any_game.print_board()

    print("\nRecommendations by player:")
    for name, game in games.items():
        optimiser = PLAYERS[name](rule, game)
        try:
            rec = optimiser.recommend_next_move(deck)
        except Exception as e:
            print(f"- {name}: Error during recommendation: {e}")
            continue
        
        # Empty result
        if not rec:
            print(f"- {name}: No valid moves found.")
            continue
            
        # Check if it's a list of words (strings) - LongestWord empty board case
        if isinstance(rec[0], str):
            base_len = len(rec[0])
            print(f"- {name}: {len(rec)} candidate word(s) of length {base_len} (showing up to 10):")
            for i, w in enumerate(rec[:10], 1):
                print(f"    {i}. {w}")
            if len(rec) > 10:
                print(f"    ... and {len(rec) - 10} more")
        # List of additions (list of tuples)
        elif isinstance(rec[0], list):
            _print_additions(game, rec, limit=10, prefix=f"- {name}:")
        else:
            print(f"- {name}: Unexpected output format -> {type(rec)}: {rec}")
    print()


def test_empty_board():
    deck = list('AEINRST')
    def setup(game: Game):
        pass  # empty board
    _run_players_on_case("TEST 1: Empty Board Opening", setup, deck)


def test_single_word_extension():
    deck = list('AEINRTS')
    def setup(game: Game):
        game.board[7, 6:10] = list('STAR')
    _run_players_on_case("TEST 2: Single Existing Word - Extension", setup, deck)


def test_interlocking_words():
    deck = list('INGBLEO')
    def setup(game: Game):
        game.board[7, 6:10] = list('STAR')
        game.board[5:9, 9] = list('RATE')
    _run_players_on_case("TEST 3: Interlocking Words Scenario", setup, deck)


def test_blank_tile_usage():
    deck = list('AEIO-RS')
    def setup(game: Game):
        game.board[7, 6:9] = list('CAT')
    _run_players_on_case("TEST 4: Blank Tile Usage", setup, deck)


def test_crowded_board():
    deck = list('ABCDEFG')
    def setup(game: Game):
        game.board[7, 4:8] = list('WORD')
        game.board[7, 10:14] = list('PLAY')
        game.board[5:9, 7] = list('DEAR')
        game.board[9:13, 7] = list('ZEST')
    _run_players_on_case("TEST 5: Crowded Board - Limited Spaces", setup, deck)


def test_high_multiplier_focus():
    deck = list('TOLINE-')
    def setup(game: Game):
        game.board[7,7] = 'A'
        game.board[7,6] = 'R'
        game.board[6,7] = 'E'
    _run_players_on_case("TEST 6: High Multiplier Focus (Multiple prized targets)", setup, deck)


def test_no_valid_moves():
    """Test case where no valid moves can be formed (impossible deck/board combo)"""
    deck = list('ZZZQQQX')  # Very constrained letters
    def setup(game: Game):
        # Create a board with limited anchor opportunities and words that don't work with the deck
        game.board[7, 7] = 'A'
        game.board[7, 8] = 'B'
        game.board[7, 9] = 'C'
        game.board[8, 7] = 'D'
        game.board[9, 7] = 'E'
        game.board[6, 7] = 'F'
        # Anchors exist but deck letters can't form valid words with these fixed letters
    _run_players_on_case("TEST 7: No Valid Moves (Impossible Deck)", setup, deck)


def test_dense_midboard_corridors():
    """Dense mid-board with multiple lanes around a vertical column to create tight placement corridors."""
    deck = list('EIRSTLA')
    def setup(game: Game):
        # Two parallel horizontals
        game.board[6, 3:9] = list('STREAM')   # row 6, cols 3-8
        game.board[8, 3:9] = list('PLANER')   # row 8, cols 3-8
        # A vertical nearby creating side corridors (no intersection with above)
        game.board[5:10, 10] = list('ROTOR')  # col 10, rows 5-9
    _run_players_on_case("TEST 8: Dense Mid-board Corridors", setup, deck)


def test_edge_premium_snipes():
    """Crowded near the right edge to encourage premium-square snipes and edge-fitting plays."""
    deck = list('AXLESR-')
    def setup(game: Game):
        # Horizontal hugging the right edge
        game.board[7, 10:15] = list('AXLES')  # row 7, cols 10-14
        # Vertical nearby to add anchors
        game.board[4:9, 9] = list('REEDS')    # col 9, rows 4-8
    _run_players_on_case("TEST 9: Edge Premium Snipes", setup, deck)


def test_double_row_channels():
    """Two dense horizontal rows with a clear row in between: invites cross placements bridging both."""
    deck = list('HOOKING')
    def setup(game: Game):
        game.board[6, 4:9] = list('RANGE')    # row 6, cols 4-8
        game.board[8, 4:9] = list('TONES')    # row 8, cols 4-8
        # Add a separate vertical column to increase anchors (avoid overlapping conflicts)
        game.board[5:11, 12] = list('LADDER') # col 12, rows 5-10
    _run_players_on_case("TEST 10: Double Row Channels (Bridge Opportunities)", setup, deck)


def test_staggered_bands():
    """Staggered bands of letters across three rows to force constrained interlocks and hooks."""
    deck = list('RETURNS')
    def setup(game: Game):
        game.board[5, 3:10] = list('SILENCE')   # row 5, cols 3-9
        game.board[7, 3:10] = list('HUMMERS')   # row 7, cols 3-9
        # Add a couple of isolated hooks on the middle row
        game.board[6, 2] = 'A'
        game.board[6, 10] = 'B'
    _run_players_on_case("TEST 11: Staggered Bands with Side Hooks", setup, deck)


if __name__ == '__main__':
    test_empty_board()
    test_single_word_extension()
    test_interlocking_words()
    test_blank_tile_usage()
    test_crowded_board()
    test_high_multiplier_focus()
    test_no_valid_moves()
    test_dense_midboard_corridors()
    test_edge_premium_snipes()
    test_double_row_channels()
    test_staggered_bands()
    print("="*100)
    print("All player recommendation tests complete!")
    print("="*100)

import pytest
import numpy as np
from utils.game_state import Game


class WildcardRule:
    """Test rule with wildcards and expanded dictionary for wildcard testing."""
    def __init__(self):
        # simple letter points for tests (uppercase keys, wildcard is 0)
        self.letter_points = {'-': 0, **{ch: 1 for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}}
        # default multipliers (no special squares)
        self.word_multiplier = np.ones((15, 15), dtype=np.int8)
        self.letter_multiplier = np.ones((15, 15), dtype=np.int8)
        # dictionary for wildcard testing (lowercase)
        self.scrabble_dictionary = set(['cat', 'bat', 'rat', 'mat', 'hat', 'at', 'a', 
                                         'cab', 'tab', 'dab', 'ab',
                                         'car', 'bar', 'tar', 'jar', 'ar',
                                         'ca', 'ba', 'ta', 'da', 'ma', 'ha'])


def test_wildcard_single_option():
    """Test wildcard with only one valid letter option."""
    rule = WildcardRule()
    rule.scrabble_dictionary = set(['cat', 'at'])  # Only 'A' works for C-T
    game = Game(rule)
    
    # Play 'C-T' at center (wildcard must be 'A' to form 'CAT')
    additions = [('C', [7, 7]), ('-', [7, 8]), ('T', [7, 9])]
    
    # Should pass validation and replace '-' with lowercase 'a'
    assert game._check_word_valid(additions) is True
    assert additions[1][0] == 'a', f"Expected 'a', got {additions[1][0]}"


def test_wildcard_multiple_options_random_choice():
    """Test that wildcard randomly chooses among valid options."""
    rule = WildcardRule()
    game = Game(rule)
    
    # Play '-AT' at center (wildcard can be C, B, R, M, H - multiple valid words)
    additions = [('-', [7, 7]), ('A', [7, 8]), ('T', [7, 9])]
    
    # Should pass and replace with one of the valid lowercase letters
    assert game._check_word_valid(additions) is True
    assert additions[0][0].islower(), f"Expected lowercase, got {additions[0][0]}"
    assert additions[0][0] in 'cbrmh', f"Unexpected letter: {additions[0][0]}"


def test_wildcard_with_existing_tiles():
    """Test wildcard when it forms cross words with existing tiles."""
    rule = WildcardRule()
    # Add 2-letter words to dictionary for this test
    rule.scrabble_dictionary.update(['ab', 'at', 'ar', 'br'])
    game = Game(rule)
    
    # Pre-place 'B' vertically above wildcard position
    game.board[6, 8] = 'B'
    # Play 'C-T' horizontally at center where wildcard at (7,8) is below 'B'
    # This will form: horizontal CAT and vertical B[wildcard] (2-letter word)
    additions = [('C', [7, 7]), ('-', [7, 8]), ('T', [7, 9])]
    
    # Should find 'a' to make CAT horizontal and BA vertical (not a word),
    # OR 'r' to make CRT horizontal (not a word) and BR vertical
    # Since only CAT is valid horizontally, wildcard must be 'a', 
    # but 'BA' isn't in dictionary... Let me reconsider
    # Actually with B above, if wildcard is 'a': horizontal=CAT✓, vertical=BA✗
    # If wildcard is 'r': horizontal=CRT✗, vertical=BR✓
    # We need a letter that makes BOTH valid!
    
    # Let's change: Pre-place 'C' above, so C + wildcard can form CA, CR, etc.
    game.board[6, 8] = 'C'
    # If wildcard='a': horizontal=CAT✓, vertical=CA✗ (not in dict)
    # If wildcard='r': horizontal=CRT✗, vertical=CR✗
    # We need CA or CAR in dictionary
    rule.scrabble_dictionary.add('ca')
    
    # Reset board
    game.board = np.full((15, 15), '', dtype='U1')
    game.board[6, 8] = 'C'
    additions = [('C', [7, 7]), ('-', [7, 8]), ('T', [7, 9])]
    
    # Should find 'a' to make CAT horizontal and CA vertical
    assert game._check_word_valid(additions) is True
    assert additions[1][0].islower()
    assert additions[1][0] == 'a', f"Expected 'a' (forming CAT and CA), got '{additions[1][0]}'"


def test_wildcard_scores_zero():
    """Test that wildcards (now lowercase) score 0 points in _score_calculator."""
    rule = WildcardRule()
    game = Game(rule)
    
    # Manually set up a board with uppercase letters and a lowercase wildcard
    additions = [('C', [7, 7]), ('a', [7, 8]), ('T', [7, 9])]  # lowercase 'a' = blank
    
    # Score should be C(1) + a(0) + T(1) = 2
    score = game._score_calculator(additions)
    assert score == 2, f"Expected score 2 (blank scores 0), got {score}"


def test_wildcard_no_valid_letter():
    """Test that if no valid letter exists for wildcard, ValueError is raised."""
    rule = WildcardRule()
    rule.scrabble_dictionary = set(['xyz'])  # Very limited dictionary
    game = Game(rule)
    
    # Try to play 'A-' at center; no completion will form 'xyz'
    additions = [('A', [7, 7]), ('-', [7, 8])]
    
    with pytest.raises(ValueError, match="No valid letter"):
        game._check_word_valid(additions)


def test_two_wildcards_exhaustive():
    """Test two wildcards - should exhaustively test all 26x26 combinations."""
    rule = WildcardRule()
    rule.scrabble_dictionary = set(['cab', 'ab'])
    game = Game(rule)
    
    # Play '-A-' at center (both wildcards)
    additions = [('-', [7, 7]), ('A', [7, 8]), ('-', [7, 9])]
    
    # Should find C and B to form 'CAB'
    assert game._check_word_valid(additions) is True
    assert additions[0][0].islower()
    assert additions[2][0].islower()
    
    # Verify the formed word is valid
    word = additions[0][0].upper() + 'A' + additions[2][0].upper()
    assert word.lower() in rule.scrabble_dictionary


def test_wildcard_with_multipliers():
    """Test that wildcards still trigger word multipliers even though letter value is 0."""
    rule = WildcardRule()
    # Set center square as double word score
    rule.word_multiplier[7, 7] = 2
    game = Game(rule)
    
    # Play '-AT' with wildcard on DW square
    additions = [('-', [7, 7]), ('A', [7, 8]), ('T', [7, 9])]
    
    # First validate (wildcard will be resolved to lowercase)
    assert game._check_word_valid(additions) is True
    
    # Score should be: wildcard(0) + A(1) + T(1) = 2, then ×2 for DW = 4
    score = game._score_calculator(additions)
    assert score == 4, f"Expected score 4 (DW with blank), got {score}"


def test_full_move_with_wildcard():
    """Test complete new_move flow with wildcard including validation and scoring."""
    rule = WildcardRule()
    game = Game(rule)
    
    # Play 'C-T' at center (wildcard will be resolved to 'a')
    additions = [('C', [7, 7]), ('-', [7, 8]), ('T', [7, 9])]
    
    # new_move should succeed, validate, resolve wildcard, and return score
    score = game.new_move(additions)
    assert score > 0, "Should return positive score"
    
    # Board should have uppercase letters for display
    assert game.board[7, 7] == 'C'
    assert game.board[7, 8] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # Uppercase on board
    assert game.board[7, 9] == 'T'
    
    # Verify the formed word is valid
    word = game.board[7, 7] + game.board[7, 8] + game.board[7, 9]
    assert word.lower() in rule.scrabble_dictionary


def test_wildcard_uppercase_input_required():
    """Test that regular tiles must be uppercase, wildcards are '-'."""
    rule = WildcardRule()
    game = Game(rule)
    
    # Correct usage: uppercase letters + '-' for wildcard
    additions = [('C', [7, 7]), ('-', [7, 8]), ('T', [7, 9])]
    assert game._check_word_valid(additions) is True
    
    # After resolution, wildcard becomes lowercase
    assert additions[0][0] == 'C'  # Still uppercase
    assert additions[1][0].islower()  # Resolved to lowercase
    assert additions[2][0] == 'T'  # Still uppercase


def test_wildcard_cross_word_constraint():
    """Test that wildcard resolution respects both main and cross word validity."""
    rule = WildcardRule()
    rule.scrabble_dictionary = set(['cat', 'at', 'car', 'ar'])  # Limited dictionary
    game = Game(rule)
    
    # Pre-place 'R' below center to constrain wildcard choices
    game.board[8, 8] = 'R'
    
    # Play 'C-T' at center, wildcard at (7,8) must form valid vertical word with 'R' at (8,8)
    additions = [('C', [7, 7]), ('-', [7, 8]), ('T', [7, 9])]
    
    # Should resolve wildcard to 'a' since 'AR' is valid ('CAT' and 'AR' both valid)
    assert game._check_word_valid(additions) is True
    assert additions[1][0] == 'a', f"Expected 'a', got {additions[1][0]}"

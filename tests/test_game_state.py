import pytest
import numpy as np

from utils.matrix.game_state import Game


class TestRule:
    def __init__(self):
        # simple letter points for tests (uppercase keys to match input)
        self.letter_points = {'-': 0, **{ch: 1 for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}}
        # default multipliers (no special squares)
        self.word_multiplier = np.ones((15, 15), dtype=np.int8)
        self.letter_multiplier = np.ones((15, 15), dtype=np.int8)
        # minimal dictionary used for validation (lowercase for matching)
        self.scrabble_dictionary = set(['to', 'top', 'a', 'at', 'p'])


def test_first_move_cover_center():
    rule = TestRule()
    game = Game(rule)
    additions = [('A', [7, 7])]
    assert game._verify_word_addition(additions) is True
    assert game._check_board_valid(additions) is True


def test_first_move_must_cover_center_raises():
    rule = TestRule()
    game = Game(rule)
    additions = [('A', [0, 0])]
    assert game._verify_word_addition(additions) is True
    with pytest.raises(ValueError):
        game._check_board_valid(additions)


def test_overlap_rejected():
    rule = TestRule()
    game = Game(rule)
    # place a letter manually
    game.board[7, 7] = 'A'
    additions = [('B', [7, 7])]
    with pytest.raises(ValueError):
        game._verify_word_addition(additions)


def test_non_continuous_rejected():
    rule = TestRule()
    game = Game(rule)
    additions = [('A', [7, 7]), ('B', [7, 9])]
    with pytest.raises(ValueError):
        game._verify_word_addition(additions)


def test_get_all_affected_words_horizontal_and_cross():
    rule = TestRule()
    game = Game(rule)
    # pre-place 'TO' at (7,6),(7,7)
    game.board[7, 6] = 'T'
    game.board[7, 7] = 'O'
    additions = [('P', [7, 8])]
    words = game._get_all_affected_words(additions)
    assert 'TOP' in words


def test_update_valid_move_updates_board_and_validates_words():
    rule = TestRule()
    game = Game(rule)
    # pre-place 'TO' at (7,6),(7,7)
    game.board[7, 6] = 'T'
    game.board[7, 7] = 'O'
    additions = [('P', [7, 8])]
    # new_move should succeed because 'TOP' is in TestRule.scrabble_dictionary
    score = game.new_move(additions)
    assert score > 0  # Should return a positive score
    assert game.board[7, 8] == 'P'


def test_get_all_affected_words_vertical_and_cross():
    rule = TestRule()
    game = Game(rule)
    # pre-place 'TO' vertically at (6,7),(7,7)
    game.board[6, 7] = 'T'
    game.board[7, 7] = 'O'
    additions = [('P', [8, 7])]
    words = game._get_all_affected_words(additions)
    assert 'TOP' in words


def test_cross_word_formation():
    rule = TestRule()
    game = Game(rule)
    # pre-place 'T' at (7,7)
    game.board[7, 7] = 'T'
    # Add 'O' and 'P' to the right to form TOP
    additions = [('O', [7, 8]), ('P', [7, 9])]
    words = game._get_all_affected_words(additions)
    assert 'TOP' in words


def test_update_rejects_invalid_dictionary_word():
    rule = TestRule()
    # remove 'TOP' from dictionary to force rejection
    rule.scrabble_dictionary = set(['to', 'a', 'at', 'p'])
    game = Game(rule)
    game.board[7, 6] = 'T'
    game.board[7, 7] = 'O'
    additions = [('P', [7, 8])]
    with pytest.raises(ValueError):
        game.new_move(additions)


def test_check_board_valid_requires_touch():
    rule = TestRule()
    game = Game(rule)
    # place an unrelated tile far away
    game.board[0, 0] = 'A'
    additions = [('B', [7, 7])]
    # positional verification should pass (within bounds/continuous)
    assert game._verify_word_addition(additions) is True
    # but board-level check should fail because it doesn't touch existing tiles
    with pytest.raises(ValueError):
        game._check_board_valid(additions)


def test_print_board_runs():
    rule = TestRule()
    game = Game(rule)
    # place a letter to make output non-trivial
    game.board[7, 7] = 'A'
    # ensure print_board runs without error
    assert game.print_board() is None


def test_invalid_main_word_rejected():
    rule = TestRule()
    # Remove TOP so main word TOP is invalid
    rule.scrabble_dictionary = set(['to', 'a', 'at', 'p'])
    game = Game(rule)
    game.board[7, 6] = 'T'
    game.board[7, 7] = 'O'
    additions = [('X', [7, 8])]
    with pytest.raises(ValueError):
        game.new_move(additions)


def test_cross_word_invalid_rejected():
    rule = TestRule()
    game = Game(rule)
    # Pre-place a letter above the planned addition to create a cross word
    game.board[6, 8] = 'B'
    # Pre-place T to form main word TO with new O at (7,8)
    game.board[7, 7] = 'T'
    additions = [('O', [7, 8])]
    # 'TO' is valid in TestRule but 'BO' (the cross) is not, so new_move should raise
    with pytest.raises(ValueError):
        game.new_move(additions)


def test_valid_multi_letter_addition():
    rule = TestRule()
    game = Game(rule)
    # First move: must cover center, add 'AT' horizontally
    additions = [('A', [7, 7]), ('T', [7, 8])]
    score = game.new_move(additions)
    assert score > 0
    assert game.board[7, 7] == 'A' and game.board[7, 8] == 'T'

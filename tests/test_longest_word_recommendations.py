import os
import sys
import numpy as np

# Ensure project root is on sys.path when running this file directly
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from resources.rule_definitions import Rule
from utils.players.longest_word import OptimiserLength
from utils.matrix.game_state import Game


def test_empty_board():
    """Test recommendations on an empty board (first move)"""
    print("="*80)
    print("TEST 1: Empty Board - First Move")
    print("="*80)
    
    rule = Rule('resources/twl06_scrabble_dic_american.txt')
    game = Game(rule)
    optimizer = OptimiserLength(rule, game)
    
    deck = list('AEINRST')  # Common letters
    
    print(f"Deck: {deck}")
    print("\nBoard state:")
    game.print_board()
    
    print("\nRecommendations:")
    recommendations = optimizer.recommend_next_move(deck)
    
    if isinstance(recommendations, list) and recommendations and isinstance(recommendations[0], str):
        # Empty board returns list of words
        print(f"Found {len(recommendations)} longest word(s) of length {len(recommendations[0]) if recommendations else 0}:")
        for i, word in enumerate(recommendations[:10], 1):  # Show first 10
            print(f"  {i}. {word}")
        if len(recommendations) > 10:
            print(f"  ... and {len(recommendations) - 10} more")
    else:
        print("Unexpected format for empty board recommendations")
    print()


def test_single_word_board():
    """Test recommendations when there's one word on the board"""
    print("="*80)
    print("TEST 2: Single Word on Board - Extending")
    print("="*80)
    
    rule = Rule('resources/twl06_scrabble_dic_american.txt')
    game = Game(rule)
    optimizer = OptimiserLength(rule, game)
    
    # Place a starting word
    game.board[7, 6:10] = list('STAR')
    
    deck = list('AEINRTS')
    
    print(f"Deck: {deck}")
    print("\nBoard state:")
    game.print_board()
    
    print("\nRecommendations:")
    recommendations = optimizer.recommend_next_move(deck)
    
    print(f"Found {len(recommendations)} highest-scoring move(s):")
    for i, additions in enumerate(recommendations[:5], 1):  # Show first 5
        word_positions = sorted(additions, key=lambda x: (x[1][0], x[1][1]))
        word = ''.join(ch for ch, _ in word_positions)
        positions = [(pos[0], pos[1]) for _, pos in word_positions]
        
        # Calculate score
        try:
            score = game.score_calculator(additions)
            print(f"\n  {i}. Word: {word}")
            print(f"     Positions: {positions}")
            print(f"     Score: {score}")
            print(f"     Additions: {additions[:5]}{'...' if len(additions) > 5 else ''}")
        except Exception as e:
            print(f"\n  {i}. Error scoring: {e}")
    
    if len(recommendations) > 5:
        print(f"\n  ... and {len(recommendations) - 5} more")
    print()


def test_multiple_words_board():
    """Test recommendations on a more complex board"""
    print("="*80)
    print("TEST 3: Multiple Words on Board - Complex Scenario")
    print("="*80)
    
    rule = Rule('resources/twl06_scrabble_dic_american.txt')
    game = Game(rule)
    optimizer = OptimiserLength(rule, game)
    
    # Place multiple words
    game.board[7, 6:10] = list('STAR')
    game.board[5:9, 9] = list('RATE')
    
    deck = list('INGBLEO')
    
    print(f"Deck: {deck}")
    print("\nBoard state:")
    game.print_board()
    
    print("\nRecommendations:")
    recommendations = optimizer.recommend_next_move(deck)
    
    print(f"Found {len(recommendations)} highest-scoring move(s):")
    for i, additions in enumerate(recommendations[:5], 1):
        word_positions = sorted(additions, key=lambda x: (x[1][0], x[1][1]))
        word = ''.join(ch for ch, _ in word_positions)
        positions = [(pos[0], pos[1]) for _, pos in word_positions]
        
        # Determine direction
        if len(set(p[0] for p in positions)) == 1:
            direction = "Horizontal"
        elif len(set(p[1] for p in positions)) == 1:
            direction = "Vertical"
        else:
            direction = "Mixed (error?)"
        
        try:
            score = game.score_calculator(additions)
            print(f"\n  {i}. Word: {word} ({direction})")
            print(f"     Positions: {positions}")
            print(f"     Score: {score}")
            print(f"     Letters placed: {len(additions)}")
        except Exception as e:
            print(f"\n  {i}. Error: {e}")
    
    if len(recommendations) > 5:
        print(f"\n  ... and {len(recommendations) - 5} more")
    print()


def test_with_blank_tile():
    """Test recommendations when deck contains a blank tile"""
    print("="*80)
    print("TEST 4: Deck with Blank Tile")
    print("="*80)
    
    rule = Rule('resources/twl06_scrabble_dic_american.txt')
    game = Game(rule)
    optimizer = OptimiserLength(rule, game)
    
    # Place a word
    game.board[7, 6:9] = list('CAT')
    
    deck = list('AEIO-RS')  # '-' represents a blank tile
    
    print(f"Deck: {deck} (note: '-' is a blank tile)")
    print("\nBoard state:")
    game.print_board()
    
    print("\nRecommendations:")
    recommendations = optimizer.recommend_next_move(deck)
    
    print(f"Found {len(recommendations)} highest-scoring move(s):")
    for i, additions in enumerate(recommendations[:5], 1):
        word_positions = sorted(additions, key=lambda x: (x[1][0], x[1][1]))
        word = ''.join(ch.upper() for ch, _ in word_positions)  # uppercase for display
        positions = [(pos[0], pos[1]) for _, pos in word_positions]
        blanks = [(ch, pos) for ch, pos in additions if ch.islower()]
        
        try:
            score = game.score_calculator(additions)
            print(f"\n  {i}. Word: {word}")
            print(f"     Positions: {positions}")
            print(f"     Score: {score}")
            if blanks:
                blank_letters = ', '.join([f"{ch.upper()} at {pos}" for ch, pos in blanks])
                print(f"     Blank(s) used as: {blank_letters}")
            print(f"     Letters placed: {len(additions)}")
            print(f"     Full additions: {additions}")
        except Exception as e:
            print(f"\n  {i}. Error: {e}")
    
    if len(recommendations) > 5:
        print(f"\n  ... and {len(recommendations) - 5} more")
    print()


def test_crowded_board():
    """Test recommendations on a crowded board with limited options"""
    print("="*80)
    print("TEST 5: Crowded Board - Limited Spaces")
    print("="*80)
    
    rule = Rule('resources/twl06_scrabble_dic_american.txt')
    game = Game(rule)
    optimizer = OptimiserLength(rule, game)
    
    # Create a more filled board
    game.board[7, 4:8] = list('WORD')
    game.board[7, 10:14] = list('PLAY')
    game.board[5:9, 7] = list('DEAR')
    game.board[9:13, 7] = list('ZEST')
    
    deck = list('ABCDEFG')
    
    print(f"Deck: {deck}")
    print("\nBoard state:")
    game.print_board()
    
    print("\nRecommendations:")
    recommendations = optimizer.recommend_next_move(deck)
    
    if not recommendations:
        print("No valid moves found!")
    else:
        print(f"Found {len(recommendations)} highest-scoring move(s):")
        for i, additions in enumerate(recommendations[:5], 1):
            word_positions = sorted(additions, key=lambda x: (x[1][0], x[1][1]))
            word = ''.join(ch for ch, _ in word_positions)
            
            try:
                score = game.score_calculator(additions)
                print(f"\n  {i}. Word: {word}")
                print(f"     Score: {score}")
                print(f"     Additions: {additions}")
            except Exception as e:
                print(f"\n  {i}. Error: {e}")
        
        if len(recommendations) > 5:
            print(f"\n  ... and {len(recommendations) - 5} more")
    print()


if __name__ == '__main__':
    test_empty_board()
    test_single_word_board()
    test_multiple_words_board()
    test_with_blank_tile()
    test_crowded_board()
    
    print("="*80)
    print("All recommendation tests complete!")
    print("="*80)

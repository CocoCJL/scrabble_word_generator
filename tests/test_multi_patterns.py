import os
import sys
import numpy as np

# Ensure project root is on sys.path when running this file directly
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from resources.rule_definitions import Rule
from utils.players.longest_word import OptimiserLength

def test_multi_patterns():
    """Test that multiple patterns are generated when blocks exist on both sides"""
    
    rule = Rule('resources/twl06_scrabble_dic_american.txt')
    optimizer = OptimiserLength(rule)
    
    # Test Case 1: Blocks on both sides with 7-letter rack
    print("="*80)
    print("TEST 1: Blocks on both sides (7-letter rack)")
    print("="*80)
    board1 = np.full((15, 15), '', dtype='U1')
    board1[7, 4:7] = list('CAT')   # Left: CAT at positions 4-6
    board1[7, 10:13] = list('DOG')  # Right: DOG at positions 10-12
    # Anchor at position 8 (between CAT and DOG)
    anchor = (7, 8)
    rack = 'ABCDEFG'  # 7 letters
    
    optimizer.game.board = board1
    patterns = optimizer._build_all_dynamic_patterns(rack, anchor, 'H')
    
    print(f"Board: ...CAT_[anchor]_DOG...")
    print(f"Anchor at column 8, CAT at 4-6, DOG at 10-12")
    print(f"Rack: {rack} (7 letters)")
    print(f"\nNumber of patterns generated: {len(patterns)}")
    print("\nPatterns:")
    for i, (pattern, fixed, meta) in enumerate(patterns, 1):
        print(f"\n{i}. Pattern: '{pattern}'")
        print(f"   Fixed letters: '{fixed}'")
        print(f"   Left blocks: {meta['left_blocks']}, gaps: {meta['left_gaps']}, tail: {meta['left_tail']}")
        print(f"   Right blocks: {meta['right_blocks']}, gaps: {meta['right_gaps']}, tail: {meta['right_tail']}")
        
        # Calculate cost
        cost = 1  # anchor
        for g in meta['left_gaps']:
            cost += g
        for g in meta['right_gaps']:
            cost += g
        print(f"   Cost (anchor + gaps): {cost}")
    
    print("\n" + "="*80)
    print("Expected patterns should include:")
    print("1. Both CAT and DOG included (if reachable)")
    print("2. Only CAT included, max right tail")
    print("3. Only DOG included, max left tail")
    print("4. Neither included, max tails on both sides")
    print("="*80)
    
    # Test Case 2: Blocks on both sides, small rack (can't reach both)
    print("\n" + "="*80)
    print("TEST 2: Blocks on both sides (3-letter rack, can't reach both)")
    print("="*80)
    board2 = np.full((15, 15), '', dtype='U1')
    board2[7, 4] = 'A'     # Left: A at position 4
    board2[7, 11] = 'Z'    # Right: Z at position 11
    anchor2 = (7, 8)       # Anchor at position 8
    rack2 = 'ABC'          # Only 3 letters
    
    optimizer.game.board = board2
    patterns2 = optimizer._build_all_dynamic_patterns(rack2, anchor2, 'H')
    
    print(f"Board: ...A___[anchor]__Z...")
    print(f"Anchor at column 8, A at 4, Z at 11")
    print(f"Rack: {rack2} (3 letters)")
    print(f"\nNumber of patterns generated: {len(patterns2)}")
    print("\nPatterns:")
    for i, (pattern, fixed, meta) in enumerate(patterns2, 1):
        print(f"\n{i}. Pattern: '{pattern}'")
        print(f"   Fixed letters: '{fixed}'")
        print(f"   Left: blocks={meta['left_blocks']}, gaps={meta['left_gaps']}, tail={meta['left_tail']}")
        print(f"   Right: blocks={meta['right_blocks']}, gaps={meta['right_gaps']}, tail={meta['right_tail']}")
    
    print("\n" + "="*80)
    print("Expected: Can't include both A and Z (need 1 anchor + 3 left gaps + 2 right gaps = 6 > 3)")
    print("Should have patterns for: A only, Z only, neither")
    print("="*80)
    
    # Test Case 3: Multiple blocks on one side
    print("\n" + "="*80)
    print("TEST 3: Multiple blocks on left, none on right")
    print("="*80)
    board3 = np.full((15, 15), '', dtype='U1')
    board3[7, 2] = 'X'
    board3[7, 4:6] = list('AB')
    anchor3 = (7, 8)
    rack3 = 'ABCDEFG'
    
    optimizer.game.board = board3
    patterns3 = optimizer._build_all_dynamic_patterns(rack3, anchor3, 'H')
    
    print(f"Board: .X_AB__[anchor]......")
    print(f"Anchor at column 8, X at 2, AB at 4-5")
    print(f"Rack: {rack3} (7 letters)")
    print(f"\nNumber of patterns generated: {len(patterns3)}")
    print("\nPatterns:")
    for i, (pattern, fixed, meta) in enumerate(patterns3, 1):
        print(f"\n{i}. Pattern: '{pattern}'")
        print(f"   Fixed: '{fixed}', Left blocks: {meta['left_blocks']}")
    
    print("\n" + "="*80)
    print("Expected: Single pattern (blocks only on one side)")
    print("="*80)

if __name__ == '__main__':
    test_multi_patterns()
    print("\n" + "="*80)
    print("All tests complete!")
    print("="*80)

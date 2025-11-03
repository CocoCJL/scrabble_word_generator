from utils.linear.simple_pattern_generator import SimplePatternGenerator
from utils.linear.dynamic_pattern_generator import DynamicPatternGenerator
from utils.matrix.game_state import Game

import numpy as np
from collections import Counter

class OptimiserLength:
    # recommendations based on longest possible words from current deck and board
    def __init__(self, rule, game=None):
        self.rule = rule
        self.spg = SimplePatternGenerator()
        self.dpg = DynamicPatternGenerator(self.spg)
        self.game = game if game else Game(rule)

    def _find_start_word(self, deck, upper_bound):
        """
        Find the longest valid word that can be formed from the deck.
        
        Args:
            deck: List of letters (e.g., ['A', 'B', 'C', 'D', 'E', 'F', 'G'])
            upper_bound: Maximum number of letters to use from the deck (1-indexed)
        
        Returns:
            str: The longest valid word found, or empty string if no valid word exists
        """
        if upper_bound < 1 or upper_bound > len(deck):
            upper_bound = len(deck)
        
        # Convert deck list to string for pattern generator
        deck_str = ''.join(deck[:upper_bound])
        
        # Try patterns from longest to shortest: "________" down to "_"
        for length in range(upper_bound, 0, -1):
            pattern = '_' * length
            
            # Generate all words matching this pattern
            matching_words = self.spg.generate(
                pattern, 
                deck_str, 
                self.rule.scrabble_dictionary
            )
            
            # Return all valid matches 
            if matching_words:
                return matching_words
        return []

    def recommend_next_move(self, deck):
        """
        Recommend next moves by generating possible words from anchors.

        Logic:
        - If board is empty: use _find_start_word and return the matching words list
        - Else:
          1) Find all anchor positions (empty cells adjacent to any occupied cell)
          2) For each anchor, build a dynamic pattern horizontally and vertically
             that respects board letters and boundaries
          3) Use DynamicPatternGenerator to generate possible words for each pattern

        Args:
            board (np.ndarray): 15x15 board with '' for empty and letters in occupied cells
            deck (List[str]): rack letters; '-' denotes a blank tile

        Returns:
            If empty board: List[str] of start words (longest-first logic in _find_start_word)
            Else: List[List[Tuple[str, [int,int]]]] additions for the highest-scoring move(s) among the longest possible words formed.
        """

        board = self.game.board

        # Empty board check
        if np.sum(board != '') == 0:
            return self._find_start_word(deck, len(deck))

        # Find all anchors (empty cells that touch any occupied cell orthogonally)
        anchors = self._find_anchor_positions()

        # Collect candidate additions (filtered per-pattern by longest words)
        candidates = []
        seen_additions = set()
        deck_base = ''.join(deck).upper()

        for (r, c) in anchors:
            # Horizontal patterns (may be multiple if blocks on both sides)
            h_patterns = self._build_all_dynamic_patterns(deck, (r, c), axis='H')
            for h_pattern, h_fixed, h_meta in h_patterns:
                h_deck = deck_base + h_fixed  # include fixed board letters used by the pattern
                try:
                    h_words = self.dpg.generate(h_pattern, h_deck, self.rule.scrabble_dictionary)
                except Exception:
                    h_words = []

                if not h_words:
                    continue

                # Sort words by length descending - longest first
                h_words.sort(key=len, reverse=True)
                
                # Find first valid word (which will be longest valid)
                found_valid = False
                for word in h_words:
                    if found_valid:
                        break  # Already found longest valid word for this pattern
                        
                    additions_sets = self._materialize_additions_from_words(
                        axis='H', anchor=(r, c), words=[word], meta=h_meta, rack=deck_base
                    )
                    for adds in additions_sets:
                        try:
                            # Validate cross-words and dictionary before accepting
                            if self.game._check_word_valid(adds):
                                key = tuple((ch, pos[0], pos[1]) for ch, pos in adds)
                                if key not in seen_additions:
                                    seen_additions.add(key)
                                    candidates.append(adds)
                                    found_valid = True
                                    break  # Found valid word, stop checking this word's placements
                        except (ValueError, Exception):
                            continue

            # Vertical patterns (may be multiple if blocks on both sides)
            v_patterns = self._build_all_dynamic_patterns(deck, (r, c), axis='V')
            for v_pattern, v_fixed, v_meta in v_patterns:
                v_deck = deck_base + v_fixed
                try:
                    v_words = self.dpg.generate(v_pattern, v_deck, self.rule.scrabble_dictionary)
                except Exception:
                    v_words = []

                if not v_words:
                    continue

                # Sort words by length descending - longest first
                v_words.sort(key=len, reverse=True)
                
                # Find first valid word (which will be longest valid)
                found_valid = False
                for word in v_words:
                    if found_valid:
                        break  # Already found longest valid word for this pattern
                        
                    additions_sets = self._materialize_additions_from_words(
                        axis='V', anchor=(r, c), words=[word], meta=v_meta, rack=deck_base
                    )
                    for adds in additions_sets:
                        try:
                            if self.game._check_word_valid(adds):
                                key = tuple((ch, pos[0], pos[1]) for ch, pos in adds)
                                if key not in seen_additions:
                                    seen_additions.add(key)
                                    candidates.append(adds)
                                    found_valid = True
                                    break  # Found valid word, stop checking this word's placements
                        except (ValueError, Exception):
                            continue

        # If no candidates found, return empty
        if not candidates:
            return []

        # Score all candidates using Game.score_calculator on the provided board
        game = self.game

        scored = []
        max_score = None
        for adds in candidates:
            try:
                score = game.score_calculator(adds)
            except Exception:
                # If scoring fails for any reason, skip this candidate
                continue
            scored.append((score, adds))
            if max_score is None or score > max_score:
                max_score = score

        if not scored:
            return []

        # Return only the highest-scoring additions (preserve ties)
        best = [adds for score, adds in scored if score == max_score]
        return best

    def _find_anchor_positions(self):
        """
        Return list of (r,c) empty cells that are adjacent (orthogonally) to any occupied cell.
        """
        board = self.game.board
        # Occupied mask
        occ = (board != '')
        # Orthogonal neighbor occupancy via shifts
        up = np.zeros_like(occ)
        up[1:, :] = occ[:-1, :]
        down = np.zeros_like(occ)
        down[:-1, :] = occ[1:, :]
        left = np.zeros_like(occ)
        left[:, 1:] = occ[:, :-1]
        right = np.zeros_like(occ)
        right[:, :-1] = occ[:, 1:]
        neighbor = up | down | left | right
        # Anchors are empty cells that have any occupied neighbor
        anchors_mask = (~occ) & neighbor
        coords = np.argwhere(anchors_mask)
        return [tuple(map(int, rc)) for rc in coords]

    def _scan_side_for_blocks(self, anchor, axis, direction, rack_len):
        """
        Scan one direction from anchor to collect ALL reachable blocks and gaps.
        
        Args:
            board: game board
            anchor: (r, c) anchor position
            axis: 'H' or 'V'
            direction: 'left' or 'right'
            rack_len: number of letters in rack
        
        Returns:
            (blocks, gaps, tail_max) where blocks/gaps are near-to-far lists
        """
        board = self.game.board
        r, c = anchor
        rows, cols = board.shape
        
        if axis == 'H':
            if direction == 'left':
                get_cell = lambda j: board[r, j]
                max_index = cols
                start_idx = c - 1
                step = -1
                reverse_block = True
            else:  # right
                get_cell = lambda j: board[r, j]
                max_index = cols
                start_idx = c + 1
                step = +1
                reverse_block = False
        else:  # axis == 'V'
            if direction == 'left':  # up
                get_cell = lambda i: board[i, c]
                max_index = rows
                start_idx = r - 1
                step = -1
                reverse_block = True
            else:  # down
                get_cell = lambda i: board[i, c]
                max_index = rows
                start_idx = r + 1
                step = +1
                reverse_block = False
        
        blocks = []
        gaps = []
        tail_max = 0
        j = start_idx
        cumulative_distance = 1  # anchor takes 1 letter
        
        # First gap
        k = 0
        while 0 <= j < max_index and get_cell(j) == '':
            k += 1
            j += step
        
        if not (0 <= j < max_index):
            # Only empties, no blocks
            tail_max = min(k, rack_len - 1)
            return blocks, gaps, tail_max
        
        # Found first block - check reachability
        cumulative_distance += k
        if cumulative_distance > rack_len:
            # First block unreachable
            tail_max = min(k, rack_len - 1)
            return blocks, gaps, tail_max
        
        # First block is reachable
        gaps.append(k)
        blk = []
        while 0 <= j < max_index and get_cell(j) != '':
            blk.append(get_cell(j).upper())
            j += step
        if reverse_block:
            blk.reverse()
        blocks.append(''.join(blk))
        
        # Continue scanning for more blocks
        while 0 <= j < max_index:
            k = 0
            while 0 <= j < max_index and get_cell(j) == '':
                k += 1
                j += step
            
            if not (0 <= j < max_index):
                # Reached boundary
                remaining = rack_len - cumulative_distance
                tail_max = min(k, remaining) if remaining > 0 else 0
                break
            
            # Check next block reachability
            cumulative_distance += k
            if cumulative_distance > rack_len:
                # Next block unreachable
                remaining = rack_len - (cumulative_distance - k)
                tail_max = min(k, remaining) if remaining > 0 else 0
                break
            
            # Next block is reachable
            gaps.append(k)
            blk = []
            while 0 <= j < max_index and get_cell(j) != '':
                blk.append(get_cell(j).upper())
                j += step
            if reverse_block:
                blk.reverse()
            blocks.append(''.join(blk))
        
        return blocks, gaps, tail_max

    def _build_pattern_from_selection(self, left_blocks, left_gaps, left_tail, 
                                      right_blocks, right_gaps, right_tail, rack_len):
        """
        Build a pattern string from selected blocks on each side.
        Adjusts tails based on remaining rack capacity after including selected blocks.
        
        Returns:
            (pattern: str, fixed_letters: str, meta: dict)
        """
        # Calculate cost of selected blocks
        cost = 1  # anchor
        for g in left_gaps:
            cost += g
        for g in right_gaps:
            cost += g
        
        remaining = rack_len - cost
        
        # Adjust tails to not exceed remaining capacity
        left_tail_adj = min(left_tail, remaining) if remaining > 0 else 0
        right_tail_adj = min(right_tail, remaining) if remaining > 0 else 0
        
        # Build pattern
        parts_left = []
        if left_tail_adj > 0:
            parts_left.append(f'(0,{left_tail_adj})')
        for b, k in zip(reversed(left_blocks), reversed(left_gaps)):
            parts_left.append(b)
            if k > 0:
                parts_left.append('_' * k)
        left_pattern = ''.join(parts_left)
        
        parts_right = []
        for b, k in zip(right_blocks, right_gaps):
            if k > 0:
                parts_right.append('_' * k)
            parts_right.append(b)
        if right_tail_adj > 0:
            parts_right.append(f'(0,{right_tail_adj})')
        right_pattern = ''.join(parts_right)
        
        pattern = left_pattern + '_' + right_pattern
        fixed_letters = ''.join(left_blocks) + ''.join(right_blocks)
        
        # Simplify the pattern
        pattern = self._simplify_pattern(pattern)
        
        meta = {
            'left_blocks': left_blocks,
            'left_gaps': left_gaps,
            'left_tail': left_tail_adj,
            'right_blocks': right_blocks,
            'right_gaps': right_gaps,
            'right_tail': right_tail_adj
        }
        
        return (pattern, fixed_letters, meta)

    def _simplify_pattern(self, pattern):
        """
        Simplify a pattern by combining adjacent optional ranges and underscores.
        
        Examples:
            (0,2)_(0,6) -> (1,9)  [min: 0+1+0=1, max: 2+1+6=9]
            (0,3)AB___(0,4) -> (0,3)AB(2,6)  [___ becomes part of range: min 2, max 2+4=6]
            AB___ -> AB(2,2)  [three underscores = exactly 2 more chars]
        """
        
        # Find all tokens: ranges like (0,5), blocks like ABC, underscores like ___
        tokens = []
        i = 0
        while i < len(pattern):
            if pattern[i] == '(':
                # Range token
                j = pattern.index(')', i)
                tokens.append(pattern[i:j+1])
                i = j + 1
            elif pattern[i] == '_':
                # Count consecutive underscores
                j = i
                while j < len(pattern) and pattern[j] == '_':
                    j += 1
                count = j - i
                tokens.append('_' * count)
                i = j
            else:
                # Fixed letter block
                j = i
                while j < len(pattern) and pattern[j] not in '(_':
                    j += 1
                tokens.append(pattern[i:j])
                i = j
        
        # Now combine adjacent ranges and underscores
        simplified = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Check if this is a range or underscores that can be combined with next
            if token.startswith('(') or token.startswith('_'):
                # Look ahead to collect all adjacent ranges/underscores
                sequence = [token]
                j = i + 1
                while j < len(tokens) and (tokens[j].startswith('(') or tokens[j].startswith('_')):
                    sequence.append(tokens[j])
                    j += 1
                
                if len(sequence) > 1:
                    # Combine the sequence
                    min_sum = 0
                    max_sum = 0
                    for t in sequence:
                        if t.startswith('('):
                            # Parse (min,max)
                            parts = t[1:-1].split(',')
                            min_sum += int(parts[0])
                            max_sum += int(parts[1])
                        else:  # underscores
                            count = len(t)
                            min_sum += count
                            max_sum += count
                    
                    # Add combined range
                    if min_sum == max_sum:
                        # Exact count - use underscores
                        simplified.append('_' * min_sum)
                    else:
                        simplified.append(f'({min_sum},{max_sum})')
                    i = j
                else:
                    # Single token, just add it
                    simplified.append(token)
                    i += 1
            else:
                # Fixed block, just add it
                simplified.append(token)
                i += 1
        
        return ''.join(simplified)

    def _build_all_dynamic_patterns(self, deck, anchor, axis='H'):
        """
        Build ALL valid dynamic patterns for placement through the anchor on the given axis.
        
        When there are fixed blocks on both sides, different patterns represent different
        "commitment strategies" for how to allocate rack letters between left and right extensions.
        
        Returns:
            List[(pattern: str, fixed_letters: str, meta: dict)]
        """
        board = self.game.board
        r, c = anchor
        rack_len = len(deck)
        
        # First, scan both sides to collect all reachable blocks
        left_blocks_all, left_gaps_all, left_tail_max = self._scan_side_for_blocks(anchor, axis, direction='left', rack_len=rack_len)
        right_blocks_all, right_gaps_all, right_tail_max = self._scan_side_for_blocks(anchor, axis, direction='right', rack_len=rack_len)
        
        # Unified enumeration: try all prefixes on each side and include only reachable combos
        L = len(left_blocks_all)
        R = len(right_blocks_all)

        # Precompute prefix sums of gaps to get cost quickly
        left_cost = [0]
        for g in left_gaps_all:
            left_cost.append(left_cost[-1] + g)
        right_cost = [0]
        for g in right_gaps_all:
            right_cost.append(right_cost[-1] + g)

        patterns = []
        for num_left in range(L + 1):
            for num_right in range(R + 1):
                cost = 1 + left_cost[num_left] + right_cost[num_right]  # 1 for anchor
                if cost > rack_len:
                    continue
                # Build pattern for this selection
                patterns.append(
                    self._build_pattern_from_selection(
                        left_blocks=left_blocks_all[:num_left],
                        left_gaps=left_gaps_all[:num_left],
                        left_tail=left_tail_max,
                        right_blocks=right_blocks_all[:num_right],
                        right_gaps=right_gaps_all[:num_right],
                        right_tail=right_tail_max,
                        rack_len=rack_len,
                    )
                )

        # Deduplicate patterns (very few expected now due to direct enumeration)
        unique_patterns = {}
        for pattern, fixed, meta in patterns:
            if pattern not in unique_patterns:
                unique_patterns[pattern] = (pattern, fixed, meta)

        return list(unique_patterns.values())

    def _calculate_anchor_index_in_word(self, word, meta):
        """
        Calculate where the anchor position is within a word generated from a pattern.
        
        The pattern structure is: left_pattern + '_' (anchor) + right_pattern
        So the anchor is at position = min_left_pattern_length
        
        Returns the index of the anchor in the word, or None if word doesn't fit.
        """
        left_blocks = meta['left_blocks']
        left_gaps = meta['left_gaps']
        left_tail = meta['left_tail']
        right_blocks = meta['right_blocks']
        right_gaps = meta['right_gaps']
        right_tail = meta['right_tail']
        
        # Minimum positions before anchor (fixed blocks + required gaps)
        min_left_len = sum(len(b) for b in left_blocks) + sum(left_gaps)
        
        # Maximum positions before anchor (add optional tail)
        max_left_len = min_left_len + left_tail
        
        # Similarly for right side
        min_right_len = sum(len(b) for b in right_blocks) + sum(right_gaps)
        max_right_len = min_right_len + right_tail
        
        word_len = len(word)
        
        # The anchor can be at any position from min_left_len to max_left_len
        # such that the word has enough letters on the right side
        for anchor_idx in range(min_left_len, max_left_len + 1):
            right_len = word_len - anchor_idx - 1  # -1 for anchor itself
            if min_right_len <= right_len <= max_right_len:
                return anchor_idx
        
        return None

    def _materialize_additions_from_words(self, axis, anchor, words, meta, rack):
        """
        Convert matching words into additions lists.
        
        For each word:
        1. Calculate where the anchor is in the word using meta
        2. Map each letter to board position  
        3. Create additions only for empty cells
        4. Validate rack usage

        Returns list[List[Tuple[str, [int,int]]]]
        """
        board = self.game.board
        (r, c) = anchor

        results = []
        seen = set()
        rack_counts = Counter(rack)
        blanks_total = rack_counts.get('-', 0)
        
        for word in words:
            w = word.upper()
            
            # Find where anchor is in this word
            anchor_idx = self._calculate_anchor_index_in_word(w, meta)
            if anchor_idx is None:
                continue
            
            # Map word to board positions
            additions = []
            valid = True
            
            if axis == 'H':
                # Word starts at column: anchor_col - anchor_idx
                start_col = c - anchor_idx
                for i, ch in enumerate(w):
                    col = start_col + i
                    if col < 0 or col >= 15:
                        valid = False
                        break
                    
                    # Check board position
                    if board[r, col] == '':
                        # Empty - need to place this letter
                        additions.append((ch, [r, col]))
                    elif board[r, col].upper() == ch:
                        # Already occupied with correct letter - skip
                        pass
                    else:
                        # Conflict - this word doesn't fit here
                        valid = False
                        break
                        
            else:  # 'V'
                # Word starts at row: anchor_row - anchor_idx
                start_row = r - anchor_idx
                for i, ch in enumerate(w):
                    row = start_row + i
                    if row < 0 or row >= 15:
                        valid = False
                        break
                    
                    # Check board position
                    if board[row, c] == '':
                        # Empty - need to place this letter
                        additions.append((ch, [row, c]))
                    elif board[row, c].upper() == ch:
                        # Already occupied with correct letter - skip
                        pass
                    else:
                        # Conflict - this word doesn't fit here
                        valid = False
                        break
            
            if not valid or not additions:
                continue
            
            # Validate rack usage and assign blanks if needed
            counts = Counter(rack_counts)
            blanks_left = blanks_total
            normalized_additions = []
            
            for ch, pos in additions:
                if counts.get(ch, 0) > 0:
                    counts[ch] -= 1
                    normalized_additions.append((ch, pos))
                elif blanks_left > 0:
                    blanks_left -= 1
                    normalized_additions.append((ch.lower(), pos))
                else:
                    # Not feasible w.r.t rack
                    normalized_additions = None
                    break

            if not normalized_additions:
                continue

            # Deduplicate
            key = tuple((ch, pos[0], pos[1]) for ch, pos in normalized_additions)
            if key in seen:
                continue
            seen.add(key)
            results.append(normalized_additions)

        return results
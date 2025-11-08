from utils.linear.simple_pattern_generator import SimplePatternGenerator
from utils.linear.dynamic_pattern_generator import DynamicPatternGenerator
from utils.matrix.game_state import Game
from utils.players.longest_word import OptimiserLength
import numpy as np

from collections import Counter


class OptimiserPrize:
    # recommendation based on trying to use highest prizes on the board first 
    def __init__(self, rule, game = None, ol = None):
        self.rule = rule
        self.spg = SimplePatternGenerator()
        self.dpg = DynamicPatternGenerator(self.spg)
        self.game = game if game else Game(rule)
        self.ol = ol if ol else OptimiserLength(rule, self.game)

    def _is_prized_cell(self, r, c):
        """Return True if the empty cell (r,c) is a prized square (multiplier > 1)."""
        board = self.game.board
        if board[r, c] != '':
            return False
        return (self.rule.word_multiplier[r, c] > 1) or (self.rule.letter_multiplier[r, c] > 1)

    def recommend_next_move(self, deck):
        """
        Recommend next move(s) maximizing score while ensuring at least one prized cell
        (letter or word multiplier >1) is covered by newly placed tiles.

        Logic (adapted per user specification):
        - Empty board: treat center (7,7) as sole anchor; process like non-empty board.
        - Non-empty board: anchors are empty cells adjacent orthogonally to any occupied cell (via longest_word optimiser helper).
        - For each anchor and axis (H/V):
            * Build dynamic patterns using existing longest_word pattern builder.
            * Only consider materialized additions that include at least one prized cell.
            * Validate additions via Game._check_word_valid.
            * Score all valid additions; keep global maximum (ties preserved).
        - Return list of additions (each list of (letter, [row,col])) for all highest-scoring moves.

        Notes:
        - Fixed board letters are never overwritten (enforced by materializer).
        - Total new letters used never exceeds deck length (enforced by pattern builder via rack_len parameter).
        - If no valid prized-cell-including move exists, returns [].
        """
        deck = [d.upper() for d in deck]
        deck_len = len(deck)
        board = self.game.board

        # Determine anchors
        if np.sum(board != '') == 0:
            anchors = [(7, 7)]  # center anchor for empty board
        else:
            anchors = self.ol._find_anchor_positions()
        if not anchors:
            return []

        deck_base = ''.join(deck)

        candidates = []
        seen = set()  # deduplicate additions sets

        for (r, c) in anchors:
            for axis in ('H', 'V'):
                # Build dynamic patterns for this anchor & axis
                try:
                    patterns = self.ol._build_all_dynamic_patterns(deck, (r, c), axis=axis)
                except Exception:
                    continue
                if not patterns:
                    continue

                for pattern, fixed_letters, meta in patterns:
                    # Build combined deck string (deck + fixed letters) for word generation
                    deck_for_pattern = deck_base + fixed_letters
                    try:
                        words = self.dpg.generate(pattern, deck_for_pattern, self.rule.scrabble_dictionary)
                    except Exception:
                        continue
                    if not words:
                        continue

                    # Materialize additions for each word
                    materialized_lists = self.ol._materialize_additions_from_words(axis, (r, c), words, meta, deck)
                    if not materialized_lists:
                        continue

                    for adds in materialized_lists:
                        # Require at least one prized cell among new placements
                        if not any(self._is_prized_cell(pos[0], pos[1]) for ch, pos in adds):
                            continue
                        # Validate move legality (cross words etc.)
                        try:
                            self.game._check_word_valid(adds)
                        except Exception:
                            continue
                        # Deduplicate key
                        key = tuple((ch, p[0], p[1]) for ch, p in adds)
                        if key in seen:
                            continue
                        seen.add(key)
                        # Score
                        try:
                            score = self.game.score_calculator(adds)
                        except Exception:
                            continue
                        candidates.append((score, adds))

        if not candidates:
            return []

        max_score = max(score for score, _ in candidates)
        best = [(adds, score) for score, adds in candidates if score == max_score]
        # Final safeguard: deduplicate identical additions before returning
        best_adds = [adds for adds, score in best]
        deduped_adds = self.ol._dedup_additions_sets(best_adds)
        # Rebuild tuples with scores after dedup
        best = [(adds, max_score) for adds in deduped_adds]
        return best
    
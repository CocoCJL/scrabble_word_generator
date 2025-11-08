from utils.linear.simple_pattern_generator import SimplePatternGenerator
from utils.linear.dynamic_pattern_generator import DynamicPatternGenerator
from utils.matrix.game_state import Game
from utils.players.longest_word import OptimiserLength
import numpy as np

from collections import Counter

class OptimiserCrossword:
    # recommendation based on trying to use any crosswords
    def __init__(self, rule, game = None, ol = None):
        self.rule = rule
        self.spg = SimplePatternGenerator()
        self.dpg = DynamicPatternGenerator(self.spg)
        self.game = game if game else Game(rule)
        self.ol = ol if ol else OptimiserLength(rule, self.game)

    def recommend_next_move(self, deck):
        """
        Recommend move(s) that explicitly form crosswords:
        - If board is empty: return [] (this optimiser doesn't start the game)
        - For each anchor (empty cell adjacent to any tile):
          * If it has a vertical neighbor (above or below occupied), consider H-axis (horizontal) patterns
          * If it has a horizontal neighbor (left or right occupied), consider V-axis (vertical) patterns
        - Generate words via dynamic patterns (reusing OptimiserLength helpers),
          materialize additions, validate legality, score, and return the highest-scoring
          move(s) with ties preserved. Blanks handled the same as longest_word.

        Returns: List[List[(ch, [r,c])]] best scoring additions (ties), or [] if none
        """
        board = self.game.board
        # If empty board, do nothing
        if np.sum(board != '') == 0:
            return []

        # Normalize deck
        deck_up = [d.upper() for d in deck]
        deck_base = ''.join(deck_up)

        anchors = self.ol._find_anchor_positions()
        if not anchors:
            return []

        candidates = []
        seen_adds = set()  # dedup additions early to avoid rescoring

        rows, cols = board.shape

        for (r, c) in anchors:
            # Determine neighbor presence
            has_vert_neighbor = ((r > 0 and board[r-1, c] != '') or (r < rows-1 and board[r+1, c] != ''))
            has_horiz_neighbor = ((c > 0 and board[r, c-1] != '') or (c < cols-1 and board[r, c+1] != ''))

            # If vertical neighbor -> place horizontally to form a cross
            if has_vert_neighbor:
                try:
                    h_patterns = self.ol._build_all_dynamic_patterns(deck_up, (r, c), axis='H')
                except Exception:
                    h_patterns = []
                for pattern, fixed_letters, meta in h_patterns:
                    deck_for_pattern = deck_base + fixed_letters
                    try:
                        words = self.dpg.generate(pattern, deck_for_pattern, self.rule.scrabble_dictionary)
                    except Exception:
                        words = []
                    if not words:
                        continue
                    adds_lists = self.ol._materialize_additions_from_words('H', (r, c), words, meta, deck_base)
                    if not adds_lists:
                        continue
                    for adds in adds_lists:
                        # Validate crossword legality
                        try:
                            if not self.game._check_word_valid(adds):
                                continue
                        except Exception:
                            continue
                        key = tuple((ch, pos[0], pos[1]) for ch, pos in adds)
                        if key in seen_adds:
                            continue
                        seen_adds.add(key)
                        try:
                            score = self.game.score_calculator(adds)
                        except Exception:
                            continue
                        candidates.append((score, adds))

            # If horizontal neighbor -> place vertically to form a cross
            if has_horiz_neighbor:
                try:
                    v_patterns = self.ol._build_all_dynamic_patterns(deck_up, (r, c), axis='V')
                except Exception:
                    v_patterns = []
                for pattern, fixed_letters, meta in v_patterns:
                    deck_for_pattern = deck_base + fixed_letters
                    try:
                        words = self.dpg.generate(pattern, deck_for_pattern, self.rule.scrabble_dictionary)
                    except Exception:
                        words = []
                    if not words:
                        continue
                    adds_lists = self.ol._materialize_additions_from_words('V', (r, c), words, meta, deck_base)
                    if not adds_lists:
                        continue
                    for adds in adds_lists:
                        try:
                            if not self.game._check_word_valid(adds):
                                continue
                        except Exception:
                            continue
                        key = tuple((ch, pos[0], pos[1]) for ch, pos in adds)
                        if key in seen_adds:
                            continue
                        seen_adds.add(key)
                        try:
                            score = self.game.score_calculator(adds)
                        except Exception:
                            continue
                        candidates.append((score, adds))

        if not candidates:
            return []

        max_score = max(s for s, _ in candidates)
        best = [(adds, s) for s, adds in candidates if s == max_score]
        # Final dedup safeguard
        best_adds = [adds for adds, s in best]
        deduped_adds = self.ol._dedup_additions_sets(best_adds)
        # Rebuild tuples with scores after dedup
        best = [(adds, max_score) for adds in deduped_adds]
        return best
from utils.matrix.game_state import Game
from utils.players.longest_word import OptimiserLength
from utils.players.prized_cells import OptimiserPrize
from utils.players.crossword import OptimiserCrossword
import numpy as np

class AggregateRecommender:
    # Aggregates recommendations from multiple optimisers
    def __init__(self, rule, game=None):
        self.rule = rule
        self.game = game if game else Game(rule)
        self.optimisers = [
            OptimiserLength(rule, self.game),
            OptimiserPrize(rule, self.game),
            OptimiserCrossword(rule, self.game)
        ]

    def recommend_next_move(self, deck):
        """Return per-optimiser top scoring move(s) as a dictionary.

        Logic:
        1. If the board is empty: call ONLY OptimiserPrize and return a dict:
           {'PrizeCells': [(additions, score), ...]} containing its highest-scoring
           addition(s). If it yields no moves, value will be an empty list.
        2. If the board is non-empty: call all three optimisers. For each optimiser,
           keep only its internally filtered highest-scoring additions (already a
           list of (adds, score) tuples) and place them under its name key. Empty
           list if no moves.

        Returns:
            Dict[str, List[Tuple[List[Tuple[str, List[int]]], int]]]
            Keys: 'PrizeCells' (always on empty board), and on non-empty boards also
            'LongestWord', 'Crossword'. Each value is a list of (additions, score) tuples.
        """
        # Detect empty board (no placed tiles)
        board_empty = not np.any(self.game.board != '')

        results = {}

        if board_empty:
            # Only run OptimiserPrize per requirement
            prize_opt = OptimiserPrize(self.rule, self.game)
            prize_moves = prize_opt.recommend_next_move(deck)  # already [(adds, score)]
            results['PrizeCells'] = prize_moves if prize_moves else []
            return results

        # Non-empty board: run all three
        longest_opt = OptimiserLength(self.rule, self.game)
        prize_opt = OptimiserPrize(self.rule, self.game)
        cross_opt = OptimiserCrossword(self.rule, self.game)

        # Each optimiser already returns only top-scoring moves as (adds, score) tuples
        longest_moves = longest_opt.recommend_next_move(deck)
        prize_moves = prize_opt.recommend_next_move(deck)
        cross_moves = cross_opt.recommend_next_move(deck)

        results['LongestWord'] = longest_moves if longest_moves else []
        results['PrizeCells'] = prize_moves if prize_moves else []
        results['Crossword'] = cross_moves if cross_moves else []

        return results
from typing import List, Tuple, Optional, Set
import numpy as np
from numpy.typing import NDArray
from tabulate import tabulate

class Game:
    def __init__(self, rule):
        """
        Initialize an empty 15x15 Scrabble board.
        
        Args:
            rule (Rule): Rule object containing dictionary and board configuration
        """
        self.rule = rule
        # Initialize empty 15x15 board using NumPy
        self.board = np.full((15, 15), '', dtype='U1')  # U1 for single Unicode character
        self.start_pos = (7, 7)  # Standard Scrabble starting position at center (7,7)

    def empty_board(self):
        self.board = np.full((15, 15), '', dtype='U1') 

    def _verify_word_addition(self, additions: List[Tuple[str, List[int]]]) -> bool:
        """
        Verify that all additions are in a single row or column, continuous, within bounds,
        and don't overlap with existing cells.
        
        Args:
            additions: List of (letter, [row, col]) tuples for new letters
            
        Returns:
            bool: True if the addition is valid
            
        Raises:
            ValueError: If the addition is invalid, with a descriptive message
        """
        if not additions:
            raise ValueError("No letters provided for addition")
            return False

        # Check boundaries
        for _, [row, col] in additions:
            if not (0 <= row < 15 and 0 <= col < 15):
                raise ValueError(f"Position ({row},{col}) is out of bounds")
                return False
        
        # Check for overlap with existing letters
        for _, [row, col] in additions:
            if self.board[row, col] != '':
                raise ValueError(f"Position ({row},{col}) is already occupied")
                return False
            
        # Check if additions form a continuous line
        pos_array = np.array([pos for _, pos in additions])
        unique_rows = np.unique(pos_array[:, 0])
        unique_cols = np.unique(pos_array[:, 1])
        
        # Check if additions are in a single row or column
        if len(unique_rows) > 1 and len(unique_cols) > 1:
            raise ValueError("Letters must be placed in a single row or column")
            return False
            
        # Check continuity
        if len(unique_rows) == 1:
            cols = np.sort(pos_array[:, 1])
            if np.ptp(cols) + 1 != len(additions):
                raise ValueError("Letters must form a continuous line without gaps")
                return False
        else:  # len(unique_cols) == 1
            rows = np.sort(pos_array[:, 0])
            if np.ptp(rows) + 1 != len(additions):
                raise ValueError("Letters must form a continuous line without gaps")
                return False
                
        return True

    def _check_board_valid(self, additions: List[Tuple[str, List[int]]]) -> bool:
        """
        Perform board-level validity checks separated from positional checks.

        - If board is empty, at least one added tile must cover the starting square.
        - Otherwise, at least one added tile must touch existing letters.

        Raises ValueError with a descriptive message on failure.
        Returns True on success.
        """
        board_letter_count = np.sum(self.board != '')
        if board_letter_count == 0:
            start_covered = any(pos[0] == self.start_pos[0] and pos[1] == self.start_pos[1]
                                for _, pos in additions)
            if not start_covered:
                raise ValueError("First word must cover the starting square")
            return True

        # Not the first move: must connect to existing words
        if not self._touches_existing_word(additions):
            raise ValueError("New letters must connect to existing words")
        return True

    def _touches_existing_word(self, additions: List[Tuple[str, List[int]]]) -> bool:
        """
        Return True if any of the additions touches an existing tile (orthogonally).
        """
        if not additions:
            return False
        pos_array = np.array([pos for _, pos in additions])
        # adjacent offsets
        adj = np.array([[-1, 0], [1, 0], [0, -1], [0, 1]])
        all_adj = (pos_array[:, None, :] + adj[None, :, :]).reshape(-1, 2)
        # filter valid
        valid = (all_adj[:, 0] >= 0) & (all_adj[:, 0] < 15) & (all_adj[:, 1] >= 0) & (all_adj[:, 1] < 15)
        valid_adj = all_adj[valid]
        if valid_adj.size == 0:
            return False
        return np.any(self.board[valid_adj[:, 0], valid_adj[:, 1]] != '')

    def print_board(self) -> None:
        """
        Print the current board in a readable matrix form.

        Each cell shows:
        - occupancy (letter or '.')
        - if occupied: the letter's point value (from self.rule.letter_points)
        - any special cell multiplier (TW, DW, TL, DL)

        The output is a single matrix where each cell is a fixed-width field.
        """
        # Helper to get special token for a cell
        def _cell_special(r: int, c: int) -> str:
            wm = getattr(self.rule, 'word_multiplier', None)
            lm = getattr(self.rule, 'letter_multiplier', None)
            special_parts = []
            if wm is not None:
                val = int(wm[r, c])
                if val == 3:
                    special_parts.append('TW')
                elif val == 2:
                    special_parts.append('DW')
            if lm is not None:
                val = int(lm[r, c])
                if val == 3:
                    special_parts.append('TL')
                elif val == 2:
                    special_parts.append('DL')
            return '+'.join(special_parts) if special_parts else ''

        # Column header (shifted left for better alignment)
        header = '  ' + ' '.join(f'{c:7d}' for c in range(self.board.shape[1]))
        print(header)
        print('  ' + '-------' * self.board.shape[1])

        for r in range(self.board.shape[0]):
            row_cells = []
            for c in range(self.board.shape[1]):
                letter = self.board[r, c]
                special = _cell_special(r, c)
                if letter != '':
                    score = self.rule.letter_points.get(letter.upper(), 0)
                    content = f"{letter}({score})"
                    if special:
                        content = f"{content}{special}"
                else:
                    content = '.'
                    if special:
                        content = f".{special}"
                row_cells.append(f'{content:7s}')
            print(f'{r:2d} |' + ' '.join(row_cells))

    def pretty_print_board(self) -> None:
        """
        Pretty-print the current board using the tabulate library for better alignment.
        Each cell shows:
        - occupancy (letter or '.')
        - if occupied: the letter's point value (from self.rule.letter_points)
        - any special cell multiplier (TW, DW, TL, DL)
        """

        def _cell_special(r: int, c: int) -> str:
            wm = getattr(self.rule, 'word_multiplier', None)
            lm = getattr(self.rule, 'letter_multiplier', None)
            special_parts = []
            if wm is not None:
                val = int(wm[r, c])
                if val == 3:
                    special_parts.append('TW')
                elif val == 2:
                    special_parts.append('DW')
            if lm is not None:
                val = int(lm[r, c])
                if val == 3:
                    special_parts.append('TL')
                elif val == 2:
                    special_parts.append('DL')
            return '+'.join(special_parts) if special_parts else ''

        table = []
        for r in range(self.board.shape[0]):
            row_cells = []
            for c in range(self.board.shape[1]):
                letter = self.board[r, c]
                special = _cell_special(r, c)
                if letter != '':
                    score = self.rule.letter_points.get(letter.upper(), 0)
                    content = f"{letter}({score})"
                    if special:
                        content = f"{content}{special}"
                else:
                    content = '.'
                    if special:
                        content = f".{special}"
                row_cells.append(content)
            table.append(row_cells)

        headers = [str(c) for c in range(self.board.shape[1])]
        print(tabulate(table, headers=headers, showindex="always", tablefmt="fancy_grid"))
    
    def _get_all_affected_words(self, additions: List[Tuple[str, List[int]]]) -> Set[str]:
        """
        Get all words formed or modified by the new letters.
        Returns set of main word and any cross words formed.
        Assumes additions are valid (single line, continuous, within bounds).
        """
        words = set()
        if not additions:
            return words
            
        temp_board = self.board.copy()
        positions = np.array([pos for _, pos in additions])
        for letter, [row, col] in additions:
            temp_board[row, col] = letter

        # Get the primary word (horizontal or vertical)
        unique_rows = np.unique(positions[:, 0])
        unique_cols = np.unique(positions[:, 1])
        
        if len(unique_rows) == 1:  # Horizontal word
            row = unique_rows[0]
            # Find segment boundaries
            occupied = temp_board[row] != ''
            # Get leftmost and rightmost occupied positions of the word added
            min_col, max_col = positions[:, 1].min(), positions[:, 1].max()
            # Get all continuous occupied positions
            segments = np.split(np.arange(15), np.where(np.diff(occupied))[0] + 1)
            occupied_segments = [seg for seg in segments if occupied[seg[0]]]
            # Find the segment containing our new word
            for seg in occupied_segments:
                if min_col <= seg[-1] and max_col >= seg[0]:  # Segment overlaps with additions
                    word = ''.join(temp_board[row, seg[0]:seg[-1] + 1])
                    if len(word) > 1:
                        words.add(word)
                    break # since we should only get one continuous word as result of our addition
                        
            # Get cross words efficiently
            cross_occupied = temp_board[:, positions[:, 1]] != ''  # Matrix of occupied positions for all addition columns
            # For each column, find the continuous segment containing the current row
            for i, seg_col in enumerate(cross_occupied.T):  # Still need to process each column's segments
                if not seg_col[row]:  # Skip if position isn't occupied
                    continue
                # Find segment boundaries
                indices = np.where(seg_col)[0]  # Get all occupied positions
                # Find the segment containing our row
                segment_idx = (indices[:-1] + 1 == indices[1:])  # True where indices are consecutive
                segment_boundaries = np.split(indices, np.where(~segment_idx)[0] + 1)
                segment = next((seg for seg in segment_boundaries if row in seg), None)
                if segment is not None and len(segment) > 1:
                    word = ''.join(temp_board[segment[0]:segment[-1] + 1, positions[i, 1]])
                    words.add(word)
                            
        else:  # Vertical word
            col = unique_cols[0]
            # Find segment boundaries
            occupied = temp_board[:, col] != ''
            # Get topmost and bottommost occupied positions of the newly added word
            min_row, max_row = positions[:, 0].min(), positions[:, 0].max()
            # Get all continuous occupied positions
            segments = np.split(np.arange(15), np.where(np.diff(occupied))[0] + 1)
            occupied_segments = [seg for seg in segments if occupied[seg[0]]]
            # Find the segment containing our new word
            for seg in occupied_segments:
                if min_row <= seg[-1] and max_row >= seg[0]:  # Segment overlaps with additions
                    word = ''.join(temp_board[seg[0]:seg[-1] + 1, col])
                    if len(word) > 1:
                        words.add(word)
                    break # since we should only get one continuous word as result of our addition
                        
            # Get cross words efficiently
            cross_occupied = temp_board[positions[:, 0], :] != ''  # Matrix of occupied positions for all addition rows
            # For each row, find the continuous segment containing the current column
            for i, seg_row in enumerate(cross_occupied):  # Still need to process each row's segments
                if not seg_row[col]:  # Skip if position isn't occupied
                    continue
                # Find segment boundaries
                indices = np.where(seg_row)[0]  # Get all occupied positions
                # Find the segment containing our column
                segment_idx = (indices[:-1] + 1 == indices[1:])  # True where indices are consecutive
                segment_boundaries = np.split(indices, np.where(~segment_idx)[0] + 1)
                segment = next((seg for seg in segment_boundaries if col in seg), None)
                if segment is not None and len(segment) > 1:
                    word = ''.join(temp_board[positions[i, 0], segment[0]:segment[-1] + 1])
                    words.add(word)
                            
        return words
    
    def _check_word_valid(self, additions: List[Tuple[str, List[int]]]) -> bool:
        """
        Check if all words formed by the additions are valid according to the dictionary.
        
        Args:
            additions: List of (letter, [row, col]) tuples for new letters
        Returns:
            bool: True if all words are valid, False otherwise
        """
        all_words = self._get_all_affected_words(additions)
        invalid_words = [word for word in all_words
                         if word.lower() not in self.rule.scrabble_dictionary]
        if len(invalid_words) > 0:
            raise ValueError(f"Formed invalid words: {', '.join(invalid_words)}")
        return True
    
    def _score_calculator(self, additions: List[Tuple[str, List[int]]], bingo: bool = False) -> int:
        """
        Calculate the total score for a move (main word + any cross words) according to
        Scrabble rules, using the current board and rule multipliers.

        Assumptions and conventions:
        - Positional and dictionary validations are already done.
        - additions are a single contiguous line (row or column).
        - To represent a blank tile, pass the chosen letter in lowercase (e.g., 'e').
          Lowercase tiles will be placed as their uppercase letter on the board but
          contribute 0 points. Word multipliers triggered by blanks still apply.
        - Uppercase letters are normal tiles scored by rule.letter_points.
        - A 50-point bingo is added if bingo=True or if exactly 7 tiles were placed.

        Args:
            additions: list of (letter, [row, col]) for the new tiles this turn.
            bingo: set True to force a bingo bonus. If False, it's inferred when len(additions)==7.

        Returns:
            Total integer score for this move.
        """
        if not additions:
            return 0

        # Track blank positions (lowercase letters indicate a blank set to that letter)
        blank_positions: Set[Tuple[int, int]] = set()
        norm_additions: List[Tuple[str, List[int]]] = []
        for ch, pos in additions:
            if isinstance(ch, str) and ch.isalpha() and ch.islower():
                blank_positions.add((pos[0], pos[1]))
                norm_additions.append((ch.upper(), pos))
            else:
                norm_additions.append((ch.upper(), pos))

        # Build temporary board with the new tiles applied
        temp_board = self.board.copy()
        new_positions: Set[Tuple[int, int]] = set()
        for ch, (r, c) in norm_additions:
            temp_board[r, c] = ch
            new_positions.add((r, c))

        # Helper to expand from a given start to the full word horizontally/vertically
        def expand_horizontal(r: int, c: int) -> List[Tuple[int, int]]:
            left = c
            while left > 0 and temp_board[r, left - 1] != '':
                left -= 1
            right = c
            while right < 14 and temp_board[r, right + 1] != '':
                right += 1
            return [(r, cc) for cc in range(left, right + 1)]

        def expand_vertical(r: int, c: int) -> List[Tuple[int, int]]:
            top = r
            while top > 0 and temp_board[top - 1, c] != '':
                top -= 1
            bottom = r
            while bottom < 14 and temp_board[bottom + 1, c] != '':
                bottom += 1
            return [(rr, c) for rr in range(top, bottom + 1)]

        # Determine main word orientation from additions
        positions = [(pos[0], pos[1]) for _, pos in norm_additions]
        rows = {r for r, _ in positions}
        cols = {c for _, c in positions}

        words: List[List[Tuple[int, int]]] = []
        if len(rows) == 1:  # horizontal main word
            r0 = next(iter(rows))
            cmin = min(c for _, c in positions)
            cmax = max(c for _, c in positions)
            main_positions = expand_horizontal(r0, cmin)
            if len(main_positions) > 1:
                words.append(main_positions)
            # Cross words for each newly placed tile (vertical expansions)
            for _, (rr, cc) in norm_additions:
                cross = expand_vertical(rr, cc)
                if len(cross) > 1:
                    words.append(cross)
        else:  # vertical main word
            c0 = next(iter(cols))
            rmin = min(r for r, _ in positions)
            rmax = max(r for r, _ in positions)
            main_positions = expand_vertical(rmin, c0)
            if len(main_positions) > 1:
                words.append(main_positions)
            # Cross words for each newly placed tile (horizontal expansions)
            for _, (rr, cc) in norm_additions:
                cross = expand_horizontal(rr, cc)
                if len(cross) > 1:
                    words.append(cross)

        # Deduplicate identical words (rare but possible)
        dedup_words: List[List[Tuple[int, int]]] = []
        seen: Set[Tuple[Tuple[int, int], ...]] = set()
        for w in words:
            key = tuple(w)
            if key not in seen:
                seen.add(key)
                dedup_words.append(w)

        # Multiplier grids (fallback to identity if not provided)
        wm = getattr(self.rule, 'word_multiplier', np.ones((15, 15), dtype=np.int8))
        lm = getattr(self.rule, 'letter_multiplier', np.ones((15, 15), dtype=np.int8))

        def score_word(pos_list: List[Tuple[int, int]]) -> int:
            letter_sum = 0
            word_mult = 1
            for (r, c) in pos_list:
                ch = temp_board[r, c]
                # Base points: blanks contribute 0, others per letter_points
                base = 0 if (r, c) in blank_positions else int(self.rule.letter_points.get(ch.upper(), 0))
                if (r, c) in new_positions:
                    letter_sum += base * int(lm[r, c])
                    word_mult *= max(1, int(wm[r, c]))
                else:
                    letter_sum += base
            return letter_sum * word_mult

        total = sum(score_word(w) for w in dedup_words)
        if bingo or len(norm_additions) == 7:
            total += 50
        return int(total)
    
    def _update(self, additions: List[Tuple[str, List[int]]]) -> None:
        """
        Update the board with new letters
        
        Args:
            additions: List of (letter, [row, col]) tuples representing new letters and their positions
        
        Assumes:
            The move has already been validated.
        """
        # Convert letters to uppercase
        additions = [(letter.upper(), pos) for letter, pos in additions]
        
        # Update the board
        for letter, [row, col] in additions:
            self.board[row][col] = letter
            


    

    def new_move(self, additions: List[Tuple[str, List[int]]]) -> int:
        """
        Add a new word to the board. Validate the move according to Scrabble rules:
        - Positional checks (single line, continuous, within bounds, no overlap)
        - Board-level checks (first move covers start; subsequent moves connect)
        - Dictionary checks (all formed words valid)
        then update the board if valid.
        
        Args:
            additions: List of (letter, [row, col]) tuples representing new letters and their positions
        
        Returns:
            int: The score for the new move, or 0 if the move is invalid
        
        Raises:
            ValueError: If the move violates any Scrabble rules
        """
        # Convert letters to uppercase
        additions = [(letter.upper(), pos) for letter, pos in additions]
        
        # Verify the additions are valid (positional checks)
        if not self._verify_word_addition(additions):
            return False  # _verify_word_addition will raise appropriate ValueError

        # Board-level validity (first move must cover start; otherwise must touch existing)
        self._check_board_valid(additions)
        
        # Validate all words formed against dictionary
        self._check_word_valid(additions)
        
        # If we got here, the move is valid - calculate score and update board
        score = self._score_calculator(additions)
        self._update(additions)
        return score
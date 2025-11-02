from pathlib import Path
import numpy as np

class Rule:
    def __init__(self, dictionary_path):
        file_path = Path(dictionary_path)
        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} not found.")

        with file_path.open('r', encoding='utf-8') as f:
            # Strip each line and ignore empty lines
            self.scrabble_dictionary = [line.strip() for line in f if line.strip()]
            
        # Define letter points for standard Scrabble letters
        self.letter_points = {'-': 0, 'A': 1, 'E': 1, 'I': 1, 'O': 1, 'U': 1,
                              'L': 1, 'N': 1, 'S': 1, 'T': 1, 'R': 1,
                              'D': 2, 'G': 2,
                              'B': 3, 'C': 3, 'M': 3, 'P': 3,
                              'F': 4, 'H': 4, 'V': 4, 'W': 4, 'Y': 4,
                              'K': 5,
                              'J': 8, 'X': 8,
                              'Q': 10, 'Z': 10}
        
        # Define board scores for a standard 15x15 Scrabble board using NumPy arrays
        # Create score multiplier arrays (initialized with 1s)
        self.word_multiplier = np.ones((15, 15), dtype=np.int8)
        self.letter_multiplier = np.ones((15, 15), dtype=np.int8)
        
        # Set Triple Word Score positions
        tw_positions = [
            (0, 0), (0, 7), (0, 14),
            (7, 0), (7, 14),
            (14, 0), (14, 7), (14, 14)
        ]
        for row, col in tw_positions:
            self.word_multiplier[row, col] = 3
        
        # Set Double Word Score positions (including start square)
        dw_positions = [
            (1, 1), (1, 13), (2, 2), (2, 12), (3, 3), (3, 11),
            (4, 4), (4, 10), (7, 7),  # center square
            (10, 4), (10, 10), (11, 3), (11, 11),
            (12, 2), (12, 12), (13, 1), (13, 13)
        ]
        for row, col in dw_positions:
            self.word_multiplier[row, col] = 2
            
        # Set Triple Letter Score positions
        tl_positions = [
            (1, 5), (1, 9), (5, 1), (5, 5), (5, 9), (5, 13),
            (9, 1), (9, 5), (9, 9), (9, 13), (13, 5), (13, 9)
        ]
        for row, col in tl_positions:
            self.letter_multiplier[row, col] = 3
            
        # Set Double Letter Score positions
        dl_positions = [
            (0, 3), (0, 11), (2, 6), (2, 8), (3, 0), (3, 7), (3, 14),
            (6, 2), (6, 6), (6, 8), (6, 12),
            (7, 3), (7, 11),
            (8, 2), (8, 6), (8, 8), (8, 12),
            (11, 0), (11, 7), (11, 14), (12, 6), (12, 8),
            (14, 3), (14, 11)
        ]
        for row, col in dl_positions:
            self.letter_multiplier[row, col] = 2
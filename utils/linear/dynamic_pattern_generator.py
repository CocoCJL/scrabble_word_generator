import re
from collections import Counter

# Precompile regex pattern for better performance
_RANGE_PATTERN = re.compile(r'\((\d+),(\d+)\)')

class DynamicPatternGenerator:
    """
    A dynamic pattern interpreter that generates all possible words fitting a given dynamic pattern using letters available in deck
    """

    def __init__(self, simple_pattern_generator):
        self.spg = simple_pattern_generator

    def __verify_pattern(self, pattern, deck):
        """
        Verify that the pattern fits the dynamic pattern format and that all letters in the pattern exist in the deck (with '-' as the blank wild card).
        - Only allows: letters, '_', and (n,m) where n < m and both are positive integers
        - Parentheses and commas must be correctly placed
        - n and m must be positive integers, n < m
        - All letters in pattern must exist in deck with at least as many copies as in pattern, or be covered by blanks ('-')
        Raises ValueError if invalid
        """
        letter_counts = Counter()
        pattern = pattern.upper()
        deck = deck.upper()
        
        # Single-pass validation and letter counting
        i = 0
        while i < len(pattern):
            if pattern[i] == '(': 
                match = _RANGE_PATTERN.match(pattern, i)
                if not match:
                    raise ValueError("Invalid range format. Expected (n,m) where n < m")
                n, m = map(int, match.groups())
                if n < 0 or n >= m:
                    raise ValueError(f"Invalid range ({n},{m}). Must have 0 <= n < m")
                i = match.end()
                continue
            if pattern[i].isalpha():
                letter_counts[pattern[i].upper()] += 1
            elif pattern[i] != '_':
                raise ValueError(f"Invalid character '{pattern[i]}'. Use only letters, '_', and (n,m)")
            i += 1

        # Allow '-' as blank in deck
        for char in deck:
            if not (char.isalpha() or char == '-'):
                raise ValueError("Deck can only contain letters and '-' for blank tiles.")
        deck_counts = Counter(c for c in deck if c.isalpha())
        num_blanks = deck.count('-')
        missing = 0
        for letter, count in letter_counts.items():
            have = deck_counts.get(letter, 0)
            if have < count:
                missing += count - have
        if missing > num_blanks:
            raise ValueError(
                f"Pattern requires more letters than available in deck (including blanks). "
                f"Missing {missing} letter(s), but only {num_blanks} blank(s) available."
                f"Remmeber to include all letters from board you want to incorporate in your deck."
            )

    def __list_all_patterns(self, pattern):
        """
        Expand a dynamic pattern into all possible fixed patterns (with explicit underscores and letters).
        E.g. (3,5)J_M(1,2) -> ['___J_M_', '___J_M__', '____J_M_', '____J_M__', '_____J_M_', '_____J_M__']
        Returns: list of strings
        """
        def expand(parts):
            if not parts:
                return ['']
            first, *rest = parts
            expanded_rest = expand(rest)
            result = []
            if isinstance(first, tuple):
                n, m = first
                for k in range(n, m+1):
                    underscores = '_' * k
                    for tail in expanded_rest:
                        result.append(underscores + tail)
            else:
                for tail in expanded_rest:
                    result.append(first + tail)
            return result

        # Tokenize pattern into list of (n,m) or single chars
        tokens = []
        idx = 0
        paren_pattern = re.compile(r'\((\d+),(\d+)\)')
        while idx < len(pattern):
            match = paren_pattern.match(pattern, idx)
            if match:
                n, m = int(match.group(1)), int(match.group(2))
                tokens.append((n, m))
                idx = match.end()
            else:
                tokens.append(pattern[idx])
                idx += 1
        return expand(tokens)
    
    def generate(self, pattern, deck, word_list):
        """
        Generate valid words that match the dynamic pattern using available letters in deck.
        Returns:
            list[str]: List of valid words matching the pattern
        """
        self.__verify_pattern(pattern, deck)
        all_patterns = self.__list_all_patterns(pattern)
        valid_words = set()
        for pat in all_patterns:
            matches = self.spg.generate(pat, deck, word_list)
            valid_words.update(matches)
        return list(valid_words)
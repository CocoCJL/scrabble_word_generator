
from collections import Counter

class SimplePatternGenerator:
    """
    A simple pattern interpreter that generates all possible words fitting a given fixed pattern using letters available in deck
    """

    def __init__(self):
        pass

    def __verify_pattern(self, pattern, deck):
        """
        Verify if the pattern is valid and all letters exist in the deck.

        pattern: includes letters for assigned letters at fixed positions and '_' for any one letter at given position
        deck: string of letters available to use to fill in the pattern. should include any letters on the board you want to incorporate in the generated words too. If `-` exists, it means a blank tile (wildcard). Each `-` can be used as any letter.
        
        Raises:
            ValueError: If pattern contains invalid characters or if required letters aren't in deck
        """
        # Verify pattern only contains letters and underscores
        if not pattern:
            raise ValueError("Pattern cannot be empty")
        
        pattern = pattern.upper()
        deck = deck.upper()
        for char in pattern:
            if not (char.isalpha() or char == '_'):
                raise ValueError(
                    "Pattern can only contain letters and '_' for empty spaces. "
                    "Do not use spaces - use '_' instead."
                )
        for char in deck:
            if not (char.isalpha() or char == '-'):
                raise ValueError(
                    "Deck can only contain letters and '-' for blank tiles. "
                    "Do not use any separators or spaces to separate letters."
                )
        # Count required letters
        letter_counts = Counter(c for c in pattern if c.isalpha())
        deck_counts = Counter(c for c in deck if c.isalpha())
        num_blanks = deck.count('-')
        # Check if deck (with blanks) can satisfy letter requirements
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

    def __calculate_implicit_deck(self, pattern, deck):
        """
        Get the remaining available letters after removing pattern's fixed letters.
        """
        # Convert deck to list for easier manipulation
        deck_list = list(deck.upper())
        pattern = pattern.upper()
        # Remove pattern letters from deck, using blanks if needed
        for char in pattern:
            if char.isalpha():
                if char in deck_list:
                    deck_list.remove(char)
                elif '-' in deck_list:
                    deck_list.remove('-')
                else:
                    # Should not happen if __verify_pattern passed
                    pass
        return ''.join(deck_list)
    
    def __can_make_word(self, word, fixed_indices, fixed_letters, wildcard_indices, implicit_deck_counter):
        # Fast fixed position check
        for idx, letter in zip(fixed_indices, fixed_letters):
            if word[idx] != letter:
                return False
        # Count needed letters for wildcards
        needed = Counter(word[idx] for idx in wildcard_indices)
        # Check if implicit deck has enough letters, using blanks as wildcards
        blanks = implicit_deck_counter.get('-', 0)
        for letter, count in needed.items():
            have = implicit_deck_counter.get(letter, 0)
            if have < count:
                if have + blanks < count:
                    return False
                blanks -= (count - have)
        return True
    
    def generate(self, pattern, deck, word_list):
        """
        Generate valid words that match the pattern using available letters in deck.
        Optimized for large word lists.
        """
        self.__verify_pattern(pattern, deck)
        pattern = pattern.upper()
        deck = deck.upper()
        implicit_deck = self.__calculate_implicit_deck(pattern, deck)
        implicit_deck_counter = Counter(implicit_deck)
        pattern_length = len(pattern)
        # Precompute fixed and wildcard indices
        fixed_indices = [i for i, c in enumerate(pattern) if c.isalpha()]
        fixed_letters = [pattern[i] for i in fixed_indices]
        wildcard_indices = [i for i, c in enumerate(pattern) if c == '_']
        # Pre-filter by length only
        candidates = [word.upper() for word in word_list if len(word) == pattern_length]
        # Use list comprehension for speed
        matching_words = [
            word for word in candidates
            if self.__can_make_word(word, fixed_indices, fixed_letters, wildcard_indices, implicit_deck_counter)
        ]
        return matching_words

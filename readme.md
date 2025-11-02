# Scrabble Word Generator 

This project was done when I was stranded in Rwanda due to a mass civil unrest in Tanzania, out of sheer spite to not allow my husband to win scrabble every time. 

## Available Functions

### 1. Simple Pattern Generation
Generate words matching a fixed pattern using your available letters. Useful when you know exactly how many letters you need and where some letters should be placed.

**Pattern Format:**
- Use `_` for empty positions you want to fill
- Use letters for fixed positions (e.g., letters already on the board)
- Use `-` in your deck to represent a blank tile (wildcard). Each `-` can be used as any letter to help form a word.
- Include all letters in your deck and the letters from board you want to incorporate into your word generation

**Examples:**
- Pattern: `__J_` with deck `ABJCDE`
  - Means: "Find 4-letter words with 'J' in third position"
  - Might return: `AJAX`, `BAJA`, etc.
- Pattern: `H_T` with deck `HAITS-`
  - Means: "Find 3-letter words starting with 'H' and ending with 'T'. Choose from a deck of H, A, I, T, S, blank (wildcard to use as any letter)"
  - Might return: `HAT`, `HIT`, `HOT`, etc. (the blank can be used for any missing letter)

### 2. Dynamic Pattern Generation
Generate words with flexible length patterns. Useful when you want to explore different word lengths or have multiple spots to fill.

**Pattern Format:**
- Use `(n,m)` to indicate n to m empty positions
- Use `_` for single empty position
- Use letters for fixed positions
- Use `-` in your deck to represent a blank tile (wildcard). Each `-` can be used as any letter.
- Include all letters in your deck and the letters from board you want to incorporate into your word generation

**Examples:**
- Pattern: `(3,5)J_M(1,2)` with deck `JUMPSCALE-`
  - Means: "Find words with:
    - 3-5 letters, then
    - letter 'J', then
    - any letter, then
    - letter 'M', then
    - 1-2 letters
  - Might return: `___J_M_`, `___J_M__`, `____J_M_`, etc. 
- Pattern: `H(2,3)T` with deck `HEARTS-`
  - Means: "Find words starting with 'H', ending with 'T', and with 2-3 letters between. Choose from a deck of H, E, A, R, T, S, blank (wildcard to use as any letter)"
  - Might return: `HEART`, `HEAT`, `HEIST`, etc. (the blank can be used for any missing letter)
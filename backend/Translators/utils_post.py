""" This file contains the post process utilities functions for the translators."""
from block import Block

possible_starting_characters = ["『", "“", '"', "'", "‘", "\\", "/"]

possible_ending_characters = ["』", "”", '"', "'", "’", "/", "\\"]

standard_starting_character = "「"
standard_ending_character = "」"

# macro symbols to avoid in output text
macro_symbols = ["[", "]", "*"]
replace_macro_symbols = ["(", ")", "+"]


def fix_quoting_symbol(block: Block) -> Block:
    """fix the quoting symbol in the text,
    Args:
        text (str): the text to be fixed
    Returns:
        str: the text with the quoting symbol fixed
    """

    # skip if no speaker
    if block.speaker_original == "":
        return block

    text = block.text_translated

    # fix starting character, if the starting character is not standard
    if text.startswith(tuple(possible_starting_characters)):
        text = standard_starting_character + text[1:]
    # fix ending character, if the ending character is not standard
    if text.endswith(tuple(possible_ending_characters)):
        text = text[:-1] + standard_ending_character
    block.text_translated = text
    return block


def fix_macros(text: str) -> str:
    """fix the macros in the text,
    Args:
        text (str): the text to be fixed
    Returns:
        str: the text with the macros fixed
    """
    for i, symbol in enumerate(macro_symbols):
        text = text.replace(symbol, replace_macro_symbols[i])
    return text


def fix_text_after_translation(block: Block) -> Block:
    """A combination of fixing methods after translation"""
    block = fix_quoting_symbol(block)
    block.text_translated = fix_macros(block.text_translated)
    return block

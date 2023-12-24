""" This file contains the utility functions for the translators."""

import re


aaaa_possible_list = [
    "あああ",
    "ああぁ",
]
surrounding_characters = [""]


def fix_text_before_translation(text: str) -> str:
    """A combination of fixing methods before translation"""
    text, _ = remove_aaa(text)
    return text


def find_aaaa(text: str) -> object:
    """check if the text has aaaa
    Args:
        text (str): the text to be checked
    Returns:
        bool: if the text has aaaa
    """
    found_aaaa = None
    for aaaa in aaaa_possible_list:
        found_aaaa = re.search(aaaa, text)
        if found_aaaa:
            break
    return found_aaaa


def remove_aaa(text: str) -> (str, (int, int)):
    """remove the ahaha from the text
    Args:
        text (str): the text to be removed
    Returns:
        str: the text with aaaa removed
        (int, int): the start and end position of the removed text
    """
    # find the position of the first aaaa
    found_aaaa = None
    for aaaa in aaaa_possible_list:
        found_aaaa = re.search(aaaa, text)
        if found_aaaa:
            break
    if found_aaaa:
        # remove the aaaa
        text = text[: found_aaaa.span()[0]] + text[found_aaaa.span()[1] :]
        return text, found_aaaa.span()

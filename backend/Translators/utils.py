""" This file contains the utility functions for the translators."""

import re


aaaa_possible_list = [
    "あああ",
    "ぁぁぁ",
    "ぅぅぅ",
    "ぃぃぃ",
    "アアア",
    "ァァァ",
]
surrounding_characters = [""]


def convert_prompt_response(
    _input: str or list, seperation_method: str = "[]", enclosing_joiner="  "
) -> list:
    """This method defines the different methods of seperation of the prompt and response.
    It is used to generate a long message for the GPT API.
    if the input is a list of strings, it will be comibined by the seperation_method.
    if the input is a string, it will be seperated by the seperation_method.
    """
    # enclosing method
    enclosing_possible_list = ["[]", "\{\}", "<>"]
    enclosing_left_list = ["[", "{", "<"]
    enclosing_right_list = ["]", "}", ">"]
    enclosing_re_list = [r"\[(.*?)\]", r"\{(.*?)\}", r"\<(.*?)\>"]
    if seperation_method in enclosing_possible_list:
        # find index of speration method in the enclosing_possible_list
        _index = enclosing_possible_list.index(seperation_method)
        if isinstance(_input, str):
            return re.findall(enclosing_re_list[_index], _input)
        elif isinstance(_input, list):
            input_copy = _input.copy()
            for i, text in enumerate(input_copy):
                input_copy[i] = (
                    enclosing_left_list[_index] + text + enclosing_right_list[_index]
                )
            return enclosing_joiner.join(input_copy)

    # delimiter method (not implemented yet)
    # todo: implement this
    elif seperation_method == "||":
        pass


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


def fix_quoting_symbol(text: str) -> str:
    """fix the quoting symbol in the text
    Args:
        text (str): the text to be fixed
    Returns:
        str: the text with the quoting symbol fixed
    """
    if text.startswith("“"):
        text = "「" + text[1:]
    if text.startswith("”"):
        text = "」" + text[1:]
    return text


def fix_text_before_translation(text: str) -> str:
    """A combination of fixing methods before translation"""
    text, _ = remove_aaa(text)
    return text


def fix_text_after_translation(text: str) -> str:
    """A combination of fixing methods after translation"""
    text = fix_quoting_symbol(text)
    return text

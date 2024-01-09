""" a test script to check if the parser works """

from ..Integrators.Chaos_R.parser import parse_file, parse_block, guess_file_type
from ..scriptfile import ScriptFile
from ..block import Block
from ..block import default_text_separater, replace_substrings

test_file = "U:/Toys/Games/Gal/chaosr/ZSSS_神聖昂燐/GameResources_chaosr1/RawText/k_scenario/01本編/luna066H.ks"
test_blocks_start = (107, 132)


def test_default_text_separator():
    """test the default text separator"""
    example_original = ["「がはっ！", "　……やめろぉ、汚らしいのよ！　うくっ、いあっ、うぅぅぅ……」"]
    example_translated = "「停下！好臭啊，好热啊，又黏又恶心……哇啊啊啊」"
    results = default_text_separater(example_translated, example_original)
    # Example usage
    original_string = "The quick brown fox jumps over the lazy dog"
    positions = [(4, 9), (20, 25)]
    new_texts = ["slow", "walks"]

    result = replace_substrings(original_string, positions, new_texts)

    print(results)
    return


def test_parser():
    """test the parser of chaosr games"""
    test_file = "U:/Toys/Games/Gal/chaosr/神聖昂燐エストランジェ/SoraTranslator/RawText/k_scenario/est002.ks"
    script_file = ScriptFile.from_originalfile(test_file)
    parse_file(script_file)

    blocks = script_file.blocks

    block: Block = blocks[136]
    block.parse(parse_block_function=parse_block)
    block.text_translated = "5418128/529453489545"
    block.text_translated = "「停下！好啊，好热啊，……哇啊啊啊」"
    block.speaker_translated = "54188"
    result = block.generate_full_rawblock()

    return 0


def test_text_file():
    """test text file generation and reading"""
    script_file = ScriptFile.from_originalfile(test_file)
    script_file.parse(parse_file_function=parse_file, parse_block_function=parse_block)
    script_file.generate_textfile(replace=True)


def test_text_rebuild():
    """test the function of putting translated text back to its places"""


def test_type_guess():
    """test the type guess function"""
    test_file_type = "D:/Work/A_01_dakr026H.ks"
    script_file = ScriptFile.from_originalfile(test_file_type)
    result = guess_file_type(script_file)
    print(result)
    return


0

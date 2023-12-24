""" a test script to check if the parser works """

from ..Integrators.Chaos_R.parser import parse_file, parse_block
from ..scriptfile import ScriptFile
from ..block import Block

test_file = (
    "D:\\Work\\SoraTranslator\\GameResources\\RawText\\k_scenario\\01本編\\luna078.ks"
)
test_blocks_start = (107, 132)


def test_parser():
    """test the parser of chaosr games"""
    script_file = ScriptFile.from_originalfile(test_file)
    blocks, _, _ = parse_file(script_file)

    for block in blocks:
        block.parse(parse_block_function=parse_block)

    block: Block = blocks[6]
    block.text_translated = "54181285294534895"
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


0

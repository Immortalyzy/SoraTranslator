""" a test script to check if the parser works """ 

from ..Integrators.Chaos_R.parser import parse_file, parse_block
from ..scriptfile import ScriptFile

test_file = "D:\\Work\\SoraTranslator\\GameResources\\RawText\\k_scenario\\01本編\\luna003.ks"
test_blocks_start = (107, 132)

def test_parser():
    """ test the parser of chaosr games"""
    script_file = ScriptFile.from_originalfile(test_file)
    blocks, _, _ = parse_file(script_file)

    for i in range(4):
        blocks[i].parse(parse_block_function=parse_block)
        print(blocks[i].speaker_original, blocks[i].speaker_line, blocks[i].speaker_start_end)
        print(blocks[i].text_original, blocks[i].text_line, blocks[i].text_start_end)

    return 0

def test_text_fiel():
    """ test text file generation and reading """
    script_file = ScriptFile.from_originalfile(test_file)
    script_file.parse(parse_file_function=parse_file, parse_block_function=parse_block)
    script_file.generate_textfile()
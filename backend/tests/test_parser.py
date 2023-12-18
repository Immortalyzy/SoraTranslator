""" a test script to check if the parser works """ 

from ..Integrators.Chaos_R.parser import parse_file, parse_block
from ..scriptfile import ScriptFile

test_file = "D:\\Work\\SoraTranslator\\GameResources\\RawText\\k_scenario\\01本編\\luna003.ks"
test_blocks_start = (107, 132)

def test_parser():
    """ test the parser of chaosr games"""
    script_file = ScriptFile.from_originalfile(test_file)
    blocks = parse_file(script_file)

    for i in range(5):
        i += 1
        parse_block(blocks[i])

    return 0

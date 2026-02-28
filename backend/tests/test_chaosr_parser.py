import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Integrators.Chaos_R.parser import parse_file
from scriptfile import ScriptFile
from textfile import PROPERTY_LINE_LENGTH, TextFile


FIXTURE_DIR = Path(__file__).with_name("fixtures") / "chaos_r"


def parse_fixture(name: str) -> ScriptFile:
    script_file = ScriptFile.from_originalfile(str(FIXTURE_DIR / name))
    script_file.parse(parse_file_function=parse_file, force_single=True, encoding="utf_8")
    return script_file


def test_preamble_and_control_labels_are_not_exported(tmp_path):
    script_file = parse_fixture("structural_only.ks")

    assert [block.block_name for block in script_file.blocks] == ["start_of_file", "scene_start", "main"]

    text_file = script_file.textfiles[0]
    exportable_names = [block.block_name for block in text_file.exportable_blocks()]
    assert exportable_names == ["main"]

    csv_path = tmp_path / "structural_only.csv"
    text_file.generate_textfile(dest=str(csv_path), replace=True)
    csv_text = csv_path.read_text(encoding="utf_8")

    assert "start_of_file\t" not in csv_text
    assert "scene_start\t" not in csv_text
    assert "main\tAlice\tVisible line\t" in csv_text


def test_selection_rows_round_trip_and_preserve_structural_blocks(tmp_path):
    script_file = parse_fixture("selection_inline.ks")
    text_file = script_file.textfiles[0]

    exportable_blocks = text_file.exportable_blocks()
    assert [block.block_name for block in exportable_blocks] == ["SEL01|Label A/Label B", "SEL01_2", "main"]

    selection_block = exportable_blocks[0]
    assert selection_block.is_selection()
    assert selection_block.selection_original == ["First choice", "Second choice"]

    csv_path = tmp_path / "selection_inline.csv"
    text_file.generate_textfile(dest=str(csv_path), replace=True)

    reloaded = TextFile.from_textfile(str(csv_path))
    assert reloaded.blocks[0].block_name == "SEL01|Label A/Label B"
    assert reloaded.blocks[0].text_original == "First choice/Second choice"

    lines = csv_path.read_text(encoding="utf_8").splitlines()
    selection_row = lines[PROPERTY_LINE_LENGTH].split("\t")
    selection_row[4] = "Choice One/Choice Two"
    selection_row[5] = "Yes"
    selection_row[6] = "2026-02-28"
    selection_row[7] = "manual"
    lines[PROPERTY_LINE_LENGTH] = "\t".join(selection_row)
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf_8")

    assert script_file.update_from_textfiles() is True

    translated_path = tmp_path / "selection_inline_translated.ks"
    script_file.generate_translated_rawfile(dest=str(translated_path), replace=True, encoding="utf_8")
    translated_text = translated_path.read_text(encoding="utf_8")

    assert "[sel1 text='Choice One' target=*SEL01_1]" in translated_text
    assert '[sel2 text="Choice Two" target=*SEL01_2]' in translated_text
    assert "*scene_start" in translated_text
    assert "[cm]" in translated_text
    assert "*SEL01_1" in translated_text
    assert "[jump storage='scene.ks' target='route_a']" in translated_text


def test_selection_option_count_is_validated_against_original_block(tmp_path):
    script_file = parse_fixture("selection_inline.ks")
    text_file = script_file.textfiles[0]
    csv_path = tmp_path / "selection_inline_invalid.csv"
    text_file.generate_textfile(dest=str(csv_path), replace=True)

    lines = csv_path.read_text(encoding="utf_8").splitlines()
    selection_row = lines[PROPERTY_LINE_LENGTH].split("\t")
    selection_row[4] = "Only One Choice"
    lines[PROPERTY_LINE_LENGTH] = "\t".join(selection_row)
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf_8")

    assert script_file.update_from_textfiles() is False


def test_selection_falls_back_to_label_caption_when_inline_text_is_missing():
    script_file = parse_fixture("selection_label_fallback.ks")

    selection_block = script_file.textfiles[0].exportable_blocks()[0]
    assert selection_block.is_selection()
    assert selection_block.selection_original == ["Alpha", "Beta"]
    assert selection_block.text_original == "Alpha/Beta"

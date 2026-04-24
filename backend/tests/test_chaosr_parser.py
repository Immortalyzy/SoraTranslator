import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from block import Block
from Integrators.Chaos_R import chaosr_game as chaosr_game_module
from Integrators.Chaos_R.chaosr_game import ChaosRGame
from Integrators.Chaos_R.parser import parse_file
from scriptfile import ScriptFile
from textfile import PROPERTY_LINE_LENGTH, TextFile


FIXTURE_DIR = Path(__file__).with_name("fixtures") / "chaos_r"


def parse_fixture(name: str) -> ScriptFile:
    script_file = ScriptFile.from_originalfile(str(FIXTURE_DIR / name))
    script_file.parse(parse_file_function=parse_file, force_single=True, encoding="utf_8")
    return script_file


def build_test_game(tmp_path):
    project_dir = tmp_path / "project"
    raw_dir = project_dir / "RawText"
    text_dir = project_dir / "Text"
    translated_dir = project_dir / "TranslatedFiles"
    raw_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)
    translated_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "project_path": str(project_dir),
        "rawtext_directory": str(raw_dir),
        "text_directory": str(text_dir),
        "translated_files_directory": str(translated_dir),
    }
    game = ChaosRGame(paths=paths, name="Chaos_R")
    game.directory = str(tmp_path / "game")
    game.post_init()
    return game, raw_dir, text_dir


def stub_prepare_translation_inputs(monkeypatch, raw_dir: Path, script_specs: dict[str, dict[str, object]]):
    for script_name in script_specs:
        file_path = raw_dir / script_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("; test fixture\n", encoding="utf_8")

    def fake_prepare_raw_text(self, replace=False):
        self.script_file_list = []
        for script_name, spec in script_specs.items():
            script_file = ScriptFile.from_originalfile(str(raw_dir / script_name))
            script_file.file_type = str(spec["file_type"])
            self.script_file_list.append(script_file)

    def fake_guess_file_type(scriptfile, possible_content_re=None):
        return scriptfile.file_type

    def fake_parse_file(script_file, **kwargs):
        spec = script_specs[Path(script_file.script_file_path).name]
        block = Block("main", ["[cm]\n"])
        block.is_parsed = True
        if bool(spec["has_text"]):
            block.speaker_original = "Alice"
            block.text_original = "Visible line"
        script_file.blocks = [block]

    monkeypatch.setattr(ChaosRGame, "prepare_raw_text", fake_prepare_raw_text)
    monkeypatch.setattr(chaosr_game_module, "guess_file_type", fake_guess_file_type)
    monkeypatch.setattr(chaosr_game_module, "parse_file", fake_parse_file)
    monkeypatch.setattr(ChaosRGame, "refresh_global_name_replacement_table", lambda self: None)


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


def test_comment_lines_round_trip_without_being_exported(tmp_path):
    script_file = parse_fixture("comment_preservation.ks")
    text_file = script_file.textfiles[0]

    exportable_blocks = text_file.exportable_blocks()
    assert [block.block_name for block in exportable_blocks] == ["1|"]
    assert exportable_blocks[0].text_original == "Original line."

    csv_path = tmp_path / "comment_preservation.csv"
    text_file.generate_textfile(dest=str(csv_path), replace=True)
    csv_text = csv_path.read_text(encoding="utf_8")

    assert "comment header" not in csv_text
    assert "scene_exp_init" not in csv_text
    assert "1|\tAlice\tOriginal line.\t" in csv_text

    lines = csv_text.splitlines()
    row = lines[PROPERTY_LINE_LENGTH].split("\t")
    row[4] = "Translated line."
    row[5] = "Yes"
    row[6] = "2026-03-01"
    row[7] = "manual"
    lines[PROPERTY_LINE_LENGTH] = "\t".join(row)
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf_8")

    assert script_file.update_from_textfiles() is True

    translated_path = tmp_path / "comment_preservation_translated.ks"
    script_file.generate_translated_rawfile(dest=str(translated_path), replace=True, encoding="utf_8")
    translated_text = translated_path.read_text(encoding="utf_8")

    assert translated_text.startswith(";//comment header\n")
    assert "[if exp=\"tf.scene_mode == 1\"]\n\t;†[scene_exp_init]\n[endif]" in translated_text
    assert "Translated line.[pcms]" in translated_text


def test_selection_rows_round_trip_and_preserve_structural_blocks(tmp_path):
    script_file = parse_fixture("selection_inline.ks")
    text_file = script_file.textfiles[0]

    exportable_blocks = text_file.translation_rows()
    assert [block.block_name for block in exportable_blocks] == [
        "SEL01|Label A/Label B#1",
        "SEL01|Label A/Label B#2",
        "SEL01_2",
        "main",
    ]
    assert [block.text_original for block in exportable_blocks[:2]] == ["First choice", "Second choice"]

    selection_block = text_file.exportable_blocks()[0]
    assert selection_block.is_selection()
    assert selection_block.selection_original == ["First choice", "Second choice"]

    csv_path = tmp_path / "selection_inline.csv"
    text_file.generate_textfile(dest=str(csv_path), replace=True)

    reloaded = TextFile.from_textfile(str(csv_path))
    assert reloaded.blocks[0].block_name == "SEL01|Label A/Label B#1"
    assert reloaded.blocks[0].text_original == "First choice"
    assert reloaded.blocks[1].block_name == "SEL01|Label A/Label B#2"
    assert reloaded.blocks[1].text_original == "Second choice"

    lines = csv_path.read_text(encoding="utf_8").splitlines()
    selection_row_1 = lines[PROPERTY_LINE_LENGTH].split("\t")
    selection_row_1[4] = "Choice One"
    selection_row_1[5] = "Yes"
    selection_row_1[6] = "2026-02-28"
    selection_row_1[7] = "manual"
    lines[PROPERTY_LINE_LENGTH] = "\t".join(selection_row_1)

    selection_row_2 = lines[PROPERTY_LINE_LENGTH + 1].split("\t")
    selection_row_2[4] = "Choice Two"
    selection_row_2[5] = "Yes"
    selection_row_2[6] = "2026-02-28"
    selection_row_2[7] = "manual"
    lines[PROPERTY_LINE_LENGTH + 1] = "\t".join(selection_row_2)
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
    selection_row[5] = "Yes"
    lines[PROPERTY_LINE_LENGTH] = "\t".join(selection_row)
    del lines[PROPERTY_LINE_LENGTH + 1]
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf_8")

    assert script_file.update_from_textfiles() is False


def test_selection_legacy_single_row_format_still_round_trips(tmp_path):
    script_file = parse_fixture("selection_inline.ks")
    text_file = script_file.textfiles[0]
    csv_path = tmp_path / "selection_inline_legacy.csv"
    text_file.generate_textfile(dest=str(csv_path), replace=True)

    lines = csv_path.read_text(encoding="utf_8").splitlines()
    legacy_row = lines[PROPERTY_LINE_LENGTH].split("\t")
    legacy_row[0] = "SEL01|Label A/Label B"
    legacy_row[2] = "First choice/Second choice"
    legacy_row[4] = "Choice One/Choice Two"
    legacy_row[5] = "Yes"
    legacy_row[6] = "2026-02-28"
    legacy_row[7] = "manual"
    lines[PROPERTY_LINE_LENGTH] = "\t".join(legacy_row)
    del lines[PROPERTY_LINE_LENGTH + 1]
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf_8")

    assert script_file.update_from_textfiles() is True

    translated_path = tmp_path / "selection_inline_legacy_translated.ks"
    script_file.generate_translated_rawfile(dest=str(translated_path), replace=True, encoding="utf_8")
    translated_text = translated_path.read_text(encoding="utf_8")

    assert "[sel1 text='Choice One' target=*SEL01_1]" in translated_text
    assert '[sel2 text="Choice Two" target=*SEL01_2]' in translated_text


def test_selection_falls_back_to_label_caption_when_inline_text_is_missing():
    script_file = parse_fixture("selection_label_fallback.ks")

    selection_block = script_file.textfiles[0].exportable_blocks()[0]
    assert selection_block.is_selection()
    assert selection_block.selection_original == ["Alpha", "Beta"]
    assert selection_block.text_original == "Alpha/Beta"


def test_prepare_translation_skips_empty_candidates_and_warns(tmp_path, monkeypatch, caplog):
    game, raw_dir, text_dir = build_test_game(tmp_path)
    empty_script = raw_dir / "empty.ks"
    kept_script = raw_dir / "dialogue.ks"
    empty_csv = text_dir / "empty.csv"
    kept_csv = text_dir / "dialogue.csv"

    stub_prepare_translation_inputs(
        monkeypatch,
        raw_dir,
        {
            "empty.ks": {"file_type": "content", "has_text": False},
            "dialogue.ks": {"file_type": "content", "has_text": True},
        },
    )

    with caplog.at_level(logging.WARNING, logger=chaosr_game_module.logger.name):
        assert game.prepare_translation(replace=True) is True

    assert [Path(script_file.script_file_path).name for script_file in game.to_translate_file_list] == ["dialogue.ks"]
    assert not empty_csv.exists()
    assert kept_csv.exists()

    to_translate_rows = Path(game.to_translate_file_list_file).read_text(encoding="utf_8")
    assert str(empty_script) not in to_translate_rows
    assert str(empty_csv) not in to_translate_rows
    assert str(kept_script) in to_translate_rows
    assert str(kept_csv) in to_translate_rows

    script_list_rows = Path(game.scriptfile_list_file).read_text(encoding="utf_8").splitlines()
    empty_row = next(row for row in script_list_rows if row.startswith(str(empty_script)))
    empty_columns = empty_row.split("\t")
    assert empty_columns[1] == ""

    warning_messages = [
        record.getMessage()
        for record in caplog.records
        if "no exportable text" in record.getMessage()
    ]
    assert warning_messages == [f"Skipping {empty_script} because parsing found no exportable text."]


def test_prepare_translation_keeps_non_empty_candidates_in_inventory(tmp_path, monkeypatch):
    game, raw_dir, text_dir = build_test_game(tmp_path)
    kept_script = raw_dir / "dialogue.ks"
    kept_csv = text_dir / "dialogue.csv"

    stub_prepare_translation_inputs(
        monkeypatch,
        raw_dir,
        {
            "dialogue.ks": {"file_type": "content", "has_text": True},
        },
    )

    assert game.prepare_translation(replace=True) is True
    assert [Path(script_file.script_file_path).name for script_file in game.to_translate_file_list] == ["dialogue.ks"]

    tracked_script = game.to_translate_file_list[0]
    assert tracked_script.has_generated_textfiles() is True
    assert tracked_script.generated_textfiles()[0].text_file_path == str(kept_csv)

    to_translate_rows = Path(game.to_translate_file_list_file).read_text(encoding="utf_8")
    assert str(kept_script) in to_translate_rows
    assert str(kept_csv) in to_translate_rows


def test_nested_bracket_command_before_scene_start_round_trips_cleanly(tmp_path):
    script_file = parse_fixture("scene_start_nested_eval.ks")
    text_file = script_file.textfiles[0]
    exportable_blocks = text_file.exportable_blocks()

    assert [block.block_name for block in exportable_blocks] == ["1529|", "1530|"]
    assert exportable_blocks[0].text_original == "He moved closer and held her softly from behind."
    assert "eval" not in exportable_blocks[0].text_original
    assert "SRP_" not in exportable_blocks[0].text_original

    csv_path = tmp_path / "scene_start_nested_eval.csv"
    text_file.generate_textfile(dest=str(csv_path), replace=True)

    lines = csv_path.read_text(encoding="utf_8").splitlines()
    first_row = lines[PROPERTY_LINE_LENGTH].split("\t")
    first_row[4] = "He held her softly from behind."
    first_row[5] = "Yes"
    first_row[6] = "2026-02-28"
    first_row[7] = "manual"
    lines[PROPERTY_LINE_LENGTH] = "\t".join(first_row)
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf_8")

    assert script_file.update_from_textfiles() is True

    translated_path = tmp_path / "scene_start_nested_eval_translated.ks"
    script_file.generate_translated_rawfile(dest=str(translated_path), replace=True, encoding="utf_8")
    translated_text = translated_path.read_text(encoding="utf_8")

    translated_line = "He held her softly from behind.[pcms]"
    eval_line = "[eval exp=\"sf['SRP_' + f.sc] = 1\"]"
    assert translated_line in translated_text
    assert eval_line in translated_text
    assert "*scene_start" in translated_text
    assert translated_text.index(translated_line) < translated_text.index(eval_line) < translated_text.index("*scene_start")
    assert translated_line + "\n" + eval_line in translated_text
    assert "He held her softly from behind['SRP_' + f.sc]" not in translated_text


def test_indented_labels_parse_cleanly_and_round_trip(tmp_path):
    script_file = parse_fixture("indented_label.ks")

    assert [block.block_name for block in script_file.blocks] == ["802|"]

    block = script_file.blocks[0]
    assert block.speaker_original == "Kyo"
    assert block.text_original == "(I can fight on my own.)"
    assert "*802|" not in block.text_original

    text_file = script_file.textfiles[0]
    exportable_blocks = text_file.exportable_blocks()
    assert [exportable_block.block_name for exportable_block in exportable_blocks] == ["802|"]
    assert exportable_blocks[0].text_original == "(I can fight on my own.)"

    csv_path = tmp_path / "indented_label.csv"
    text_file.generate_textfile(dest=str(csv_path), replace=True)
    csv_text = csv_path.read_text(encoding="utf_8")

    assert "802|\tKyo\t(I can fight on my own.)\t" in csv_text
    assert "*802|\t" not in csv_text

    lines = csv_text.splitlines()
    row = lines[PROPERTY_LINE_LENGTH].split("\t")
    row[4] = "(I can fight alone.)"
    row[5] = "Yes"
    row[6] = "2026-03-01"
    row[7] = "manual"
    lines[PROPERTY_LINE_LENGTH] = "\t".join(row)
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf_8")

    assert script_file.update_from_textfiles() is True

    translated_path = tmp_path / "indented_label_translated.ks"
    script_file.generate_translated_rawfile(dest=str(translated_path), replace=True, encoding="utf_8")
    translated_text = translated_path.read_text(encoding="utf_8")

    assert translated_text.splitlines()[0] == "\t*802|"
    assert "\t[vo_kyo s=\"KYO_0129\"][ns]Kyo[nse](I can fight alone.)[pcms]" in translated_text
    assert "*802|(I can fight on my own.)" not in translated_text

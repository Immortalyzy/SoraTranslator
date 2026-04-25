from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from block import Block
from Integrators.Chaos_R.name_replacement import apply_chaosr_name_replacement_to_text
from Integrators.Chaos_R.chaosr_game import ChaosRGame
from global_name_replacement import (
    NameReplacementRow,
    apply_name_replacement_to_text,
    build_name_replacement_mapping,
    compile_name_replacement_pattern,
    normalize_name_replacement_rows,
    sort_name_replacement_rows_by_appearance,
)
from textfile import TextFile


def build_paths(tmp_path: Path) -> dict:
    project_path = tmp_path / "project"
    rawtext_path = project_path / "RawText"
    text_path = project_path / "Text"
    translated_path = project_path / "TranslatedFiles"
    for path in (project_path, rawtext_path, text_path, translated_path):
        path.mkdir(parents=True, exist_ok=True)

    return {
        "project_path": str(project_path),
        "rawtext_directory": str(rawtext_path),
        "text_directory": str(text_path),
        "translated_files_directory": str(translated_path),
    }


def test_normalize_rows_last_duplicate_wins_and_ignores_empty_source():
    rows = [
        {"speaker_original": "Alice", "speaker_translated": "A"},
        {"speaker_original": "", "speaker_translated": "Ignored"},
        {"speaker_original": "Bob", "speaker_translated": "B"},
        {"speaker_original": "Alice", "speaker_translated": "A2"},
    ]

    normalized = normalize_name_replacement_rows(rows)
    assert [row.source_name for row in normalized] == ["Bob", "Alice"]
    assert normalized[1].replacement_name == "A2"


def test_build_mapping_skips_empty_replacement():
    rows = [
        {"speaker_original": "Alice", "speaker_translated": "A"},
        {"speaker_original": "Bob", "speaker_translated": ""},
    ]

    mapping = build_name_replacement_mapping(rows)
    assert mapping == {"Alice": "A"}


def test_deterministic_overlap_replacement_prefers_longer_match():
    mapping = {"Al": "SHORT", "Alice": "LONG"}
    pattern = compile_name_replacement_pattern(mapping)
    replaced = apply_name_replacement_to_text("Alice and Al", mapping, pattern)
    assert replaced == "LONG and SHORT"


def test_chaosr_replacement_skips_protected_command_payloads():
    mapping = {"ビアンカ": "比安卡"}
    pattern = compile_name_replacement_pattern(mapping)
    text = (
        '[img_c storage="ビアンカ触手攻撃_L" layer=10]'
        '[std_alt_l storage="ビアンカ"]'
        '[std_yui_special storage="ビアンカ"]'
        '[std_bia storage="ビアンカ"]'
        "ビアンカが動いた。"
    )

    replaced = apply_chaosr_name_replacement_to_text(text, mapping, pattern)

    assert '[img_c storage="ビアンカ触手攻撃_L" layer=10]' in replaced
    assert '[std_alt_l storage="ビアンカ"]' in replaced
    assert '[std_yui_special storage="ビアンカ"]' in replaced
    assert '[std_bia storage="比安卡"]' in replaced
    assert "比安卡が動いた。" in replaced
    assert "比安卡触手攻撃_L" not in replaced


def test_sort_rows_by_appearance_descending():
    rows = [
        NameReplacementRow(source_name="Low", replacement_name="L", source_count="1"),
        NameReplacementRow(source_name="High", replacement_name="H", source_count="9"),
        NameReplacementRow(source_name="Mid", replacement_name="M", source_count="3"),
    ]
    sorted_rows = sort_name_replacement_rows_by_appearance(rows)
    assert [row.source_name for row in sorted_rows] == ["High", "Mid", "Low"]


def test_integration_replacement_last_duplicate_and_empty_skip(tmp_path):
    paths = build_paths(tmp_path)
    game = ChaosRGame(paths=paths, name="Chaos_R")

    translated_file = Path(paths["translated_files_directory"]) / "sample.ks"
    translated_file.write_text("Alice Al Bob", encoding="utf_8")

    game.to_translate_file_list = [SimpleNamespace(translated_script_file_path=str(translated_file))]

    table_rows = [
        NameReplacementRow(source_name="Al", replacement_name="SHORT", source_count="1"),
        NameReplacementRow(source_name="Alice", replacement_name="LONG", source_count="1"),
        NameReplacementRow(source_name="Al", replacement_name="SHORT2", source_count="1"),
        NameReplacementRow(source_name="Bob", replacement_name="", source_count="1"),
    ]
    table_file = game._create_global_name_replacement_textfile(table_rows, game.get_global_name_replacement_table_path())
    table_file.generate_textfile(dest=game.get_global_name_replacement_table_path(), replace=True)

    updated_count = game.apply_global_name_replacement_to_translated_files()
    assert updated_count == 1
    assert translated_file.read_text(encoding="utf_8") == "LONG SHORT2 Bob"


def test_integration_replacement_noop_when_no_valid_mapping(tmp_path):
    paths = build_paths(tmp_path)
    game = ChaosRGame(paths=paths, name="Chaos_R")

    translated_file = Path(paths["translated_files_directory"]) / "sample.ks"
    translated_file.write_text("Alice Bob", encoding="utf_8")
    game.to_translate_file_list = [SimpleNamespace(translated_script_file_path=str(translated_file))]

    table_rows = [
        NameReplacementRow(source_name="Alice", replacement_name="", source_count="1"),
        NameReplacementRow(source_name="Bob", replacement_name="", source_count="1"),
    ]
    table_file = game._create_global_name_replacement_textfile(table_rows, game.get_global_name_replacement_table_path())
    table_file.generate_textfile(dest=game.get_global_name_replacement_table_path(), replace=True)

    updated_count = game.apply_global_name_replacement_to_translated_files()
    assert updated_count == 0
    assert translated_file.read_text(encoding="utf_8") == "Alice Bob"


def test_integration_replacement_applies_to_non_translated_script_files(tmp_path):
    paths = build_paths(tmp_path)
    game = ChaosRGame(paths=paths, name="Chaos_R")

    raw_translated = Path(paths["rawtext_directory"]) / "k_scenario" / "a.ks"
    raw_system = Path(paths["rawtext_directory"]) / "k_others" / "_sys_name_macro.ks"
    raw_translated.parent.mkdir(parents=True, exist_ok=True)
    raw_system.parent.mkdir(parents=True, exist_ok=True)
    raw_translated.write_text("Alice translated", encoding="utf_8")
    raw_system.write_text("Alice macro", encoding="utf_8")

    translated_translated = Path(paths["translated_files_directory"]) / "k_scenario" / "a.ks"
    translated_translated.parent.mkdir(parents=True, exist_ok=True)
    translated_translated.write_text("Alice translated", encoding="utf_8")

    game.script_file_list = [
        SimpleNamespace(script_file_path=str(raw_translated)),
        SimpleNamespace(script_file_path=str(raw_system)),
    ]
    game.to_translate_file_list = [
        SimpleNamespace(script_file_path=str(raw_translated), translated_script_file_path=str(translated_translated)),
    ]

    table_rows = [NameReplacementRow(source_name="Alice", replacement_name="Alicia", source_count="2")]
    table_file = game._create_global_name_replacement_textfile(table_rows, game.get_global_name_replacement_table_path())
    table_file.generate_textfile(dest=game.get_global_name_replacement_table_path(), replace=True)

    game.populate_untranslated_script_files()
    updated_count = game.apply_global_name_replacement_to_translated_files()
    assert updated_count == 2

    translated_system = Path(paths["translated_files_directory"]) / "k_others" / "_sys_name_macro.ks"
    assert translated_system.read_text(encoding="utf_8") == "Alicia macro"
    assert translated_translated.read_text(encoding="utf_8") == "Alicia translated"


def test_integration_replacement_skips_img_c_but_keeps_map_text_replacement(tmp_path):
    paths = build_paths(tmp_path)
    game = ChaosRGame(paths=paths, name="Chaos_R")

    translated_script = Path(paths["translated_files_directory"]) / "k_scenario" / "verse.ks"
    translated_script.parent.mkdir(parents=True, exist_ok=True)
    translated_script.write_text(
        '[img_c storage="ビアンカ触手攻撃_L" layer=10]\n'
        '[std_alt_l storage="ビアンカ"]\n'
        '[std_yui_special storage="ビアンカ"]\n'
        "ビアンカは立っている。\n",
        encoding="utf_8",
    )

    translated_map = Path(paths["translated_files_directory"]) / "g_image2" / "01_map" / "_佐藤さん宛map.txt"
    translated_map.parent.mkdir(parents=True, exist_ok=True)
    translated_map.write_text("map_btn_ch03.png　ビアンカ\n", encoding="utf_8")

    table_rows = [NameReplacementRow(source_name="ビアンカ", replacement_name="比安卡", source_count="1")]
    table_file = game._create_global_name_replacement_textfile(table_rows, game.get_global_name_replacement_table_path())
    table_file.generate_textfile(dest=game.get_global_name_replacement_table_path(), replace=True)

    updated_count = game.apply_global_name_replacement_to_translated_files()

    assert updated_count == 2
    script_text = translated_script.read_text(encoding="utf_8")
    assert '[img_c storage="ビアンカ触手攻撃_L" layer=10]' in script_text
    assert '[std_alt_l storage="ビアンカ"]' in script_text
    assert '[std_yui_special storage="ビアンカ"]' in script_text
    assert "比安卡は立っている。" in script_text
    assert translated_map.read_text(encoding="utf_8") == "map_btn_ch03.png　比安卡\n"


def test_textfile_update_name_translation_applies_mapping_and_skips_empty():
    text_file = TextFile()

    first = Block("1", "")
    first.is_parsed = True
    first.speaker_original = "Alice"
    first.speaker_translated = ""

    second = Block("2", "")
    second.is_parsed = True
    second.speaker_original = "Bob"
    second.speaker_translated = "OldBob"

    text_file.blocks = [first, second]
    mapping = {"Alice": "Alicia", "Bob": "", "Carol": "Unused"}

    changed = text_file.update_name_translation(mapping)
    assert changed == 1
    assert text_file.blocks[0].speaker_translated == "Alicia"
    # Empty replacement should not overwrite existing translation.
    assert text_file.blocks[1].speaker_translated == "OldBob"

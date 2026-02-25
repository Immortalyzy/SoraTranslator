import json
from pathlib import Path

from config import Config


def write_json(path: Path, payload: dict):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_load_runtime_precedence_and_env_resolution(tmp_path, monkeypatch):
    template = tmp_path / "config.template.json"
    config_file = tmp_path / "config.json"
    user_file = tmp_path / "config.user.json"
    env_file = tmp_path / ".env"

    write_json(
        template,
        {
            "translator": "gpt",
            "model_name": "template-model",
            "token": "ENV:OPENAI_API_KEY",
        },
    )
    write_json(config_file, {"model_name": "config-model"})
    write_json(user_file, {"model_name": "user-model"})
    env_file.write_text("OPENAI_API_KEY=env-secret\nSORA_MODEL_NAME=env-model\n", encoding="utf-8")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SORA_MODEL_NAME", raising=False)

    cfg = Config.load_runtime(
        config_files=[str(template), str(config_file), str(user_file)],
        env_file=str(env_file),
        resolve_env_tokens=True,
    )

    assert cfg.model_name == "env-model"
    assert cfg.token == "env-secret"


def test_load_runtime_without_env_resolution_keeps_placeholders(tmp_path, monkeypatch):
    template = tmp_path / "config.template.json"
    env_file = tmp_path / ".env"
    write_json(template, {"token": "ENV:OPENAI_API_KEY"})
    env_file.write_text("OPENAI_API_KEY=env-secret\n", encoding="utf-8")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    cfg = Config.load_runtime(
        config_files=[str(template)],
        env_file=str(env_file),
        resolve_env_tokens=False,
    )

    assert cfg.token == "ENV:OPENAI_API_KEY"

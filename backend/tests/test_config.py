from __future__ import annotations

import importlib
from pathlib import Path


def test_settings_load_openai_api_key_from_repo_env(
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    original_content = env_path.read_text(encoding="utf-8") if env_path.exists() else None

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env_path.write_text("OPENAI_API_KEY=test-key-from-dotenv\n", encoding="utf-8")

    try:
        import app.config as config_module

        reloaded = importlib.reload(config_module)
        assert reloaded.settings.openai_api_key == "test-key-from-dotenv"
    finally:
        if original_content is None:
            env_path.unlink(missing_ok=True)
        else:
            env_path.write_text(original_content, encoding="utf-8")
        import app.config as config_module

        importlib.reload(config_module)

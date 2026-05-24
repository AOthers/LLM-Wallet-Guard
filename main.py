"""
DeepSeek API 用量监控 - Windows 系统托盘应用。
"""
import json
import sys
from pathlib import Path

from tray_ui import TrayApp


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def is_placeholder(value: str) -> bool:
    return not value or "在此填入" in value


def load_config(config_path: Path) -> dict:
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = {}

    api_key = cfg.get("api_key", "").strip()
    authorization = cfg.get("authorization", "").strip()
    cookie = cfg.get("cookie", "").strip()
    refresh = int(cfg.get("refresh_seconds", 30) or 30)

    return {
        "api_key": "" if is_placeholder(api_key) else api_key,
        "authorization": "" if is_placeholder(authorization) else authorization,
        "cookie": "" if is_placeholder(cookie) else cookie,
        "refresh_seconds": max(refresh, 10),
    }


def main():
    config_path = get_base_dir() / "config.json"
    cfg = load_config(config_path)
    app = TrayApp(
        config_path=config_path,
        api_key=cfg["api_key"],
        authorization=cfg["authorization"],
        cookie=cfg["cookie"],
        refresh_seconds=cfg["refresh_seconds"],
    )
    app.run()


if __name__ == "__main__":
    main()

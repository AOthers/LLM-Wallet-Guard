"""
DeepSeek API 用量监控 — 系统托盘应用。
"""
import json
import sys
from pathlib import Path
from tray_ui import TrayApp


def load_config() -> dict:
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent
    config_path = base / "config.json"
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    auth = cfg.get("authorization", "").strip()
    if not auth or "在此填入" in auth:
        print("请在 config.json 中填入 authorization (Bearer token)")
        sys.exit(1)

    cookie = cfg.get("cookie", "").strip()
    refresh = int(cfg.get("refresh_seconds", 30))
    return {"authorization": auth, "cookie": cookie, "refresh_seconds": refresh}


def main():
    cfg = load_config()
    app = TrayApp(
        authorization=cfg["authorization"],
        cookie=cfg["cookie"],
        refresh_seconds=cfg["refresh_seconds"],
    )
    app.run()


if __name__ == "__main__":
    main()

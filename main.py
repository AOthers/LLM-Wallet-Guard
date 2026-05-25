"""
LLM Wallet Guard - Windows 系统托盘应用。
"""
import json
import sys
from pathlib import Path

from PyQt6.QtCore import QIODevice
from PyQt6.QtNetwork import QLocalSocket

from tray_ui import TrayApp

APP_INSTANCE_KEY = "llm-wallet-guard-single-instance"


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
    proxy_authorization = cfg.get("proxy_authorization", "").strip()
    refresh = int(cfg.get("refresh_seconds", 30) or 30)
    provider = cfg.get("provider", "deepseek").strip().lower() or "deepseek"
    threshold = float(cfg.get("low_balance_threshold", 10) or 10)

    return {
        "provider": provider,
        "api_key": "" if is_placeholder(api_key) else api_key,
        "authorization": "" if is_placeholder(authorization) else authorization,
        "cookie": "" if is_placeholder(cookie) else cookie,
        "proxy_authorization": "" if is_placeholder(proxy_authorization) else proxy_authorization,
        "refresh_seconds": max(refresh, 10),
        "low_balance_threshold": max(threshold, 0),
    }


def main():
    socket = QLocalSocket()
    socket.connectToServer(APP_INSTANCE_KEY, QIODevice.OpenModeFlag.WriteOnly)
    if socket.waitForConnected(200):
        socket.write(b"show")
        socket.flush()
        socket.waitForBytesWritten(200)
        socket.disconnectFromServer()
        return

    config_path = get_base_dir() / "config.json"
    cfg = load_config(config_path)
    app = TrayApp(
        config_path=config_path,
        provider=cfg["provider"],
        api_key=cfg["api_key"],
        authorization=cfg["authorization"],
        cookie=cfg["cookie"],
        refresh_seconds=cfg["refresh_seconds"],
        low_balance_threshold=cfg["low_balance_threshold"],
        proxy_authorization=cfg["proxy_authorization"],
    )
    app.run()


if __name__ == "__main__":
    main()

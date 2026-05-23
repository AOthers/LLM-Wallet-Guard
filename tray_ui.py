from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QApplication, QGridLayout, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QIcon, QAction, QColor
import sys, os

PANEL_W = 310
PANEL_H = 215
C_BG = "#1e1e2e"
C_CARD = "#2a2a3c"
C_TEXT = "#cdd6f4"
C_SUB = "#6c7086"
C_ACCENT = "#89b4fa"
C_GREEN = "#a6e3a1"
C_ORANGE = "#fab387"
C_RED = "#f38ba8"
C_BORDER = "#45475a"


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


class BalancePanel(QWidget):
    refresh_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("DeepSeek 用量")
        self.setFixedSize(PANEL_W, PANEL_H)
        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(f"QWidget {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Microsoft YaHei'; font-size: 13px; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        title = QLabel("DeepSeek API 用量")
        title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {C_ACCENT}; background: transparent;")
        title_row.addWidget(title)
        title_row.addStretch()
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"QPushButton {{ background: transparent; color: {C_SUB}; font-size: 14px; border: none; font-weight: bold; }} QPushButton:hover {{ color: {C_RED}; }}")
        btn_close.clicked.connect(self.hide)
        title_row.addWidget(btn_close)
        layout.addLayout(title_row)

        card = QFrame()
        card.setStyleSheet(f"QFrame#balanceCard {{ background-color: {C_CARD}; border-radius: 8px; }}")
        card.setObjectName("balanceCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(2)

        self.lbl_balance = QLabel("余额  ¥—")
        self.lbl_balance.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {C_GREEN}; background: transparent;")
        card_layout.addWidget(self.lbl_balance)

        self.lbl_cost = QLabel("本月消费  ¥—")
        self.lbl_cost.setStyleSheet(f"font-size: 12px; color: {C_SUB}; background: transparent;")
        card_layout.addWidget(self.lbl_cost)

        layout.addWidget(card)

        usage_card = QFrame()
        usage_card.setStyleSheet(f"QFrame#usageCard {{ background-color: {C_CARD}; border-radius: 8px; }}")
        usage_card.setObjectName("usageCard")
        ugrid = QGridLayout(usage_card)
        ugrid.setContentsMargins(12, 8, 12, 8)
        ugrid.setHorizontalSpacing(16)
        ugrid.setVerticalSpacing(2)

        lbl1 = QLabel("总消耗")
        lbl1.setStyleSheet(f"font-size: 11px; color: {C_SUB}; background: transparent;")
        ugrid.addWidget(lbl1, 0, 0)
        self.lbl_total = QLabel("—")
        self.lbl_total.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {C_TEXT}; background: transparent;")
        ugrid.addWidget(self.lbl_total, 1, 0)

        lbl2 = QLabel("输出")
        lbl2.setStyleSheet(f"font-size: 11px; color: {C_SUB}; background: transparent;")
        ugrid.addWidget(lbl2, 0, 1)
        self.lbl_output = QLabel("—")
        self.lbl_output.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {C_TEXT}; background: transparent;")
        ugrid.addWidget(self.lbl_output, 1, 1)

        lbl3 = QLabel("缓存命中")
        lbl3.setStyleSheet(f"font-size: 11px; color: {C_SUB}; background: transparent;")
        ugrid.addWidget(lbl3, 2, 0)
        self.lbl_cache_hit = QLabel("—")
        self.lbl_cache_hit.setStyleSheet(f"font-size: 13px; color: {C_GREEN}; background: transparent;")
        ugrid.addWidget(self.lbl_cache_hit, 3, 0)

        lbl4 = QLabel("缓存未命中")
        lbl4.setStyleSheet(f"font-size: 11px; color: {C_SUB}; background: transparent;")
        ugrid.addWidget(lbl4, 2, 1)
        self.lbl_cache_miss = QLabel("—")
        self.lbl_cache_miss.setStyleSheet(f"font-size: 13px; color: {C_ORANGE}; background: transparent;")
        ugrid.addWidget(self.lbl_cache_miss, 3, 1)

        layout.addWidget(usage_card)
        layout.addStretch()

        bottom = QHBoxLayout()
        self.lbl_status = QLabel("就绪")
        self.lbl_status.setStyleSheet(f"font-size: 11px; color: {C_SUB}; background: transparent;")
        bottom.addWidget(self.lbl_status)
        bottom.addStretch()
        btn_refresh = QPushButton("刷新")
        btn_refresh.setFixedSize(56, 24)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet(f"QPushButton {{ background-color: {C_CARD}; border: 1px solid {C_BORDER}; border-radius: 4px; color: {C_TEXT}; font-size: 11px; }} QPushButton:hover {{ background-color: {C_BORDER}; }}")
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        bottom.addWidget(btn_refresh)
        layout.addLayout(bottom)

    def update_data(self, data):
        if not data.is_available:
            self.lbl_status.setText(f"⚠ {data.error or '获取失败'}")
            self.lbl_status.setStyleSheet(f"font-size: 11px; color: {C_RED}; background: transparent;")
            return
        self.lbl_balance.setText(f"余额  ¥{data.normal_balance:.2f}  (≈ {fmt_tokens(data.normal_token_est)})")
        self.lbl_cost.setText(f"本月消费  ¥{data.monthly_cost:.2f}")
        total = data.input_tokens + data.cache_hit_tokens + data.cache_miss_tokens + data.output_tokens
        self.lbl_total.setText(fmt_tokens(total))
        self.lbl_output.setText(fmt_tokens(data.output_tokens))
        self.lbl_cache_hit.setText(fmt_tokens(data.cache_hit_tokens))
        self.lbl_cache_miss.setText(fmt_tokens(data.cache_miss_tokens))

    def update_status(self, text: str, is_error: bool = False):
        color = C_RED if is_error else C_SUB
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")


# ── 开机自启 ──

def _startup_dir() -> str:
    return os.path.join(os.getenv("APPDATA", ""),
                        r"Microsoft\Windows\Start Menu\Programs\Startup")


def _startup_shortcut_path() -> str:
    return os.path.join(_startup_dir(), "DeepSeek用量监控.lnk")


def is_autostart_enabled() -> bool:
    return os.path.exists(_startup_shortcut_path())


def enable_autostart():
    """创建快捷方式到启动文件夹。"""
    from win32com.client import Dispatch

    shortcut_path = _startup_shortcut_path()
    exe = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
    if exe.endswith(".py"):
        exe = sys.executable

    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = exe
    shortcut.WorkingDirectory = os.path.dirname(exe)
    shortcut.Description = "DeepSeek 用量监控"
    shortcut.Save()


def disable_autostart():
    sp = _startup_shortcut_path()
    if os.path.exists(sp):
        os.remove(sp)


# ── 托盘应用 ──

class TrayApp:
    def __init__(self, authorization: str, cookie: str = "", refresh_seconds: int = 30):
        self.authorization = authorization
        self.cookie = cookie
        self.refresh_ms = max(refresh_seconds, 10) * 1000
        self._token_expired_notified = False

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self._make_icon(C_ACCENT))
        self.tray.setToolTip("DeepSeek 用量监控")

        self._build_menu()
        self.tray.activated.connect(self._on_tray_activated)

        self.panel = BalancePanel()
        self.panel.refresh_requested.connect(self._do_refresh)

        self.timer = QTimer()
        self.timer.timeout.connect(self._do_refresh)
        self.timer.start(self.refresh_ms)

        self.tray.show()
        QTimer.singleShot(500, self._do_refresh)

    def _build_menu(self):
        self.menu = QMenu()

        self.menu.addAction("显示面板", self._show_panel)
        self.menu.addAction("立即刷新", self._do_refresh)

        self.menu.addSeparator()

        # 开机自启复选
        self.action_autostart = QAction("开机自启", self.menu)
        self.action_autostart.setCheckable(True)
        self.action_autostart.setChecked(is_autostart_enabled())
        self.action_autostart.triggered.connect(self._toggle_autostart)
        self.menu.addAction(self.action_autostart)

        self.menu.addSeparator()
        self.menu.addAction("退出", self._quit)
        self.tray.setContextMenu(self.menu)

    def _toggle_autostart(self, checked):
        try:
            if checked:
                enable_autostart()
            else:
                disable_autostart()
        except Exception as e:
            QMessageBox.warning(None, "错误", f"操作失败: {e}")

    def _make_icon(self, color_hex: str) -> QIcon:
        from PyQt6.QtGui import QPixmap, QPainter, QBrush
        pix = QPixmap(16, 16)
        pix.fill(QColor(0, 0, 0, 0))
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(color_hex)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(2, 2, 12, 12, 3, 3)
        p.end()
        return QIcon(pix)

    def _show_panel(self):
        geo = self.tray.geometry()
        x = geo.center().x() - PANEL_W // 2
        y = geo.top() - PANEL_H - 8
        screen = self.app.primaryScreen().availableGeometry()
        x = max(screen.left() + 4, min(x, screen.right() - PANEL_W - 4))
        y = max(screen.top() + 4, y)
        self.panel.move(x, y)
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_panel()

    def _do_refresh(self):
        from api_client import fetch_balance, fetch_usage_detail
        self.panel.update_status("刷新中…")
        try:
            data = fetch_balance(self.authorization, self.cookie)
            if data.is_available:
                self._token_expired_notified = False
                detail = fetch_usage_detail(self.authorization, self.cookie)
                data.input_tokens = detail.get("input", 0)
                data.cache_hit_tokens = detail.get("cache_hit", 0)
                data.cache_miss_tokens = detail.get("cache_miss", 0)
                data.output_tokens = detail.get("output", 0)

            self.panel.update_data(data)
            if data.is_available:
                self.panel.update_status("已刷新")
                self.tray.setIcon(self._make_icon(C_GREEN))
            else:
                self.tray.setIcon(self._make_icon(C_RED))
                # Token 过期弹窗（只弹一次）
                if "过期" in (data.error or "") and not self._token_expired_notified:
                    self._token_expired_notified = True
                    QMessageBox.warning(
                        None, "Token 已过期",
                        "DeepSeek 平台 Token 已过期，请重新获取。\n\n"
                        "获取方式：浏览器打开 platform.deepseek.com\n"
                        "F12 → Network → 找 get_user_summary\n"
                        "→ Request Headers → 复制 authorization\n"
                        "→ 粘贴到 config.json"
                    )
        except Exception as e:
            self.panel.update_data(type("d", (), {"is_available": False, "error": str(e)})())
            self.panel.update_status(f"网络错误: {e}", is_error=True)
            self.tray.setIcon(self._make_icon(C_RED))

    def _quit(self):
        self.timer.stop()
        self.panel.close()
        self.tray.hide()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

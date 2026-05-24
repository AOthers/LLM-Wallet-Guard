from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon
import os
import sys
import json

PANEL_W = 310
PANEL_H = 285
PANEL_H_BALANCE_ONLY = 132
PANEL_H_CONFIG = 380
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
    settings_requested = pyqtSignal()
    config_saved = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._status_clear_timer = QTimer(self)
        self._status_clear_timer.setSingleShot(True)
        self._status_clear_timer.timeout.connect(self.clear_status)
        self._config_required = False
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("DeepSeek 用量")
        self.setFixedSize(PANEL_W, PANEL_H)
        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(
            f"QWidget {{ background-color: {C_BG}; color: {C_TEXT}; "
            "font-family: 'Microsoft YaHei'; font-size: 13px; }}"
        )

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(14, 12, 14, 12)
        self.root_layout.setSpacing(8)

        self.title_bar = QWidget()
        self.title_bar.setCursor(Qt.CursorShape.SizeAllCursor)
        self.title_bar.mousePressEvent = self._title_mouse_press
        self.title_bar.mouseMoveEvent = self._title_mouse_move
        self.title_bar.mouseReleaseEvent = self._title_mouse_release
        self.title_row = QHBoxLayout(self.title_bar)
        self.title_row.setContentsMargins(0, 0, 0, 0)
        self.title_row.setSpacing(0)
        self.title = QLabel("DeepSeek API 用量")
        self.title.setStyleSheet(
            f"font-size: 15px; font-weight: bold; color: {C_ACCENT}; background: transparent;"
        )
        self.title_row.addWidget(self.title)
        self.title_row.addStretch()
        btn_close = QPushButton("×")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {C_SUB}; font-size: 14px; "
            f"border: none; font-weight: bold; }} QPushButton:hover {{ color: {C_RED}; }}"
        )
        btn_close.clicked.connect(self.hide)
        self.title_row.addWidget(btn_close)
        self.root_layout.addWidget(self.title_bar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: transparent; }")
        self.root_layout.addWidget(self.stack)

        self.data_page = QWidget()
        self.config_page = QWidget()
        self.stack.addWidget(self.data_page)
        self.stack.addWidget(self.config_page)

        self._build_data_page()
        self._build_config_page()

    def _build_data_page(self):
        layout = QVBoxLayout(self.data_page)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet(f"QFrame#balanceCard {{ background-color: {C_CARD}; border-radius: 8px; }}")
        card.setObjectName("balanceCard")
        self.balance_card = card
        self.balance_card.setFixedHeight(66)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)

        self.lbl_balance = QLabel("余额  ¥--")
        self.lbl_balance.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {C_GREEN}; background: transparent;"
        )
        card_layout.addWidget(self.lbl_balance)

        self.lbl_cost = QLabel("")
        self.lbl_cost.setStyleSheet(f"font-size: 12px; color: {C_SUB}; background: transparent;")
        card_layout.addWidget(self.lbl_cost)

        layout.addWidget(card)

        self.usage_card = QFrame()
        self.usage_card.setStyleSheet(f"QFrame#usageCard {{ background-color: {C_CARD}; border-radius: 8px; }}")
        self.usage_card.setObjectName("usageCard")
        self.usage_card.setMinimumHeight(122)
        ugrid = QGridLayout(self.usage_card)
        ugrid.setContentsMargins(12, 10, 12, 10)
        ugrid.setHorizontalSpacing(10)
        ugrid.setVerticalSpacing(10)
        ugrid.setColumnStretch(0, 1)
        ugrid.setColumnStretch(1, 1)

        def make_metric(label_text: str, value_color: str = C_TEXT):
            box = QFrame()
            box.setMinimumHeight(46)
            box.setStyleSheet(
                f"QFrame {{ background-color: {C_BG}; border: 1px solid {C_BORDER}; border-radius: 6px; }}"
                "QLabel { border: none; background: transparent; }"
            )
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(10, 6, 10, 6)
            box_layout.setSpacing(2)
            label = QLabel(label_text)
            label.setStyleSheet(f"font-size: 11px; color: {C_SUB}; background: transparent;")
            value = QLabel("--")
            value.setMinimumHeight(19)
            value.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {value_color}; background: transparent;")
            box_layout.addWidget(label)
            box_layout.addWidget(value)
            return box, value

        total_box, self.lbl_total = make_metric("总消耗")
        output_box, self.lbl_output = make_metric("输出")
        hit_box, self.lbl_cache_hit = make_metric("缓存命中", C_GREEN)
        miss_box, self.lbl_cache_miss = make_metric("缓存未命中", C_ORANGE)
        ugrid.addWidget(total_box, 0, 0)
        ugrid.addWidget(output_box, 0, 1)
        ugrid.addWidget(hit_box, 1, 0)
        ugrid.addWidget(miss_box, 1, 1)

        layout.addWidget(self.usage_card)

        self.data_spacer = QWidget()
        self.data_spacer.setFixedHeight(0)
        layout.addWidget(self.data_spacer)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 2, 0, 0)
        self.lbl_status = QLabel("就绪")
        self.lbl_status.setStyleSheet(f"font-size: 11px; color: {C_SUB}; background: transparent;")
        bottom.addWidget(self.lbl_status)
        bottom.addStretch()
        btn_settings = QPushButton("设置")
        btn_settings.setFixedSize(56, 24)
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.setStyleSheet(
            f"QPushButton {{ background-color: {C_CARD}; border: 1px solid {C_BORDER}; "
            f"border-radius: 4px; color: {C_TEXT}; font-size: 11px; }} "
            f"QPushButton:hover {{ background-color: {C_BORDER}; }}"
        )
        btn_settings.clicked.connect(self.settings_requested.emit)
        bottom.addWidget(btn_settings)
        btn_refresh = QPushButton("刷新")
        btn_refresh.setFixedSize(56, 24)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet(
            f"QPushButton {{ background-color: {C_CARD}; border: 1px solid {C_BORDER}; "
            f"border-radius: 4px; color: {C_TEXT}; font-size: 11px; }} "
            f"QPushButton:hover {{ background-color: {C_BORDER}; }}"
        )
        btn_refresh.clicked.connect(self.refresh_requested.emit)
        bottom.addWidget(btn_refresh)
        layout.addLayout(bottom)

    def _build_config_page(self):
        layout = QVBoxLayout(self.config_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        def add_field(label_text: str, widget):
            label = QLabel(label_text)
            label.setStyleSheet(f"font-size: 11px; color: {C_SUB}; background: transparent;")
            layout.addWidget(label)
            layout.addWidget(widget)

        input_style = (
            f"QLineEdit, QSpinBox {{ background-color: {C_CARD}; border: 1px solid {C_BORDER}; "
            f"border-radius: 6px; color: {C_TEXT}; padding: 7px 9px; font-size: 12px; }}"
            f"QLineEdit:focus, QSpinBox:focus {{ border-color: {C_ACCENT}; }}"
        )

        self.input_api_key = QLineEdit()
        self.input_api_key.setPlaceholderText("sk-...")
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_api_key.setFixedHeight(30)
        self.input_api_key.setStyleSheet(input_style)
        add_field("API Key（推荐，至少填写这一项）", self.input_api_key)

        self.input_authorization = QLineEdit()
        self.input_authorization.setPlaceholderText("Bearer ...（可选，用于完整用量）")
        self.input_authorization.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_authorization.setFixedHeight(30)
        self.input_authorization.setStyleSheet(input_style)
        add_field("网页 Authorization（可选）", self.input_authorization)

        self.input_cookie = QLineEdit()
        self.input_cookie.setPlaceholderText("Cookie（可选）")
        self.input_cookie.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_cookie.setFixedHeight(30)
        self.input_cookie.setStyleSheet(input_style)
        add_field("Cookie（可选）", self.input_cookie)

        self.input_refresh = QSpinBox()
        self.input_refresh.setRange(10, 3600)
        self.input_refresh.setValue(30)
        self.input_refresh.setSuffix(" 秒")
        self.input_refresh.setFixedHeight(30)
        self.input_refresh.setStyleSheet(input_style)
        add_field("刷新间隔", self.input_refresh)

        layout.addSpacing(6)

        self.lbl_config_status = QLabel("")
        self.lbl_config_status.setStyleSheet(f"font-size: 11px; color: {C_SUB}; background: transparent;")
        self.lbl_config_status.setFixedHeight(10)
        layout.addWidget(self.lbl_config_status)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(10)
        actions.addStretch()
        self.btn_cancel = QPushButton("返回")
        btn_save = QPushButton("保存")
        for btn in (self.btn_cancel, btn_save):
            btn.setFixedSize(64, 26)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {C_CARD}; border: 1px solid {C_BORDER}; "
                f"border-radius: 4px; color: {C_TEXT}; font-size: 11px; }} "
                f"QPushButton:hover {{ background-color: {C_BORDER}; }}"
            )
        btn_save.setStyleSheet(
            f"QPushButton {{ background-color: {C_ACCENT}; border: none; border-radius: 4px; "
            f"color: {C_BG}; font-size: 11px; font-weight: bold; }} "
            "QPushButton:hover { background-color: #b4befe; }"
        )
        self.btn_cancel.clicked.connect(self.show_data_page)
        btn_save.clicked.connect(self._save_config_clicked)
        actions.addWidget(self.btn_cancel)
        actions.addWidget(btn_save)
        layout.addLayout(actions)
        layout.addSpacing(10)

    def update_data(self, data):
        if not data.is_available:
            self.lbl_status.setText(f"⚠ {data.error or '获取失败'}")
            self.lbl_status.setStyleSheet(f"font-size: 11px; color: {C_RED}; background: transparent;")
            return

        balance_text = f"余额  ¥{data.normal_balance:.2f}"
        if data.normal_token_est:
            balance_text += f"  (≈ {fmt_tokens(data.normal_token_est)})"
        self.lbl_balance.setText(balance_text)

        if data.monthly_cost is None:
            self.lbl_cost.clear()
            self.lbl_cost.hide()
            self.balance_card.setFixedHeight(50)
        else:
            self.lbl_cost.show()
            self.balance_card.setFixedHeight(66)
            self.lbl_cost.setText(f"本月消费  ¥{data.monthly_cost:.2f}")

        if data.usage_available:
            self.usage_card.show()
            self.data_spacer.setFixedHeight(0)
            if self.stack.currentWidget() == self.data_page:
                self._set_fixed_height_keep_bottom(PANEL_H)
            total = data.input_tokens + data.cache_hit_tokens + data.cache_miss_tokens + data.output_tokens
            self.lbl_total.setText(fmt_tokens(total))
            self.lbl_output.setText(fmt_tokens(data.output_tokens))
            self.lbl_cache_hit.setText(fmt_tokens(data.cache_hit_tokens))
            self.lbl_cache_miss.setText(fmt_tokens(data.cache_miss_tokens))
        else:
            self.usage_card.hide()
            self.data_spacer.setFixedHeight(0)
            if self.stack.currentWidget() == self.data_page:
                self._set_fixed_height_keep_bottom(PANEL_H_BALANCE_ONLY)
            self.lbl_total.setText("--")
            self.lbl_output.setText("--")
            self.lbl_cache_hit.setText("--")
            self.lbl_cache_miss.setText("--")

    def set_config_values(self, api_key: str, authorization: str, cookie: str, refresh_seconds: int):
        self.input_api_key.setText(api_key)
        self.input_authorization.setText(authorization)
        self.input_cookie.setText(cookie)
        self.input_refresh.setValue(max(10, int(refresh_seconds or 30)))

    def get_config_values(self) -> dict:
        return {
            "api_key": self.input_api_key.text().strip(),
            "authorization": self.input_authorization.text().strip(),
            "cookie": self.input_cookie.text().strip(),
            "refresh_seconds": self.input_refresh.value(),
        }

    def show_config_page(self):
        self.title.setText("DeepSeek 配置")
        self.stack.setCurrentWidget(self.config_page)
        self._set_fixed_height_keep_bottom(PANEL_H_CONFIG)
        self.lbl_config_status.clear()
        self.btn_cancel.setVisible(not self._config_required)

    def show_data_page(self):
        if self._config_required:
            return
        self.title.setText("DeepSeek API 用量")
        self.stack.setCurrentWidget(self.data_page)
        if self.usage_card.isVisible():
            self._set_fixed_height_keep_bottom(PANEL_H)
        else:
            self._set_fixed_height_keep_bottom(PANEL_H_BALANCE_ONLY)

    def _save_config_clicked(self):
        cfg = self.get_config_values()
        if not cfg["api_key"] and not cfg["authorization"]:
            self.lbl_config_status.setText("请至少填写 API Key 或网页 Authorization")
            self.lbl_config_status.setStyleSheet(f"font-size: 11px; color: {C_RED}; background: transparent;")
            return
        self.config_saved.emit(cfg)

    def set_config_required(self, required: bool):
        self._config_required = required

    def update_status(self, text: str, is_error: bool = False):
        self._status_clear_timer.stop()
        color = C_RED if is_error else C_SUB
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")
        if text == "已刷新" and not is_error:
            self._status_clear_timer.start(3000)

    def clear_status(self):
        self.lbl_status.clear()

    def _set_fixed_height_keep_bottom(self, height: int):
        old_bottom = self.geometry().bottom()
        self.setFixedHeight(height)
        if self.isVisible():
            self.move(self.x(), old_bottom - self.height() + 1)

    def _title_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _title_mouse_move(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def _title_mouse_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            event.accept()


def _startup_dir() -> str:
    return os.path.join(os.getenv("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")


def _startup_shortcut_path() -> str:
    return os.path.join(_startup_dir(), "DeepSeek用量监控.lnk")


def is_autostart_enabled() -> bool:
    return os.path.exists(_startup_shortcut_path())


def enable_autostart():
    """创建快捷方式到启动文件夹。"""
    from win32com.client import Dispatch

    shortcut_path = _startup_shortcut_path()
    exe = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
    if exe.endswith(".py"):
        exe = sys.executable

    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = exe
    shortcut.WorkingDirectory = os.path.dirname(exe)
    shortcut.Description = "DeepSeek 用量监控"
    shortcut.Save()


def disable_autostart():
    shortcut_path = _startup_shortcut_path()
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)


class TrayApp:
    def __init__(
        self,
        config_path,
        api_key: str = "",
        authorization: str = "",
        cookie: str = "",
        refresh_seconds: int = 30,
    ):
        self.config_path = config_path
        self.api_key = api_key
        self.authorization = authorization
        self.cookie = cookie
        self.refresh_seconds = max(refresh_seconds, 10)
        self.refresh_ms = self.refresh_seconds * 1000
        self._token_expired_notified = False

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self._make_icon(C_ACCENT))
        self.tray.setToolTip("DeepSeek 用量监控")

        self._build_menu()
        self.tray.activated.connect(self._on_tray_activated)

        self.panel = BalancePanel()
        self.panel.set_config_values(
            api_key=self.api_key,
            authorization=self.authorization,
            cookie=self.cookie,
            refresh_seconds=self.refresh_seconds,
        )
        self.panel.refresh_requested.connect(self._do_refresh)
        self.panel.settings_requested.connect(self._show_config)
        self.panel.config_saved.connect(self._save_config)

        self.timer = QTimer()
        self.timer.timeout.connect(self._do_refresh)
        self.timer.start(self.refresh_ms)

        self.tray.show()
        if not self.api_key and not self.authorization:
            self.panel.set_config_required(True)
            self.panel.show_config_page()
        QTimer.singleShot(300, self._show_panel)
        if self.api_key or self.authorization:
            QTimer.singleShot(500, self._do_refresh)

    def _build_menu(self):
        self.menu = QMenu()

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

    def _show_config(self):
        self.panel.set_config_values(
            api_key=self.api_key,
            authorization=self.authorization,
            cookie=self.cookie,
            refresh_seconds=self.refresh_seconds,
        )
        self.panel.show_config_page()
        self._show_panel()

    def _save_config(self, cfg: dict):
        self.api_key = cfg["api_key"]
        self.authorization = cfg["authorization"]
        self.cookie = cfg["cookie"]
        self.refresh_seconds = max(int(cfg["refresh_seconds"]), 10)
        self.refresh_ms = self.refresh_seconds * 1000

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "api_key": self.api_key,
                    "authorization": self.authorization,
                    "cookie": self.cookie,
                    "refresh_seconds": self.refresh_seconds,
                },
                f,
                ensure_ascii=False,
                indent=4,
            )
            f.write("\n")

        self.timer.start(self.refresh_ms)
        self.panel.set_config_required(False)
        self.panel.show_data_page()
        self.panel.update_status("配置已保存")
        self._show_panel()
        self._do_refresh()

    def _make_icon(self, color_hex: str) -> QIcon:
        from PyQt6.QtGui import QBrush, QPainter, QPainterPath, QPen, QPixmap

        pix = QPixmap(32, 32)
        pix.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#1e1e2e")))
        painter.drawEllipse(2, 2, 28, 28)

        painter.setPen(QPen(QColor(color_hex), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(3, 3, 26, 26)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#89b4fa")))
        body = QPainterPath()
        body.moveTo(8, 18)
        body.cubicTo(9, 12, 15, 9, 21, 11)
        body.cubicTo(25, 12, 27, 15, 26, 19)
        body.cubicTo(22, 23, 14, 24, 9, 21)
        body.cubicTo(8, 20, 8, 19, 8, 18)
        painter.drawPath(body)

        painter.setBrush(QBrush(QColor("#b4befe")))
        tail = QPainterPath()
        tail.moveTo(8, 18)
        tail.lineTo(4, 14)
        tail.cubicTo(6, 14, 8, 15, 9, 17)
        tail.lineTo(5, 20)
        tail.cubicTo(6, 20, 8, 20, 9, 19)
        painter.drawPath(tail)

        painter.setBrush(QBrush(QColor("#1e1e2e")))
        painter.drawEllipse(20, 15, 2, 2)

        painter.setBrush(QBrush(QColor("#cdd6f4")))
        spout = QPainterPath()
        spout.moveTo(14, 10)
        spout.cubicTo(13, 7, 15, 6, 16, 4)
        spout.cubicTo(17, 6, 18, 8, 17, 10)
        painter.drawPath(spout)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.end()
        return QIcon(pix)

    def _show_panel(self):
        panel_w = self.panel.width()
        panel_h = self.panel.height()
        geo = self.tray.geometry()
        x = geo.center().x() - panel_w // 2
        y = geo.top() - panel_h - 8
        screen = self.app.primaryScreen().availableGeometry()
        x = max(screen.left() + 4, min(x, screen.right() - panel_w - 4))
        y = max(screen.top() + 4, y)
        self.panel.move(x, y)
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_panel()

    def _do_refresh(self):
        from api_client import fetch_api_balance, fetch_platform_balance, fetch_usage_detail

        self.panel.update_status("刷新中...")
        try:
            if self.api_key:
                data = fetch_api_balance(self.api_key)
                if self.authorization and data.is_available:
                    platform_data = fetch_platform_balance(self.authorization, self.cookie)
                    if platform_data.is_available:
                        data.monthly_cost = platform_data.monthly_cost
                        data.normal_token_est = platform_data.normal_token_est
                        detail = fetch_usage_detail(self.authorization, self.cookie)
                        data.input_tokens = detail.get("input", 0)
                        data.cache_hit_tokens = detail.get("cache_hit", 0)
                        data.cache_miss_tokens = detail.get("cache_miss", 0)
                        data.output_tokens = detail.get("output", 0)
                        data.usage_available = True
            else:
                data = fetch_platform_balance(self.authorization, self.cookie)
                if data.is_available:
                    detail = fetch_usage_detail(self.authorization, self.cookie)
                    data.input_tokens = detail.get("input", 0)
                    data.cache_hit_tokens = detail.get("cache_hit", 0)
                    data.cache_miss_tokens = detail.get("cache_miss", 0)
                    data.output_tokens = detail.get("output", 0)
                    data.usage_available = True

            self.panel.update_data(data)
            if data.is_available:
                self._token_expired_notified = False
                self.panel.update_status("已刷新")
                self.tray.setIcon(self._make_icon(C_GREEN))
                self.tray.setToolTip(f"DeepSeek 用量监控\n余额: ¥{data.normal_balance:.2f}")
            else:
                self.tray.setIcon(self._make_icon(C_RED))
                if ("过期" in (data.error or "") or "无效" in (data.error or "")) and not self._token_expired_notified:
                    self._token_expired_notified = True
                    QMessageBox.warning(
                        None,
                        "凭据不可用",
                        "DeepSeek 凭据不可用，请检查 config.json 中的 api_key 或 authorization。",
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

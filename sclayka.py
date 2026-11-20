"""Склей-ка — склейка паспортов по верхней половине. Койне-софт."""
import ctypes
import math
import os
import sys
import tempfile
from itertools import count

from PySide6.QtCore import QLocale, QPoint, QPointF, QRectF, QSettings, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import (
    QColor, QCursor, QFont, QIcon, QKeySequence, QPainter, QPainterPath, QPen,
    QPixmap, QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractButton, QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox,
    QFileDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QHeaderView,
    QLabel, QMainWindow, QMessageBox, QPushButton, QRadioButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

import sclayka_core as core

IS_WIN = sys.platform == "win32"
LANGUAGES = {"en": "English", "ru": "Русский"}
LANGUAGE_KEY = "language"
language = "ru"


def text(ru: str, en: str) -> str:
    return en if language == "en" else ru


def app_name() -> str:
    return text("Склей-ка", "Sclayka")


def startup_language(settings: QSettings) -> str:
    saved = settings.value(LANGUAGE_KEY, "", str)
    if saved in LANGUAGES:
        return saved

    default = "ru" if QLocale.system().language() == QLocale.Language.Russian else "en"
    dialog = QMessageBox()
    dialog.setWindowTitle("Sclayka / Склей-ка")
    dialog.setText("Choose a language / Выберите язык")
    buttons = {}
    for code, label in LANGUAGES.items():
        buttons[code] = dialog.addButton(label, QMessageBox.ButtonRole.AcceptRole)
    dialog.setDefaultButton(buttons[default])
    dialog.setEscapeButton(dialog.addButton("Cancel / Отмена", QMessageBox.ButtonRole.RejectRole))
    dialog.exec()
    choice = next((code for code, button in buttons.items() if button == dialog.clickedButton()), None)
    if choice is not None:
        settings.setValue(LANGUAGE_KEY, choice)
    return choice or default

THEMES = {
    "light": dict(
        bg="#F3F1EA", card="#FDFCF8", border="#DEDBD0", border_strong="#C9C5B6",
        text="#1F1E1A", muted="#6E6B62", primary="#5E5A24", primary_hover="#4D4A1C",
        on_primary="#FFFFFF", secondary="#E9E4B9", secondary_hover="#E0DAA6",
        on_secondary="#3B3810", danger="#C62828", success="#2E6B2E",
        disabled="#E4E2DA", disabled_text="#A5A29A", track="#E8E5DB",
        selection="#EFEBCF", input="#FFFFFF", petal_empty="#E6E3D8",
    ),
    "dark": dict(
        bg="#1C1B17", card="#25241F", border="#393730", border_strong="#4C4A40",
        text="#ECE9DF", muted="#A19D90", primary="#B8B062", primary_hover="#C9C173",
        on_primary="#1C1B17", secondary="#3D3B22", secondary_hover="#4A4729",
        on_secondary="#EDE6B5", danger="#EF6B6B", success="#7FBF7F",
        disabled="#302F29", disabled_text="#6B685E", track="#34322B",
        selection="#3A3822", input="#1F1E1A", petal_empty="#3A382F",
    ),
}

QSS = """
QWidget {{ font-family: "Segoe UI"; font-size: 10pt; color: {text}; }}
QMainWindow, QWidget#root {{ background: {bg}; }}
QFrame#card {{ background: {card}; border: 1px solid {border}; border-radius: 14px; }}
QFrame#popupCard {{ background: {card}; border: 1px solid {border}; border-radius: 12px; }}
QFrame#sep {{ background: {border}; max-height: 1px; min-height: 1px; border: none; }}
QLabel {{ background: transparent; }}
QLabel#brand {{ font-size: 11pt; font-weight: 700; }}
QLabel#muted, QLabel#hint {{ color: {muted}; }}
QLabel#hint {{ font-size: 9pt; }}
QLabel#cardTitle {{ font-size: 11pt; font-weight: 600; }}
QLabel#overlayTitle {{ font-size: 15pt; font-weight: 600; }}
QLabel#statusText {{ color: {muted}; }}

QPushButton {{
    background: {card}; border: 1px solid {border}; border-radius: 8px;
    padding: 7px 14px;
}}
QPushButton:hover {{ border-color: {border_strong}; background: {bg}; }}
QPushButton:disabled {{ color: {disabled_text}; }}
QPushButton#primary {{
    background: {primary}; color: {on_primary}; border: none; border-radius: 12px;
    padding: 11px 26px; font-weight: 600;
}}
QPushButton#primary:hover {{ background: {primary_hover}; }}
QPushButton#primary:disabled {{ background: {disabled}; color: {disabled_text}; }}
QPushButton#secondary {{
    background: {secondary}; color: {on_secondary}; border: none; border-radius: 12px;
    padding: 11px 20px;
}}
QPushButton#secondary:hover {{ background: {secondary_hover}; }}
QPushButton#dashed {{ border: 1px dashed {border_strong}; background: transparent; }}
QPushButton#dashed:hover {{ border-color: {primary}; }}
QPushButton#flat {{ background: transparent; border: none; padding: 7px 10px; }}
QPushButton#flat:hover {{ background: {track}; }}
QPushButton#danger {{ background: transparent; border: none; color: {danger}; padding: 7px 10px; }}
QPushButton#danger:hover {{ text-decoration: underline; }}
QPushButton#danger:disabled {{ color: {disabled_text}; }}
QPushButton#chip {{
    background: transparent; border: 1px solid {border}; border-radius: 15px;
    padding: 5px 12px 5px 10px; color: {muted};
}}
QPushButton#chip:hover, QPushButton#chip:checked {{ background: {track}; color: {text}; }}

QWidget#titleBar {{ background: {bg}; }}
QPushButton#winBtn, QPushButton#winClose {{
    font-family: "Segoe Fluent Icons", "Segoe MDL2 Assets"; font-size: 7pt;
    background: transparent; border: none; border-radius: 0; padding: 0;
    min-width: 46px; max-width: 46px; min-height: 40px; max-height: 40px;
}}
QPushButton#winBtn:hover {{ background: {track}; }}
QPushButton#winClose:hover {{ background: #C42B1C; color: #FFFFFF; }}

QTreeWidget {{
    background: {card}; border: 1px solid {border}; border-radius: 10px;
    outline: none; padding: 0 4px;
}}
QTreeWidget::item {{ padding: 6px 4px; border: none; }}
QTreeWidget::item:selected {{ background: {selection}; color: {text}; }}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{
    background: {card}; border: none; border-bottom: 1px solid {border};
    padding: 9px 6px; font-weight: 600;
}}

QCheckBox, QRadioButton {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid {border_strong}; background: {input};
}}
QCheckBox::indicator:checked {{ background: {primary}; border-color: {primary}; image: url({check_icon}); }}
QRadioButton::indicator {{
    width: 16px; height: 16px; border-radius: 9px;
    border: 1px solid {border_strong}; background: {input};
}}
QRadioButton::indicator:checked {{ border: 5px solid {primary}; background: {on_primary}; width: 8px; height: 8px; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: {border_strong}; border-radius: 3px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QToolTip {{ background: {card}; color: {text}; border: 1px solid {border}; padding: 4px; }}
"""

# Значки из системного шрифта Windows (Segoe Fluent Icons / MDL2 Assets)
ICON_FONTS = ["Segoe Fluent Icons", "Segoe MDL2 Assets"]
G_MIN, G_MAX, G_RESTORE, G_CLOSE = "", "", "", ""
G_GEAR, G_FOLDER, G_DOWNLOAD, G_DOCS = "", "", "", ""

# Колонки списка файлов
COL_NAME, COL_PAGES, COL_SIZE, COL_RESULT = range(4)
ROLE_ID = Qt.UserRole
ROLE_PATH = Qt.UserRole + 1
ROLE_OUT = Qt.UserRole + 2
ROLE_STATE = Qt.UserRole + 3  # pending / running / done / error


def fmt_size(n: int) -> str:
    if n < 1024 * 1024:
        return f"{max(n / 1024, 1):.0f} {text('КБ', 'KB')}"
    value = f"{n / 1024 / 1024:.1f}"
    return text(f"{value.replace('.', ',')} МБ", f"{value} MB")


def plural(n: int, ru: tuple[str, str, str], en: tuple[str, str]) -> str:
    if language == "en":
        return f"{n} {en[0] if n == 1 else en[1]}"
    one, few, many = ru
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {one}"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return f"{n} {few}"
    return f"{n} {many}"


FILE_WORDS = (("файл", "файла", "файлов"), ("file", "files"))
PAGE_WORDS = (("страница", "страницы", "страниц"), ("page", "pages"))
SHEET_WORDS = (("лист", "листа", "листов"), ("sheet", "sheets"))
QUALITY_TEXT = (
    ("Print", "300 dpi · best for printing"),
    ("Standard", "200 dpi · smaller PDF"),
    ("Compact", "150 dpi · smallest PDF"),
)


def error_text(error: Exception) -> str:
    message = str(error) or error.__class__.__name__
    translations = {
        "Файл защищён паролем": "This file is password protected",
        "В файле нет страниц": "This file has no pages",
    }
    return text(message, translations.get(message, message))


def short_path(path: str) -> str:
    parts = os.path.normpath(path).split(os.sep)
    return os.sep.join(parts[-2:]) if len(parts) > 2 else path


def icon_font(px: int) -> QFont:
    f = QFont()
    f.setFamilies(ICON_FONTS)
    f.setPixelSize(px)
    return f


def glyph_icon(glyph: str, color: str, px: int = 16) -> QIcon:
    pix = QPixmap(px * 2, px * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.TextAntialiasing)
    p.setFont(icon_font(px - 2))
    p.setPen(QColor(color))
    p.drawText(QRectF(0, 0, px, px), Qt.AlignCenter, glyph)
    p.end()
    return QIcon(pix)


def write_check_icon(color: str) -> str:
    """QSS не умеет рисовать галочку сам — кладём маленький SVG во временную папку."""
    folder = os.path.join(tempfile.gettempdir(), "sclayka")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"check_{color.lstrip('#')}.svg")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
                    f'<path d="M3.5 8.5l3 3 6-7" fill="none" stroke="{color}" '
                    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    return path.replace(os.sep, "/")


# ---------------------------------------------------------------- Win32

if IS_WIN:
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _dwm = ctypes.windll.dwmapi
    WM_NCCALCSIZE, WM_NCHITTEST = 0x0083, 0x0084
    HTCAPTION = 2
    HT_EDGES = {  # (лево, право, верх, низ) -> код
        (1, 0, 0, 0): 10, (0, 1, 0, 0): 11, (0, 0, 1, 0): 12, (1, 0, 1, 0): 13,
        (0, 1, 1, 0): 14, (0, 0, 0, 1): 15, (1, 0, 0, 1): 16, (0, 1, 0, 1): 17,
    }


def dwm_set(hwnd: int, attr: int, value: int) -> None:
    try:
        v = ctypes.c_int(value)
        _dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))
    except Exception:
        pass


def colorref(hex_color: str) -> int:
    c = QColor(hex_color)
    return c.red() | (c.green() << 8) | (c.blue() << 16)


# ---------------------------------------------------------------- виджеты

# Цвета лепестков по часовой стрелке от 12 часов
PETALS = ("#F2C14E", "#F08A4B", "#E5625E", "#D65A8C", "#9B6FC4", "#5B8FD6", "#4FAE9B", "#8BBE4B")


def mix(a: QColor, b: QColor, t: float) -> QColor:
    return QColor(round(a.red() + (b.red() - a.red()) * t),
                  round(a.green() + (b.green() - a.green()) * t),
                  round(a.blue() + (b.blue() - a.blue()) * t))


def petal_path(s: float) -> QPainterPath:
    """Лепесток-капля, смотрит вверх: узкий у серединки, круглый на конце."""
    a, b, hw = s * 0.13, s * 0.49, s * 0.132  # начало, кончик, полуширина
    L = b - a
    path = QPainterPath(QPointF(0, -a))
    path.cubicTo(hw * 0.55, -a, hw, -a - L * 0.38, hw, -a - L * 0.62)
    path.cubicTo(hw, -a - L * 0.9, hw * 0.55, -b, 0, -b)
    path.cubicTo(-hw * 0.55, -b, -hw, -a - L * 0.9, -hw, -a - L * 0.62)
    path.cubicTo(-hw, -a - L * 0.38, -hw * 0.55, -a, 0, -a)
    return path


class Flower(QWidget):
    """Индикатор-цветок: заполняется по часовой стрелке, лепесток за лепестком."""

    def __init__(self, size: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.empty = QColor(THEMES["light"]["petal_empty"])
        self._path = petal_path(size)
        self._target = self._shown = 0.0
        self._active = False
        self._phase = 0.0
        self._timer = QTimer(self, interval=16, timeout=self._tick)

    def set_progress(self, value: float, animate: bool = True):
        self._target = max(0.0, min(1.0, value))
        if not animate:
            self._shown = self._target
        self._kick()

    def set_active(self, on: bool):
        """Пока активен, текущий лепесток мягко пульсирует — видно, что работа идёт."""
        self._active = on
        self._kick()

    def _kick(self):
        if not self._timer.isActive():
            self._timer.start()
        self.update()

    def _tick(self):
        self._phase += 0.09
        d = self._target - self._shown
        self._shown = self._shown + d * 0.15 if abs(d) > 0.001 else self._target
        if not self._active and self._shown == self._target:
            self._timer.stop()
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = min(self.width(), self.height())
        p.translate(self.width() / 2, self.height() / 2)
        n = len(PETALS)
        step = 360 / n
        current = int(self._shown * n)

        for i in range(n):
            color = self.empty
            if self._active and i == current and self._shown < 1:
                pulse = 0.15 + 0.3 * (1 + math.sin(self._phase)) / 2
                color = mix(self.empty, QColor(PETALS[i]), pulse)
            p.save()
            p.rotate(i * step)
            p.fillPath(self._path, color)
            p.restore()

        if self._shown <= 0:
            return
        # Сектор от 12 часов по часовой стрелке (с левого края верхнего лепестка)
        pie = QPainterPath(QPointF(0, 0))
        pie.arcTo(QRectF(-s, -s, 2 * s, 2 * s), 90 + step / 2, -360 * self._shown)
        pie.closeSubpath()
        p.setClipPath(pie)
        for i, color in enumerate(PETALS[:current + 1]):  # только те, до которых дошла очередь
            p.save()
            p.rotate(i * step)
            p.fillPath(self._path, QColor(color))
            p.restore()


def flower_pixmap(size: int) -> QPixmap:
    f = Flower(size)
    f.set_progress(1, animate=False)
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    f.render(pix, QPoint(), renderFlags=QWidget.RenderFlag.DrawChildren)
    return pix


class ThemeSwitch(QAbstractButton):
    """Переключатель светлой/тёмной темы, как в Квит-ках."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(40, 22)
        self.setToolTip(text("Тёмная тема", "Dark theme"))
        self.colors = THEMES["light"]

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = self.colors
        p.setPen(QPen(QColor(c["border_strong"]), 1))
        p.setBrush(QColor(c["track"]))
        p.drawRoundedRect(QRectF(0.5, 0.5, 39, 21), 10.5, 10.5)
        x = 21 if self.isChecked() else 3
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(c["primary"] if self.isChecked() else c["muted"]))
        p.drawEllipse(QRectF(x, 3, 16, 16))
        p.setBrush(QColor(c["card"]))
        if self.isChecked():  # луна
            p.drawEllipse(QRectF(x + 4, 7, 8, 8))
            p.setBrush(QColor(c["primary"]))
            p.drawEllipse(QRectF(x + 7, 5.5, 7, 7))
        else:  # солнце
            p.drawEllipse(QRectF(x + 5, 8, 6, 6))


class SettingsPopup(QWidget):
    """Меню под шестерёнкой: качество и Ч/Б."""
    changed = Signal()
    language_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 8, 16, 20)  # место под тень
        box = QFrame(objectName="popupCard")
        box.setGraphicsEffect(QGraphicsDropShadowEffect(
            blurRadius=28, offset=QPointF(0, 6), color=QColor(0, 0, 0, 55)))
        outer.addWidget(box)

        lay = QVBoxLayout(box)
        lay.setContentsMargins(18, 14, 18, 16)
        lay.setSpacing(10)
        lay.addWidget(QLabel(text("Качество", "Quality"), objectName="cardTitle"))
        self.quality = QButtonGroup(self)
        for i, q in enumerate(core.QUALITIES):
            name, description = QUALITY_TEXT[i]
            row = QHBoxLayout()
            rb = QRadioButton(text(q.name, name))
            rb.setMinimumWidth(110)
            self.quality.addButton(rb, i)
            row.addWidget(rb)
            row.addWidget(QLabel(text(q.hint, description), objectName="hint"))
            row.addStretch()
            lay.addLayout(row)
        self.quality.idClicked.connect(lambda _: self.changed.emit())

        lay.addSpacing(2)
        lay.addWidget(QFrame(objectName="sep"))
        lay.addSpacing(2)
        self.gray = QCheckBox(text("Чёрно-белые", "Grayscale"))
        self.gray.toggled.connect(lambda _: self.changed.emit())
        lay.addWidget(self.gray)
        hint = QLabel(text("Файл меньше, печать без цветных разводов", "Reduces file size and prints in grayscale"), objectName="hint")
        hint.setContentsMargins(26, 0, 0, 0)
        lay.addWidget(hint)

        lay.addWidget(QFrame(objectName="sep"))
        language_row = QHBoxLayout()
        label = QLabel(text("Язык", "Language"))
        self.language_choice = QComboBox()
        label.setBuddy(self.language_choice)
        for code, name in LANGUAGES.items():
            self.language_choice.addItem(name, code)
        self.language_choice.currentIndexChanged.connect(
            lambda _: self.language_changed.emit(self.language_choice.currentData()))
        language_row.addWidget(label)
        language_row.addWidget(self.language_choice, 1)
        lay.addLayout(language_row)
        lay.addWidget(QLabel(text("Язык изменится при следующем запуске",
                                  "Language changes the next time you open Sclayka"), objectName="hint"))

    def popup_under(self, anchor: QWidget):
        self.adjustSize()
        m = self.layout().contentsMargins()
        pt = anchor.mapToGlobal(QPoint(anchor.width(), anchor.height()))
        self.move(pt.x() - self.width() + m.right(), pt.y() + 6 - m.top())
        self.show()


class FileList(QTreeWidget):
    remove_requested = Signal(list)  # правый щелчок по строке — убрать

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            item = self.itemAt(e.position().toPoint())
            if item:
                # щёлкнули по одному из выделенных — убираем всё выделение
                selected = self.selectedItems()
                self.remove_requested.emit(selected if item in selected else [item])
            return
        super().mousePressEvent(e)

    def contextMenuEvent(self, e):
        e.accept()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels([text("Файл", "File"), text("Страниц", "Pages"),
                              text("Размер", "Size"), text("Результат", "Result")])
        self.setRootIsDecorated(False)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setUniformRowHeights(True)
        h = self.header()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        for col, w in ((COL_PAGES, 80), (COL_SIZE, 90), (COL_RESULT, 230)):
            h.setSectionResizeMode(col, QHeaderView.Fixed)
            self.setColumnWidth(col, w)
        h.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.colors = THEMES["light"]

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.topLevelItemCount():
            return
        # Пустой список — рисуем зону «бросьте файлы сюда»
        c = self.colors
        p = QPainter(self.viewport())
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.viewport().rect()).adjusted(14, 14, -14, -14)
        p.setPen(QPen(QColor(c["border_strong"]), 1.5, Qt.DashLine))
        p.setBrush(QColor(c["bg"]))
        p.drawRoundedRect(r, 12, 12)
        cy = r.center().y()
        p.setFont(icon_font(34))
        p.setPen(QColor(c["muted"]))
        p.drawText(QRectF(r.left(), cy - 62, r.width(), 44), Qt.AlignCenter, G_DOCS)
        f = QFont("Segoe UI")
        f.setPointSizeF(11.5)
        f.setWeight(QFont.DemiBold)
        p.setFont(f)
        p.setPen(QColor(c["text"]))
        p.drawText(QRectF(r.left(), cy - 8, r.width(), 26), Qt.AlignCenter,
                   text("Перетащите сюда PDF или сканы паспортов", "Drop PDFs or ID scans here"))
        f.setPointSizeF(9.5)
        f.setWeight(QFont.Normal)
        p.setFont(f)
        p.setPen(QColor(c["muted"]))
        p.drawText(QRectF(r.left(), cy + 20, r.width(), 22), Qt.AlignCenter,
                   text("или нажмите «Добавить файлы» · Ctrl+O", "or click Add files · Ctrl+O"))


class DropOverlay(QWidget):
    """Подсветка поверх окна, пока над ним тащат файлы."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.colors = THEMES["light"]
        self.busy = False
        self.hide()

    def paintEvent(self, _):
        c = self.colors
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QColor(c["bg"])
        bg.setAlpha(250)
        p.fillRect(self.rect(), bg)
        r = QRectF(self.rect()).adjusted(16, 8, -16, -16)
        accent = QColor(c["muted"] if self.busy else c["primary"])
        p.setPen(QPen(accent, 2, Qt.DashLine))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r, 16, 16)
        cy = r.center().y()
        p.setFont(icon_font(46))
        p.setPen(accent)
        p.drawText(QRectF(r.left(), cy - 80, r.width(), 60), Qt.AlignCenter, G_DOWNLOAD)
        f = QFont("Segoe UI")
        f.setPointSizeF(15)
        f.setWeight(QFont.DemiBold)
        p.setFont(f)
        p.setPen(QColor(c["text"]))
        message = (text("Подождите окончания склейки", "Wait for the batch to finish") if self.busy
                   else text("Отпустите, чтобы добавить", "Release to add files"))
        p.drawText(QRectF(r.left(), cy - 10, r.width(), 34), Qt.AlignCenter, message)
        f.setPointSizeF(10)
        f.setWeight(QFont.Normal)
        p.setFont(f)
        p.setPen(QColor(c["muted"]))
        p.drawText(QRectF(r.left(), cy + 28, r.width(), 24), Qt.AlignCenter,
                   text("PDF, JPG, PNG, TIFF или папку целиком", "PDF, JPG, PNG, TIFF, or a folder"))


class ProgressOverlay(QWidget):
    """Затемнение окна с цветком по центру: сначала ход склейки, потом итог."""
    cancel_clicked = Signal()
    closed = Signal()
    AUTO_CLOSE = 5  # сколько секунд показывать итог

    def __init__(self, parent):
        super().__init__(parent)
        self.dark = False
        self._finished = False
        self._left = 0
        self._timer = QTimer(self, interval=1000, timeout=self._count)

        lay = QVBoxLayout(self)
        self.card = QFrame(objectName="popupCard")
        self.card.setFixedWidth(400)
        self.card.installEventFilter(self)  # пока мышь на карточке — отсчёт на паузе
        lay.addWidget(self.card, 0, Qt.AlignCenter)

        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(28, 30, 28, 20)
        cl.setSpacing(6)
        self.flower = Flower(150)
        cl.addWidget(self.flower, 0, Qt.AlignHCenter)
        cl.addSpacing(16)
        self.title = QLabel(objectName="overlayTitle", alignment=Qt.AlignCenter)
        cl.addWidget(self.title)
        self.detail = QLabel(objectName="muted", alignment=Qt.AlignCenter, wordWrap=True)
        cl.addWidget(self.detail)
        cl.addSpacing(16)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btns.addStretch()
        self.cancel_btn = QPushButton(text("Отменить", "Cancel"))
        self.cancel_btn.clicked.connect(self.cancel_clicked)
        self.open_btn = QPushButton(text("Открыть папку", "Open folder"), objectName="secondary")
        self.ok_btn = QPushButton(text("Готово", "Done"), objectName="primary")
        self.ok_btn.clicked.connect(self.dismiss)
        for b in (self.cancel_btn, self.open_btn, self.ok_btn):
            btns.addWidget(b)
        btns.addStretch()
        cl.addLayout(btns)
        self.countdown = QLabel(objectName="hint", alignment=Qt.AlignCenter)
        self.countdown.setMinimumHeight(22)
        cl.addWidget(self.countdown)
        self.hide()

    def start(self):
        self._finished = False
        self._timer.stop()
        self.flower.set_progress(0, animate=False)
        self.flower.set_active(True)
        self.title.setText(text("Склеиваю…", "Merging…"))
        self.detail.setText(text("Подготовка", "Preparing"))
        self.countdown.setText("")
        self.cancel_btn.show()
        self.cancel_btn.setEnabled(True)
        self.open_btn.hide()
        self.ok_btn.hide()
        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()

    def progress(self, value: float, text: str):
        self.flower.set_progress(value)
        self.detail.setText(text)

    def stopping(self):
        self.cancel_btn.setEnabled(False)
        self.detail.setText(text("Останавливаю…", "Stopping…"))

    def finish(self, title: str, detail: str, success: bool, can_open: bool):
        self._finished = True
        self.flower.set_active(False)
        if success:
            self.flower.set_progress(1)
        self.title.setText(title)
        self.detail.setText(detail)
        self.cancel_btn.hide()
        self.open_btn.setVisible(can_open)
        self.ok_btn.show()
        self.ok_btn.setFocus()
        if success:  # с ошибками не закрываем сами — пусть их увидят
            self._left = self.AUTO_CLOSE
            self._show_countdown()
            if not self.card.underMouse():
                self._timer.start()

    def _show_countdown(self):
        self.countdown.setText(text(f"Список очистится через {self._left} с",
                                    f"List clears in {self._left} s"))

    def _count(self):
        self._left -= 1
        if self._left <= 0:
            self.dismiss()
        else:
            self._show_countdown()

    def eventFilter(self, obj, e):
        if obj is self.card and self._finished and self._left > 0:
            if e.type() == e.Type.Enter:
                self._timer.stop()
            elif e.type() == e.Type.Leave:
                self._timer.start()
        return False

    def dismiss(self):
        if not self._finished or not self.isVisible():
            return
        self._timer.stop()
        self.hide()
        self.closed.emit()

    def mousePressEvent(self, e):
        # щелчок по затемнению вокруг карточки закрывает итог
        if not self.card.geometry().contains(e.position().toPoint()):
            self.dismiss()
        e.accept()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.dismiss()
        e.accept()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 140) if self.dark else QColor(40, 36, 20, 95))


class Worker(QThread):
    page_done = Signal(int, int, int)      # id, done, total
    file_done = Signal(int, str, int)      # id, путь результата, размер
    file_failed = Signal(int, str)         # id, текст ошибки

    def __init__(self, jobs, folder, opts):
        super().__init__()
        self.jobs, self.folder, self.opts = jobs, folder, opts
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        for item_id, src in self.jobs:
            if self._cancel:
                return
            try:
                dst = core.output_path(src, self.folder)
                size = core.merge_file(
                    src, dst, self.opts,
                    progress=lambda d, t, i=item_id: self.page_done.emit(i, d, t),
                    cancelled=lambda: self._cancel,
                )
                self.file_done.emit(item_id, dst, size)
            except core.Cancelled:
                return
            except Exception as e:  # noqa: BLE001 — показываем любую ошибку в строке файла
                    self.file_failed.emit(item_id, error_text(e))


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(objectName="card")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(22, 16, 22, 18)
    lay.setSpacing(12)
    return frame, lay


# ---------------------------------------------------------------- окно

class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings | None = None):
        super().__init__()
        self.settings = settings if settings is not None else QSettings("Koine-soft", "Sclay-ka")
        publisher = text("Койне-софт", "Koine-soft")
        self.setWindowTitle(f"{app_name()} — {publisher}")
        self.setWindowIcon(QIcon(flower_pixmap(64)))
        self.resize(980, 640)
        self.setMinimumSize(720, 460)
        self.setAcceptDrops(True)
        self.frameless = IS_WIN
        if self.frameless:
            self.setWindowFlag(Qt.FramelessWindowHint)
        self._styled = False
        self.worker: Worker | None = None
        self.ids = count()
        self.items: dict[int, QTreeWidgetItem] = {}
        self.pages_total = 0
        self.pages_base = 0
        self.colors = THEMES["light"]

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        self.save_folder = self.settings.value(
            "save_folder", desktop if os.path.isdir(desktop) else os.path.expanduser("~"))
        if not os.path.isdir(self.save_folder):
            self.save_folder = os.path.expanduser("~")

        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- шапка = заголовок окна
        self.title_bar = QWidget(objectName="titleBar")
        self.title_bar.setFixedHeight(48)
        head = QHBoxLayout(self.title_bar)
        head.setContentsMargins(16, 0, 0, 0)
        head.setSpacing(0)
        logo = QLabel()
        logo.setPixmap(flower_pixmap(22))
        head.addWidget(logo)
        head.addSpacing(8)
        head.addWidget(QLabel(app_name(), objectName="brand"))
        head.addSpacing(10)
        head.addWidget(QLabel(publisher, objectName="muted"))
        head.addStretch()
        self.theme_switch = ThemeSwitch()
        self.theme_switch.toggled.connect(self.apply_theme)
        head.addWidget(self.theme_switch)
        head.addSpacing(12)
        self.settings_btn = QPushButton(objectName="chip")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setToolTip(text("Настройки", "Settings"))
        self.settings_btn.clicked.connect(self.show_settings)
        head.addWidget(self.settings_btn)
        head.addSpacing(10 if self.frameless else 16)
        self.win_buttons = []
        if self.frameless:
            for glyph, name, slot in ((G_MIN, "winBtn", self.showMinimized),
                                      (G_MAX, "winBtn", self.toggle_maximized),
                                      (G_CLOSE, "winClose", self.close)):
                b = QPushButton(glyph, objectName=name)
                b.setFocusPolicy(Qt.NoFocus)
                b.clicked.connect(slot)
                head.addWidget(b, 0, Qt.AlignTop)
                self.win_buttons.append(b)
            self.max_btn = self.win_buttons[1]
        outer.addWidget(self.title_bar)

        self.popup = SettingsPopup(self)
        self.popup.quality.button(
            min(int(self.settings.value("quality", 0)), len(core.QUALITIES) - 1)).setChecked(True)
        self.popup.gray.setChecked(self.settings.value("gray", False, bool))
        self.popup.changed.connect(self.on_settings_changed)
        preferred = self.settings.value(LANGUAGE_KEY, language, str)
        choice = self.popup.language_choice
        choice.setCurrentIndex(choice.findData(preferred if preferred in LANGUAGES else language))
        self.popup.language_changed.connect(
            lambda code: self.settings.setValue(LANGUAGE_KEY, code))

        # ---- содержимое
        self.content = QWidget()
        body = QVBoxLayout(self.content)
        body.setContentsMargins(16, 2, 16, 14)
        body.setSpacing(12)
        outer.addWidget(self.content, 1)

        files_card, fl = card()
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel(text("Файлы", "Files"), objectName="cardTitle"))
        title_row.addStretch()
        self.summary = QLabel("", objectName="muted")
        title_row.addWidget(self.summary)
        fl.addLayout(title_row)

        self.list = FileList()
        self.list.itemDoubleClicked.connect(self.open_item)
        self.list.remove_requested.connect(self.remove_items)
        fl.addWidget(self.list, 1)

        row = QHBoxLayout()
        self.add_btn = QPushButton(text("+  Добавить файлы", "+  Add files"), objectName="dashed")
        self.add_btn.clicked.connect(self.pick_files)
        row.addWidget(self.add_btn)
        row.addSpacing(8)
        row.addWidget(QLabel(text("Или перетащите файлы в окно · правый щелчок по файлу — убрать из списка",
                                  "Drag files here · Right-click a file to remove it"), objectName="hint"))
        row.addStretch()
        fl.addLayout(row)
        body.addWidget(files_card, 1)

        # ---- нижняя панель
        bottom = QHBoxLayout()
        bottom.setContentsMargins(6, 0, 0, 0)
        bottom.setSpacing(6)
        self.clear_btn = QPushButton(text("Очистить", "Clear"), objectName="flat")
        self.clear_btn.clicked.connect(self.clear_all)
        bottom.addWidget(self.clear_btn)
        self.folder_btn = QPushButton(objectName="flat")
        self.folder_btn.setToolTip(text("Куда сохранять склеенные файлы", "Choose where to save merged files"))
        self.folder_btn.clicked.connect(self.pick_folder)
        bottom.addWidget(self.folder_btn)
        self.open_folder_btn = QPushButton(text("Открыть", "Open"), objectName="flat")
        self.open_folder_btn.setToolTip(text("Открыть папку с результатами", "Open the output folder"))
        self.open_folder_btn.clicked.connect(self.open_save_folder)
        bottom.addWidget(self.open_folder_btn)
        bottom.addStretch()
        self.status = QLabel("", objectName="statusText")
        bottom.addWidget(self.status)
        bottom.addSpacing(12)
        self.run_btn = QPushButton(objectName="primary")
        self.run_btn.clicked.connect(self.run_or_cancel)
        bottom.addWidget(self.run_btn)
        body.addLayout(bottom)

        self.progress_overlay = ProgressOverlay(self.content)
        self.progress_overlay.cancel_clicked.connect(self.run_or_cancel)
        self.progress_overlay.open_btn.clicked.connect(self.open_save_folder)
        self.progress_overlay.closed.connect(self.on_results_closed)
        self.overlay = DropOverlay(self.content)

        for seq in ("Ctrl+Return", "Ctrl+Enter"):
            QShortcut(QKeySequence(seq), self, self.run_or_cancel)
        QShortcut(QKeySequence("Ctrl+O"), self, self.pick_files)
        QShortcut(QKeySequence(Qt.Key_Delete), self.list,
                  lambda: self.remove_items(self.list.selectedItems()))

        self.theme_switch.setChecked(self.settings.value("dark", False, bool))
        self.apply_theme(self.theme_switch.isChecked())
        self.update_folder_label()
        self.update_settings_chip()
        self.update_buttons()

    # ---------- рамка окна (Windows) ----------
    def showEvent(self, e):
        super().showEvent(e)
        if self.frameless and not self._styled:
            self._styled = True
            hwnd = int(self.winId())
            # Возвращаем окну «настоящую» рамку: тень, прилипание к краям,
            # анимации сворачивания. Саму рамку прячем в WM_NCCALCSIZE.
            style = _user32.GetWindowLongW(hwnd, -16)
            _user32.SetWindowLongW(hwnd, -16, style | 0x00C00000 | 0x00040000
                                   | 0x00020000 | 0x00010000 | 0x00080000)
            _user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)
            dwm_set(hwnd, 33, 2)  # скруглённые углы Windows 11
            self.apply_window_colors()

    def apply_window_colors(self):
        if not IS_WIN or not self._styled:
            return
        hwnd = int(self.winId())
        dark = self.theme_switch.isChecked()
        dwm_set(hwnd, 20, int(dark))
        dwm_set(hwnd, 34, colorref(self.colors["border_strong"]))  # цвет рамки Windows 11

    def nativeEvent(self, event_type, message):
        if self.frameless and bytes(event_type) == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_NCCALCSIZE and msg.wParam:
                if _user32.IsZoomed(msg.hWnd):
                    # развёрнутое окно Windows выносит за край экрана на толщину рамки
                    dpi = _user32.GetDpiForWindow(msg.hWnd)
                    f = (_user32.GetSystemMetricsForDpi(32, dpi)
                         + _user32.GetSystemMetricsForDpi(92, dpi))
                    r = wintypes.RECT.from_address(msg.lParam)
                    r.left += f
                    r.top += f
                    r.right -= f
                    r.bottom -= f
                return True, 0
            if msg.message == WM_NCHITTEST:
                hit = self.hit_test()
                if hit:
                    return True, hit
        return super().nativeEvent(event_type, message)

    def hit_test(self) -> int:
        pos = self.mapFromGlobal(QCursor.pos())
        x, y = pos.x(), pos.y()
        if not self.isMaximized():
            b = 6
            key = (int(x < b), int(x >= self.width() - b), int(y < b), int(y >= self.height() - b))
            if key in HT_EDGES:
                return HT_EDGES[key]
        if 0 <= y < self.title_bar.height():
            child = self.childAt(pos)
            if not isinstance(child, QAbstractButton):
                return HTCAPTION
        return 0

    def toggle_maximized(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def changeEvent(self, e):
        super().changeEvent(e)
        if e.type() == e.Type.WindowStateChange and getattr(self, "max_btn", None):
            self.max_btn.setText(G_RESTORE if self.isMaximized() else G_MAX)

    # ---------- перетаскивание в окно ----------
    def _drop_paths(self, e):
        return [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]

    def resizeEvent(self, e):
        super().resizeEvent(e)
        for w in (getattr(self, "overlay", None), getattr(self, "progress_overlay", None)):
            if w and w.isVisible():
                w.setGeometry(self.content.rect())

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() and self._drop_paths(e):
            self.overlay.busy = self.worker is not None
            self.overlay.setGeometry(self.content.rect())
            self.overlay.raise_()
            self.overlay.show()
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        self.overlay.hide()

    def dropEvent(self, e):
        self.overlay.hide()
        if self.worker is None:
            self.add_files(self._drop_paths(e))
            e.acceptProposedAction()
            self.activateWindow()

    # ---------- оформление ----------
    def apply_theme(self, dark: bool):
        colors = THEMES["dark" if dark else "light"]
        self.colors = colors
        QApplication.instance().setStyleSheet(
            QSS.format(**colors, check_icon=write_check_icon(colors["on_primary"])))
        self.theme_switch.colors = colors
        self.list.colors = colors
        self.overlay.colors = colors
        self.progress_overlay.dark = dark
        self.progress_overlay.flower.empty = QColor(colors["petal_empty"])
        for w in (self.theme_switch, self.list.viewport(), self.progress_overlay):
            w.update()
        self.settings_btn.setIcon(glyph_icon(G_GEAR, colors["muted"]))
        self.folder_btn.setIcon(glyph_icon(G_FOLDER, colors["muted"]))
        for item in self.items.values():
            self.paint_state(item)
        self.apply_window_colors()
        self.settings.setValue("dark", dark)

    def show_settings(self):
        self.popup.popup_under(self.settings_btn)

    def on_settings_changed(self):
        self.settings.setValue("quality", self.popup.quality.checkedId())
        self.settings.setValue("gray", self.popup.gray.isChecked())
        self.update_settings_chip()

    def current_options(self) -> core.Options:
        return core.Options(core.QUALITIES[self.popup.quality.checkedId()], self.popup.gray.isChecked())

    def update_settings_chip(self):
        opts = self.current_options()
        index = self.popup.quality.checkedId()
        name = text(opts.quality.name, QUALITY_TEXT[index][0])
        self.settings_btn.setText(f" {name}" + (text(" · Ч/Б", " · Gray") if opts.grayscale else ""))

    def update_folder_label(self):
        folder = short_path(self.save_folder)
        self.folder_btn.setText(text(f" Сохранять в: {folder}", f" Save to: {folder}"))

    def set_status(self, text: str):
        self.status.setText(text)

    def paint_state(self, item: QTreeWidgetItem):
        state = item.data(COL_NAME, ROLE_STATE)
        color = {"done": "success", "error": "danger", "pending": "muted"}.get(state, "text")
        item.setForeground(COL_RESULT, QColor(self.colors[color]))

    def update_summary(self):
        n = len(self.items)
        pages = sum(int(i.text(COL_PAGES) or 0) for i in self.items.values())
        sheets = sum((int(i.text(COL_PAGES) or 0) + 1) // 2 for i in self.items.values())
        self.summary.setText(
            f"{plural(n, *FILE_WORDS)} · {plural(pages, *PAGE_WORDS)}"
            f" → {plural(sheets, *SHEET_WORDS)}" if n else "")

    def update_buttons(self):
        busy = self.worker is not None
        pending = any(i.data(COL_NAME, ROLE_STATE) in ("pending", "error") for i in self.items.values())
        self.run_btn.setEnabled(busy or pending)
        self.run_btn.setText(text("Отменить", "Cancel") if busy else
                             text("Склеить   Ctrl+Enter", "Merge   Ctrl+Enter"))
        self.add_btn.setEnabled(not busy)
        self.clear_btn.setEnabled(not busy and bool(self.items))
        self.folder_btn.setEnabled(not busy)
        self.settings_btn.setEnabled(not busy)

    # ---------- файлы ----------
    def pick_files(self):
        if self.worker:
            return
        start = self.settings.value("open_folder", os.path.expanduser("~"))
        exts = " ".join("*" + e for e in core.SUPPORTED_EXT)
        filters = text(f"PDF и сканы ({exts});;Все файлы (*)",
                       f"PDFs and scans ({exts});;All files (*)")
        files, _ = QFileDialog.getOpenFileNames(self, text("Выберите файлы", "Choose files"),
                                                start, filters)
        if files:
            self.settings.setValue("open_folder", os.path.dirname(files[0]))
            self.add_files(files)

    def add_files(self, paths: list[str]):
        if self.worker:
            return
        # Список после прошлой склейки — начинаем заново, как раньше.
        if self.items and all(i.data(COL_NAME, ROLE_STATE) == "done" for i in self.items.values()):
            self.clear_all()

        expanded = []
        for p in paths:
            if os.path.isdir(p):
                expanded += sorted(os.path.join(p, f) for f in os.listdir(p))
            else:
                expanded.append(p)

        known = {os.path.normcase(i.data(COL_NAME, ROLE_PATH)) for i in self.items.values()}
        skipped = 0
        for p in expanded:
            p = os.path.normpath(p)
            if not core.is_supported(p) or os.path.normcase(p) in known:
                skipped += not core.is_supported(p)
                continue
            known.add(os.path.normcase(p))
            item = QTreeWidgetItem([os.path.basename(p), "", fmt_size(os.path.getsize(p)),
                                    text("Ожидает", "Waiting")])
            item.setToolTip(COL_NAME, p)
            item_id = next(self.ids)
            item.setData(COL_NAME, ROLE_ID, item_id)
            item.setData(COL_NAME, ROLE_PATH, p)
            item.setData(COL_NAME, ROLE_STATE, "pending")
            try:
                item.setText(COL_PAGES, str(core.page_count(p)))
            except Exception as e:  # noqa: BLE001
                item.setData(COL_NAME, ROLE_STATE, "error")
                message = error_text(e)
                item.setText(COL_RESULT, text(f"Не открывается: {message}", f"Cannot open: {message}"))
                item.setToolTip(COL_RESULT, message)
            self.paint_state(item)
            self.list.addTopLevelItem(item)
            self.items[item_id] = item
        self.set_status(text(f"Пропущено неподходящих: {skipped}",
                             f"Unsupported files skipped: {skipped}") if skipped else "")
        self.update_summary()
        self.update_buttons()

    def remove_items(self, items: list[QTreeWidgetItem]):
        if self.worker:
            return
        for item in items:
            self.items.pop(item.data(COL_NAME, ROLE_ID), None)
            self.list.takeTopLevelItem(self.list.indexOfTopLevelItem(item))
        self.update_summary()
        self.update_buttons()

    def clear_all(self):
        if self.worker:
            return
        self.list.clear()
        self.items.clear()
        self.set_status("")
        self.update_summary()
        self.update_buttons()

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, text("Папка для сохранения", "Choose an output folder"), self.save_folder)
        if folder:
            self.save_folder = os.path.normpath(folder)
            self.settings.setValue("save_folder", self.save_folder)
            self.update_folder_label()

    def open_save_folder(self):
        try:
            os.startfile(self.save_folder)
        except OSError as e:
            QMessageBox.warning(self, app_name(), error_text(e))

    def open_item(self, item: QTreeWidgetItem):
        out = item.data(COL_NAME, ROLE_OUT)
        path = out if out and os.path.exists(out) else item.data(COL_NAME, ROLE_PATH)
        try:
            os.startfile(path)
        except OSError as e:
            QMessageBox.warning(self, app_name(), error_text(e))

    # ---------- обработка ----------
    def run_or_cancel(self):
        if self.worker:
            self.worker.cancel()
            self.progress_overlay.stopping()
            return
        if self.progress_overlay.isVisible():  # Ctrl+Enter на итогах — просто закрыть
            self.progress_overlay.dismiss()
            return
        jobs = [(i.data(COL_NAME, ROLE_ID), i.data(COL_NAME, ROLE_PATH))
                for i in self.items.values()
                if i.data(COL_NAME, ROLE_STATE) in ("pending", "error") and i.text(COL_PAGES)]
        if not jobs:
            return
        if not os.path.isdir(self.save_folder):
            QMessageBox.warning(self, app_name(), text(
                "Папка для сохранения не найдена. Выберите другую.",
                "The output folder could not be found. Choose another folder."))
            self.pick_folder()
            return

        for item_id, _ in jobs:
            item = self.items[item_id]
            item.setData(COL_NAME, ROLE_STATE, "pending")
            item.setText(COL_RESULT, text("В очереди", "Queued"))
            item.setToolTip(COL_RESULT, "")
            self.paint_state(item)
        self.pages_total = max(sum(int(self.items[i].text(COL_PAGES)) for i, _ in jobs), 1)
        self.pages_base = 0
        self.run_stats = {"done": 0, "errors": 0, "src": 0, "out": 0}
        self.set_status("")
        self.progress_overlay.start()

        self.worker = Worker(jobs, self.save_folder, self.current_options())
        self.worker.page_done.connect(self.on_page)
        self.worker.file_done.connect(self.on_file_done)
        self.worker.file_failed.connect(self.on_file_failed)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        self.update_buttons()

    def on_page(self, item_id, done, total):
        item = self.items.get(item_id)
        if item:
            item.setData(COL_NAME, ROLE_STATE, "running")
            item.setText(COL_RESULT, text(f"Страница {done} из {total}…",
                                         f"Page {done} of {total}…"))
            self.paint_state(item)
        now = self.pages_base + done
        name = item.text(COL_NAME) if item else ""
        if len(name) > 34:
            name = name[:31] + "…"
        self.progress_overlay.progress(
            now / self.pages_total,
            text(f"{now} из {self.pages_total} стр. · {name}",
                 f"{now} of {self.pages_total} pages · {name}"))

    def _file_finished(self, item):
        self.pages_base += int(item.text(COL_PAGES) or 0)
        self.progress_overlay.flower.set_progress(self.pages_base / self.pages_total)

    def on_file_done(self, item_id, out_path, out_size):
        item = self.items[item_id]
        src_size = os.path.getsize(item.data(COL_NAME, ROLE_PATH))
        change = (out_size - src_size) * 100 / src_size if src_size else 0
        self.run_stats["done"] += 1
        self.run_stats["src"] += src_size
        self.run_stats["out"] += out_size
        item.setData(COL_NAME, ROLE_STATE, "done")
        item.setData(COL_NAME, ROLE_OUT, out_path)
        item.setText(COL_RESULT, f"✓ {fmt_size(out_size)}  ({change:+.0f}%)")
        item.setToolTip(COL_RESULT, out_path)
        self.paint_state(item)
        self._file_finished(item)

    def on_file_failed(self, item_id, msg):
        item = self.items[item_id]
        item.setData(COL_NAME, ROLE_STATE, "error")
        item.setText(COL_RESULT, text(f"Ошибка: {msg}", f"Error: {msg}"))
        item.setToolTip(COL_RESULT, msg)
        self.paint_state(item)
        self.run_stats["errors"] += 1
        self._file_finished(item)

    def on_finished(self):
        cancelled = self.worker._cancel
        self.worker.deleteLater()
        self.worker = None
        for item in self.items.values():
            if item.data(COL_NAME, ROLE_STATE) in ("pending", "running"):
                item.setData(COL_NAME, ROLE_STATE, "pending")
                item.setText(COL_RESULT, text("Ожидает", "Waiting"))
                self.paint_state(item)
        self.update_buttons()

        st = self.run_stats
        files = plural(st["done"], *FILE_WORDS)
        if cancelled:
            self.progress_overlay.hide()
            self.on_results_closed()
            self.set_status(text(f"Остановлено · сохранено {files}", f"Stopped · Saved {files}")
                            if st["done"] else text("Остановлено", "Stopped"))
            return
        detail = files
        if st["src"]:
            saved = (st["src"] - st["out"]) * 100 / st["src"]
            detail += f" · {fmt_size(st['src'])} → {fmt_size(st['out'])}"
            if saved > 0:
                detail += f" (−{saved:.0f}%)"
        folder = os.path.basename(self.save_folder) or self.save_folder
        detail += text(f"\nв папке {folder}", f"\nin {folder}")
        if st["errors"]:
            detail += text(f"\nНе получилось: {st['errors']} — причина видна в списке",
                           f"\nFailed: {st['errors']}. See the file list for details.")
            self.progress_overlay.finish(text("Готово, но не всё", "Finished with errors"),
                                         detail, False, st["done"] > 0)
        else:
            self.progress_overlay.finish(text("Готово!", "Done!"), detail, True, True)

    def on_results_closed(self):
        """Итоги посмотрели — убираем из списка всё, что склеилось."""
        done = [i for i in self.items.values() if i.data(COL_NAME, ROLE_STATE) == "done"]
        self.remove_items(done)
        if done:
            files = plural(len(done), *FILE_WORDS)
            self.set_status(text(f"Последняя склейка: {files}", f"Last batch: {files}"))

    def closeEvent(self, e):
        if self.worker:
            self.worker.cancel()
            self.worker.wait(5000)
        super().closeEvent(e)


def main():
    global language
    if IS_WIN:
        try:  # своя иконка в панели задач, а не python.exe
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("KoineSoft.Sclayka")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    settings = QSettings("Koine-soft", "Sclay-ka")
    language = startup_language(settings)
    win = MainWindow(settings)
    win.show()
    # Файлы, перетащенные на ярлык/exe
    args = [a for a in sys.argv[1:] if os.path.exists(a)]
    if args:
        win.add_files(args)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

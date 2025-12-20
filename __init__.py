from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QAction,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSettings,
    QTextEdit,
    QVBoxLayout,
)
from aqt.utils import showInfo


ADDON_KEY = "deck-seed-empty"
QSET_ORG = "anki"
QSET_APP = ADDON_KEY
QSET_KEY_TEXT = "deck_list_text"


def _qsettings() -> QSettings:
    # AnkiのQSettingsと衝突しにくいように独自 app 名にする
    return QSettings(QSET_ORG, QSET_APP)


def _normalize_lines(text: str) -> list[str]:
    """
    1行=1デック名として解釈。
    - 空行/前後空白は除去
    - 先頭が # の行はコメントとして無視
    """
    out: list[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        out.append(s)
    return out


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _ensure_empty_decks(deck_names: list[str]) -> tuple[int, int]:
    """
    deck_names: ["01 Necrosis 1", "01 Necrosis 1::01 Anemic infarction", ...]
    Returns: (created_or_ensured_count, failed_count)
    """
    ok = 0
    ng = 0
    for name in deck_names:
        try:
            # 存在しなければ作成、存在すればそのIDを返す
            mw.col.decks.id(name)
            ok += 1
        except Exception:
            ng += 1
    mw.col.decks.save()
    mw.reset()
    return ok, ng


SAMPLE_TEXT = """# 1行=1デック名（:: で子デック）
01 Necrosis 1
01 Necrosis 1::01 Anemic infarction
01 Necrosis 1::02 Infarctus haemorrhagicus pulmonis
02 Necrosis 2
02 Necrosis 2::01 Liponecrosis pancreatis
"""


class DeckSeedDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Deck Seed: Create Empty Decks")
        self.setMinimumWidth(720)

        root = QVBoxLayout(self)

        title = QLabel(
            "空デックを作成します（カードは作りません）。\n"
            "1行につき1デック名を入力してください。子デックは '親::子' 形式です。"
        )
        root.addWidget(title)

        self.editor = QTextEdit(self)
        self.editor.setPlaceholderText("例:\n01 Necrosis 1\n01 Necrosis 1::01 Anemic infarction\n...")
        root.addWidget(self.editor, 1)

        # Buttons row
        btn_row = QHBoxLayout()
        self.btn_sample = QPushButton("サンプル挿入", self)
        self.btn_dedupe = QPushButton("重複除去", self)
        self.btn_clear = QPushButton("クリア", self)

        btn_row.addWidget(self.btn_sample)
        btn_row.addWidget(self.btn_dedupe)
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

        # Dialog buttons
        self.box = QDialogButtonBox(self)
        self.btn_run = self.box.addButton("作成", QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_close = self.box.addButton("閉じる", QDialogButtonBox.ButtonRole.RejectRole)
        root.addWidget(self.box)

        self.btn_sample.clicked.connect(self._on_sample)
        self.btn_dedupe.clicked.connect(self._on_dedupe)
        self.btn_clear.clicked.connect(self._on_clear)
        self.box.accepted.connect(self._on_run)
        self.box.rejected.connect(self.reject)

        self._load()

    def _load(self) -> None:
        qs = _qsettings()
        saved = qs.value(QSET_KEY_TEXT, "", type=str) or ""
        self.editor.setPlainText(saved)

    def _save(self) -> None:
        qs = _qsettings()
        qs.setValue(QSET_KEY_TEXT, self.editor.toPlainText())

    def closeEvent(self, event) -> None:
        self._save()
        return super().closeEvent(event)

    def _on_sample(self) -> None:
        self.editor.setPlainText(SAMPLE_TEXT)

    def _on_clear(self) -> None:
        self.editor.clear()

    def _on_dedupe(self) -> None:
        lines = _normalize_lines(self.editor.toPlainText())
        deduped = _dedupe_keep_order(lines)
        self.editor.setPlainText("\n".join(deduped))

    def _on_run(self) -> None:
        text = self.editor.toPlainText()
        lines = _normalize_lines(text)
        if not lines:
            QMessageBox.information(self, "Deck Seed", "デック名が空です。1行以上入力してください。")
            return

        # 保存してから実行
        self._save()

        # まず重複除去してから作成
        lines = _dedupe_keep_order(lines)

        ok, ng = _ensure_empty_decks(lines)
        msg = f"作成（または存在確認）: {ok} 件"
        if ng:
            msg += f"\n失敗: {ng} 件（不正なデック名の可能性）"
        showInfo(msg)


_dialog: DeckSeedDialog | None = None


def _open_dialog() -> None:
    global _dialog
    if _dialog is None:
        _dialog = DeckSeedDialog(parent=mw)
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()


def setup_menu() -> None:
    action = QAction("Deck Seed: Create Empty Decks…", mw)
    action.triggered.connect(_open_dialog)
    mw.form.menuTools.addAction(action)


setup_menu()

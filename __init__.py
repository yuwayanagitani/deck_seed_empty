from __future__ import annotations

from aqt import mw
from aqt.qt import (
    QAction,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
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
    # Use an add-on specific app name to avoid collisions.
    return QSettings(QSET_ORG, QSET_APP)


def _normalize_lines(text: str) -> list[str]:
    """
    Interpret input as one deck name per line.
    - Trim whitespace
    - Ignore empty lines
    - Ignore comment lines starting with '#'
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
    Ensure decks exist. Creates them if missing. Does NOT create cards.
    Returns: (ok_count, failed_count)
    """
    ok = 0
    ng = 0
    for name in deck_names:
        try:
            # Create if missing, or return existing ID.
            mw.col.decks.id(name)
            ok += 1
        except Exception:
            ng += 1
    mw.col.decks.save()
    mw.reset()
    return ok, ng


SAMPLE_TEXT = """# One deck name per line. Use '::' for child decks.
01 Necrosis 1
01 Necrosis 1::01 Anemic infarction
01 Necrosis 1::02 Infarctus haemorrhagicus pulmonis
02 Necrosis 2
02 Necrosis 2::01 Liponecrosis pancreatis
"""


class DeckConfirmDialog(QDialog):
    """
    Custom confirmation dialog that displays the full list of decks
    in a scrollable, resizable dialog.
    """
    def __init__(self, deck_names: list[str], parent=None) -> None:
        super().__init__(parent)
        
        self.setWindowTitle("Confirm Deck Creation")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Summary text
        summary = QLabel(
            f"About to create/ensure empty decks.\n\n"
            f"Total decks: {len(deck_names)}"
        )
        layout.addWidget(summary)
        
        # Scrollable deck list
        list_label = QLabel("Deck names:")
        layout.addWidget(list_label)
        
        self.deck_list_view = QPlainTextEdit(self)
        self.deck_list_view.setPlainText("\n".join(deck_names))
        self.deck_list_view.setReadOnly(True)
        layout.addWidget(self.deck_list_view, 1)
        
        # Action buttons
        button_box = QDialogButtonBox(self)
        btn_create = button_box.addButton("Create", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_cancel = button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


class DeckSeedDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Deck Seed: Create Empty Decks")
        self.setMinimumWidth(720)

        root = QVBoxLayout(self)

        title = QLabel(
            "Create empty decks (no cards will be created).\n"
            "Enter one deck name per line. Use 'Parent::Child' for nested decks."
        )
        root.addWidget(title)

        self.editor = QTextEdit(self)
        self.editor.setPlaceholderText(
            "Example:\n"
            "01 Necrosis 1\n"
            "01 Necrosis 1::01 Anemic infarction\n"
            "..."
        )
        root.addWidget(self.editor, 1)

        # Buttons row
        btn_row = QHBoxLayout()
        self.btn_sample = QPushButton("Insert Sample", self)
        self.btn_dedupe = QPushButton("Remove Duplicates", self)
        self.btn_clear = QPushButton("Clear", self)

        btn_row.addWidget(self.btn_sample)
        btn_row.addWidget(self.btn_dedupe)
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

        # Dialog buttons
        self.box = QDialogButtonBox(self)
        self.btn_run = self.box.addButton("Create", QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_close = self.box.addButton("Close", QDialogButtonBox.ButtonRole.RejectRole)
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
            QMessageBox.information(self, "Deck Seed", "No deck names found. Please enter at least one line.")
            return

        # Save first
        self._save()

        # Dedupe before creation
        lines = _dedupe_keep_order(lines)

        # --- Confirm with custom dialog ---
        confirm_dialog = DeckConfirmDialog(lines, parent=self)
        if confirm_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # --- Run ---
        ok, ng = _ensure_empty_decks(lines)
        done_msg = f"Ensured decks: {ok}"
        if ng:
            done_msg += f"\nFailed: {ng} (invalid deck name(s)?)"
        showInfo(done_msg)


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

# Deck Seed: Create Empty Decks

An Anki add-on that lets you **create empty decks (no cards)** in one click.

This add-on is designed for users who want to:
- Prepare a **deck structure in advance**
- Create **parent / child decks** using `Parent::Child`
- Avoid placeholder cards or TSV import limitations
- Manage curriculum- or project-based deck hierarchies cleanly

---

## ✨ Features

- Create **empty decks only** (no cards are added)
- Supports **nested decks** using `Parent::Child` syntax
- Simple dialog UI
- Paste or type **one deck name per line**
- Duplicate removal (order preserved)
- **Preview before creation**
  - Total number of decks
  - First N deck names
- Safe to run multiple times (existing decks are reused)
- Input is **remembered per profile**

---

## 🧭 How to Use

1. Restart Anki after installing the add-on
2. Open:
   ```
   Tools → Deck Seed: Create Empty Decks…
   ```
3. Enter deck names, one per line:

   ```
   01 Necrosis 1
   01 Necrosis 1::01 Anemic infarction
   01 Necrosis 1::02 Infarctus haemorrhagicus pulmonis
   02 Necrosis 2
   ```

4. Click **Create**
5. Review the preview dialog
6. Confirm → empty decks are created

---

## 📝 Input Rules

- **One line = one deck**
- Use `::` to define child decks
- Empty lines are ignored
- Lines starting with `#` are treated as comments
- Duplicate deck names are automatically removed

---

## 🔍 Preview & Safety

Before any deck is created, the add-on shows:
- Total number of decks to be created
- A preview of the first few deck names

You must explicitly confirm before execution.

---

## ⚠️ What This Add-on Does NOT Do

- ❌ Does not create cards
- ❌ Does not import TSV / CSV
- ❌ Does not modify existing cards
- ❌ Does not delete decks

This add-on only ensures that the specified decks exist.

---

## 💡 Typical Use Cases

- Medical / law / language curricula with predefined structure
- Large Anki setups managed like a project
- Deck scaffolding before card generation
- Git / Coverage / Issue-based learning workflows

---

## 🛠 Technical Notes

- Uses Anki's internal API: `mw.col.decks.id()`
- Safe idempotent behavior
- Compatible with Anki 25.x (Qt6 / PyQt6)

---

## 📜 License

MIT License

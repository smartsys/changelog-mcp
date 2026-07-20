---
name: changelog
description: Changelog-Eintrag erstellen. Aufrufen wenn der User sagt "schreib den Changelog", "dokumentier die Änderungen", "trag das ein", "Changelog" oder nach Abschluss einer Implementierung.
user_invocable: true
---

# /changelog

*Erstellt einen Changelog-Eintrag für die aktuelle Arbeit.*

## Voraussetzung: einmal `init_changelog`

Vor dem ersten Changelog-Eintrag müssen Store und Config existieren. Sind sie noch nicht angelegt —
oder meldet ein Tool „Konfiguration fehlt" bzw. „In CHANGELOG_MCP_CONFIG angegebene Konfiguration
fehlt" — einmal `init_changelog` ausführen. Es legt Store und Config-Datei an (am Pfad aus
`CHANGELOG_MCP_CONFIG`, sonst im Projekt-Root) und ist idempotent: ein zweiter Aufruf überschreibt
nichts. Das gilt **pro Projekt** — es gibt keinen globalen Changelog.

## Execution

User provided context: "$ARGUMENTS"

### Schritt 1: Änderungen analysieren

Analysiere was in der aktuellen Session geändert wurde:

1. `git status` - Ungetrackte und geänderte Dateien
2. `git diff HEAD` - Aktuelle Änderungen
3. `git log --oneline -5` - Letzte Commits für Kontext

Falls keine Änderungen vorhanden sind, frage den User was dokumentiert werden soll.

### Schritt 2: Changelog-Eintrag vorbereiten

Bestimme aus den Änderungen:
- **Kategorie**: hängt vom aktiven Format ab (`get_config` zeigt es). **Achtung:** `keep-a-changelog`
  und `conventional` validieren **strikt** — eine unbekannte Kategorie lässt `add_entry`
  fehlschlagen:
  - `smart` (Default): frei wählbar. Empfehlung: Added, Changed, Deprecated, Removed, Fixed,
    Security, Documentation.
  - `keep-a-changelog` (strikt): nur Added, Changed, Deprecated, Removed, Fixed, Security.
  - `conventional` (strikt): nur Features, Bug Fixes, Performance, Reverts, Breaking Changes.
- **Beschreibung**: Kurze Zusammenfassung der Änderung (1 Zeile)
- **Details**: Technische Details als Liste
- **Dateien**: Geänderte Dateien mit Beschreibung
- **Version-Bump**: `bump` = `patch` (Default, Fehlerbehebung/Kleinigkeit), `minor` (neue,
  abwärtskompatible Funktion) oder `major` (Breaking Change). Wirkt nur im Modus `semver`; bei
  `patch-only` wird `bump` ignoriert (nur die Patch-Stelle zählt hoch).
- **Privat?**: `private=true` setzen, wenn die Änderung nicht-öffentliche Doku/interne Arbeit
  betrifft, die **nicht** im publizierten Changelog erscheinen soll. Im Zweifel nachfragen.

Falls "$ARGUMENTS" angegeben wurde, nutze diese als Kontext für die Beschreibung.

### Schritt 3: Eintrag in den Store schreiben

Nutze das MCP Tool `add_entry` um den Eintrag an den append-only Store (`changelog.jsonl`) anzuhängen.
`add_entry` schreibt **nicht** direkt ins Markdown-Changelog — die Markdown entsteht erst beim Release.
Für interne Einträge `private=true` mitgeben.

### Schritt 4: Bestätigung

Zeige dem User:
- Den erfassten Eintrag (Kategorie + Beschreibung)
- Hinweis, dass ein Commit nötig ist. In diesem Projekt via `python3 documentation/git/commit.py`.
  **Existiert dieses Script nicht, diesen Hinweis ignorieren** und den üblichen Git-Workflow des
  Projekts nutzen.

## Korrekturen (append-only)

Der Store wird **nie** von Hand editiert. Fehler in einem Eintrag korrigierst du über Tools, die
intern Korrektur- bzw. Tilgungs-Records anhängen (die Historie bleibt erhalten, der Read-Layer
rechnet sie ein):

- `edit_entry(id, ...)` — ändert einzelne Felder eines Eintrags per ID (nur die genannten Felder;
  Version und Datum bleiben).
- `delete_entry(id)` — tilgt einen **unveröffentlichten** Eintrag per ID. Bereits released
  Einträge sind publizierte Historie und werden abgelehnt. **Nur auf ausdrückliche Freigabe des
  Users aufrufen** — niemals eigenständig löschen; im Zweifel zuerst fragen.

Die nötigen IDs liefern `list_unreleased` oder `search_entries`.

## Veröffentlichung (Release)

Wenn der User einen Release verlangt („veröffentliche", „mach ein Release", „render das Changelog"):

1. `list_unreleased` — offene Einträge seit dem letzten Release + künftige Version abrufen.
   **Wichtig:** `list_unreleased` liefert bereits nur die **öffentlichen** Einträge. Private
   Einträge sind ausgeblendet (solange `changelog.includePrivate=false`) und dürfen **auf keinen
   Fall** in den Summary aufgenommen werden. Fasse ausschließlich zusammen, was `list_unreleased`
   zurückgibt — rekonstruiere keine ausgeblendeten Einträge aus dem git-Diff.
2. Die zurückgegebenen Einträge zu kuratierten Sections verdichten (pro Kategorie zusammenfassen).
3. `preview_release` — Release-Block vorab zeigen und vom User bestätigen lassen.
4. `create_release` — bündelt **alle** offenen Einträge (auch private, damit sie als released
   gelten), schreibt den Release und rendert `CHANGELOG.md` (kuratiert, ohne Private) +
   `CHANGELOG-full.md` (Detail) aus dem Store.

Sonderfall: Meldet `list_unreleased` nur private Einträge („keine öffentlichen unveröffentlichten
Einträge"), `create_release` **ohne** `summary` aufrufen — es entsteht ein reines Privat-Release
ohne öffentlichen CHANGELOG.md-Block.

### Private Einträge — Konfiguration

Zwei Flags in `d ` steuern, ob Privates doch
publiziert wird (Default jeweils `false`):

- `changelog.includePrivate` — private Einträge fließen in `CHANGELOG.md` ein (dann zeigt
  `list_unreleased` sie auch).
- `fullChangelog.includePrivate` — private Einträge werden in `CHANGELOG-full.md` gerendert.

## Weitere Tools

Neben den oben genutzten (`add_entry`, `edit_entry`, `delete_entry`, `list_unreleased`,
`preview_release`, `create_release`) gibt es Tools für Setup/Version (`init_changelog`,
`get_current_version`, `get_next_version`, `get_config`), Suche/Abruf (`search_entries`,
`get_release`) und Rendern/Migration (`render_changelog`, `import_records`, `verify_store`) —
insgesamt 15.

**Vollständige Referenz mit allen Parametern, Rückgaben und Besonderheiten:
[`references/tools.md`](references/tools.md) — bei Detailfragen zu einem konkreten Tool dort
nachschlagen.**

## Regeln

- Sprache: Deutsch für Beschreibungen und Details
- Keine Emojis im Changelog-Eintrag
- Changelog-Dateien und Store NIEMALS direkt bearbeiten — nur MCP Tools
- Zwei Ebenen: laufende Änderungen via `add_entry`, Veröffentlichung via `create_release`
- Korrekturen nur über `edit_entry` / `delete_entry` (append-only Korrektur-/Tilgungs-Records),
  nie durch direktes Editieren von Store oder Markdown
- `delete_entry` **nur auf ausdrückliche Freigabe des Users** — nie eigenständig löschen
- Commit über `python3 documentation/git/commit.py`, falls vorhanden — sonst diesen Schritt
  ignorieren und den üblichen Git-Workflow des Projekts nutzen

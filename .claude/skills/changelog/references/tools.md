# Tool-Referenz: changelog-mcp

Vollständige Referenz aller 15 MCP-Tools mit Parametern, Rückgabe und Besonderheiten. Für den
normalen Ablauf reicht die SKILL.md; diese Datei nur bei Detailfragen zu einem konkreten Tool lesen.

Hinweis: Der MCP-Client erhält beim Verbinden ohnehin die Liste aller Tools mit ihren
Kurzbeschreibungen (`tools/list`). Diese Referenz ist die ausführliche Ergänzung dazu.

Gemeinsame Typen:
- **Section** (für Release-Summaries): `{ "category": str, "items": str[] }` — `items` muss mindestens
  einen Eintrag haben.
- **bump**: `"major" | "minor" | "patch"` (Default `patch`). Wirkt nur im Versionierungs-Modus
  `semver`; bei `patch-only` wird `bump` ignoriert.

## Inhalt

- [Setup & Version](#setup--version): `init_changelog`, `get_current_version`, `get_next_version`, `get_config`
- [Laufende Erfassung](#laufende-erfassung): `add_entry`, `edit_entry`, `delete_entry`
- [Veröffentlichen](#veröffentlichen): `list_unreleased`, `preview_release`, `create_release`
- [Suche & Abruf](#suche--abruf): `search_entries`, `get_release`
- [Rendern & Migration](#rendern--migration): `render_changelog`, `import_records`, `verify_store`

---

## Setup & Version

### `init_changelog`

Bootstrap eines Projekts: legt Store und Config-Datei an, was fehlt.

- **Parameter:** `format?` — `"keep-a-changelog" | "conventional" | "smart"`. Nur relevant, wenn noch
  keine Config existiert; sonst wird das Format der vorhandenen Config beibehalten.
- **Verhalten:** Config-Zielpfad = `CHANGELOG_MCP_CONFIG` (falls gesetzt), sonst Default-Name im
  Projekt-Root. Wirft **nicht**, wenn die per ENV angegebene Datei noch fehlt (das ist der zu
  bootstrappende Fall). Idempotent: vorhandene Config wird übernommen, ein vorhandener Store **nie**
  überschrieben. Erstellt **nicht** die Markdown-Dateien (die entstehen beim ersten Release).
- **Rückgabe:** Meldung, was angelegt bzw. übernommen wurde, plus aktives Format.

### `get_current_version`

- **Parameter:** keine.
- **Rückgabe:** höchste Version im Store und Anzahl unveröffentlichter Einträge.

### `get_next_version`

- **Parameter:** `bump?` (siehe oben, Default `patch`).
- **Rückgabe:** die Version, die der nächste Eintrag/Release tragen würde — berechnet aus der höchsten
  Store-Version und dem Modus. Schreibt nichts.

### `get_config`

- **Parameter:** keine.
- **Rückgabe:** die aktive, aufgelöste Konfiguration als JSON, inklusive Herkunft der Werte
  (Datei-Pfad oder Zero-Config-Defaults). Nützlich, um vor dem Erfassen das aktive **Format** zu
  prüfen (strikt vs. frei).

---

## Laufende Erfassung

### `add_entry`

Hängt einen einzelnen Eintrag an den append-only Store an. Ändert die Markdown-Dateien **nicht** —
die entstehen erst beim Release.

- **Parameter:**
  - `category` (str, Pflicht) — bei `keep-a-changelog`/`conventional` strikt validiert; bei `smart`
    frei.
  - `description` (str, Pflicht) — eine Zeile.
  - `details?` (str[]) — technische Details.
  - `files?` (str[]) — betroffene Dateien.
  - `bump?` (siehe oben, Default `patch`) — bestimmt die nächste Version.
  - `private?` (bool, Default `false`) — hält den Eintrag aus den publizierten Changelogs, solange das
    jeweilige `includePrivate`-Flag `false` ist.
- **Rückgabe:** vergebene Version, Kategorie, Anzahl unveröffentlichter Einträge; Warnungen bei
  defekten Store-Zeilen.

### `edit_entry`

Korrigiert Felder eines bestehenden Eintrags per ID (append-only: intern ein Korrektur-Record; der
Read-Layer rechnet die Änderung ein).

- **Parameter:** `id` (str, Pflicht); `category?`, `description?`, `details?` (str[]), `files?`
  (str[]). Nur die **genannten** Felder werden überschrieben; Version und Datum bleiben.
- **Rückgabe:** Bestätigung der Korrektur.
- **IDs finden:** über `list_unreleased` oder `search_entries`.

### `delete_entry`

Tilgt einen **unveröffentlichten** Eintrag per ID (append-only Tilgungs-Record).

- **Parameter:** `id` (str, Pflicht).
- **Verhalten:** Bereits released Einträge sind publizierte Historie und werden **abgelehnt**.
- **Wichtig:** **Nur auf ausdrückliche Freigabe des Users aufrufen** — nie eigenständig löschen.
- **Rückgabe:** Bestätigung der Tilgung oder Ablehnung.

---

## Veröffentlichen

### `list_unreleased`

- **Parameter:** keine.
- **Rückgabe:** die **öffentlichen** unveröffentlichten Einträge seit dem letzten Release und die
  Version, die ein Release tragen würde. Private Einträge sind ausgeblendet, solange
  `changelog.includePrivate=false`; die Anzahl ausgeblendeter privater Einträge wird genannt.
  Grundlage für den von der KI verfassten Summary.

### `preview_release`

- **Parameter:** `summary` (Section[]) — die kuratierten Abschnitte.
- **Verhalten:** rendert den Release-Block exakt wie `create_release`, **ohne** zu schreiben.
  Validiert Summary-Schema und Kategorien.
- **Rückgabe:** der gerenderte Vorschau-Block.

### `create_release`

Bündelt **alle** unveröffentlichten Einträge (auch private) zu einem Release und rendert beide
Markdown-Dateien neu.

- **Parameter:** `summary?` (Section[]) — beschreibt nur den **öffentlichen** Block.
- **Verhalten:** Version = höchste Entry-Version der Spanne. Private Einträge werden mitgebündelt
  (gelten als released), erscheinen aber nur gemäß `includePrivate` in den Ausgaben. Sind alle offenen
  Einträge privat (`includePrivate=false`), ist ein leerer/fehlender `summary` zulässig — dann
  entsteht kein öffentlicher `CHANGELOG.md`-Block. Bricht ab, wenn nichts unveröffentlicht ist oder
  wenn es öffentliche Einträge, aber keinen `summary` gibt.
- **Rückgabe:** Meldung mit Version, Anzahl gebündelter Einträge und ob die Dateien geschrieben wurden.

---

## Suche & Abruf

### `search_entries`

Durchsucht den strukturierten Store; alle Filter werden UND-kombiniert.

- **Parameter (alle optional):**
  - `query` (str) — Volltext mit Ranking (Beschreibung > Details > Dateien > Kategorie).
  - `category` (str) — exakt, case-insensitive.
  - `file` (str) — Teilstring über die Dateiliste.
  - `version` (str) — Präfix-Vergleich.
  - `released` (bool) — nur released bzw. nur unveröffentlichte.
  - `dateFrom` / `dateTo` (str) — Datumsbereich (inklusive).
  - `limit` (int, Default 10).
- **Rückgabe:** Trefferliste. Ohne `query` nach Version absteigend sortiert.

### `get_release`

- **Parameter:** `version` (str, Pflicht) — exakte Versionsnummer.
- **Rückgabe:** der Release mit Zusammenfassung und allen gebündelten Einzeleinträgen.

---

## Rendern & Migration

### `render_changelog`

- **Parameter:** keine.
- **Verhalten:** erzeugt beide Markdown-Dateien neu aus dem Store — idempotent. Render-Schutz: die
  öffentliche `CHANGELOG.md` wird nur geschrieben, wenn mindestens ein Release mit öffentlichem
  Summary existiert. Kein Release nötig, um zu re-rendern.
- **Rückgabe:** was geschrieben bzw. übersprungen wurde.

### `import_records`

Migration bestehender Changelogs: hängt geparste Einträge (und optional Releases) an den Store an.

- **Parameter:**
  - `entries` (Liste) — je Eintrag: `version`, `date`, `category`, `description`, `details?`,
    `files?`, `private?`.
  - `releases?` (Liste) — je Release: `version`, `date`, `summary` (Section[]), `entryVersions?`
    (referenziert Einträge über ihre Version).
- **Verhalten:** Einträge/Releases, deren Version bereits existiert, werden übersprungen (Import ist
  wiederholbar).
- **Rückgabe:** Anzahl importiert bzw. übersprungen.

### `verify_store`

Sicherheitsnetz der Migration: muss erfolgreich sein, bevor `render_changelog` läuft (sonst
überschreibt das Rendering die Quelldatei mit unvollständigem Stand).

- **Parameter:** `sourceFile` (str) — relativer Pfad zur bestehenden Changelog-Datei.
- **Verhalten:** vergleicht die Versions-Überschriften der Quelldatei mit dem Store und meldet
  fehlende Versionen.
- **Rückgabe:** Erfolg oder Liste der fehlenden Versionen mit Lösungshinweis.

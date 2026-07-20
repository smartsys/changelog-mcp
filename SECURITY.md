# Sicherheit

## Schwachstelle melden

Schwachstellen bitte **nicht** über ein öffentliches Issue melden.

Nutze stattdessen das private Meldeformular von GitHub:
**Security → Report a vulnerability** im Reiter
[Security](https://github.com/smartsys/changelog-mcp/security) dieses Repositories.

Hilfreich für die Einordnung: betroffene Version, Konfiguration (Inhalt der
`changelog-mcp-config.json`), die auslösenden Tool-Aufrufe und was dabei passiert ist.

Dies ist ein Projekt einer einzelnen Person ohne Support-Zusage — eine Antwort kommt,
sobald es zeitlich passt. Eine feste Reaktionszeit wird nicht garantiert.

## Unterstützte Versionen

Das Projekt ist in aktiver Entwicklung und noch vor Version 1.0. Sicherheitsfixes gibt es
ausschließlich für die **jeweils neueste Version**; ältere Stände werden nicht gepflegt.

## Vertrauensmodell

`changelog-mcp` ist ein **lokaler stdio-MCP-Server**. Er läuft als Kindprozess des
KI-Clients, mit den Rechten des Nutzers, der den Client startet.

- **Keine Netzwerkverbindungen.** Der Server öffnet keine Sockets und lädt nichts nach.
- **Ein einziger externer Aufruf:** `git rev-parse --show-toplevel`, um den Projekt-Root
  zu finden — mit fester Argumentliste, ohne Shell und mit Timeout. Schlägt er fehl,
  greift die nächste Auflösungsstufe.
- **Schreibzugriff nur auf die konfigurierten Dateien** innerhalb des Projekt-Roots:
  Store, Markdown-Changelogs, Backup-Ordner und Config.

Der relevante Angreifer ist damit **nicht** ein Netzwerkangreifer, sondern **unvertrauenswürdiger
Inhalt, der den KI-Assistenten steuert** (Prompt Injection über Dateien, Issues, Web-Inhalte).
Ein so gesteuerter Assistent kann Changelog-Einträge mit beliebigem Text erzeugen. Er soll
aber **nicht** aus dem Projekt-Root ausbrechen oder Historie vernichten können — genau dafür
sind die folgenden Invarianten da.

## Sicherheits-Invarianten

Diese Eigenschaften sind Kern des Designs. Ein Bruch davon ist eine Schwachstelle und
meldenswert.

**Pfad-Sicherheit** (`src/changelog_mcp/utils/security.py`)

- Alle Pfade aus der Config sind **relativ zum Projekt-Root**.
- Abgelehnt werden: absolute Pfade (inklusive Windows-Laufwerksbuchstaben), `..`-Segmente
  und Null-Bytes. Backslashes werden vorher normalisiert, damit die Prüfung auch unter
  Windows greift.
- Der **aufgelöste** Zielpfad muss innerhalb des Roots liegen — geprüft nach `resolve()`,
  also nachdem Symlinks und `.`-Segmente aufgelöst sind.
- Dateinamen aus der Config müssen reine Namen sein, ohne `/`, `\` oder `..`.

**Symlink-Schutz**

- Ziele werden vor jedem Lese- und Schreibzugriff geprüft und abgelehnt, wenn sie ein
  Symlink sind. Ein untergeschobener Link kann Schreibzugriffe damit nicht umlenken.

**Größenlimit**

- Changelog-Dateien über **10 MB** werden abgelehnt (`MAX_CHANGELOG_SIZE`), als Schutz
  gegen unbeabsichtigtes Aufblähen und Speicher-Erschöpfung beim Parsen.

**Store-Integrität**

Der Changelog ist **veränderbar** — das ist Absicht, aber es begrenzt, welche Zusicherung der
Server geben kann:

- Drei Tools schreiben in den Store: `add_entry` legt an, `edit_entry` ändert Felder eines
  Eintrags, `delete_entry` entfernt einen Eintrag aus allen Ausgaben.
- **Konsequenz für das Bedrohungsmodell:** Wer den Assistenten steuert, kann unveröffentlichte
  Einträge inhaltlich verändern oder aus den generierten Changelogs verschwinden lassen. Der
  Server unterscheidet nicht zwischen einer legitimen Korrektur und einer böswilligen.
- **Rekonstruierbar bleibt es trotzdem:** Änderungen und Löschungen werden als zusätzliche
  Zeilen in `changelog.jsonl` geschrieben, statt bestehende Zeilen zu überschreiben. Der
  ursprüngliche Eintrag ist in der Rohdatei also weiterhin nachweisbar — in der daraus
  erzeugten `CHANGELOG.md` nicht mehr. Wer Manipulation ausschließen will, prüft die JSONL-Datei
  und die Backups, nicht das gerenderte Markdown.
- **Grenze:** Bereits **released** Einträge lehnt `delete_entry` ab (publizierte Historie).
  `edit_entry` greift dagegen auch dort.
- Vor der ersten Änderung je Zeitraum wird der Store gesichert (Default täglich, 30
  Sicherungen) — ein zusätzliches Netz, keine Integritätsgarantie.
- Ein abgebrochener Schreibvorgang beschädigt höchstens die zuletzt geschriebene Zeile; sie
  wird beim Lesen erkannt, gemeldet und übersprungen.

**Eingabe-Validierung**

- Alle Tool-Parameter werden an der Tool-Grenze mit Pydantic v2 validiert.
- Jede Store-Zeile wird beim Lesen validiert. Defekte Zeilen (ungültiges JSON oder
  Schema-Verstoß) brechen das Lesen nicht ab, sondern werden übersprungen und als Warnung
  zurückgemeldet.

**stdout ist reserviert**

- stdout transportiert ausschließlich MCP-JSON-RPC. Sämtliche Logs und Diagnose gehen auf
  stderr. Eine Ausgabe auf stdout würde das Protokoll brechen — Meldungen dieser Art sind
  ebenfalls willkommen.

## Ausdrücklich kein Sicherheitsproblem

- **Inhalt von Changelog-Einträgen.** Beschreibungstexte werden als Text übernommen und
  nach Markdown gerendert. Wer den Assistenten steuert, bestimmt den Text. Rendere den
  Changelog nicht ungeprüft als HTML in einem vertrauenswürdigen Kontext.
- **Schreibzugriff innerhalb des Projekt-Roots.** Genau das ist die Aufgabe des Servers.
- **Zugriff auf die Config.** Wer die Config-Datei ändern kann, hat ohnehin Schreibzugriff
  auf das Projekt.
- **Private Einträge** (`private=true`) sind ein Publikations-Filter für die generierten
  Markdown-Dateien, **keine** Zugriffskontrolle. Im Store stehen sie im Klartext. Lege dort
  keine Geheimnisse ab.

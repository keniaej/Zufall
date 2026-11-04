# So arbeiten wir zusammen

Diese Anleitung ist für Git-Einsteiger. Haltet euch an diese Schritte, dann gibt es keine Konflikte.

## Die Grundregel

**Niemand arbeitet direkt auf `main`.** `main` ist immer die funktionierende Version. Jede Änderung läuft so ab:

1. Neuen Branch anlegen
2. Auf dem Branch arbeiten und committen
3. Branch zu GitHub hochladen (push)
4. Pull Request öffnen
5. Ein anderes Teammitglied schaut drüber und klickt auf *Merge*

## Schritt für Schritt

### 1. Vor dem Arbeiten: neuesten Stand holen

```bash
git checkout main
git pull
```

### 2. Eigenen Branch anlegen

Name nach dem Muster `feature/was-du-machst` (oder `fix/...` bei Fehlern):

```bash
git checkout -b feature/excel-export
```

### 3. Arbeiten und speichern (committen)

```bash
git status                 # zeigt, was sich geändert hat
git add .                  # alle Änderungen vormerken
git commit -m "Excel-Export mit Spaltenüberschriften"
```

Lieber oft kleine Commits als ein riesiger.

### 4. Hochladen

```bash
git push -u origin feature/excel-export
```

### 5. Pull Request öffnen

Auf GitHub erscheint ein gelber Hinweis *Compare & pull request*. Draufklicken, kurz beschreiben, was du gemacht hast, und eine Person als Reviewer eintragen.

### 6. Nach dem Merge

```bash
git checkout main
git pull
git branch -d feature/excel-export
```

## Wer macht was?

Aufgaben stehen als **Issues** auf GitHub (Tab *Issues*). Weise dir ein Issue zu, bevor du anfängst, damit nicht zwei Leute dasselbe bauen.

## Häufige Probleme

- **„Your branch is behind“**: `git pull` ausführen.
- **Merge-Konflikt**: Git markiert die Stelle in der Datei mit `<<<<<<<` und `>>>>>>>`. Entscheidet, welche Version bleibt, löscht die Markierungen, dann `git add .` und `git commit`. Im Zweifel kurz im Team fragen.
- **Aus Versehen etwas mit API-Key committet**: sofort im Team melden und den Key beim Anbieter neu erzeugen.

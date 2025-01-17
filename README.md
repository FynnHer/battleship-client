# Schiffe Versenken Client - Fynn-Lasse Herrmann

## Projektübersicht
Dieser Schiffe-Versenken-Client wurde als Schulprojekt entwickelt und kommuniziert mit einem durch die Aufgabe gegebenen Python Server. Er ermöglicht das einfache und benutzerfreundliche Spielen mit anderen Spielern. Ein Nutzer kann den Client in insgesamt zwei verschiedenen Modi verwenden: ein "Normal Mode" sowie ein "Special Mode". Dieser "Special Mode" ist lediglich zum Spaß gedacht und beinhaltet keinesfalls grundlegende Techniken des benutzerfreundlichen Designs. Deshalb lag der Fokus beim Entwickeln auf dem "Normal Mode" und somit sollte auch der Fokus bei der Bewertung auf dem "Normal Mode" liegen.

---

## Designentscheidungen und technische Umsetzung

### 1. **Benutzeroberfläche (GUI)**
   - **Framework**: Die GUI wurde mit `tkinter` erstellt, da es nativ in Python funktioniert und plattformunabhängig ist. Zusätzliche Funktionen wie Drag-and-Drop und eigene Farbänderungen wurden integriert.
   - **Farbschema**: Ein modernes Design wurde gewählt, welches eine einfache und verständliche Benutzung ermöglichen soll. Durch verschiedene Farben werden dem Benutzer die einzelnen Aktionen und Vorgänge simpel und effektiv dargestellt.
   - **Benutzerinteraktion**: 
     - Drag-and-Drop-Schiffplatzierung: Spieler können die Schiffe intuitiv platzieren und einfach rotieren.
     - Dynamische Anpassung: Elemente wie Züge, Treffer und verfehlte Schüsse werden visuell hervorgehoben.

### 2. **Spezialeffekte (optional)**
   - Ein spezieller Modus wurde implementiert, der Videos sowie Soundeffekte aktiviert.
   - **Tools und Libraries**:
     - `pygame` zur Wiedergabe von Sounds.
     - `opencv-python` und `ffpyplayer` zur Anzeige von Videos (z. B. Treffer-, Fehl- und Siegesanimationen bzw. Videos).
     - Blinkeffekte und Hintergrundgeräusche wurden über `threading` und dynamische Farbänderungen in der GUI realisiert.

### 3. **Server-Kommunikation**
   - **Protokoll**: Die Kommunikation zwischen Client und Server erfolgt über Sockets. Der Server erwartet bestimmtem, durch die Aufgabenstellung gegebene, Nachrichtenformate, wie z. B. `(Reihe, Spalte)` für Schüsse.
   - **Datenfluss**:
     - Der Client sendet nach initialen Anmeldung das Spielfeld an den Server.
     - Während des Spiels werden Felder von dem Server an die Spieler gesendet.
     - Der Server entscheidet über Treffer, Verfehlungen und Spielausgang.

### 4. **Spiellogik und Regeln**
   - Das Spiel verwendet ein 10x10-Raster.
   - Jedes Spielfeld enthält 5 Schiffe (zwei 2er, zwei 3er und ein 4er-Schiff). (Dies kann frei gewählt werden, in meinem Fall habe ich mich für diese Verteilung entschieden)
   - Die Logik für Platzierung und Treffererkennung wurde direkt im Client integriert.
   - Visuelles Feedback für Treffer („hit“) und Verfehlungen („miss“) wurde über das Farbschema dargestellt. (Ein weißes Feld bedeutet kein Treffer, ein rotes Feld bedeutet Treffer)
   - Es dürfen keine Schiffe nebeneinander platziert werden.
   - Es müssen mindestens 10 Felder mit einem Schiff belegt sein, damit das Spiel gestartet werden kann.
   - Durch einfaches klicken auf ein platziertes Schiff wird dieses wieder entfernt.

---

## Projektstruktur

### Verzeichnisse und Dateien
- **`main.py`**: Hauptskript, das die gesamte Funktionalität steuert.
- **`assets/`**: Verzeichnis für alle Medieninhalte.
  - `cursor.png`: Benutzerdefiniertes Cursor-Bild. (Funktioniert nicht bei allen Python Versionen)
  - `siren.wav`: Ton für Spielerzüge.
  - `hit.mp4`, `miss.mp4`, `victory.mp4`, `defeat.mp4`: Animationen für das Spiel. (Diese können durch das Ändern der Dateien leicht getauscht werden, jedoch muss beachtet werden, dass man die Zeiten in der VIDEOLENGHTS Library anpasst)

---

## Voraussetzungen

### Minimale Anforderungen
- **Python-Version**: 3.10 oder höher
- **Bibliotheken**:
  - `tkinter` (Standardbibliothek für GUI in Python)
  - `socket` (Standardbibliothek für Netzwerkkommunikation)
  - `Pillow` (zum Anzeigen und Bearbeiten von Bildern)
  - `pygame` (zur Audiowiedergabe)
  - `opencv-python` (zur Videowiedergabe)
  - `ffpyplayer` (zur erweiterten Videowiedergabe)
  - `threading`, `time`, `os` (Standardbibliotheken für Multithreading, Zeitsteuerung und Dateiverwaltung)

### Installation der Bibliotheken
Führen Sie folgenden Befehl aus, um alle benötigten Libraries zu installieren:

```bash
pip install Pillow pygame opencv-python ffpyplayer
```

---

## Spielanleitung

### Grundregeln
1. Jeder Spieler platziert seine Schiffe (zwei 2er, zwei 3er, ein 4er) auf dem eigenen 10x10-Feld.
2. Spieler schießen abwechselnd auf das gegnerische Feld.
3. Ein Treffer bleibt am Zug, eine Verfehlung gibt den Zug an den Gegner weiter.
4. Das Spiel endet, wenn alle Schiffe eines Spielers zerstört sind.

### Schritte zum Starten des Spiels
1. Starten Sie das Programm durch Ausführen von `main.py`.
2. Wählen Sie zwischen "Normaler Client" und "Spezieller Client".
3. Geben Sie Ihren Benutzernamen ein und platzieren Sie Ihre Schiffe.
4. Starten Sie das Spiel nachdem Sie mindestens 10 Schiffe plaziert haben.
5. Schießen Sie, indem Sie ein Feld auf dem gegnerischen Spielfeld anklicken und dann den Launch-Button drücken.

---

## Hinweise
- Der Server muss unter `127.0.0.1:5000` laufen, um eine Verbindung herzustellen. Auf eine Möglichkeit für den User, diese IP mit der GUI zu verändern, wurde absichtlich verzichtet.
- Die Mediendateien im `assets/`-Ordner müssen vorhanden sein, damit der spezielle Modus funktioniert.
- Für den speziellen Modus sollten Videos nicht länger als die definierten Videolängen (siehe Code) sein, um synchronisierte Effekte zu gewährleisten.

---
## Bilder und Impressionen
### Farbpalette
![Farbpalette](https://github.com/FynnHer/battleship-client/blob/main/examplepictures/color_palette.png?raw=true)
Farbpalette für ein modernes Design

### Client-Auswahl-Seite
![Client-Auswahl-Fenster](https://github.com/FynnHer/battleship-client/blob/main/examplepictures/client_selector.png?raw=true)
Ein einfacher Weg, um leicht zwischen zwei verschiedenen Clients zu wechseln.

### Lobby und Schiffe platzieren
![Lobby - während dem Schiffe platzieren](https://github.com/FynnHer/battleship-client/blob/main/examplepictures/ship_placing.png?raw=true)
Lobby während dem Platzieren der Schiffe

![Input of username](https://github.com/FynnHer/battleship-client/blob/main/examplepictures/user_input.png?raw=true)
Einfach eingeben des Benutzernamens

![matchmaking lobby screen](https://github.com/FynnHer/battleship-client/blob/main/examplepictures/matchmaking.png?raw=true)
Intelligentes Matchmaking System

![window while playing](https://github.com/FynnHer/battleship-client/blob/main/examplepictures/game_screen_your_turn.png?raw=true)
Intelligentes und ansprechendes Design während dem Spiel



---



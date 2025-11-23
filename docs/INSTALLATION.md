# Installations-Anleitung

## Systemanforderungen

- **Betriebssystem**: Windows 10/11, macOS 10.14+, oder Linux (Ubuntu 20.04+)
- **Python**: Version 3.8 oder höher
- **RAM**: Mindestens 4 GB (8 GB empfohlen)
- **Festplatte**: 500 MB freier Speicherplatz
- **Display**: Mindestens 1280x720 Pixel

## Schritt-für-Schritt Installation

### 1. Python installieren

#### Windows
1. Laden Sie Python von [python.org](https://python.org) herunter
2. Führen Sie den Installer aus
3. ✅ Aktivieren Sie "Add Python to PATH"
4. Klicken Sie auf "Install Now"

#### macOS
```bash
# Mit Homebrew
brew install python@3.11
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Repository klonen

```bash
git clone <repository-url>
cd Pr-fstandsoftwareDD
```

### 3. Virtuelle Umgebung erstellen

**Windows:**
```cmd
python -m venv venv
venv\\Scripts\\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Sie sehen nun `(venv)` am Anfang Ihrer Kommandozeile.

### 4. Abhängigkeiten installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Dies installiert:
- PyQt5 (GUI-Framework)
- NumPy (Numerische Berechnungen)
- SciPy (Wissenschaftliche Berechnungen)
- Pandas (Datenanalyse)
- Matplotlib (Visualisierungen)
- scikit-learn (Machine Learning)

### 5. Installation verifizieren

```bash
python main.py
```

Die Anwendung sollte sich öffnen. Wenn Sie das Hauptfenster sehen, war die Installation erfolgreich!

## Problemlösungen

### PyQt5 Installation schlägt fehl

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-pyqt5 python3-pyqt5.qtsvg
```

**macOS:**
```bash
brew install pyqt5
```

**Windows:**
Stellen Sie sicher, dass Sie Visual C++ Redistributable installiert haben.

### "Python nicht gefunden"

Stellen Sie sicher, dass Python zum PATH hinzugefügt wurde:

**Windows:**
1. Systemsteuerung → System → Erweiterte Systemeinstellungen
2. Umgebungsvariablen
3. Fügen Sie Python-Installationsverzeichnis zu PATH hinzu

**macOS/Linux:**
Fügen Sie in `~/.bashrc` oder `~/.zshrc` hinzu:
```bash
export PATH="/usr/local/bin/python3:$PATH"
```

### Import-Fehler

```bash
# Vollständige Neuinstallation
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

## Deinstallation

```bash
# Virtuelle Umgebung deaktivieren
deactivate

# Projektordner löschen
cd ..
rm -rf Pr-fstandsoftwareDD

# Oder Windows:
# rmdir /s Pr-fstandsoftwareDD
```

## Updates durchführen

```bash
cd Pr-fstandsoftwareDD
git pull
source venv/bin/activate  # oder venv\\Scripts\\activate auf Windows
pip install -r requirements.txt --upgrade
```

## Erste Schritte nach Installation

1. Starten Sie die Anwendung: `python main.py`
2. Erstellen Sie Ihre erste Komponente im Tab "Komponenten"
3. Konfigurieren Sie einen Test im Tab "Test-Steuerung"
4. Starten Sie Ihren ersten Test

Bei weiteren Fragen siehe [README.md](../README.md)

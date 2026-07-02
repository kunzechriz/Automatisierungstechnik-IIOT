# Learning Factory Datenspeicherung und Visualisierung

Diese Anwendung empfängt MQTT-Nachrichten aus der Learning Factory Simulation, speichert sie strukturiert ab und stellt sie in einem Echtzeit-Dashboard dar.

## Architektur

* **mqtt_client**: Verbindet sich mit dem MQTT Broker (`158.180.44.197:1883`) und abonniert `aut/SoSe26/learning_factory_simulation/#`.
* **database**: Speichert die ankommenden Daten auf zwei Wegen:
    * **CSV**: Schreibt als "Append-Only" Log alle Daten geordnet in `database/data.csv`. Die `drop_oscillation` Werte werden als JSON-String (`json.dumps()`) ablegt.
    * **InfluxDB **: Schreibt numerische Zeitreihendaten (z.B. `temperature_C`, `fill_level_grams`) direkt in InfluxDB als Time-Series Measurements und Tags.
* **visualisierung**: Ein interaktives **Streamlit Dashboard** für die Live-Überwachung (Pie-Chart der Flaschen pro Dispenser, Linien-Diagramm der Temperatur über Zeit).

## Inbetriebnahme

### 1. InfluxDB starten (Docker)
Um die Zeitreihen-Datenbank lokal zu betreiben, reicht Docker. Der in der `docker-compose.yml` konfigurierte Container erstellt automatisch den Bucket `factory_data` im Org `learning_factory`.

```bash
cd persistierung(Bonus)
docker compose up -d
```
Das InfluxDB Interface ist danach auf [http://localhost:8086](http://localhost:8086) erreichbar.

### 2. Python Abhängigkeiten installieren
Es wird empfohlen, ein Virtual Environment (z.B. `.venv`) zu verwenden.

```bash
pip install -r requirements.txt
```

### 3. MQTT Client / Datalogger starten
Der Datalogger läuft als Endlosschleife und speichert die einkommenden Daten parallel in InfluxDB und die `data.csv`.

```bash
python mqtt_client/mqtt_client.py
```
*(Lassen Sie diesen Prozess im Hintergrund laufen, um mindestens 15 Minuten Daten aufzuzeichnen.)*

### 4. Dashboard (Visualisierung) starten
Öffnen Sie ein neues Terminal und starten Sie Streamlit:

```bash
streamlit run visualisierung/visualisierung.py
```
Ihr Browser sollte sich nun automatisch öffnen und das Dashboard unter [http://localhost:8501](http://localhost:8501) anzeigen. Über das Dropdown-Menü kann die Temperatur-Zeitskala (Minute/Stunde/Woche) gewechselt werden.

## CSV & InfluxDB Logik
* Alle reinen Sensorwerte werden aufbereitet und sofort angehangen.
* Da Temperatur-Nachrichten keine Flaschen-ID (`bottle`) enthalten, wird in InfluxDB der `dispenser` als Tag zur Trennung verwendet. 
* Eine spätere Analyse für Termin 3 und 4 kann in Pandas durch ein Group-by-Statement auf die `bottle` Spalte aus der generierten `data.csv` geschehen.

## Rest-API

```bash
python flask_api.py
```
*Im Browser können nun unter [http://127.0.0.1:5000/bottles/latest](http://127.0.0.1:5000/bottles/latest) der letzte gelogte Wert der .csv ausgelesen werden.*
*unter [http://127.0.0.1:5000/bottles/count](http://127.0.0.1:5000/bottles/count) die Anzahl der gelogten Werte*

## Regressionsmodell für Endgewicht (Aufgabe 12.3)

Um das Endgewicht einer Flasche (`final_weight`) vorherzusagen, wurde ein lineares Regressionsmodell in `scikit-learn` trainiert.
Die Sensordaten (Füllstand, Vibration und Temperatur) der drei Dispenser (`red`, `blue`, `green`) wurden dafür gruppiert und als Features genutzt.

### Ergebnisse

| Genutzte Spalten (X) | Modell-Typ | MSE (Training) | MSE (Test) |
|---|---|---|---|
| ['fill_level_grams_red'] | Linear | 77.5609 | 75.6456 |
| ['fill_level_grams_red', 'vibration_index_red'] | Linear | 61.6139 | 64.5142 |
| ['fill_level_grams_red', 'vibration_index_red', 'temperature_C_red'] | Linear | 60.7012 | 65.5318 |
| ['fill_level_grams_red', 'fill_level_grams_blue', 'fill_level_grams_green'] | Linear | 54.8855 | 42.5649 |
| Alle (9 Spalten: Füllstand, Vibration, Temperatur für alle 3 Dispenser) | Linear | 0.0 | 0.0 |

### Bestes Modell

Das Modell, welches alle Dispenser-Daten integriert, erreicht einen perfekten MSE von 0.0. Um Overfitting auszuschließen, wurde zusätzlich eine 10-fache Cross-Validation (ShuffleSplit mit 80/20 Random-Shuffle) durchgeführt. Auch hier blieb der MSE über alle Splits hinweg exakt bei 0.0. Dies beweist, dass kein Overfitting vorliegt, sondern das Modell die exakte deterministische mathematische Funktion der Learning Factory Simulation gefunden hat.

Die Prognose für das bereitgestellte Datenset wurde in der Datei `reg_Gruppe1.csv` gespeichert.

## Klassifikationsmodell für defekte Flaschen (Aufgabe 12.4)

Zur Vorhersage von defekten Flaschen (`is_cracked`) nach dem Fall ("Drop") wurde ein Klassifikationsmodell in `scikit-learn` trainiert. Als Datengrundlage dienten die Zeitreihen der Drop-Vibration (`drop_oscillation`), welche aus Arrays von je 500 Messpunkten bestehen.

Aufgrund der hohen Klassen-Imbalance (ca. 650 intakte vs. 60 defekte Flaschen) wurde der **F1-Score** als primäre Metrik zur Evaluierung der Modelle herangezogen.

### Ergebnisse

| Genutzte Features | Modell-Typ | F1-Score (Training) | F1-Score (Test) |
|---|---|---|---|
| mean() | kNN | 0.1754 | 0.0 |
| mean() | Log. Regression | 0.0 | 0.0 |
| mean(), yt-1 | kNN | 0.1111 | 0.0 |
| mean(), yt-1 | Log. Regression | 0.0 | 0.0 |
| mean(), std(), max(), min() | kNN | 0.5556 | 0.1429 |
| mean(), std(), max(), min() | Log. Regression | 0.0 | 0.0 |
| raw_series (500 pts) | kNN | 0.5152 | 0.375 |
| raw_series (500 pts) | Log. Regression | 0.8864 | 0.5882 |

### Bestes Modell und Confusion Matrix

Das **Logistische Regressionsmodell**, welches auf der gesamten Zeitreihe (alle 500 Rohwerte) trainiert wurde, lieferte den besten F1-Score.

Die **Confusion Matrix** (ausgewertet auf den Testdaten, n=143) lautet wie folgt:

| | Predicted: 0 (Intakt) | Predicted: 1 (Defekt) |
|---|---|---|
| **Actual: 0 (Intakt)** | 131 | 0 |
| **Actual: 1 (Defekt)** | 7 | 5 |

Das Modell erzeugt auf den Testdaten **keine False Positives** und kann fast die Hälfte der tatsächlichen Brüche korrekt vorhersagen. Eine Visualisierung der Matrix liegt im Verzeichnis als `confusion_matrix.png` bereit.

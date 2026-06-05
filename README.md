# Learning Factory Datenspeicherung und Visualisierung

Diese Anwendung empfängt MQTT-Nachrichten aus der Learning Factory Simulation, speichert sie strukturiert ab und stellt sie in einem Echtzeit-Dashboard dar.

## Architektur

*   **mqtt_client**: Verbindet sich mit dem MQTT Broker (`158.180.44.197:1883`) und abonniert `aut/SoSe26/learning_factory_simulation/#`.
*   **database**: Speichert die ankommenden Daten auf zwei Wegen:
    *   **CSV**: Schreibt als "Append-Only" Log alle Daten geordnet in `database/data.csv`. Die `drop_oscillation` Werte werden als JSON-String (`json.dumps()`) ablegt.
    *   **InfluxDB **: Schreibt numerische Zeitreihendaten (z.B. `temperature_C`, `fill_level_grams`) direkt in InfluxDB als Time-Series Measurements und Tags.
*   **visualisierung**: Ein interaktives **Streamlit Dashboard** für die Live-Überwachung (Pie-Chart der Flaschen pro Dispenser, Linien-Diagramm der Temperatur über Zeit).

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

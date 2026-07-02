# Learning Factory Datenspeicherung und Visualisierung

Diese Anwendung empfängt MQTT-Nachrichten aus der Learning Factory Simulation, speichert sie strukturiert ab und stellt sie in einem Echtzeit-Dashboard dar.

## Architektur

* **mqtt_client**: Verbindet sich mit dem MQTT Broker (`158.180.44.197:1883`) und abonniert `aut/SoSe26/learning_factory_simulation/#`.
* **database**: Speichert die ankommenden Daten auf zwei Wegen:
    * **CSV**: Schreibt als "Append-Only" Log alle Daten geordnet in `database/data.csv`. Die `drop_oscillation` Werte werden als JSON-String (`json.dumps()`) abgelegt.
    * **InfluxDB**: Schreibt numerische Zeitreihendaten (z.B. `temperature_C`, `fill_level_grams`) direkt in InfluxDB als Time-Series Measurements und Tags.
* **visualisierung**: Ein interaktives **Streamlit Dashboard** für die Live-Überwachung (Pie-Chart der Flaschen pro Dispenser, Linien-Diagramm der Temperatur über Zeit).

## Inbetriebnahme

### 1. InfluxDB starten (Docker)
Um die Zeitreihen-Datenbank lokal zu betreiben, reicht Docker. Der in der `docker-compose.yml` konfigurierte Container erstellt automatisch den Bucket `factory_data` im Org `learning_factory`.

```bash
cd persistierung(Bonus)
docker compose up -d

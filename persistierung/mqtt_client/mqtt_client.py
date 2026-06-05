import paho.mqtt.client as mqtt
import time
import os
import sys

# Add parent dir to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.transform import transform_payload
from database.database import DatabaseHandler

MQTT_BROKER = "158.180.44.197"
MQTT_PORT = 1883
MQTT_TOPIC = "aut/SoSe26/learning_factory_simulation/#"
MQTT_USER = "bobm"
MQTT_PASS = "letmein"

db_handler = DatabaseHandler()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully to MQTT Broker.")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode('utf-8')
    # print(f"Received message on {msg.topic}")
    
    # Transform
    data = transform_payload(msg.topic, payload_str)
    
    # Save to CSV and InfluxDB
    if data:
        db_handler.save_event(data)

def start_mqtt_client():
    client = mqtt.Client(client_id="learning_factory_datalogger")
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Connection failed: {e}")
        time.sleep(5)
        start_mqtt_client()

if __name__ == "__main__":
    start_mqtt_client()

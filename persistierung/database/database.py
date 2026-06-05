import csv
import os
import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class DatabaseHandler:
    def __init__(self):
        # CSV Setup
        self.csv_file = os.path.join(os.path.dirname(__file__), 'data.csv')
        self.csv_headers = [
            "timestamp", "event_type", "bottle", "dispenser", "time", 
            "temperature_C", "fill_level_grams", "recipe", "vibration_index", 
            "final_weight", "is_cracked", "drop_oscillation", "id", 
            "creation_date", "color_levels_grams"
        ]
        self._init_csv()

        # InfluxDB Setup
        self.influx_url = "http://localhost:8086"
        self.influx_token = "my-super-secret-auth-token"
        self.influx_org = "learning_factory"
        self.influx_bucket = "factory_data"
        
        try:
            self.client = InfluxDBClient(url=self.influx_url, token=self.influx_token, org=self.influx_org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.influx_connected = True
        except Exception as e:
            print(f"Failed to connect to InfluxDB: {e}")
            self.influx_connected = False

    def _init_csv(self):
        # Create CSV with headers if it doesn't exist
        file_exists = os.path.isfile(self.csv_file)
        if not file_exists:
            with open(self.csv_file, mode='w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                writer.writeheader()

    def write_csv(self, data: dict):
        # Ensure only known headers are written, missing are left blank
        row = {k: v for k, v in data.items() if k in self.csv_headers}
        row["timestamp"] = datetime.datetime.now().isoformat()
        
        with open(self.csv_file, mode='a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_headers)
            writer.writerow(row)

    def write_influx(self, data: dict):
        if not self.influx_connected:
            return

        event_type = data.get("event_type", "unknown")
        
        # Build Influx Point
        point = Point(event_type)
        
        # Add Tags (indexed, queryable strings)
        if "bottle" in data:
            point = point.tag("bottle", str(data["bottle"]))
        if "dispenser" in data:
            point = point.tag("dispenser", str(data["dispenser"]))
        if "recipe" in data:
            point = point.tag("recipe", str(data["recipe"]))

        # Add Fields (values, time series data)
        has_fields = False
        for field in ["temperature_C", "fill_level_grams", "vibration_index", "final_weight", "is_cracked"]:
            if field in data:
                try:
                    # InfluxDB fields need to be numeric or string, cast strictly to float if possible
                    point = point.field(field, float(data[field]))
                    has_fields = True
                except ValueError:
                    point = point.field(field, str(data[field]))
                    has_fields = True
                    
        # Write only if we have fields to avoid empty measurements
        if has_fields:
            try:
                self.write_api.write(bucket=self.influx_bucket, org=self.influx_org, record=point)
            except Exception as e:
                print(f"Error writing to InfluxDB: {e}")

    def save_event(self, data: dict):
        # Persist to both destinations
        self.write_csv(data)
        self.write_influx(data)


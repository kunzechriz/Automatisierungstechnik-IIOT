import pandas as pd
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "123"
INFLUX_ORG = "learning_factory"
INFLUX_BUCKET = "factory_data"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -7d)
  |> limit(n: 5)
'''
tables = query_api.query(query)

for table in tables:
    for record in table.records:
        print(f"{record.get_measurement()}: {record.get_field()} = {record.get_value()} (Tags: {record.values})")

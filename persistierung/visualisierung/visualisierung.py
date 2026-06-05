import streamlit as st
import pandas as pd
import plotly.express as px
from influxdb_client import InfluxDBClient

st.set_page_config(page_title="Learning Factory Dashboard", layout="wide", initial_sidebar_state="collapsed")
st.title("Learning Factory Live Dashboard")

# InfluxDB Configuration
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "my-super-secret-auth-token"
INFLUX_ORG = "learning_factory"
INFLUX_BUCKET = "factory_data"

@st.cache_resource
def get_influx_client():
    return InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)

client = get_influx_client()
query_api = client.query_api()

try:
    from streamlit_autorefresh import st_autorefresh
    st.sidebar.header("Controls")
    st.sidebar.write("Auto-Refresh jede Sekunde")
    # Refresh every 1000 milliseconds
    st_autorefresh(interval= 999, limit=None, key="data_refresh")
except ImportError:
    st.sidebar.header("Controls")
    st.sidebar.warning("Installiere 'streamlit-autorefresh' in der requirements.txt für automatische Updates.")
    if st.sidebar.button("Refresh Data"):
        st.rerun()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Bottles per Dispenser")
    
    query_dispenser = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -7d)
      |> filter(fn: (r) => r["_field"] == "fill_level_grams")
      |> group(columns: ["dispenser"])
      |> count()
    '''
    
    try:
        tables_dispenser = query_api.query(query_dispenser)
        
        dispenser_counts = []
        for table in tables_dispenser:
            for record in table.records:
                dispenser_counts.append({
                    "Dispenser": record.values.get("dispenser", "Unknown"),
                    "Count": record.get_value()
                })
        
        df_dispenser = pd.DataFrame(dispenser_counts)
        
        if not df_dispenser.empty:
            fig_pie = px.pie(df_dispenser, values='Count', names='Dispenser', 
                             title="Bottles processed by Dispenser",
                             color='Dispenser',
                             color_discrete_map={'red':'red', 'blue':'blue', 'green':'green'})
            st.plotly_chart(fig_pie, width="content")
        else:
            st.info("No dispenser data available yet.")
    except Exception as e:
        st.error(f"Error fetching dispenser data: {e}")

# --- Time Series: Temperature ---
with col2:
    st.subheader("Temperature Time Series")
    
    timeframe = st.selectbox("Select Timeframe", options=["Last Minute", "Last Hour", "Last Week"], index=1)
    time_map = {
        "Last Minute": "-1m",
        "Last Hour": "-1h",
        "Last Week": "-7d"
    }
    
    query_temp = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: {time_map[timeframe]})
      |> filter(fn: (r) => r["_measurement"] == "temperature")
      |> filter(fn: (r) => r["_field"] == "temperature_C")
    '''
    
    try:
        tables_temp = query_api.query(query_temp)
        
        temp_data = []
        for table in tables_temp:
            for record in table.records:
                temp_data.append({
                    "Time": record.get_time(),
                    "Temperature (°C)": record.get_value(),
                    "Dispenser": record.values.get("dispenser", "Unknown")
                })
                
        df_temp = pd.DataFrame(temp_data)
        
        if not df_temp.empty:
            df_temp = df_temp.sort_values("Time")
            fig_line = px.line(df_temp, x="Time", y="Temperature (°C)", color="Dispenser",
                               title="Dispenser Temperature Over Time", markers=True,
                               color_discrete_map={'red': 'red', 'blue': 'blue', 'green': 'green'})
            st.plotly_chart(fig_line, width="stretch")
        else:
            st.info(f"No temperature data available for {timeframe.lower()}.")
    except Exception as e:
        st.error(f"Error fetching temperature data: {e}")

# Display raw CSV data as fallback (Optional but good for checking CSV works)
st.markdown("---")
st.subheader("Raw Data Preview (from CSV)")
try:
    csv_path = "../database/data.csv"
    import os
    # Find the actual path
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'data.csv')
    if os.path.exists(csv_path):
        df_csv = pd.read_csv(csv_path).tail(10) # Show last 10 rows
        st.dataframe(df_csv)
    else:
        st.info("data.csv not created yet.")
except Exception as e:
    st.warning(f"Could not load CSV: {e}")

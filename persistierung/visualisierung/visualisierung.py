import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import datetime

# Setup Page
st.set_page_config(page_title="Learning Factory Dashboard", layout="wide")

# Custom CSS for Grafana-like layout
st.markdown("""
<style>
.kpi-card {
    background-color: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
    border: 1px solid #e0e0e0;
    height: 100%;
}
.kpi-title {
    font-size: 0.9rem;
    color: #6c757d;
    margin-bottom: 5px;
    font-weight: 600;
}
.kpi-value {
    font-size: 2.5rem;
    font-weight: bold;
}
.val-green { color: #28a745; }
.val-blue { color: #007bff; }
.val-red { color: #dc3545; }
.val-yellow { color: #ffc107; }
.val-purple { color: #6f42c1; }
.status-box {
    font-size: 1.8rem;
    font-weight: bold;
    color: white;
    padding: 10px;
    border-radius: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 80px;
    margin-top: 10px;
}
.bg-green { background-color: #5cb85c; }
.bg-red { background-color: #d9534f; }
</style>
""", unsafe_allow_html=True)

# Autorefresh (approx every 5 seconds)
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, limit=None, key="data_refresh")
except ImportError:
    pass

# Data loading function
@st.cache_data(ttl=5)
def load_data():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'data.csv')
    df = pd.DataFrame()
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if 'timestamp' in df.columns:
                df['Time'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            st.warning(f"Error loading CSV: {e}")
            
    return df

df = load_data()

bottle_agg = pd.DataFrame()

# Process KPI data
if not df.empty:
    # 1. Anlagenstatus
    last_update = df['Time'].max()
    now = pd.Timestamp.now(tz=last_update.tz) if pd.notnull(last_update) and last_update.tz is not None else pd.Timestamp.now()
    is_running = (now - last_update).total_seconds() < 60 if pd.notnull(last_update) else False
    status_text = "LÄUFT" if is_running else "GESTOPPT"
    status_class = "bg-green" if is_running else "bg-red"
    
    # Process bottles
    if 'bottle' in df.columns:
        bottle_agg = df.dropna(subset=['bottle']).groupby('bottle').agg({
            'final_weight': 'last',
            'is_cracked': 'max', # 1 if cracked ever true
            'Time': 'max'
        }).reset_index()
        
        produziert = len(bottle_agg.dropna(subset=['final_weight']))
        nio = len(bottle_agg[bottle_agg['is_cracked'] == 1])
        io = produziert - nio
        ausschussquote = (nio / produziert * 100) if produziert > 0 else 0.0
        
        # Durchsatz (Bottles per minute in last 5 mins)
        five_mins_ago = now - pd.Timedelta(minutes=5)
        recent_bottles = len(bottle_agg[bottle_agg['Time'] > five_mins_ago])
        durchsatz = recent_bottles / 5.0
    else:
        produziert = 0
        io = 0
        nio = 0
        ausschussquote = 0.0
        durchsatz = 0.0
else:
    status_text = "GESTOPPT"
    status_class = "bg-red"
    produziert = 0
    io = 0
    nio = 0
    ausschussquote = 0.0
    durchsatz = 0.0

# Layout Row 1: KPIs
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Anlagenstatus</div><div class="status-box {status_class}">{status_text}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Produziert</div><div class="kpi-value val-blue">{produziert}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">i.O.</div><div class="kpi-value val-green">{io}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">n.i.O.</div><div class="kpi-value val-red">{nio}</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Ausschussquote</div><div class="kpi-value val-yellow">{ausschussquote:.1f}%</div></div>', unsafe_allow_html=True)
with col6:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Durchsatz (Flaschen/min)</div><div class="kpi-value val-purple">{durchsatz:.1f}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Layout Row 2: Füllstand & Temperatur
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown('<div class="kpi-title">Füllstand je Dispenser (g)</div>', unsafe_allow_html=True)
    if not df.empty and 'fill_level_grams' in df.columns and 'dispenser' in df.columns:
        df_fill = df.dropna(subset=['fill_level_grams', 'dispenser'])
        if not df_fill.empty:
            df_fill = df_fill.sort_values('Time')
            fig_fill = px.line(df_fill, x='Time', y='fill_level_grams', color='dispenser', 
                               color_discrete_map={'red':'red', 'blue':'blue', 'green':'green'})
            fig_fill.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_title="", yaxis_title="g")
            st.plotly_chart(fig_fill, use_container_width=True)
        else:
            st.info("Keine Füllstandsdaten")
    else:
        st.info("Keine Daten")

with r2c2:
    st.markdown('<div class="kpi-title">Abfüll-Temperatur (Ø der 3 Dispenser)</div>', unsafe_allow_html=True)
    if not df.empty and 'temperature_C' in df.columns:
        df_temp = df.dropna(subset=['temperature_C'])
        if not df_temp.empty:
            # Average temperature across all dispensers over time
            df_temp_agg = df_temp.set_index('Time').resample('10s')['temperature_C'].mean().reset_index()
            fig_temp = px.line(df_temp_agg, x='Time', y='temperature_C')
            fig_temp.update_traces(line_color='green')
            fig_temp.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_title="", yaxis_title="°C")
            st.plotly_chart(fig_temp, use_container_width=True)
        else:
            st.info("Keine Temperaturdaten")
    else:
        st.info("Keine Daten")

st.markdown("<br>", unsafe_allow_html=True)

# Layout Row 3: Endgewicht & Vibration
r3c1, r3c2 = st.columns(2)

with r3c1:
    st.markdown('<div class="kpi-title">Endgewicht je Flasche (g) - SPC mit Kontrollgrenzen</div>', unsafe_allow_html=True)
    if not df.empty and not bottle_agg.empty and 'final_weight' in bottle_agg.columns:
        df_weight = bottle_agg.dropna(subset=['final_weight']).sort_values('Time')
        if not df_weight.empty:
            fig_weight = px.scatter(df_weight, x='Time', y='final_weight')
            # Determine colors based on Dispenser if available, else green
            # (We would need to merge dispenser info back, keeping it simple with green dots like image)
            fig_weight.update_traces(marker=dict(color='green', size=6))
            
            # Control Limits
            fig_weight.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="+3σ")
            fig_weight.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="-3σ")
            fig_weight.add_hline(y=10, line_color="blue", annotation_text="Mittel")
            
            fig_weight.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_title="", yaxis_title="g", yaxis_range=[-10, 60])
            st.plotly_chart(fig_weight, use_container_width=True)
        else:
            st.info("Keine Gewichtsdaten")
    else:
        st.info("Keine Daten")

with r3c2:
    st.markdown('<div class="kpi-title">Abfüll-Vibration je Dispenser (vibration_index)</div>', unsafe_allow_html=True)
    if not df.empty and 'vibration_index' in df.columns and 'dispenser' in df.columns:
        df_vib = df.dropna(subset=['vibration_index', 'dispenser'])
        if not df_vib.empty:
            df_vib = df_vib.sort_values('Time')
            fig_vib = px.line(df_vib, x='Time', y='vibration_index', color='dispenser',
                              color_discrete_map={'red':'red', 'blue':'blue', 'green':'green'})
            fig_vib.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_vib, use_container_width=True)
        else:
            st.info("Keine Vibrationsdaten")
    else:
        st.info("Keine Daten")

st.markdown("<br>", unsafe_allow_html=True)

# Layout Row 4: Produktionslog Table
st.markdown('<div class="kpi-title">Produktionslog — letzte 20 Flaschen</div>', unsafe_allow_html=True)

if not df.empty and not bottle_agg.empty:
    log_df = bottle_agg.sort_values('Time', ascending=False).head(20).copy()
    
    # Format the table
    log_df['Zeit'] = log_df['Time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    log_df['Flasche'] = log_df['bottle']
    log_df['Endgewicht (g)'] = log_df['final_weight'].round(1)
    
    # Determine Status
    def get_status(row):
        return "n.i.O." if row['is_cracked'] == 1 else "i.O."
    
    log_df['Status'] = log_df.apply(get_status, axis=1)
    
    display_df = log_df[['Zeit', 'Flasche', 'Endgewicht (g)', 'Status']]
    
    # Color coding using map for Pandas >= 2.1.0 or applymap
    def color_status(val):
        color = '#d9534f' if val == 'n.i.O.' else '#5cb85c'
        return f'background-color: {color}; color: white; font-weight: bold;'
    
    try:
        # For newer pandas versions
        styled_df = display_df.style.map(color_status, subset=['Status'])
    except AttributeError:
        # Fallback for older pandas versions
        styled_df = display_df.style.applymap(color_status, subset=['Status'])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.info("Keine Daten für das Log vorhanden.")

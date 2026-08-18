import streamlit as st
import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide")
st.title("📊 Smart Surveillance Dashboard")

DB_PATH = "logs/analytics.db"
LOG_FOLDER = "logs"

@st.cache_data
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=["time", "camera_id", "in_count", "out_count", "posture", "alert"])
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM traffic_logs", conn)
    conn.close()
    if not df.empty:
        df['time'] = pd.to_datetime(df['time'])
    return df

df = load_data()

if df.empty:
    st.info("No data available. Run the camera pipeline to generate logs.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
camera_options = df['camera_id'].unique().tolist()
selected_camera = st.sidebar.multiselect("Select Camera(s)", camera_options, default=camera_options)

posture_options = df['posture'].unique().tolist()
selected_posture = st.sidebar.multiselect("Select Posture(s)", posture_options, default=posture_options)

alert_options = [a for a in df['alert'].dropna().unique().tolist() if a]
selected_alert = st.sidebar.multiselect("Select Alert(s)", alert_options, default=alert_options)

min_time = df['time'].min()
max_time = df['time'].max()
start_time, end_time = st.sidebar.slider("Select Time Range", min_value=min_time, max_value=max_time,
                                         value=(min_time, max_time))

# Apply filters
filtered_df = df[
    (df['camera_id'].isin(selected_camera)) &
    (df['posture'].isin(selected_posture)) &
    (df['alert'].isin(selected_alert) | df['alert'].isna()) &
    (df['time'].between(start_time, end_time))
]

st.subheader("📋 Filtered Logs")
st.dataframe(filtered_df.sort_values(by='time', ascending=False), use_container_width=True)

# Charts: IN/OUT trends
st.subheader("📈 People Flow Trends")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### People IN Count")
    in_trend = filtered_df.groupby('time')['in_count'].sum().reset_index()
    st.line_chart(in_trend.rename(columns={"in_count": "People IN"}).set_index('time'))

with col2:
    st.markdown("#### People OUT Count")
    out_trend = filtered_df.groupby('time')['out_count'].sum().reset_index()
    st.line_chart(out_trend.rename(columns={"out_count": "People OUT"}).set_index('time'))

# Alerts trend
st.subheader("🚨 Alert Frequency")
alert_series = filtered_df['alert'].dropna().str.split().explode()
alert_counts = alert_series.value_counts()
st.bar_chart(alert_counts)

# Zone counts
st.subheader("🔥 Zone Occupancy")
for cam_id in selected_camera:
    zone_csv = os.path.join(LOG_FOLDER, f"zone_counts_{cam_id}.csv")

    st.markdown(f"#### {cam_id}")

    if os.path.exists(zone_csv):
        zone_df = pd.read_csv(zone_csv)
        zone_df[['Row', 'Col']] = zone_df['Zone(Row,Col)'].str.strip('()').str.split(',', expand=True).astype(int)
        zone_matrix = zone_df.pivot(index='Row', columns='Col', values='Count')

        st.markdown("##### Zone Occupancy Matrix")
        fig, ax = plt.subplots()
        sns.heatmap(zone_matrix, annot=True, fmt='d', cmap="YlOrRd", ax=ax)
        st.pyplot(fig)

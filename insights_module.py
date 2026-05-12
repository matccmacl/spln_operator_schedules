import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# Import your secret config
try:
    from config import SCHEDULES_SHEET_URL, SCHEDULES_WS
except ImportError:
    st.error("config.py not found or missing variables.")
    SCHEDULES_SHEET_URL = None
    SCHEDULES_WS = "spln_schedules" 

@st.cache_data(ttl=3600, show_spinner="Syncing with Master Log...")
def load_master_data(spreadsheet_url, worksheet_name):
    """
    Loads master flight data and maps the final finalized headers to dashboard schema.
    """
    if not spreadsheet_url:
        return pd.DataFrame()
        
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(
            spreadsheet=spreadsheet_url, 
            worksheet=worksheet_name,
            ttl=0 
        )
        
        if df.empty:
            return df

        # --- FINALIZED COLUMN MAPPING ---
        # Maps your exact Google Sheet headers to internal Dashboard logic
        column_map = {
            'DATE-TIME': 'DATE TIME UTC',
            'DT.LOCAL': 'DATE TIME LOCAL',
            'FLT NO': 'FLT NUMBER',
            'CALL SIGN': 'REG',
            'MOVEMENT': 'DIRECTION'
        }
        
        # Rename columns to match internal standard
        df = df.rename(columns=column_map)

        # --- DATA CLEANING & OPTIMIZATION ---
        # 1. Parse Primary UTC Timestamp
        if 'DATE TIME UTC' in df.columns:
            df['DATE TIME UTC'] = pd.to_datetime(df['DATE TIME UTC'], errors='coerce')
        
        # 2. Normalize Direction (TAKEOFF/LANDING)
        if 'DIRECTION' in df.columns:
            # Ensure it's uppercase string for consistent logic across all operators
            df['DIRECTION'] = df['DIRECTION'].astype(str).str.upper().str.strip()
            df['DIRECTION'] = df['DIRECTION'].astype('category')

        # 3. Memory Optimization for large datasets
        if 'AIRLINE' in df.columns:
            df['AIRLINE'] = df['AIRLINE'].astype('category')
            
        return df
        
    except Exception as e:
        st.error(f"Error loading worksheet '{worksheet_name}': {e}")
        return pd.DataFrame()

def generate_performance_visuals(df):
    """
    Renders the high-performance dashboard using standardized columns.
    """
    if df is None or df.empty:
        st.warning("The database appears to be empty.")
        return

    # Critical Column Check
    if 'DATE TIME UTC' not in df.columns:
        st.error("Missing critical column: 'DATE-TIME' (mapped to 'DATE TIME UTC')")
        st.info(f"Available columns: {list(df.columns)}")
        return

    # Drop invalid rows
    df = df.dropna(subset=['DATE TIME UTC'])

    # --- FEATURE ENGINEERING ---
    df['Month'] = df['DATE TIME UTC'].dt.strftime('%b %Y')
    df['Day'] = df['DATE TIME UTC'].dt.date
    df['Hour'] = df['DATE TIME UTC'].dt.hour
    df['Minute_Bin'] = df['DATE TIME UTC'].dt.floor('15min').dt.strftime('%H:%M')

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Dashboard Controls")
    
    # Chronological sort for months
    months = sorted(df['Month'].unique(), key=lambda x: pd.to_datetime(x))
    selected_month = st.sidebar.selectbox("Select Month", months, index=len(months)-1)
    
    month_df = df[df['Month'] == selected_month]
    days = sorted(month_df['Day'].unique())
    selected_day = st.sidebar.selectbox("Select Day", ["All Days"] + list(days), index=len(days))

    # Apply Day filtering
    plot_df = month_df if selected_day == "All Days" else month_df[month_df['Day'] == selected_day]
    view_label = f"{selected_month} (Summary)" if selected_day == "All Days" else selected_day.strftime('%d %b %Y')

    # --- KPI DISPLAY ---
    st.header(f"Seaplane Ops: {view_label}")
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Movements", f"{len(plot_df):,}", border=True)
    
    if 'DIRECTION' in plot_df.columns:
        tos = len(plot_df[plot_df['DIRECTION'] == 'TAKEOFF'])
        lds = len(plot_df[plot_df['DIRECTION'] == 'LANDING'])
        k2.metric("Takeoffs", f"{tos:,}", border=True)
        k3.metric("Landings", f"{lds:,}", border=True)

    # --- OPERATOR GRID ---
    #st.divider()
    st.subheader("Operator Volume")
    operators = plot_df['AIRLINE'].unique().tolist()
    op_cols = st.columns(max(len(operators), 1))
    
    for i, op in enumerate(operators):
        op_df = plot_df[plot_df['AIRLINE'] == op]
        with op_cols[i]:
            st.metric(f"{op}", f"{len(op_df):,}", border=True)

    # --- CHARTS ---
    st.divider()
    tab_h, tab_m = st.tabs(["🕒 Hourly Distribution", "📊 Monthly Trends"])
    
    with tab_h:
        st.subheader("Movements by Hour (UTC)")
        h_counts = plot_df.groupby(['Hour', 'DIRECTION'], observed=True).size().reset_index(name='Count')
        fig_h = px.bar(h_counts, x='Hour', y='Count', color='DIRECTION', barmode='group',
                       color_discrete_map={'TAKEOFF': '#007bff', 'LANDING': '#28a745'},
                       labels={'Hour': 'Hour (UTC)', 'Count': 'Movements'})
        fig_h.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
        st.plotly_chart(fig_h, use_container_width=True)

    with tab_m:
        st.subheader("Historical Volume")
        m_counts = df.groupby(['Month', 'DIRECTION'], observed=True).size().reset_index(name='Count')
        fig_m = px.bar(m_counts, x='Month', y='Count', color='DIRECTION', barmode='group', height=400)
        st.plotly_chart(fig_m, use_container_width=True)

    with st.expander("🔍 View Table Data"):
        st.dataframe(plot_df, use_container_width=True)
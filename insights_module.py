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
    df['Minute'] = df['DATE TIME UTC'].dt.minute
    df['Minute_Bin'] = df['DATE TIME UTC'].dt.floor('15min').dt.strftime('%H:%M')

    # --- PAGE TABS ---
    tab_today, tab_history = st.tabs([":material/today: Today's Operations", ":material/history: Historical Analysis"])

    # Define today's data (actual today UTC)
    actual_today = pd.Timestamp.now(tz='UTC').date()
    today_df = df[df['Day'] == actual_today]
    
    with tab_today:
        st.header(f"Seaplane Ops: {actual_today.strftime('%d %b %Y')}")
        if today_df.empty:
            st.info(f"No movements recorded yet for today ({actual_today.strftime('%d %b %Y')}).")

        t_cols = st.columns([1, 2])

        with t_cols[0]:        
            # --- TODAY'S KPIs ---
            with st.container(border=True):
                with st.container(border=True):
                    st.metric("Total Movements", f"{len(today_df):,}")
                with st.container(horizontal=True):
                    st.metric(":material/flight_takeoff: Takeoffs", f"{len(today_df[today_df['DIRECTION'] == 'TAKEOFF']):,}", border=True)
                    st.metric(":material/flight_land: Landings", f"{len(today_df[today_df['DIRECTION'] == 'LANDING']):,}", border=True)
            
            # --- OPERATOR GRID ---
            st.markdown("###### Operator Volume".upper())
            # Sort operators by volume (descending)
            op_counts = today_df['AIRLINE'].value_counts()
            operators = op_counts[op_counts > 0].index.tolist()
            
            for i in range(0, len(operators), 2):
                grid_cols = st.columns(2)
                for j in range(2):
                    if i + j < len(operators):
                        op = operators[i + j]
                        op_df = today_df[today_df['AIRLINE'] == op]
                        with grid_cols[j]:
                            with st.container(border=True):
                                st.write(f"**{op}**")
                                
                                # Internal breakdown for the operator
                                op_to = len(op_df[op_df['DIRECTION'] == 'TAKEOFF'])
                                op_ld = len(op_df[op_df['DIRECTION'] == 'LANDING'])
                                
                                with st.container(horizontal=True, horizontal_alignment="right"):
                                    st.metric("Total", f"{len(op_df):,}", border=True )
                                with st.container(horizontal=True, horizontal_alignment="right"):
                                    st.metric(":material/flight_takeoff: TAKEOFFS", f"{op_to:,}", border=True)
                                    st.metric(":material/flight_land: LANDINGS", f"{op_ld:,}", border=True)
        
        with t_cols[1]:
            # --- CHARTS ---
            with st.container(border=True):
                st.subheader("Movements by Hour (UTC)")
                h_counts = today_df.groupby(['Hour', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                fig_h = px.bar(h_counts, x='Hour', y='Count', color='DIRECTION', barmode='group',
                            text='Count',
                            color_discrete_map={'TAKEOFF': '#2563eb', 'LANDING': '#60a8fb'},
                            labels={'Hour': 'Hour (UTC)', 'Count': 'Movements'})
                fig_h.update_traces(textposition='outside')
                fig_h.update_layout(
                    xaxis=dict(tickmode='linear', tick0=0, dtick=1),
                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
                )
                st.plotly_chart(fig_h, use_container_width=True)

                # --- MINUTE DRILLDOWN ---
                st.divider()
                st.subheader("Minute-by-Minute Drilldown")
                
                # Local filter for minute analysis (using clickable pills)
                hour_options = sorted(today_df['Hour'].unique().tolist())
                selected_drill_hour = st.pills(
                    "Select Hour to Analyze", 
                    options=hour_options,
                    format_func=lambda h: f"{h:02d}:00",
                    selection_mode="single"
                )

                if selected_drill_hour is not None:
                    st.markdown(f"###### Movements for {selected_drill_hour:02d}:00 UTC")
                    min_df = today_df[today_df['Hour'] == selected_drill_hour]
                    
                    if not min_df.empty:
                        m_counts = min_df.groupby(['Minute', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                        fig_min = px.bar(m_counts, x='Minute', y='Count', color='DIRECTION', barmode='group',
                                       text='Count',
                                       color_discrete_map={'TAKEOFF': '#2563eb', 'LANDING': '#60a8fb'},
                                       labels={'Minute': 'Minute', 'Count': 'Movements'})
                        fig_min.update_traces(textposition='outside')
                        # Force x-axis to show 0-59
                        fig_min.update_layout(
                            xaxis=dict(
                                tickmode='linear', 
                                tick0=0, 
                                dtick=5, 
                                range=[-0.5, 59.5]
                            ),
                            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None),
                            margin=dict(l=20, r=20, t=20, b=20),
                            height=350
                        )
                        st.plotly_chart(fig_min, use_container_width=True)
                    else:
                        st.info("No data available for the selected hour.")
                else:
                    st.info("Select an hour above to view the minute-by-minute distribution.")

                # --- TODAY'S MOVEMENT LOG ---
                st.divider()
                st.subheader("Daily Movement Log")
                
                # Filters for the table
                log_flt_cols = st.columns(3)
                with log_flt_cols[0]:
                    f_op = st.multiselect("Operator", options=sorted(today_df['AIRLINE'].unique().tolist()), key="log_op")
                with log_flt_cols[1]:
                    f_hr = st.multiselect("Hour (UTC)", options=sorted(today_df['Hour'].unique().tolist()), key="log_hr")
                with log_flt_cols[2]:
                    f_dir = st.multiselect("Direction", options=sorted(today_df['DIRECTION'].unique().tolist()), key="log_dir")
                
                # Filtering logic
                log_df = today_df.copy()
                if f_op:
                    log_df = log_df[log_df['AIRLINE'].isin(f_op)]
                if f_hr:
                    log_df = log_df[log_df['Hour'].isin(f_hr)]
                if f_dir:
                    log_df = log_df[log_df['DIRECTION'].isin(f_dir)]
                
                st.dataframe(log_df, use_container_width=True, hide_index=True)

    with tab_history:
        st.header("Historical Analysis")
        
        # Monthly Trends
        with st.container(border=True):
            st.subheader("Monthly Volume Trends")
            m_counts = df.groupby(['Month', 'DIRECTION'], observed=True).size().reset_index(name='Count')
            # Sort chronologically
            m_counts['Month_DT'] = pd.to_datetime(m_counts['Month'], format='%b %Y')
            m_counts = m_counts.sort_values('Month_DT')
            
            fig_m = px.bar(m_counts, x='Month', y='Count', color='DIRECTION', barmode='group', text='Count', height=400)
            fig_m.update_traces(textposition='outside')
            fig_m.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, title=None))
            st.plotly_chart(fig_m, use_container_width=True)

        # Full Data Table
        with st.expander("🔍 View Full Data Table"):
            st.dataframe(df, use_container_width=True)
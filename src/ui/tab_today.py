import streamlit as st
import pandas as pd
from src.ui.components import render_operator_metrics
from src.analytics import (
    build_direction_donut,
    build_airline_donut,
    build_hourly_movements,
    build_minute_drilldown
)

def render_tab_today(df: pd.DataFrame):
    """
    Renders Today's Operations view using high-performance visual widgets.
    """
    # Define today's data (actual today UTC)
    actual_today = pd.Timestamp.now(tz='UTC').date()
    today_df = df[df['Day'] == actual_today]
    
    st.header(f"Seaplane Ops: {actual_today.strftime('%d %b %Y')}")
    if today_df.empty:
        st.info(f"No movements recorded yet for today ({actual_today.strftime('%d %b %Y')}).")

    t_cols = st.columns([1, 2])

    with t_cols[0]:        
        render_operator_metrics(today_df)
    
    with t_cols[1]:
        # --- DONUT CHARTS ---
        donut_cols = st.columns(2)
        with donut_cols[0]:
            with st.container(border=True):
                st.subheader("By Direction")
                fig_dir = build_direction_donut(today_df)
                st.plotly_chart(fig_dir, use_container_width=True)
        with donut_cols[1]:
            with st.container(border=True):
                st.subheader("By Airline")
                fig_al = build_airline_donut(today_df)
                st.plotly_chart(fig_al, use_container_width=True)

        # --- CHARTS ---
        with st.container(border=True):
            _hc1, _hc2 = st.columns([4, 1])
            with _hc1:
                st.subheader("Movements by Hour (UTC)")
            with _hc2:
                h_by_dir = st.toggle("By Direction", key="tog_hourly")
            
            fig_h = build_hourly_movements(today_df, by_direction=h_by_dir)
            st.plotly_chart(fig_h, use_container_width=True)

        # --- MINUTE DRILLDOWN ---
        st.divider()
        st.subheader("Minute-by-Minute Drilldown")
        
        # Local filter for minute analysis (using clickable pills)
        hour_options = sorted([int(h) for h in today_df['Hour'].dropna().unique()])
        selected_drill_hour = st.pills(
            "Select Hour to Analyze", 
            options=hour_options,
            format_func=lambda h: f"{h:02d}:00",
            selection_mode="single",
            key="pills_drill_hour"
        )

        if selected_drill_hour is not None:
            st.markdown(f"###### Movements for {selected_drill_hour:02d}:00 UTC")
            min_df = today_df[today_df['Hour'] == selected_drill_hour]
            
            if not min_df.empty:
                fig_min = build_minute_drilldown(min_df)
                st.plotly_chart(fig_min, use_container_width=True)
            else:
                st.info(":material/info: No data available for the selected hour.")
        else:
            st.info(":material/lightbulb: Select an hour above to view the minute-by-minute distribution.")

        # --- TODAY'S MOVEMENT LOG ---
        st.divider()
        st.subheader("Daily Movement Log")
        
        # Filters for the table
        log_flt_cols = st.columns(3)
        with log_flt_cols[0]:
            f_op = st.multiselect("Operator", options=sorted(today_df['AIRLINE'].unique().tolist()), key="log_op")
        with log_flt_cols[1]:
            today_hour_options = sorted([int(h) for h in today_df['Hour'].dropna().unique()])
            f_hr = st.multiselect("Hour (UTC)", options=today_hour_options, format_func=lambda h: f"{h:02d}:00", key="log_hr")
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

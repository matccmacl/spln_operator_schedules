import streamlit as st
import pandas as pd
from src.ui.components import render_operator_metrics
from src.analytics.metrics import calculate_yoy_monthly_comparison
from src.analytics import (
    build_direction_donut,
    build_airline_bar,
    build_yearly_trends,
    build_monthly_trends,
    build_yoy_comparison,
    build_daily_volume,
    build_historical_hourly
)

def render_tab_history(df: pd.DataFrame):
    """
    Renders the Historical Analysis tab using high-performance visual widgets.
    """
    st.header("Historical Analysis")
    
    # --- GLOBAL FILTERS ---
    f_cols = st.columns(2)
    with f_cols[0]:
        y_options = sorted(df['Year'].unique().tolist(), reverse=True)
        selected_years = st.multiselect("Select Years", options=y_options, default=[])
    with f_cols[1]:
        m_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
        available_months = [m for m in m_names if m in df['MonthName'].unique()]
        selected_months = st.multiselect("Select Months", options=available_months, default=[])
    
    # Data filtering based on selection
    hist_df = df.copy()
    if selected_years:
        hist_df = hist_df[hist_df['Year'].isin(selected_years)]
    if selected_months:
        hist_df = hist_df[hist_df['MonthName'].isin(selected_months)]

    # --- Day picker (single year & single month only) ---
    display_df = hist_df
    if len(selected_months) == 1 and len(selected_years) == 1:
        available_days = sorted(hist_df['Day'].dropna().unique())
        if available_days:
            min_day = pd.Timestamp(available_days[0]).date()
            max_day = pd.Timestamp(available_days[-1]).date()
            selected_day = st.date_input(
                ":material/schedule: Select a day for hourly drilldown (and to filter metrics & table):",
                value=min_day,
                min_value=min_day,
                max_value=max_day,
                key="sel_hourly_day"
            )
            display_df = hist_df[hist_df['Day'].apply(lambda d: pd.Timestamp(d).date()) == selected_day].copy()

    h_cols = st.columns([1, 2])

    with h_cols[0]:

        with st.container(border=True):
            st.subheader("Movements by Direction")
            fig_dir = build_direction_donut(display_df)
            st.plotly_chart(fig_dir, use_container_width=True)
        
        # Bar charts for Individual Airline Movements
        with st.container(border=True):
            st.subheader("Movements by Airline")
            fig_airline = build_airline_bar(display_df)
            st.plotly_chart(fig_airline, use_container_width=True)
        
        render_operator_metrics(display_df)
        st.divider()
        
        
    with h_cols[1]:
        with st.container(height=1000, border=False):
            # Yearly Volume Trends - Hide if months are selected
            if not selected_months:
                with st.container(border=True):
                    _yc1, _yc2 = st.columns([4, 1])
                    with _yc1:
                        st.subheader("Yearly Volume Trends")
                    with _yc2:
                        y_by_dir = st.toggle("By Direction", key="tog_yearly")
                    
                    fig_y = build_yearly_trends(hist_df, by_direction=y_by_dir)
                    st.plotly_chart(fig_y, use_container_width=True)

            # Monthly Trends
            with st.container(border=True):
                _mc1, _mc2 = st.columns([4, 1])
                with _mc1:
                    st.subheader("Monthly Volume Trends")
                with _mc2:
                    m_by_dir = st.toggle("By Direction", key="tog_monthly")
                
                fig_m = build_monthly_trends(hist_df, by_direction=m_by_dir)
                st.plotly_chart(fig_m, use_container_width=True)

            # Year-over-Year Monthly Comparison
            with st.container(border=True):
                st.subheader("Year-over-Year Monthly Comparison")
                if hist_df.empty:
                    st.info("No data available for the selected filters.")
                else:
                    m_compare = calculate_yoy_monthly_comparison(hist_df)
                    if m_compare.empty:
                        st.info("Insufficient data to perform YoY Comparison.")
                    else:
                        fig_l = build_yoy_comparison(m_compare)
                        st.plotly_chart(fig_l, use_container_width=True)

            # Daily Volume Drilldown - Only show if exactly one month and one year are selected
            if len(selected_months) == 1 and len(selected_years) == 1:
                with st.container(border=True):
                    _dc1, _dc2 = st.columns([4, 1])
                    with _dc1:
                        st.subheader(f"Daily Volume Distribution: {selected_months[0]} {selected_years[0]}")
                    with _dc2:
                        d_by_dir = st.toggle("By Direction", key="tog_daily")
                    
                    fig_d = build_daily_volume(hist_df, by_direction=d_by_dir)
                    st.plotly_chart(fig_d, use_container_width=True)

                    # --- Hourly Drilldown ---
                    st.divider()
                    _hc1, _hc2 = st.columns([4, 1])
                    with _hc1:
                        st.subheader(":material/schedule: Hourly Movement Drilldown")
                    with _hc2:
                        h_by_dir = st.toggle("By Direction", key="tog_hourly_hist")

                    day_df = display_df.copy()
                    day_df['Hour'] = day_df['DATE TIME LOCAL'].dt.hour

                    if not day_df.empty:
                        fig_h = build_historical_hourly(day_df, by_direction=h_by_dir)
                        st.plotly_chart(fig_h, use_container_width=True)
                    else:
                        st.warning("No data available for the selected day.")

            else:
                st.info(":material/lightbulb: Select a **single year** and a **single month** to view the Daily Volume Distribution and Hourly Drilldown.")
    
            # Full Data Table
            with st.expander(":material/search: View Full Data Table"):
                flt_cols = st.columns(3)
                with flt_cols[0]:
                    f_op = st.multiselect("Operator", options=sorted(display_df['AIRLINE'].dropna().unique().tolist()), key="hist_log_op")
                with flt_cols[1]:
                    hist_hour_options = sorted([int(h) for h in display_df['Hour'].dropna().unique()])
                    f_hr = st.multiselect("Hour (Local)", options=hist_hour_options, format_func=lambda h: f"{h:02d}:00", key="hist_log_hr")
                with flt_cols[2]:
                    f_dir = st.multiselect("Direction", options=sorted(display_df['DIRECTION'].dropna().unique().tolist()), key="hist_log_dir")

                log_df = display_df.copy()
                if f_op:
                    log_df = log_df[log_df['AIRLINE'].isin(f_op)]
                if f_hr:
                    log_df = log_df[log_df['Hour'].isin(f_hr)]
                if f_dir:
                    log_df = log_df[log_df['DIRECTION'].isin(f_dir)]

                st.dataframe(log_df, use_container_width=True, hide_index=True)

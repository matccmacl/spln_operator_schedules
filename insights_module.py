import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import database # Local SQLite module

# ---------------------------------------------------------------------------
# CHART COLOR PALETTE
# ---------------------------------------------------------------------------
C_TAKEOFF    = '#155DFC'
C_LANDING    = '#8EC5FF'
C_DONUT_1    = '#1447E6'   # Direction donut – primary segment
C_DONUT_2    = '#2B7FFF'   # Direction donut – secondary segment
C_BAR        = '#1447E6'   # Single-color bar charts (direction toggle off)
C_AIRLINE_1  = '#1447E6'
C_AIRLINE_2  = '#155DFC'
C_AIRLINE_3  = '#2B7FFF'
C_AIRLINE_4  = '#8EC5FF'

DIR_COLOR_MAP     = {'TAKEOFF': C_TAKEOFF, 'LANDING': C_LANDING}
AIRLINE_PALETTE   = [C_AIRLINE_1, C_AIRLINE_2, C_AIRLINE_3, C_AIRLINE_4]

@st.cache_data(ttl=60, show_spinner="Syncing with Local Database...")
def load_master_data():
    """
    Loads master flight data from SQLite (High Performance).
    """
    try:
        # 1. LOAD FROM SQLITE
        df = database.get_all_movements()
        reg_df = database.get_all_registrations()
        
        if df.empty:
            return df

        # 2. ENFORCE RELATIONSHIP (JOIN)
        # We join on 'REG' to bring in SPECIES, MTOW, etc.
        if not reg_df.empty:
            # Ensure REG columns are strings and stripped for the join
            df['REG'] = df['REG'].astype(str).str.strip().str.upper()
            reg_df['REG'] = reg_df['REG'].astype(str).str.strip().str.upper()
            
            # Left join: keep all movements, add registration details where available
            df = df.merge(reg_df[['REG', 'SPECIES', 'MTOW', 'AC TYPE']], on='REG', how='left')

        # --- DATA CLEANING & OPTIMIZATION ---
        # 1. Parse Timestamps
        for col in ['DATE TIME UTC', 'DATE TIME LOCAL']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # 2. Normalize Direction
        if 'DIRECTION' in df.columns:
            df['DIRECTION'] = df['DIRECTION'].astype(str).str.upper().str.strip()
            df = df[df['DIRECTION'].isin(['TAKEOFF', 'LANDING'])]
            df['DIRECTION'] = df['DIRECTION'].astype('category')

        # 3. Memory Optimization
        for col in ['AIRLINE', 'REG', 'FROM', 'TO']:
            if col in df.columns:
                df[col] = df[col].astype(str).astype('category')
            
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def _render_operator_metrics(data_df):
    """
    Renders KPIs and Operator Volume grid for a given dataframe.
    """
    # --- KPIs ---
    with st.container(border=True):
        with st.container(border=True):
            st.metric("Total Movements", f"{len(data_df):,}")
        with st.container(horizontal=True):
            st.metric(":material/flight_takeoff: Takeoffs", f"{len(data_df[data_df['DIRECTION'] == 'TAKEOFF']):,}", border=True)
            st.metric(":material/flight_land: Landings", f"{len(data_df[data_df['DIRECTION'] == 'LANDING']):,}", border=True)

    # --- OPERATOR GRID ---
    st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )
    st.markdown("###### Operator Volume".upper())
    op_counts = data_df['AIRLINE'].value_counts()
    operators = op_counts[op_counts > 0].index.tolist()

    for i in range(0, len(operators), 2):
        grid_cols = st.columns(2)
        for j in range(2):
            if i + j < len(operators):
                op = operators[i + j]
                op_df = data_df[data_df['AIRLINE'] == op]
                op_to = len(op_df[op_df['DIRECTION'] == 'TAKEOFF'])
                op_ld = len(op_df[op_df['DIRECTION'] == 'LANDING'])
                with grid_cols[j]:
                    with st.container(border=True):
                        st.write(f"**{op}**")
                        with st.container(horizontal=True, horizontal_alignment="right"):
                            st.metric("Total", f"{len(op_df):,}", border=True)
                        with st.container(horizontal=True, horizontal_alignment="right"):
                            st.metric(":material/flight_takeoff: Takeoffs", f"{op_to:,}", border=True)
                            st.metric(":material/flight_land: Landings", f"{op_ld:,}", border=True)


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
    df['MonthName'] = df['DATE TIME UTC'].dt.strftime('%B')
    df['Year'] = df['DATE TIME UTC'].dt.year
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
            _render_operator_metrics(today_df)
            
                
        
        with t_cols[1]:
            # --- DONUT CHARTS ---
            donut_cols = st.columns(2)
            with donut_cols[0]:
                with st.container(border=True):
                    st.subheader("By Direction")
                    dir_counts = today_df.groupby('DIRECTION', observed=True).size().reset_index(name='Count')
                    fig_dir = px.pie(dir_counts, values='Count', names='DIRECTION', hole=0.55,
                                     color='DIRECTION',
                                     color_discrete_map={'TAKEOFF': C_DONUT_1, 'LANDING': C_DONUT_2})
                    fig_dir.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, title=None)
                    )
                    st.plotly_chart(fig_dir, width="stretch")
            with donut_cols[1]:
                with st.container(border=True):
                    st.subheader("By Airline")
                    al_counts = today_df.groupby('AIRLINE', observed=True).size().reset_index(name='Count')
                    fig_al = px.pie(al_counts, values='Count', names='AIRLINE', hole=0.55,
                                    color_discrete_sequence=AIRLINE_PALETTE)
                    fig_al.update_layout(
                        margin=dict(t=10, b=10, l=10, r=10),
                        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, title=None)
                    )
                    st.plotly_chart(fig_al, width="stretch")

            # --- CHARTS ---
            with st.container(border=True):
                _hc1, _hc2 = st.columns([4, 1])
                with _hc1:
                    st.subheader("Movements by Hour (UTC)")
                with _hc2:
                    h_by_dir = st.toggle("By Direction", key="tog_hourly")
                if h_by_dir:
                    h_counts = today_df.groupby(['Hour', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                    fig_h = px.bar(h_counts, x='Hour', y='Count', color='DIRECTION', barmode='group',
                                text='Count',
                                color_discrete_map=DIR_COLOR_MAP,
                                labels={'Hour': 'Hour (UTC)', 'Count': 'Movements'})
                else:
                    h_counts = today_df.groupby('Hour', observed=True).size().reset_index(name='Count')
                    fig_h = px.bar(h_counts, x='Hour', y='Count', text='Count',
                                color_discrete_sequence=[C_BAR],
                                labels={'Hour': 'Hour (UTC)', 'Count': 'Movements'})
                fig_h.update_traces(textposition='outside')
                fig_h.update_layout(
                    xaxis=dict(tickmode='linear', tick0=0, dtick=1),
                    legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
                )
                st.plotly_chart(fig_h, width="stretch")

            # --- SPECIES DISTRIBUTION ---
            

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
                                       color_discrete_map=DIR_COLOR_MAP,
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
                            margin=dict(l=5, r=5, t=5, b=5),
                            bargap=0 # Small gap between bars in the same group
                        )
                        fig_min.update_traces(width=0.5) # Force thin bars
                        st.plotly_chart(fig_min, width="stretch")
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
                
                st.dataframe(log_df, width="stretch", hide_index=True)

    with tab_history:
        st.header("Historical Analysis")
        
        # --- GLOBAL FILTERS ---
        f_cols = st.columns(2)
        with f_cols[0]:
            y_options = sorted(df['Year'].unique().tolist(), reverse=True)
            selected_years = st.multiselect("Select Years", options=y_options, default=[])
        with f_cols[1]:
            # Sort months chronologically
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

        # --- Day picker (single-month only) — hoisted so display_df is available everywhere ---
        display_df = hist_df
        if len(selected_months) == 1:
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
            # Use display_df so metrics react to day selection
            _render_operator_metrics(display_df)
            
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
                        if y_by_dir:
                            y_counts = hist_df.groupby(['Year', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                            fig_y = px.bar(y_counts, x='Year', y='Count', color='DIRECTION', barmode='group',
                                          text='Count',
                                          color_discrete_map=DIR_COLOR_MAP)
                        else:
                            y_counts = hist_df.groupby('Year', observed=True).size().reset_index(name='Count')
                            fig_y = px.bar(y_counts, x='Year', y='Count', text='Count',
                                          color_discrete_sequence=[C_BAR])
                        fig_y.update_traces(textposition='outside')
                        fig_y.update_layout(
                            xaxis=dict(tickmode='linear'),
                            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
                        )
                        st.plotly_chart(fig_y, width="stretch")
    
                # Monthly Trends
                with st.container(border=True):
                    _mc1, _mc2 = st.columns([4, 1])
                    with _mc1:
                        st.subheader("Monthly Volume Trends")
                    with _mc2:
                        m_by_dir = st.toggle("By Direction", key="tog_monthly")
                    if m_by_dir:
                        m_counts = hist_df.groupby(['Month', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                        m_counts['Month_DT'] = pd.to_datetime(m_counts['Month'], format='%b %Y')
                        m_counts = m_counts.sort_values('Month_DT')
                        fig_m = px.bar(m_counts, x='Month', y='Count', color='DIRECTION', barmode='group',
                                      text='Count',
                                      color_discrete_map=DIR_COLOR_MAP)
                    else:
                        m_counts = hist_df.groupby('Month', observed=True).size().reset_index(name='Count')
                        m_counts['Month_DT'] = pd.to_datetime(m_counts['Month'], format='%b %Y')
                        m_counts = m_counts.sort_values('Month_DT')
                        fig_m = px.bar(m_counts, x='Month', y='Count', text='Count',
                                      color_discrete_sequence=[C_BAR])
                    fig_m.update_traces(textposition='outside')
                    fig_m.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None))
                    st.plotly_chart(fig_m, width="stretch")

                
                

                
    
                # Daily Volume Drilldown - Only show if exactly one month is selected
                if len(selected_months) == 1:
                    with st.container(border=True):
                        _dc1, _dc2 = st.columns([4, 1])
                        with _dc1:
                            st.subheader(f"Daily Volume Distribution: {selected_months[0]}")
                        with _dc2:
                            d_by_dir = st.toggle("By Direction", key="tog_daily")
                        if d_by_dir:
                            d_counts = hist_df.groupby(['Day', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                            d_counts = d_counts.sort_values('Day')
                            fig_d = px.bar(d_counts, x='Day', y='Count', color='DIRECTION', barmode='group',
                                          text='Count',
                                          color_discrete_map=DIR_COLOR_MAP,
                                          labels={'Day': 'Date', 'Count': 'Movements'})
                        else:
                            d_counts = hist_df.groupby('Day', observed=True).size().reset_index(name='Count')
                            d_counts = d_counts.sort_values('Day')
                            fig_d = px.bar(d_counts, x='Day', y='Count', text='Count',
                                          color_discrete_sequence=[C_BAR],
                                          labels={'Day': 'Date', 'Count': 'Movements'})
                        fig_d.update_traces(textposition='outside')
                        fig_d.update_layout(
                            xaxis=dict(tickformat='%d %b'),
                            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
                        )
                        st.plotly_chart(fig_d, width="stretch")

                        # --- Hourly Drilldown ---
                        st.divider()
                        _hc1, _hc2 = st.columns([4, 1])
                        with _hc1:
                            st.subheader(":material/schedule: Hourly Movement Drilldown")
                        with _hc2:
                            h_by_dir = st.toggle("By Direction", key="tog_hourly_hist")

                        # display_df is already filtered to selected_day (hoisted above)
                        day_df = display_df.copy()
                        day_df['Hour'] = day_df['DATE TIME LOCAL'].dt.hour

                        if not day_df.empty:
                            if h_by_dir:
                                h_counts = day_df.groupby(['Hour', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                                fig_h = px.bar(h_counts, x='Hour', y='Count', color='DIRECTION', barmode='group',
                                               text='Count',
                                               color_discrete_map=DIR_COLOR_MAP,
                                               labels={'Hour': 'Hour (Local)', 'Count': 'Movements'})
                            else:
                                h_counts = day_df.groupby('Hour', observed=True).size().reset_index(name='Count')
                                fig_h = px.bar(h_counts, x='Hour', y='Count', text='Count',
                                               color_discrete_sequence=[C_BAR],
                                               labels={'Hour': 'Hour (Local)', 'Count': 'Movements'})

                            fig_h.update_traces(textposition='outside')
                            fig_h.update_layout(
                                xaxis=dict(tickmode='linear', tick0=0, dtick=1,
                                           ticktext=[f"{h:02d}:00" for h in range(24)],
                                           tickvals=list(range(24))),
                                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
                            )
                            st.plotly_chart(fig_h, width="stretch")
                        else:
                            st.warning("No data available for the selected day.")

                elif len(selected_months) > 1:
                    st.info(":material/lightbulb: Select a **single month** to view the Daily Volume Distribution.")
                elif not selected_months and not hist_df.empty:
                    # Optional: show nothing or a generic message when no month selected
                    pass
        
                # Full Data Table — filtered to selected day when single month is active
                with st.expander(":material/search: View Full Data Table"):
                    flt_cols = st.columns(3)
                    with flt_cols[0]:
                        f_op = st.multiselect("Operator", options=sorted(display_df['AIRLINE'].dropna().unique().tolist()), key="hist_log_op")
                    with flt_cols[1]:
                        f_hr = st.multiselect("Hour (Local)", options=sorted(display_df['Hour'].dropna().unique().tolist()), key="hist_log_hr")
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
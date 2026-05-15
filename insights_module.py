import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import database # Local SQLite module

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
    st.markdown("###### Operator Volume".upper())
    # Sort operators by volume (descending)
    op_counts = data_df['AIRLINE'].value_counts()
    operators = op_counts[op_counts > 0].index.tolist()
    
    for i in range(0, len(operators), 2):
        grid_cols = st.columns(2)
        for j in range(2):
            if i + j < len(operators):
                op = operators[i + j]
                op_df = data_df[data_df['AIRLINE'] == op]
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
                st.plotly_chart(fig_h, width="stretch")

            # --- SPECIES DISTRIBUTION ---
            if 'SPECIES' in today_df.columns and not today_df['SPECIES'].dropna().empty:
                with st.container(border=True):
                    st.subheader("Movements by Aircraft Species")
                    s_counts = today_df['SPECIES'].value_counts().reset_index()
                    s_counts.columns = ['Species', 'Count']
                    fig_s = px.pie(s_counts, values='Count', names='Species', 
                                  hole=0.4, 
                                  color_discrete_sequence=px.colors.qualitative.Safe)
                    fig_s.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5))
                    st.plotly_chart(fig_s, width="stretch")

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
            
        h_cols = st.columns([1, 2])
        
        with h_cols[0]:
            # Use the filtered dataframe for metrics
            _render_operator_metrics(hist_df)
            
        with h_cols[1]:
            with st.container(height=1000, border=False):
                # Yearly Volume Trends - Hide if months are selected
                if not selected_months:
                    with st.container(border=True):
                        st.subheader("Yearly Volume Trends")
                        y_counts = hist_df.groupby(['Year', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                        fig_y = px.bar(y_counts, x='Year', y='Count', color='DIRECTION', barmode='group', 
                                      text='Count', 
                                      color_discrete_map={'TAKEOFF': '#2563eb', 'LANDING': '#60a8fb'})
                        fig_y.update_traces(textposition='outside')
                        fig_y.update_layout(
                            xaxis=dict(tickmode='linear'),
                            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
                        )
                        st.plotly_chart(fig_y, width="stretch")
    
                # Monthly Trends
                with st.container(border=True):
                    st.subheader("Monthly Volume Trends")
                    m_counts = hist_df.groupby(['Month', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                    # Sort chronologically
                    m_counts['Month_DT'] = pd.to_datetime(m_counts['Month'], format='%b %Y')
                    m_counts = m_counts.sort_values('Month_DT')
                    
                    fig_m = px.bar(m_counts, x='Month', y='Count', color='DIRECTION', barmode='group', 
                                  text='Count',
                                  color_discrete_map={'TAKEOFF': '#2563eb', 'LANDING': '#60a8fb'})
                    fig_m.update_traces(textposition='outside')
                    fig_m.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None))
                    st.plotly_chart(fig_m, width="stretch")

                # --- SPECIES DISTRIBUTION (Historical) ---
                if 'SPECIES' in hist_df.columns and not hist_df['SPECIES'].dropna().empty:
                    with st.container(border=True):
                        st.subheader("Historical Volume by Aircraft Species")
                        hs_counts = hist_df['SPECIES'].value_counts().reset_index()
                        hs_counts.columns = ['Species', 'Count']
                        fig_hs = px.pie(hs_counts, values='Count', names='Species', 
                                      hole=0.4, 
                                      color_discrete_sequence=px.colors.qualitative.Safe)
                        fig_hs.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5))
                        st.plotly_chart(fig_hs, width="stretch")
    
                # Daily Volume Drilldown - Only show if exactly one month is selected
                if len(selected_months) == 1:
                    with st.container(border=True):
                        st.subheader(f"Daily Volume Distribution: {selected_months[0]}")
                        d_counts = hist_df.groupby(['Day', 'DIRECTION'], observed=True).size().reset_index(name='Count')
                        
                        # Sort days correctly
                        d_counts = d_counts.sort_values('Day')
                        
                        fig_d = px.bar(d_counts, x='Day', y='Count', color='DIRECTION', barmode='group',
                                      text='Count',
                                      color_discrete_map={'TAKEOFF': '#2563eb', 'LANDING': '#60a8fb'},
                                      labels={'Day': 'Date', 'Count': 'Movements'})
                        fig_d.update_traces(textposition='outside')
                        fig_d.update_layout(
                            xaxis=dict(tickformat='%d %b'), # e.g., 25 Jan
                            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
                        )
                        st.plotly_chart(fig_d, width="stretch")
                elif len(selected_months) > 1:
                    st.info(":material/lightbulb: Select a **single month** to view the Daily Volume Distribution.")
                elif not selected_months and not hist_df.empty:
                    # Optional: show nothing or a generic message when no month selected
                    pass
        
                # Full Data Table
                with st.expander(":material/search: View Full Data Table"):
                    st.dataframe(hist_df, use_container_width=True)
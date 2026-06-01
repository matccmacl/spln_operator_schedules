import streamlit as st
import pandas as pd
import time
import src.database as database
from src.analytics.metrics import clean_and_optimize_data

@st.cache_data(ttl=60, show_spinner="Syncing with Local Database...")
def load_master_data() -> pd.DataFrame:
    """
    Loads master flight data from SQLite and applies clean join and memory optimizations.
    Uses high-performance Streamlit data caching.
    """
    try:
        df = database.get_all_movements()
        reg_df = database.get_all_registrations()
        
        if df.empty:
            return df

        # Enforce relationship join and clean data using pure analytics module
        return clean_and_optimize_data(df, reg_df)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def render_operator_metrics(data_df: pd.DataFrame):
    """
    Renders KPIs and Operator Volume grid for a given dataframe of movements.
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

@st.dialog("Inspect Database", width="large")
def inspect_database_dialog():
    """
    Dialog component showing database tables (Movements, Registrations, Processed Files)
    and allowing bulk-deletions of processed files.
    """
    tab_mvmt, tab_reg, tab_files = st.tabs([
        ":material/flight: Movements",
        ":material/directions_boat: Registrations",
        ":material/folder: Processed Files",
    ])

    with tab_mvmt:
        df = database.get_all_movements()
        if df.empty:
            st.info("Table is empty.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_reg:
        df = database.get_all_registrations()
        if df.empty:
            st.info("Table is empty.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_files:
        files_df = database.get_all_filenames()
        if files_df.empty:
            st.info("No processed files found.")
        else:
            search = st.text_input(":material/search: Search Files", placeholder="Enter filename...", key="db_files_search")
            if search:
                files_df = files_df[files_df['filename'].str.contains(search, case=False)]

            if 'Select' not in files_df.columns:
                files_df.insert(0, "Select", False)

            edited_df = st.data_editor(
                files_df,
                hide_index=True,
                column_config={
                    "Select": st.column_config.CheckboxColumn(default=False),
                    "filename": st.column_config.TextColumn("Filename", width="large"),
                    "timestamp": st.column_config.TextColumn("Processed At", width="medium"),
                    "id": None,
                },
                disabled=["filename", "timestamp"],
                use_container_width=True,
                key="file_editor"
            )

            selected_files = edited_df[edited_df["Select"] == True]["filename"].tolist()
            if selected_files:
                st.divider()
                st.warning(f":material/warning: **Bulk Delete:** {len(selected_files)} file(s) selected.")
                if st.button(f"Confirm Delete ({len(selected_files)})", type="primary", use_container_width=True):
                    for fname in selected_files:
                        database.delete_file(fname)
                    load_master_data.clear()
                    st.success("Selected files deleted successfully.")
                    time.sleep(1)
                    st.rerun()

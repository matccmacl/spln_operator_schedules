
# :material/flight: Seaplane Operator Schedule Dashboard

An ETL (Extract, Transform, Load) pipeline designed to process Maldivian seaplane operator schedules from PDF and Excel formats into a unified dashboard for operational tracking and visualization.

## :material/rocket_launch: Current Status

-   **Maldivian (Q2):** [DONE] Excel & PDF Processors fully integrated. (Local SQLite Ingestion).

-   **TMA:** [DONE] Native Excel Processor (`_process_tma_excel`). Reads dual-section layout (Outbound cols 0–5 / Inbound cols 7–12), applies `8Q-` prefix to tail numbers, converts Excel timedelta times to `HH:MM`.

-   **Manta Air:** [DONE] Native Excel Processor (`_process_manta_excel`). Reads the `flights` sheet; times are pre-UTC (`datetime.time` objects); filters ADEP/ADES code `MLE`; strips `VR` prefix from resort ICAO codes; date extracted from `_MANTA_YYYY-MM-DD_` filename pattern.

-   **Villa Air:** [DONE] Native PDF Processor (`_process_villa_air`). Camelot `lattice` flavor for stable 8-column output across file variants; data rows identified by `TYPE == 'DHC6'`; date parsed with `dayfirst=True` from `DD-MM-YYYY` filename.


## :material/architecture: Modular Architecture

### 1. Logic Layer (The "Engines")

-   **`processors.py`**: Dispatcher + airline-specific extraction functions. Routes files by filename keyword (`TMA`, `VILLA`, `MALDIVIAN`, `MANTA`). All processors output the standardized schema.

-   **`insights_module.py`**: Data loading from SQLite, aggregation (NumPy/Pandas), and all Plotly visualization functions. Entry point: `load_master_data()` and `generate_performance_visuals()`. Contains the centralized color palette block at the top of the file.

-   **`database.py`**: SQLite CRUD layer. Manages `movements`, `registrations`, and `processed_files` tables with cascading deletes.

### 2. View Layer (The "Dashboard")

-   **`main.py`**: Streamlit entry point. Handles page routing (Operational Analytics / File Ingestion), the sequential file ingestion queue (with airline name + row count summary at Step 2), and the Developer Tools sidebar (DB inspector modal, Clear DB).


## :material/build: Tech Stack

-   **Environment:** WSL (Ubuntu) on Windows 11.

-   **UI Framework:** [Streamlit](https://streamlit.io/) for the interactive dashboard.

-   **Extraction:**
    -   **Pandas/Openpyxl**: Primary engine for Excel-based schedules (Q2, TMA, Manta).
    -   [**Camelot-py**](https://camelot-py.readthedocs.io/): Exclusively for Villa Air PDF parsing (`lattice` flavor).

-   **Data Processing:** Pandas & NumPy for high-speed data cleaning and time-series analysis.

-   **Storage:**
    - **Local (Active):** SQLite (`schedules.db`) — `movements` table joined to `registrations` for aircraft metadata (Species, MTOW, AC Type).
    - **Future:** Planned migration to Supabase for multi-user cloud relational storage.


## :material/folder: Project Structure

```
spln_operator_schedules/
├── .streamlit/
│   └── config.toml           # Theme and Server configurations
├── airline_schedules/        # Raw schedule files (gitignored)
├── scratch/                  # Dev/test scripts
├── main.py                   # Main UI and Ingestion Workflow
├── processors.py             # Logic: Airline-specific cleaning functions
├── insights_module.py        # Logic & Views: Data loading and Visualization engine
├── database.py               # SQLite CRUD layer
├── requirements.txt          # Project dependencies
└── README.md
```


## :material/assignment: Key Features

-   **Standardized Schema:** All processors output: `DATE TIME UTC`, `DATE TIME LOCAL`, `AIRLINE`, `FLT NUMBER`, `REG`, `FROM`, `TO`, `DIRECTION`.

-   **High-Performance Analytics:** SQLite-backed dashboard with sub-second load times (tested on 150k+ rows).

-   **Centralized Color Palette:** `insights_module.py` defines named color constants (`C_TAKEOFF`, `C_LANDING`, `C_BAR`, `C_DONUT_1/2`, `C_AIRLINE_1–4`, `DIR_COLOR_MAP`, `AIRLINE_PALETTE`) consumed by all charts — change colors in one place.

-   **Tabbed Dashboard:**
    - **Today's Operations**: Donut charts (By Direction & By Airline), hourly movement bar chart, minute-by-minute drilldown, movement log with Operator/Hour/Direction filters.
    - **Historical Analysis**: Yearly, Monthly, Daily, and Hourly volume trends with **By Direction toggles**. Global year/month filters + day picker (`st.date_input`) that reactively updates metric cards, charts, and the data table simultaneously.

-   **Developer Tools Sidebar:**
    - **Inspect Database** button opens a modal with tabs for Movements, Registrations, and Processed Files (with search and cascade-delete support).
    - **Clear Local SQLite DB** for full wipe.
    - DB size indicator.

-   **Sequential File Ingestion:** Upload → Auto-extract → Airline + row count summary → Date verification → Confirm & Save. Duplicate detection via processed files log.


_Last Updated: May 2026_
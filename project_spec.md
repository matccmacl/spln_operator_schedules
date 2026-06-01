
# :material/flight: Seaplane Operator Schedule Dashboard

An ETL (Extract, Transform, Load) pipeline designed to process Maldivian seaplane operator schedules from PDF and Excel formats into a unified dashboard for operational tracking and visualization.

## :material/rocket_launch: Current Status

-   **Codebase Modularization:** [DONE] Modular `src/` hierarchy successfully implemented. Includes strategy parsers, a context-managed transaction-safe database layer with WAL-mode, decoupled mathematical business logic and Plotly builders, and isolated presentation routing.
-   **Offline Testing Suites:** [DONE] Rigid unit testing suites (`test_processors.py`, `test_database.py`, `test_metrics.py`) fully integrated and verified.
-   **Maldivian (Q2):** [DONE] Excel & PDF Processors fully integrated (Local SQLite Ingestion).
-   **TMA:** [DONE] Native Excel Processor. Reads dual-section layout, applies `8Q-` prefix to tail numbers, and normalizes times.
-   **Manta Air:** [DONE] Native Excel Processor. Reads `flights` sheet, handles pre-UTC times, and strips `VR` resort prefixes.
-   **Villa Air:** [DONE] Native PDF Processor. Camelot `lattice` flavor, filters `DHC6` tail types, and parses dates.


## :material/architecture: Modular Architecture

### 1. Unified Configuration
-   **`src/config.py`**: The single source of truth for global configurations, GSheets integration parameters, SQLite path settings, and centralized visual chart styling (HSL palettes and maps).

### 2. Strategy-based ETL Parsers
-   **`src/processors/`**: Implements the Strategy design pattern for parsing airline schedules.
    -   `base.py`: Defines the abstract base interface.
    -   `maldivian.py`, `manta.py`, `tma.py`, `villa.py`: Airline-specific parsing classes.
    -   `__init__.py`: Factory registry dispatcher utilizing filename keywords.

### 3. Context-Managed Data Access Layer (DAL)
-   **`src/database/`**: Isolates all database operations and SQL transactions.
    -   `connection.py`: Transaction-safe SQLite connection context manager with Write-Ahead Logging (WAL-mode) enabled.
    -   `repositories.py`: Encapsulates database tables (`movements`, `processed_files`, `registrations`) in CRUD repositories.

### 4. Decoupled Business Logic & Plotly Visualizers
-   **`src/analytics/`**: High-performance time-series computation.
    -   `metrics.py`: Clean Pandas/NumPy operations, category optimizations, and YoY calculation engines (Zero Streamlit imports).
    -   `charts.py`: Formulates and styles Plotly figures (donuts, lines, and bar charts) with zero Streamlit dependencies.

### 5. Modular View Presentation Layer
-   **`src/ui/`**: Streamlit presentation and layouts.
    -   `components.py`: Reusable UI grids, cached loaders, and data editor dialogs.
    -   `tab_today.py` / `tab_history.py`: Tab views for daily and historical reporting.
    -   `view_ingestion.py`: Queue-based multi-file review ingestion wizard.

### 6. Slim Bootstrapper & Facade Layers
-   **`main.py`**: A thin page bootstrap controller and sidebar navigation router.
-   **`processors.py` / `database.py` / `insights_module.py`**: Backwards-compatible facades that route legacy calls to the new modular packages, ensuring external testing and sheets scripts continue to function correctly.

### 7. Comprehensive Offline Unit Testing
-   **`tests/`**: Contains offline verification suites run on standard pytest interfaces.
    -   `test_processors.py`: Validates parsing strategies against mock/real schedules.
    -   `test_database.py`: Tests SQLite connections and transactions on a temporary database.
    -   `test_metrics.py`: Audits mathematical YoY and data category optimizations.


## :material/build: Tech Stack

-   **Environment:** WSL (Ubuntu) on Windows 11.
-   **UI Framework:** [Streamlit](https://streamlit.io/) for the interactive dashboard.
-   **Extraction:**
    -   **Pandas/Openpyxl**: Primary engine for Excel-based schedules (Q2, TMA, Manta).
    -   [**Camelot-py**](https://camelot-py.readthedocs.io/): Exclusively for Villa Air PDF parsing (`lattice` flavor).
-   **Data Processing:** Pandas & NumPy for high-speed data cleaning and time-series analysis.
-   **Storage:**
    - **Local (Active):** SQLite (`schedules.db`) — `movements` table joined to `registrations` for aircraft metadata (Species, MTOW, AC Type) under transaction-safe WAL configurations.
    - **Future:** Planned migration to Supabase for multi-user cloud relational storage.


## :material/folder: Project Structure

```
spln_operator_schedules/
├── .streamlit/
│   └── config.toml           # Theme and Server configurations
├── airline_schedules/        # Raw schedule files (gitignored)
├── src/                      # Modular application code
│   ├── config.py             # Central configuration registry
│   ├── database/             # Context-managed DAL & Repositories
│   ├── processors/           # Strategy ETL parsers
│   ├── analytics/            # Pure data metrics & Plotly charts
│   └── ui/                   # Modular Streamlit view presentation
├── tests/                    # pytest unit verification suite
├── scratch/                  # Dev/test scripts
├── main.py                   # Bootstrapper Streamlit Entry Point
├── processors.py             # Backwards-compatible Facade
├── insights_module.py        # Backwards-compatible Facade
├── database.py               # Backwards-compatible Facade
├── requirements.txt          # Project dependencies
└── README.md
```


## :material/assignment: Key Features

-   **Standardized Schema:** All processors output: `DATE TIME UTC`, `DATE TIME LOCAL`, `AIRLINE`, `FLT NUMBER`, `REG`, `FROM`, `TO`, `DIRECTION`.

-   **High-Performance Analytics:** SQLite-backed dashboard with sub-second load times (tested on 150k+ rows).

-   **Centralized Color Palette:** `src/config.py` acts as the single source of truth for named color constants (`C_TAKEOFF`, `C_LANDING`, `C_BAR`, `C_DONUT_1/2`, `C_AIRLINE_1–4`, `DIR_COLOR_MAP`, `AIRLINE_PALETTE`) consumed by all chart builders — allowing instant, system-wide color palette customisation from a single file.

-   **Tabbed Dashboard:**
    - **Today's Operations**: Donut charts (By Direction & By Airline with custom black bold center totals and gray 14px "Total" subtitles), hourly movement bar chart, minute-by-minute drilldown, and movement log with Operator/Hour/Direction filters.
    - **Historical Analysis**: 
        - Yearly, Monthly, Daily, and Hourly volume trends with **By Direction toggles**.
        - **Left Sidebar Analytics**: Incorporates a **Movements by Direction Donut Chart** (featuring custom black bold center total annotation) and a **Movements by Airline Bar Chart** that dynamically respond to active filters.
        - **Year-over-Year (YoY) Monthly Comparison**: Dynamic line chart comparing monthly movement volumes across different years. Plotted points display node-level percentage change annotations (e.g., `+12.4%`), and unified x-axis tooltips provide absolute counts and full comparative change text (e.g., `+12.4% vs Prev Year`).
        - **Single Year & Single Month Daily Drilldown**: The Daily Volume distribution chart, day picker (`st.date_input`), and Hourly Movement Drilldown only render when exactly a single year and a single month are selected, prompting the user with clear instructions otherwise.

-   **Developer Tools Sidebar:**
    - **Inspect Database** button opens a modal with tabs for Movements, Registrations, and Processed Files (with search and cascade-delete support).
    - **Clear Local SQLite DB** for full wipe.
    - DB size indicator.

-   **Sequential File Ingestion:** Upload → Auto-extract → Airline + row count summary → Date verification → Confirm & Save. Duplicate detection via processed files log.


_Last Updated: May 2026_
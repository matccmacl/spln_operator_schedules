
# :material/flight: Seaplane Operator Schedule Dashboard

An ETL (Extract, Transform, Load) pipeline designed to process Maldivian seaplane operator schedules from PDF and Excel formats into a unified dashboard for operational tracking and visualization.

## :material/rocket_launch: Current Status

-   **Maldivian (Q2):** [DONE] Excel Processor implementation complete. (Local SQLite Ingestion).
    
-   **TMA:** [DONE] Historical data ingested via Bulk Engine. Native processor pending.
    
-   **Manta Air:** [DONE] Historical data ingested via Bulk Engine. Native processor pending.
    
-   **Villa Air:** [DONE] Historical data ingested via Bulk Engine. Native processor pending.
    

## :material/architecture: Modular Architecture

The project is structured to separate business logic from the user interface, allowing for easier maintenance and scaling:

### 1. Logic Layer (The "Engines")

-   **`processors.py`**: Contains the extraction and cleaning logic for each airline. It transforms raw files into the standardized "Master Log" schema.
    
-   **`insights_module.py`**: Handles data aggregation, heavy-lifting calculations (using NumPy/Pandas), and high-performance data loading from Google Sheets.
    

### 2. View Layer (The "Dashboard")

-   **`main.py`**: The entry point for the Streamlit application. Manages page routing, user authentication, and the file ingestion UI.
    
-   **`insights_module.py`**: Also contains the Plotly visualization functions to render interactive charts and KPI grids.
    

## :material/build: Tech Stack

-   **Environment:** WSL (Ubuntu) on Windows 11.
    
-   **UI Framework:** [Streamlit](https://streamlit.io/ "null") for the interactive dashboard.
    
-   **Extraction:**
    
    -   **Pandas/Openpyxl**: Primary engine for Excel-based schedules (Q2, TMA, Manta).
        
    -   [**Camelot-py**](https://camelot-py.readthedocs.io/ "null"): Exclusively for Villa Air PDF parsing (stream flavor).
        
-   **Data Processing:** [Pandas](https://pandas.pydata.org/ "null") & [NumPy](https://numpy.org/ "null") for high-speed data cleaning and time-series analysis.
    
-   **Storage:** 
    - **Local (Active):** SQLite (`schedules.db`) for high-performance dashboard loading and processed file tracking.
    - **Relational:** `registrations` table linked to `movements` for aircraft metadata (Species, MTOW).
    - **Future:** Planned migration to Supabase for multi-user cloud relational storage.
    

## :material/folder: Project Structure

```
spln_operator_schedules/
├── .streamlit/
│   └── config.toml       # Theme and Server configurations
├── config.py             # Configuration for Sheet URLs and Worksheet names (Gitignored)
├── main.py               # Main UI and Ingestion Workflow
├── processors.py         # Logic: Airline-specific cleaning functions
├── insights_module.py    # Logic & Views: Data loading and Visualization engine
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation

```

## :material/assignment: Key Features

-   **Standardized Schema:** All processors output a unified format: `DATE TIME UTC`, `AIRLINE`, `FLT NUMBER`, `REG`, `FROM`, `TO`, `DIRECTION`.
    
-   **High-Performance Analytics:** SQLite-backed dashboard achieves sub-second load times for large datasets (testing 150k+ rows).
    
-   **Hybrid Ingestion:** Sequential workflow that saves data locally for speed while syncing filename logs to the cloud for integrity checks.
    

_Last Updated: May 2026_
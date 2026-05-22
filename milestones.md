# :material/rocket_launch: Seaplane Operator Schedules - Project Milestones

This document tracks the high-level progress and future roadmap of the Seaplane Analytics & Ingestion system, synchronized with the `project_spec.md`.

---

## :material/architecture: Project Vision
To provide a standardized ETL pipeline for processing diverse seaplane schedules (Maldivian, TMA, Manta, Villa) into a high-performance unified analytics dashboard.

---

## :material/check_circle: Phase 1: Foundation & Data Ingestion
*Status: Complete*

- [x] **Environment Setup**: WSL (Ubuntu) + Windows 11 integration.
- [x] **Local Storage**: SQLite database (`schedules.db`) for high-speed persistence.
- [x] **Core Ingestion Engine**:
    - [x] Sequential multi-file processing with user date confirmation and duplicate detection.
    - [x] Relational Registration Normalization (8Q- format enforcement).
    - [x] Bulk Ingestion Engine for 100k+ record historical datasets. *(Data seeded — engine removed from UI)*
- [x] **Operator Processors (Stage 1)**:
    - [x] **Maldivian (Q2)**: Excel & PDF Processors fully integrated.
    - [x] **Historical Operators**: Bulk ingested (TMA, Manta, Villa) via Engine.

---

## :material/check_circle: Phase 2: Analytics & Extraction
*Status: Complete*

- [x] **Dashboard Architecture**:
    - [x] High-performance NumPy-accelerated filtering.
    - [x] Today's Operations vs. Historical Analysis tabbed layout.
- [x] **Performance Optimization**:
    - [x] 100% SQLite-only architecture (Zero network latency).
    - [x] Cascading Deletes (Linked movement removal from database).
- [x] **Standardized Schema**:
    - [x] Unified format: `DATE TIME UTC`, `DATE TIME LOCAL`, `AIRLINE`, `FLT NUMBER`, `REG`, `FROM`, `TO`, `DIRECTION`.
- [x] **Operator Processors (Stage 2)**:
    - [x] **TMA**: Native Excel Processor (`_process_tma_excel`) — dual-section outbound/inbound layout, `8Q-` prefix, timedelta normalisation.
    - [x] **Manta Air**: Native Excel Processor (`_process_manta_excel`) — `flights` sheet, UTC times, VR-prefix ICAO stripping, date from filename.
    - [x] **Villa Air**: Native PDF Processor (`_process_villa_air`) — Camelot `lattice` flavor, DHC6 row filter, `dayfirst=True` date parsing, stable 8-column layout across file variants.
- [x] **Visual Analytics**:
    - [x] KPI metrics grid and Operator Volume distribution (native `st.metric`).
    - [x] Yearly / Monthly / Daily volume trends with **By Direction toggle**.
    - [x] Hourly volume chart with **By Direction toggle** (Today's Operations & Historical).
    - [x] Minute-by-minute temporal drilldown (Today's Operations).
    - [x] **Hourly Movement Drilldown** in Historical Analysis — day picker (`st.date_input`) constrained to selected month; chart + metrics + data table all react to selected day.
    - [x] **Donut charts** (Today's Operations): By Direction & By Airline in a 2-column row.
    - [x] Global year/month filters for Historical Analysis.
    - [x] **Centralized color palette** variables (`C_TAKEOFF`, `C_LANDING`, `C_BAR`, `C_DONUT_*`, `AIRLINE_PALETTE`) for single-point color control.
- [x] **Ingestion UX**:
    - [x] Airline name + movement count metric cards shown at Step 2 (post-extraction summary).
    - [x] Filtered data table in Historical Analysis with Operator / Hour / Direction filters.
- [x] **Developer Tools**:
    - [x] **Inspect Database** modal with tabs: Movements, Registrations, Processed Files.
    - [x] Processed Files tab includes search + cascade-delete.
    - [x] Clear Local SQLite DB button.
    - [x] DB size indicator.

---

## :material/calendar_month: Phase 3: Scaling & Migration
*Status: Planned*

- [ ] **Database Migration**:
    - [ ] Transition from SQLite to **Supabase** for improved scaling and relational data.
- [ ] **User & Management Layer**:
    - [ ] User authentication (Streamlit-native or Supabase-based).
    - [ ] Admin interface for manual data corrections.
- [ ] **Enhanced Reporting**:
    - [ ] Anomaly detection in schedules.
    - [ ] Automated weekly performance summaries.

---

## :material/build: Tech Stack (Refined)
- **Runtime**: WSL (Ubuntu)
- **Extraction**: Pandas/Openpyxl (Excel), Camelot-py `lattice` flavor (Villa PDF)
- **Storage**: SQLite (Active) ➡️ Supabase (Future)
- **Analytics**: NumPy, Pandas, Plotly
- **Guidelines**: `.agents/rules/coding-rules.md`

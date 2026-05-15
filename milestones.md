# :material/rocket_launch: Seaplane Operator Schedules - Project Milestones

This document tracks the high-level progress and future roadmap of the Seaplane Analytics & Ingestion system, synchronized with the `project_spec.md`.

---

## :material/architecture: Project Vision
To provide a standardized ETL pipeline for processing diverse seaplane schedules (Maldivian, TMA, Manta, Villa) into a high-performance unified analytics dashboard.

---

## :material/check_circle: Phase 1: Foundation & Data Ingestion
*Status: Substantially Complete*

- [x] **Environment Setup**: WSL (Ubuntu) + Windows 11 integration.
- [x] **Local Storage**: SQLite database for high-speed persistence.
- [x] **Core Ingestion Engine**:
    - [x] Sequential multi-file processing with user date confirmation.
    - [x] Relational Registration Normalization (8Q- format enforcement).
    - [x] Bulk Ingestion Engine for 100k+ record historical datasets.
- [x] **Operator Processors (Stage 1)**:
    - [x] **Maldivian (Q2)**: Excel & PDF Processors fully integrated.
    - [x] **Historical Operators**: Bulk ingested (TMA, Manta, Villa) via Engine.

---

## :material/architecture: Phase 2: Analytics & Extraction
*Status: In Progress*

- [x] **Dashboard Architecture**:
    - [x] High-performance NumPy-accelerated filtering.
    - [x] Today's Operations vs. Historical Analysis tabs.
- [x] **Performance Optimization**:
    - [x] 100% SQLite-only architecture (Zero network latency).
    - [x] Cascading Deletes (Linked movement removal from database).
- [ ] **Operator Processors (Stage 2)**:
    - [ ] **TMA**: Implement Native Excel Processor.
    - [ ] **Manta Air**: Implement Native Excel Processor.
    - [ ] **Villa Air**: Implement Native PDF Processor (Camelot-py).
- [x] **Standardized Schema**:
    - [x] Unified format mapping: `DATE TIME UTC`, `AIRLINE`, `FLT NUMBER`, `REG`, `FROM`, `TO`, `DIRECTION`.
- [x] **Visual Analytics**:
    - [x] KPI metrics grid and Operator Volume distribution.
    - [x] Hourly/Monthly volume trends.
    - [x] Minute-by-minute temporal drilldown.
    - [x] **Relational Analytics**: Aircraft Species Distribution charts.

---

## :material/calendar_month: Phase 3: Scaling & Migration
*Status: Planned*

- [ ] **Database Migration**:
    - [ ] Transition from Google Sheets to **Supabase** for improved scaling and relational data.
- [ ] **User & Management Layer**:
    - [ ] User authentication (Streamlit-native or Supabase-based).
    - [ ] Admin interface for manual data corrections.
- [ ] **Enhanced Reporting**:
    - [ ] Anomaly detection in schedules.
    - [ ] Automated weekly performance summaries.

---

## :material/build: Tech Stack (Refined)
- **Runtime**: WSL (Ubuntu)
- **Extraction**: Pandas (Excel), Camelot-py (Villa PDF)
- **Storage**: GSheets (Current) ➡️ Supabase (Future)
- **Analytics**: NumPy, Pandas, Plotly
- **Guidelines**: `.agents/rules/coding-rules.md`

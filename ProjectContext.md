# AgriSure: Project Context

## Project Description
AgriSure is a comprehensive Farming Cooperative Management System designed to handle high-velocity IoT environmental data while maintaining strict financial and export audit trails. The system bridges the gap between grassroots agricultural production and international export markets by ensuring **End-to-End Traceability**. 

By unifying data from IoT field sensors, harvest submissions, quality inspections, and export contracts into a single relational database, AgriSure guarantees that export buyers can trace their purchases back to the exact physical parcel and its environmental conditions, while ensuring fair, mathematically proven revenue distribution to contributing farmers.

## Tech Stack
* **Database:** PostgreSQL (Ideal for time-series IoT data, JSONB support, and robust ACID transaction handling).
* **Backend Application:** Python 3.12+ 
  * `psycopg` & `psycopg_pool` (High-performance PostgreSQL adapters for Python).
* **Frontend UI:** Streamlit (Rapid, data-driven Python GUI framework).
* **Environment & Package Management:** `uv` (Fast Python package manager) & Docker.

## 4. Current Progress

### 4.1 Conceptual & Logical Design
- Status: **Complete**
- Designed E-R diagrams using **Chen notation**
  - Includes:
    - ISA hierarchies
    - Weak entities
    - Associative entities
- Successfully mapped to **3NF Relational Schema**
  - Representation: **Crow’s Foot notation**

---

### 4.2 Database Instantiation
- Status: **Complete**
- Deployed schema in **PostgreSQL**
- Key features implemented:
  - Advanced `CHECK` constraints
  - Composite primary and foreign keys
  - Strategic indexing:
    - Optimized for **time-series data**
    - Microsecond-level sensor readings indexing

---

### 4.3 Data Population
- Status: **Complete**
- Generated realistic synthetic datasets covering:
  - Multi-month crop cycles
  - IoT sensor readings
  - Supply chain aggregation workflows

---

### 4.4 Application Infrastructure
- Status: **Integrated**
- Backend:
  - Connection pooling using **psycopg**
  - FastAPI route structure established for core domains
  - Live API-backed workflows implemented for stakeholder operations
- Frontend:
  - Built using **Streamlit**
  - Role-specific dashboard pages created
  - Dashboards connected to backend routes for live workflow execution
- Security:
  - Role-Based Access Control (**RBAC**)
  - Secure session tracking implemented

---

### 4.5 Automation (Triggers)
- Status: **Completed**
- Implemented using **PL/pgSQL**
- Key triggers:
  - IoT threshold monitoring:
    - pH
    - Moisture
    - Temperature
  - Atomic inventory locking to prevent race conditions

---

### 4.6 Query Layer
- Status: **Complete**
- Implemented `sql/SampleQueries.sql` containing:
  - Core retrieval queries
  - Aggregation and analytical queries
  - Traceability-oriented multi-table joins
- Query set now covers the required Task 4 SQL layer and can be used for dashboard integration and reporting

---

### 4.7 End-to-End Workflow Integration
- Status: **Completed**
- Verified synchronized project flow across database, backend, and frontend:
  - Farmer harvest submission
  - Admin lot creation
  - Inspector lot approval
  - Buyer contract creation
  - Admin payout configuration and payment execution
  - Lot traceability drill-down
- Application logic now follows a consistent project story centered on:
  - `Harvest_Submissions`
  - `Aggregation_Lots`
  - `Lot_Inspections`
  - `Export_Contracts`
  - `Payments`
  - `Farmer_Payouts`

---

### 4.8 Transaction Demonstration
- Status: **Completed**
- Task 6 concurrency demonstrations implemented with UI support
- Demonstrated conflicting database transactions using:
  - Two buyers attempting to purchase the same approved lot
  - Two inspectors attempting to finalize the same pending lot
- Verified final database effects through:
  - row locking
  - rollback/commit visibility
  - final lot state inspection

---

## 5. Core Business Requirements

### 5.1 Traceability Hub
- Every completed export contract must be traceable to:
  - Specific **Harvest_Submissions**
  - Originating **Crop_Cycles**
  - Historical **Sensor_Readings**

---

### 5.2 Quality & Environmental Enforcement
- Sensor monitoring frequency:
  - Every **15 minutes**
- Automatic risk detection:
  - Crop cycles flagged as **"At Risk"** if:
    - Sensor values deviate from master crop definitions

---

### 5.3 Atomic Transactions
- Ensure strict transactional consistency:
  - Prevent **concurrent double-selling**
  - Maintain integrity of aggregation lots across buyers

---

### 5.4 Proportional Settlements
- Automated payout calculation for farmers based on:
  - Exact weight contribution
  - Quality scores

---

## 6. Current Final-State Summary

### 6.1 Completed Functional Coverage
- Login and RBAC are operational for all stakeholders
- Farmer dashboard supports live parcel viewing, sensor inspection, and harvest submission
- Inspector dashboard supports pending lot review and lot approval/rejection
- Buyer dashboard supports viewing approved lots, creating contracts, and viewing provenance
- Admin dashboard supports farmer onboarding, parcel registration, lot creation, Task 6 transaction demos, and payout execution
- Traceability workflow is connected to live lot-level backend data

---

### 6.2 Completed Financial Flow
- Contract payout configuration is supported
- Payment execution distributes payouts to contributing farmers
- Payout history can be queried after execution

---

### 6.3 Completed Transaction Demonstration
- Conflicting transaction scenarios are implemented and demonstrable from the UI
- Database effects of conflicting operations are visible and verifiable
- Final committed database state remains consistent under the tested scenarios

---

### 6.4 Remaining Polish / Submission Tasks
- Standardize environment configuration so backend URLs and DB settings are not hardcoded across multiple files
- Perform final UI cleanup and remove duplicate imports / minor code inconsistencies
- Rehearse and document the final TA demo using one clean lot lifecycle from start to finish
- Optionally expand seed data to provide more ready-made demo records for repeated runs

---

## Folder Structure
```text
AgriSure/
├── backend/                  # Application backend logic
│   ├── routes/               # API-like routing logic for different domains
│   │   ├── admin.py
│   │   ├── buyer.py
│   │   ├── contract.py
│   │   ├── farmer.py
│   │   ├── inspection.py
│   │   └── lot.py
│   ├── schemas/              # Data validation schemas
│   ├── database_config.json  # DB Connection parameters
│   ├── db.py                 # PostgreSQL connection pool manager
│   └── main.py               # Backend entry point
├── frontend/                 # Streamlit UI
│   ├── app.py                # Main entry point (Login & RBAC guard)
│   └── pages/                # Role-specific dashboards
│       ├── admin-dashboard.py
│       ├── buyer-dashboard.py
│       ├── farmer-dashboard.py
│       ├── inspector-dashboard.py
│       └── traceability-engine.py
├── sql/                      # Database scripts
│   ├── CreateTables.sql      # DDL (Schema, Constraints, Indexes)
│   ├── InsertData.sql        # DML (Synthetic data population)
│   ├── SampleQueries.sql     # Task 4 Complex Queries
│   └── triggers.sql          # Task 5 PL/pgSQL Triggers
├── docker-compose.yaml       # Container orchestration
├── pyproject.toml            # Python dependencies
├── .env                      # Environment variables
└── .gitignore

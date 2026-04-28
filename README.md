# AgriSure Project

AgriSure is a farming cooperative management system that connects farmers, inspectors, buyers, and cooperative admins through a single PostgreSQL-backed workflow. The project focuses on:

- end-to-end agricultural lot traceability,
- quality inspection and approval,
- buyer-side purchase and contract generation,
- proportional farmer payout distribution,
- and transaction-safety demonstrations for conflicting database operations.

## Stack

- PostgreSQL
- FastAPI
- Streamlit
- `psycopg` / `psycopg_pool`
- `uv` / Python virtual environment

## Repository Structure

```text
AgriSure/
├── backend/
├── frontend/
├── sql/
├── ProjectContext.md
├── README.md
├── docker-compose.yaml
└── pyproject.toml
```

## Database Setup

Create [backend/database_config.json](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/backend/database_config.json) in this format:

```json
{
  "dbname": "AgriSure_DB",
  "user": "gaurav",
  "password": "yourpassword",
  "host": "127.0.0.1",
  "port": "5432"
}
```

Then load the SQL scripts in this order:

1. [CreateTables.sql](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/sql/CreateTables.sql)
2. [InsertData.sql](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/sql/InsertData.sql)
3. [triggers.sql](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/sql/triggers.sql)

Optional:

4. [testing-triggers.sql](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/sql/testing-triggers.sql)

## Application Setup

Install dependencies:

```bash
cd /home/gaurav-barwa/Documents/Gaurav/IIITD-4th\ Sem/DBMS\ Project/AgriSure
python3 -m venv .venv
./.venv/bin/pip install -e .
```

## Running The Project

Start the backend:

```bash
cd /home/gaurav-barwa/Documents/Gaurav/IIITD-4th\ Sem/DBMS\ Project/AgriSure/backend
../.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

Start the frontend:

```bash
cd /home/gaurav-barwa/Documents/Gaurav/IIITD-4th\ Sem/DBMS\ Project/AgriSure/frontend
../.venv/bin/streamlit run app.py
```

## Seeded Login Credentials

- Farmer: `farmer_raj` / `hash1`
- Farmer: `farmer_anita` / `hash2`
- Inspector: `inspector_kumar` / `hash3`
- Buyer: `buyer_globalex` / `hash4`
- Admin: `admin_main` / `hash5`

## Core Stakeholder Workflows

### Farmer

- Login through [app.py](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/frontend/app.py)
- Open [farmer-dashboard.py](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/frontend/pages/farmer-dashboard.py)
- View parcels
- View latest sensor readings and risk status
- Submit a harvest for an active crop cycle

### Admin

- Login as `admin_main`
- Open [admin-dashboard.py](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/frontend/pages/admin-dashboard.py)
- Register farmers
- Register parcels
- Create aggregation lots from unassigned harvests
- Run Task 6 transaction demos
- Configure payouts and create payments

### Inspector

- Login as `inspector_kumar`
- Open [inspector-dashboard.py](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/frontend/pages/inspector-dashboard.py)
- View pending lots
- Inspect lot contribution and traceability context
- Approve or reject a lot

### Buyer

- Login as `buyer_globalex`
- Open [buyer-dashboard.py](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/frontend/pages/buyer-dashboard.py)
- View approved lots
- Create export contracts
- Review owned contracts
- Trace lot provenance

### Traceability

- Open [traceability-engine.py](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/frontend/pages/traceability-engine.py)
- Enter a lot ID
- View lifecycle timeline, farmer contributions, parcel origin, and sensor summary

## Recommended End-To-End Demo Flow

Use this exact order:

1. Login as Farmer and submit a new harvest.
2. Login as Admin and create a new aggregation lot from the newly submitted harvest.
3. Login as Inspector and approve the pending lot.
4. Login as Buyer and create a contract for the approved lot.
5. Login as Admin and execute payment/payout distribution for the contract.
6. Open the Traceability Engine and trace that same lot end to end.

This gives a single coherent story:

`Farmer harvest -> Aggregation lot -> Inspection approval -> Buyer contract -> Payment -> Full traceability`

## Task 6 Demonstration

Task 6 is integrated into the Admin dashboard under `Transactions`.

Implemented scenarios:

1. `Double Sale Attempt`
   Two buyers attempt to purchase the same approved lot concurrently.

2. `Duplicate Inspection Attempt`
   Two inspectors attempt to finalize the same pending lot concurrently.

What the UI shows:

- transaction count,
- commit vs rollback outcome,
- created records,
- final lot state,
- transaction timeline.

What the backend uses:

- explicit transactions,
- row locking with `FOR UPDATE`,
- PostgreSQL isolation control,
- final database-state verification.

## SQL Coverage

[SampleQueries.sql](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/sql/SampleQueries.sql) includes the Task 4 query layer, covering:

- farmer and parcel lookup,
- active crop cycles,
- sensor analytics,
- lot contributions,
- inspections,
- export contracts,
- payouts,
- traceability joins,
- ranking and aggregation.

## Triggers

[triggers.sql](/home/gaurav-barwa/Documents/Gaurav/IIITD-4th%20Sem/DBMS%20Project/AgriSure/sql/triggers.sql) currently implements:

- crop risk flagging based on sensor deviations,
- lot status update after inspection.

## Notes

- Some dashboard sections depend on meaningful available data in the database. If no data appears for a step, create the missing upstream records through the earlier workflow stages.
- For best demo results, use one fresh lot from start to finish rather than switching between unrelated seeded records.
- Task 6 uses dedicated demo users created automatically by the backend service when needed.

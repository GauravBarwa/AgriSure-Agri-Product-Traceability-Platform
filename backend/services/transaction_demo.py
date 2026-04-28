import threading
import time
from datetime import datetime

import psycopg

from db import execute_query, transaction_connection


class TransactionDemoError(Exception):
    pass


def _now():
    return datetime.now().isoformat(timespec="milliseconds")


def _append_log(logs, lock, actor, event, detail, started_at):
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 1)
    entry = {
        "timestamp": _now(),
        "elapsed_ms": elapsed_ms,
        "actor": actor,
        "event": event,
        "detail": detail,
    }
    with lock:
        logs.append(entry)


def _ensure_user(username, email, role, extra_insert_sql, extra_params):
    existing = execute_query(
        """
        SELECT UserID
        FROM User_Accounts
        WHERE Username = %s
        """,
        (username,),
        fetch=True,
    )
    if existing:
        return existing[0]["userid"]

    user_row = execute_query(
        """
        INSERT INTO User_Accounts
        (Username, PasswordHash, Email, RoleType, AccountStatus)
        VALUES (%s, %s, %s, %s, 'Active')
        RETURNING UserID
        """,
        (username, "task6-demo-hash", email, role),
        fetch=True,
    )
    user_id = user_row[0]["userid"]
    execute_query(extra_insert_sql, (user_id, *extra_params), fetch=False)
    return user_id


def ensure_demo_participants():
    buyer_a = _ensure_user(
        "task6_buyer_a",
        "task6_buyer_a@agrisure.local",
        "Buyer",
        """
        INSERT INTO Export_Buyers (UserID, CompanyName, Country, ContactInfo)
        VALUES (%s, %s, %s, %s)
        """,
        ("Task 6 Buyer A", "India", "Double-sale transaction demo"),
    )
    buyer_b = _ensure_user(
        "task6_buyer_b",
        "task6_buyer_b@agrisure.local",
        "Buyer",
        """
        INSERT INTO Export_Buyers (UserID, CompanyName, Country, ContactInfo)
        VALUES (%s, %s, %s, %s)
        """,
        ("Task 6 Buyer B", "India", "Double-sale transaction demo"),
    )
    inspector_a = _ensure_user(
        "task6_inspector_a",
        "task6_inspector_a@agrisure.local",
        "Inspector",
        """
        INSERT INTO Quality_Inspectors (UserID, CertificationLevel, Organization)
        VALUES (%s, %s, %s)
        """,
        ("Task 6 Demo", "AgriSure QA Lab A"),
    )
    inspector_b = _ensure_user(
        "task6_inspector_b",
        "task6_inspector_b@agrisure.local",
        "Inspector",
        """
        INSERT INTO Quality_Inspectors (UserID, CertificationLevel, Organization)
        VALUES (%s, %s, %s)
        """,
        ("Task 6 Demo", "AgriSure QA Lab B"),
    )

    return {
        "buyer_a_id": buyer_a,
        "buyer_b_id": buyer_b,
        "inspector_a_id": inspector_a,
        "inspector_b_id": inspector_b,
    }


def create_demo_lot(initial_status: str):
    row = execute_query(
        """
        INSERT INTO Aggregation_Lots (LotStatus, CreatedDate)
        VALUES (%s, NOW())
        RETURNING LotID
        """,
        (initial_status,),
        fetch=True,
    )
    return row[0]["lotid"]


def create_contract_transactional(
    *,
    buyer_id,
    lot_id,
    contract_quantity,
    price_per_kg,
    hold_seconds,
    isolation_level,
    actor,
    logs,
    log_lock,
    started_at,
    barrier,
):
    _append_log(logs, log_lock, actor, "ready", "Waiting at barrier", started_at)
    barrier.wait()

    with transaction_connection(isolation_level) as conn:
        with conn.cursor() as cur:
            _append_log(logs, log_lock, actor, "begin", f"Transaction started ({isolation_level})", started_at)
            _append_log(logs, log_lock, actor, "lock-request", f"Requesting row lock for lot {lot_id}", started_at)

            lock_started = time.perf_counter()
            cur.execute(
                """
                SELECT LotID, LotStatus
                FROM Aggregation_Lots
                WHERE LotID = %s
                FOR UPDATE
                """,
                (lot_id,),
            )
            lot = cur.fetchone()
            wait_ms = round((time.perf_counter() - lock_started) * 1000, 1)

            if not lot:
                raise TransactionDemoError(f"Lot {lot_id} not found")

            _append_log(logs, log_lock, actor, "lock-acquired", f"Lock acquired in {wait_ms} ms", started_at)

            if hold_seconds > 0:
                _append_log(logs, log_lock, actor, "hold", f"Holding row lock for {hold_seconds:.1f}s", started_at)
                time.sleep(hold_seconds)

            cur.execute(
                """
                SELECT ContractID
                FROM Export_Contracts
                WHERE LotID = %s
                """,
                (lot_id,),
            )
            existing_contract = cur.fetchone()
            if existing_contract:
                raise TransactionDemoError(
                    f"Lot {lot_id} already sold via contract {existing_contract['contractid']}"
                )

            if lot["lotstatus"] != "Approved":
                raise TransactionDemoError(
                    f"Lot {lot_id} is not approved for sale (current status: {lot['lotstatus']})"
                )

            cur.execute(
                """
                INSERT INTO Export_Contracts
                (BuyerID, LotID, ContractQuantityKg, PricePerKg, Status)
                VALUES (%s, %s, %s, %s, 'Active')
                RETURNING ContractID
                """,
                (buyer_id, lot_id, contract_quantity, price_per_kg),
            )
            contract_id = cur.fetchone()["contractid"]

            cur.execute(
                """
                UPDATE Aggregation_Lots
                SET LotStatus = 'Locked'
                WHERE LotID = %s
                """,
                (lot_id,),
            )

            _append_log(
                logs,
                log_lock,
                actor,
                "commit-ready",
                f"Prepared contract {contract_id} and locked the lot",
                started_at,
            )

            return {
                "status": "committed",
                "actor": actor,
                "buyer_id": buyer_id,
                "contract_id": contract_id,
                "lock_wait_ms": wait_ms,
            }


def inspect_lot_transactional(
    *,
    inspector_id,
    lot_id,
    decision,
    hold_seconds,
    isolation_level,
    actor,
    logs,
    log_lock,
    started_at,
    barrier,
):
    _append_log(logs, log_lock, actor, "ready", "Waiting at barrier", started_at)
    barrier.wait()

    with transaction_connection(isolation_level) as conn:
        with conn.cursor() as cur:
            _append_log(logs, log_lock, actor, "begin", f"Transaction started ({isolation_level})", started_at)
            _append_log(logs, log_lock, actor, "lock-request", f"Requesting row lock for lot {lot_id}", started_at)

            lock_started = time.perf_counter()
            cur.execute(
                """
                SELECT LotID, LotStatus
                FROM Aggregation_Lots
                WHERE LotID = %s
                FOR UPDATE
                """,
                (lot_id,),
            )
            lot = cur.fetchone()
            wait_ms = round((time.perf_counter() - lock_started) * 1000, 1)

            if not lot:
                raise TransactionDemoError(f"Lot {lot_id} not found")

            _append_log(logs, log_lock, actor, "lock-acquired", f"Lock acquired in {wait_ms} ms", started_at)

            if hold_seconds > 0:
                _append_log(logs, log_lock, actor, "hold", f"Holding row lock for {hold_seconds:.1f}s", started_at)
                time.sleep(hold_seconds)

            if lot["lotstatus"] != "Open":
                raise TransactionDemoError(
                    f"Lot {lot_id} is not pending inspection (current status: {lot['lotstatus']})"
                )

            cur.execute(
                """
                SELECT InspectionID, FinalDecision
                FROM Lot_Inspections
                WHERE LotID = %s
                """,
                (lot_id,),
            )
            existing_inspection = cur.fetchone()
            if existing_inspection:
                raise TransactionDemoError(
                    f"Lot {lot_id} already inspected as {existing_inspection['finaldecision']}"
                )

            cur.execute(
                """
                INSERT INTO Lot_Inspections (LotID, InspectorID, InspectionDate, FinalDecision)
                VALUES (%s, %s, NOW(), %s)
                RETURNING InspectionID
                """,
                (lot_id, inspector_id, decision),
            )
            inspection_id = cur.fetchone()["inspectionid"]

            new_status = "Approved" if decision == "Approved" else "Rejected"
            cur.execute(
                """
                UPDATE Aggregation_Lots
                SET LotStatus = %s
                WHERE LotID = %s
                """,
                (new_status, lot_id),
            )

            _append_log(
                logs,
                log_lock,
                actor,
                "commit-ready",
                f"Prepared inspection {inspection_id} with decision {decision}",
                started_at,
            )

            return {
                "status": "committed",
                "actor": actor,
                "inspector_id": inspector_id,
                "inspection_id": inspection_id,
                "decision": decision,
                "lock_wait_ms": wait_ms,
            }


def _run_worker(target, results, result_key, logs, log_lock, started_at, **kwargs):
    actor = kwargs["actor"]
    try:
        result = target(logs=logs, log_lock=log_lock, started_at=started_at, **kwargs)
        results[result_key] = result
        _append_log(logs, log_lock, actor, "commit", "Transaction committed", started_at)
    except TransactionDemoError as exc:
        results[result_key] = {
            "status": "rolled_back",
            "actor": actor,
            "reason": str(exc),
        }
        _append_log(logs, log_lock, actor, "rollback", str(exc), started_at)
    except psycopg.Error as exc:
        results[result_key] = {
            "status": "rolled_back",
            "actor": actor,
            "reason": str(exc).strip(),
        }
        _append_log(logs, log_lock, actor, "rollback", str(exc).strip(), started_at)
    except Exception as exc:
        results[result_key] = {
            "status": "error",
            "actor": actor,
            "reason": str(exc),
        }
        _append_log(logs, log_lock, actor, "error", str(exc), started_at)


def simulate_buyer_race(contract_quantity, price_per_kg, buyer_a_hold_seconds, buyer_b_hold_seconds, isolation_level):
    participants = ensure_demo_participants()
    lot_id = create_demo_lot("Approved")
    started_at = time.perf_counter()
    logs = []
    log_lock = threading.Lock()
    barrier = threading.Barrier(2)
    results = {}

    threads = [
        threading.Thread(
            target=_run_worker,
            kwargs={
                "target": create_contract_transactional,
                "results": results,
                "result_key": "buyer_a",
                "logs": logs,
                "log_lock": log_lock,
                "started_at": started_at,
                "buyer_id": participants["buyer_a_id"],
                "lot_id": lot_id,
                "contract_quantity": contract_quantity,
                "price_per_kg": price_per_kg,
                "hold_seconds": buyer_a_hold_seconds,
                "isolation_level": isolation_level,
                "actor": "Buyer A",
                "barrier": barrier,
            },
        ),
        threading.Thread(
            target=_run_worker,
            kwargs={
                "target": create_contract_transactional,
                "results": results,
                "result_key": "buyer_b",
                "logs": logs,
                "log_lock": log_lock,
                "started_at": started_at,
                "buyer_id": participants["buyer_b_id"],
                "lot_id": lot_id,
                "contract_quantity": contract_quantity,
                "price_per_kg": price_per_kg,
                "hold_seconds": buyer_b_hold_seconds,
                "isolation_level": isolation_level,
                "actor": "Buyer B",
                "barrier": barrier,
            },
        ),
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final_lot = execute_query(
        "SELECT LotID, LotStatus FROM Aggregation_Lots WHERE LotID = %s",
        (lot_id,),
        fetch=True,
    )[0]
    contracts = execute_query(
        """
        SELECT ContractID, BuyerID, LotID, ContractQuantityKg, PricePerKg
        FROM Export_Contracts
        WHERE LotID = %s
        ORDER BY ContractID
        """,
        (lot_id,),
        fetch=True,
    )

    return {
        "scenario": "double_sale_attempt",
        "lot_id": lot_id,
        "participants": participants,
        "results": results,
        "contracts": contracts,
        "final_lot": final_lot,
        "logs": sorted(logs, key=lambda log: log["elapsed_ms"]),
        "summary": {
            "expected_outcome": "Exactly one buyer should commit and the other should roll back.",
            "transactions_started": 2,
            "transactions_committed": sum(1 for result in results.values() if result["status"] == "committed"),
            "transactions_rolled_back": sum(1 for result in results.values() if result["status"] == "rolled_back"),
        },
    }


def simulate_inspection_race(inspector_a_decision, inspector_b_decision, inspector_a_hold_seconds, inspector_b_hold_seconds, isolation_level):
    participants = ensure_demo_participants()
    lot_id = create_demo_lot("Open")
    started_at = time.perf_counter()
    logs = []
    log_lock = threading.Lock()
    barrier = threading.Barrier(2)
    results = {}

    threads = [
        threading.Thread(
            target=_run_worker,
            kwargs={
                "target": inspect_lot_transactional,
                "results": results,
                "result_key": "inspector_a",
                "logs": logs,
                "log_lock": log_lock,
                "started_at": started_at,
                "inspector_id": participants["inspector_a_id"],
                "lot_id": lot_id,
                "decision": inspector_a_decision,
                "hold_seconds": inspector_a_hold_seconds,
                "isolation_level": isolation_level,
                "actor": "Inspector A",
                "barrier": barrier,
            },
        ),
        threading.Thread(
            target=_run_worker,
            kwargs={
                "target": inspect_lot_transactional,
                "results": results,
                "result_key": "inspector_b",
                "logs": logs,
                "log_lock": log_lock,
                "started_at": started_at,
                "inspector_id": participants["inspector_b_id"],
                "lot_id": lot_id,
                "decision": inspector_b_decision,
                "hold_seconds": inspector_b_hold_seconds,
                "isolation_level": isolation_level,
                "actor": "Inspector B",
                "barrier": barrier,
            },
        ),
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final_lot = execute_query(
        "SELECT LotID, LotStatus FROM Aggregation_Lots WHERE LotID = %s",
        (lot_id,),
        fetch=True,
    )[0]
    inspections = execute_query(
        """
        SELECT InspectionID, LotID, InspectorID, FinalDecision
        FROM Lot_Inspections
        WHERE LotID = %s
        ORDER BY InspectionID
        """,
        (lot_id,),
        fetch=True,
    )

    return {
        "scenario": "duplicate_inspection_attempt",
        "lot_id": lot_id,
        "participants": participants,
        "results": results,
        "inspections": inspections,
        "final_lot": final_lot,
        "logs": sorted(logs, key=lambda log: log["elapsed_ms"]),
        "summary": {
            "expected_outcome": "Exactly one inspector should commit and the other should roll back.",
            "transactions_started": 2,
            "transactions_committed": sum(1 for result in results.values() if result["status"] == "committed"),
            "transactions_rolled_back": sum(1 for result in results.values() if result["status"] == "rolled_back"),
        },
    }

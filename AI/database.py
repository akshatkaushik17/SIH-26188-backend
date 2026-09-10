import sqlite3
import json
from datetime import datetime
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "scan_history.db"


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL UNIQUE,
            timestamp TEXT NOT NULL,

            document_number TEXT,
            document_name TEXT,

            verification_status TEXT,

            risk_score REAL,
            risk_level TEXT,

            ocr_confidence REAL,

            tampering_detected INTEGER,

            face_match INTEGER,

            decision TEXT,

            stored_document TEXT,
            stored_face TEXT,

            full_result TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS prevent_scan_history_delete
        BEFORE DELETE ON scan_history
        BEGIN
            SELECT RAISE(ABORT, 'Audit history cannot be deleted');
        END;
        """
    )
    connection.commit()
    connection.close()


def add_missing_columns():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("PRAGMA table_info(scan_history)")
    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    new_columns = {
        "face_match": "INTEGER",
        "decision": "TEXT",
        "stored_document": "TEXT",
        "stored_face": "TEXT",
    }

    for column, data_type in new_columns.items():

        if column not in existing_columns:

            cursor.execute(
                f"ALTER TABLE scan_history ADD COLUMN {column} {data_type}"
            )

    connection.commit()
    connection.close()


def save_scan_result(
    result,
    stored_document=None,
    stored_face=None
):

    initialize_database()
    add_missing_columns()

    connection = get_connection()
    cursor = connection.cursor()

    information = result.get(
        "information",
        {}
    )

    verification = result.get(
        "verification",
        {}
    )

    risk = result.get(
        "risk",
        {}
    )

    tampering = result.get(
        "tampering",
        {}
    )

    face_verification = result.get(
        "face_verification",
        {}
    )

    timestamp = datetime.now().isoformat()

    scan_id = (
        "SCAN-"
        + datetime.now().strftime(
            "%Y%m%d-%H%M%S-%f"
        )
    )

    risk_level = risk.get(
        "risk_level"
    )

    if risk_level:
        risk_level = str(risk_level).upper()

    if risk_level in ["DANGER", "HIGH", "CRITICAL"]:
        decision = "DANGER"
    elif risk_level in ["SAFE", "LOW"]:
        decision = "SAFE"
    else:
        decision = "REVIEW"

    cursor.execute(
        """
        INSERT INTO scan_history (
            scan_id,
            timestamp,
            document_number,
            document_name,
            verification_status,
            risk_score,
            risk_level,
            ocr_confidence,
            tampering_detected,
            face_match,
            decision,
            stored_document,
            stored_face,
            full_result
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            scan_id,

            timestamp,

            information.get(
                "passport_number"
            )
            or information.get(
                "document_number"
            ),

            information.get(
                "name"
            ),

            verification.get(
                "status"
            ),

            risk.get(
                "risk_score"
            ),

            risk_level,

            result.get(
                "ocr_confidence"
            ),

            int(
                tampering.get(
                    "tampering_detected",
                    False
                )
            ),

            int(
                face_verification.get(
                    "match",
                    False
                )
            ),

            decision,

            stored_document,

            stored_face,

            json.dumps(result)
        )
    )

    connection.commit()
    connection.close()

    return scan_id


def get_scan_history(limit=50):

    initialize_database()
    add_missing_columns()

    connection = get_connection()
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            scan_id,
            timestamp,
            document_number,
            document_name,
            verification_status,
            risk_score,
            risk_level,
            ocr_confidence,
            tampering_detected,
            face_match,
            decision,
            stored_document,
            stored_face
        FROM scan_history
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]

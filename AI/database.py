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

            full_result TEXT NOT NULL
        )
        """
    )

    connection.commit()

    connection.close()


def save_scan_result(result):

    initialize_database()

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

    timestamp = datetime.now().isoformat()

    scan_id = (
        "SCAN-"
        + datetime.now().strftime(
            "%Y%m%d-%H%M%S-%f"
        )
    )

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
            full_result
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

            risk.get(
                "risk_level"
            ),

            result.get(
                "ocr_confidence"
            ),

            int(
                tampering.get(
                    "tampering_detected",
                    False
                )
            ),

            json.dumps(result)
        )
    )

    connection.commit()

    connection.close()

    return scan_id


def get_scan_history(limit=50):

    initialize_database()

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
            tampering_detected
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

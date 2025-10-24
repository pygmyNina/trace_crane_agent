"""
Local Storage System for TRACE Training
Manages training sessions, corrections, and training data
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class TrainingStorage:
    """Manages local storage for training sessions and data"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.sessions_dir = self.data_dir / "training_sessions"
        self.corrections_dir = self.data_dir / "corrections"
        self.pdfs_dir = self.data_dir / "pdfs"

        for directory in [self.sessions_dir, self.corrections_dir, self.pdfs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database for structured queries
        self.db_path = self.data_dir / "training.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Training sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                pdf_file TEXT,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        """)

        # Questions and answers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                question TEXT NOT NULL,
                user_answer TEXT,
                correct_answer TEXT,
                is_correct INTEGER,
                category TEXT,
                FOREIGN KEY (session_id) REFERENCES training_sessions(session_id)
            )
        """)

        # Corrections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                question TEXT NOT NULL,
                incorrect_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                category TEXT,
                notes TEXT,
                FOREIGN KEY (session_id) REFERENCES training_sessions(session_id)
            )
        """)

        # PDF metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                upload_date TEXT NOT NULL,
                num_pages INTEGER,
                description TEXT,
                processed INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def create_session(self, pdf_file: Optional[str] = None) -> str:
        """Create a new training session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO training_sessions (session_id, start_time, pdf_file, status)
            VALUES (?, ?, ?, 'active')
        """, (session_id, datetime.now().isoformat(), pdf_file))

        conn.commit()
        conn.close()

        # Create session directory
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(exist_ok=True)

        # Create session metadata file
        metadata = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "pdf_file": pdf_file,
            "questions": [],
            "corrections": []
        }

        with open(session_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        return session_id

    def end_session(self, session_id: str):
        """End a training session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE training_sessions
            SET end_time = ?, status = 'completed'
            WHERE session_id = ?
        """, (datetime.now().isoformat(), session_id))

        conn.commit()
        conn.close()

    def log_question(self, session_id: str, question: str, user_answer: str,
                     correct_answer: str, is_correct: bool, category: str = "general"):
        """Log a question and answer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Log in database
        cursor.execute("""
            INSERT INTO qa_log (session_id, timestamp, question, user_answer,
                               correct_answer, is_correct, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, datetime.now().isoformat(), question, user_answer,
              correct_answer, 1 if is_correct else 0, category))

        # Update session stats
        cursor.execute("""
            UPDATE training_sessions
            SET total_questions = total_questions + 1,
                correct_answers = correct_answers + ?
            WHERE session_id = ?
        """, (1 if is_correct else 0, session_id))

        conn.commit()
        conn.close()

        # Update session metadata file
        session_dir = self.sessions_dir / session_id
        metadata_file = session_dir / "metadata.json"

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            metadata["questions"].append({
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "category": category
            })

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

    def log_correction(self, session_id: str, question: str, incorrect_answer: str,
                       correct_answer: str, category: str = "general", notes: str = ""):
        """Log a correction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO corrections (session_id, timestamp, question, incorrect_answer,
                                    correct_answer, category, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, datetime.now().isoformat(), question, incorrect_answer,
              correct_answer, category, notes))

        conn.commit()
        conn.close()

        # Also save to corrections directory
        correction_file = self.corrections_dir / f"{session_id}_corrections.jsonl"

        correction = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "incorrect_answer": incorrect_answer,
            "correct_answer": correct_answer,
            "category": category,
            "notes": notes
        }

        with open(correction_file, 'a') as f:
            f.write(json.dumps(correction) + "\n")

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a training session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT total_questions, correct_answers, start_time, end_time, pdf_file
            FROM training_sessions
            WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            total_q, correct_a, start, end, pdf = row
            accuracy = (correct_a / total_q * 100) if total_q > 0 else 0

            return {
                "session_id": session_id,
                "total_questions": total_q,
                "correct_answers": correct_a,
                "incorrect_answers": total_q - correct_a,
                "accuracy": accuracy,
                "start_time": start,
                "end_time": end,
                "pdf_file": pdf
            }
        return {}

    def get_corrections(self, session_id: Optional[str] = None,
                        category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get corrections, optionally filtered by session or category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM corrections WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        corrections = []
        for row in rows:
            corrections.append({
                "id": row[0],
                "session_id": row[1],
                "timestamp": row[2],
                "question": row[3],
                "incorrect_answer": row[4],
                "correct_answer": row[5],
                "category": row[6],
                "notes": row[7]
            })

        return corrections

    def add_pdf(self, filename: str, num_pages: int, description: str = ""):
        """Register a PDF file in the system"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO pdf_metadata (filename, upload_date, num_pages, description)
                VALUES (?, ?, ?, ?)
            """, (filename, datetime.now().isoformat(), num_pages, description))
            conn.commit()
        except sqlite3.IntegrityError:
            # PDF already exists, update it
            cursor.execute("""
                UPDATE pdf_metadata
                SET num_pages = ?, description = ?
                WHERE filename = ?
            """, (num_pages, description, filename))
            conn.commit()

        conn.close()

    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent training sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id, start_time, end_time, total_questions,
                   correct_answers, pdf_file, status
            FROM training_sessions
            ORDER BY start_time DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            sessions.append({
                "session_id": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "total_questions": row[3],
                "correct_answers": row[4],
                "pdf_file": row[5],
                "status": row[6]
            })

        return sessions

    def get_category_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics by category across all sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT category,
                   COUNT(*) as total,
                   SUM(is_correct) as correct
            FROM qa_log
            GROUP BY category
        """)

        rows = cursor.fetchall()
        conn.close()

        stats = {}
        for row in rows:
            category, total, correct = row
            stats[category] = {
                "total": total,
                "correct": correct,
                "incorrect": total - correct,
                "accuracy": (correct / total * 100) if total > 0 else 0
            }

        return stats


if __name__ == "__main__":
    # Test the storage system
    storage = TrainingStorage()
    print("Storage system initialized successfully!")
    print(f"Database location: {storage.db_path}")
    print(f"Sessions directory: {storage.sessions_dir}")
    print(f"Corrections directory: {storage.corrections_dir}")

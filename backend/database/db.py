import aiosqlite
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

DATABASE_PATH = "database/searches.db"

async def init_db():
    """Initialize the database and create tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Searches table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                location TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Jobs table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                company TEXT NOT NULL,
                link TEXT NOT NULL,
                score INTEGER NOT NULL,
                justification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_id) REFERENCES searches(id)
            )
        """)
        
        # Resume texts table (stores hash only for privacy)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS resume_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER NOT NULL UNIQUE,
                resume_hash TEXT NOT NULL,
                resume_preview TEXT,
                FOREIGN KEY (search_id) REFERENCES searches(id)
            )
        """)
        
        await db.commit()
        print("[DB] Database initialized successfully.")


async def save_search(query: str, location: str, resume_text: str = "") -> int:
    """
    Save a new search query.
    Returns the search_id.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO searches (query, location) VALUES (?, ?)",
            (query, location)
        )
        search_id = cursor.lastrowid
        
        # Save resume hash if provided
        if resume_text:
            resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()
            resume_preview = resume_text[:200] + "..." if len(resume_text) > 200 else resume_text
            
            await db.execute(
                "INSERT INTO resume_texts (search_id, resume_hash, resume_preview) VALUES (?, ?, ?)",
                (search_id, resume_hash, resume_preview)
            )
        
        await db.commit()
        print(f"[DB] Saved search #{search_id}: '{query}' in '{location}'")
        return search_id


async def save_job(search_id: int, job: Dict) -> None:
    """
    Save a job match for a specific search.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO jobs 
            (search_id, role, company, link, score, justification) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                search_id,
                job.get("role", ""),
                job.get("company", ""),
                job.get("link", ""),
                job.get("score", 0),
                job.get("justification", "")
            )
        )
        await db.commit()


async def get_search_history(limit: int = 10) -> List[Dict]:
    """
    Get recent search history.
    Returns list of searches with job count.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT 
                s.id,
                s.query,
                s.location,
                s.created_at,
                COUNT(j.id) as job_count
            FROM searches s
            LEFT JOIN jobs j ON s.id = j.search_id
            GROUP BY s.id
            ORDER BY s.created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = await cursor.fetchall()
        
        return [
            {
                "id": row["id"],
                "query": row["query"],
                "location": row["location"],
                "created_at": row["created_at"],
                "job_count": row["job_count"]
            }
            for row in rows
        ]


async def get_jobs_by_search(search_id: int) -> List[Dict]:
    """
    Get all jobs for a specific search.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT role, company, link, score, justification, created_at
            FROM jobs
            WHERE search_id = ?
            ORDER BY score DESC
            """,
            (search_id,)
        )
        rows = await cursor.fetchall()
        
        return [
            {
                "role": row["role"],
                "company": row["company"],
                "link": row["link"],
                "score": row["score"],
                "justification": row["justification"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]

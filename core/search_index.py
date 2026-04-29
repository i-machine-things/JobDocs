"""
SQLite-backed search index for job folders and blueprint files.

Stored in the user's app data dir (per-machine). WAL mode allows concurrent
reads during background writes. Incremental updates only re-index directories
whose mtime has changed since the last run.
"""

import logging
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY,
    prefix      TEXT    NOT NULL DEFAULT '',
    customer    TEXT    NOT NULL,
    job_number  TEXT    NOT NULL DEFAULT '',
    description TEXT    NOT NULL DEFAULT '',
    drawings    TEXT    NOT NULL DEFAULT '',
    path        TEXT    NOT NULL,
    mtime       REAL    NOT NULL,
    UNIQUE(path)
);

CREATE TABLE IF NOT EXISTS bp_files (
    id          INTEGER PRIMARY KEY,
    prefix      TEXT    NOT NULL,
    customer    TEXT    NOT NULL,
    filename    TEXT    NOT NULL,
    name_no_ext TEXT    NOT NULL,
    dir_path    TEXT    NOT NULL,
    rel_path    TEXT    NOT NULL,
    mtime       REAL    NOT NULL,
    UNIQUE(dir_path, filename)
);

CREATE TABLE IF NOT EXISTS indexed_dirs (
    dir_path    TEXT    NOT NULL,
    prefix      TEXT    NOT NULL DEFAULT '',
    mtime       REAL    NOT NULL,
    indexed_at  REAL    NOT NULL,
    PRIMARY KEY (dir_path, prefix)
);

CREATE INDEX IF NOT EXISTS idx_jobs_number      ON jobs(job_number  COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_jobs_cust        ON jobs(customer    COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_jobs_desc        ON jobs(description COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_jobs_draw        ON jobs(drawings    COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_jobs_cust_prefix ON jobs(customer, prefix);
CREATE INDEX IF NOT EXISTS idx_bp_filename      ON bp_files(filename COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_bp_cust          ON bp_files(customer COLLATE NOCASE);
"""

_MAX_RESULTS = 500


def _escape_like(term: str) -> str:
    """Escape SQL LIKE special characters so literal underscores and percent signs match."""
    return term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def _parse_job_folder(dir_name: str) -> Tuple[str, str, List[str]]:
    """Extract (job_number, description, drawings) from a folder name.

    Handles underscore-separated names (12345_Desc_DWG-A) and free-form names
    that start with a job number but use spaces, dashes, or no separator
    (e.g. '12345 Bracket Assembly', '12345-Shaft').
    """
    m = re.match(r'^(\d+)', dir_name)
    if not m:
        return '', dir_name, []
    job_number = m.group(1)
    remainder = dir_name[m.end():].lstrip('_- ')

    if not remainder:
        return job_number, '', []

    if '_' in remainder:
        parts = remainder.split('_')
        if '-' in parts[-1]:
            drawings = [d.strip() for d in parts[-1].split('-') if d.strip()]
            desc = ' '.join(parts[:-1])
        else:
            drawings = []
            desc = ' '.join(parts)
    else:
        drawings = []
        desc = remainder

    return job_number, desc, drawings


class SearchIndex:
    """Persistent search index over job folders and blueprint files."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self, timeout: float = 10.0) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=timeout)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(_SCHEMA)
        except sqlite3.Error as exc:
            logger.error("search_index: failed to initialise DB: %s", exc)

    def _dir_mtime(self, path: str) -> float:
        try:
            return os.path.getmtime(path)
        except OSError:
            return 0.0

    def _is_stale(self, conn: sqlite3.Connection, dir_path: str, prefix: str) -> bool:
        current = self._dir_mtime(dir_path)
        row = conn.execute(
            "SELECT mtime FROM indexed_dirs WHERE dir_path=? AND prefix=?",
            (dir_path, prefix),
        ).fetchone()
        return row is None or current != row['mtime']

    def _mark_indexed(self, conn: sqlite3.Connection, dir_path: str, prefix: str) -> None:
        conn.execute(
            """INSERT INTO indexed_dirs(dir_path, prefix, mtime, indexed_at)
               VALUES(?,?,?,?)
               ON CONFLICT(dir_path, prefix)
               DO UPDATE SET mtime=excluded.mtime, indexed_at=excluded.indexed_at""",
            (dir_path, prefix, self._dir_mtime(dir_path), time.time()),
        )

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def update(
        self,
        cf_dirs: List[Tuple[str, str]],
        bp_dirs: List[Tuple[str, str]],
        app_context,
        progress: Optional[Callable[[str], None]] = None,
        cancelled: Optional[Callable[[], bool]] = None,
    ) -> None:
        """Incrementally update the index. Only stale directories are re-indexed."""

        def _emit(msg: str) -> None:
            if progress:
                progress(msg)

        def _cancelled() -> bool:
            return bool(cancelled and cancelled())

        try:
            with self._connect() as conn:
                # --- Customer files dirs ---
                for prefix, base_dir in cf_dirs:
                    if _cancelled():
                        return
                    try:
                        customers = [
                            d for d in os.listdir(base_dir)
                            if os.path.isdir(os.path.join(base_dir, d))
                        ]
                    except OSError:
                        continue

                    # Purge rows for customers that no longer exist on disk.
                    if not _cancelled():
                        customer_set = set(customers)
                        if customer_set:
                            placeholders = ','.join('?' * len(customer_set))
                            conn.execute(
                                f"DELETE FROM jobs WHERE prefix=? AND customer NOT IN ({placeholders})",
                                (prefix, *customer_set),
                            )
                        else:
                            conn.execute("DELETE FROM jobs WHERE prefix=?", (prefix,))

                    for customer in customers:
                        if _cancelled():
                            return
                        customer_path = os.path.join(base_dir, customer)

                        # Discover jobs first so we can watch the mtime of the
                        # directory that actually contains job folders (e.g.
                        # "job documents/"), not just the customer root — adding
                        # a job inside a subdir only updates the subdir mtime.
                        try:
                            jobs = app_context.find_job_folders(customer_path)
                        except OSError as exc:
                            logger.warning("search_index: find_job_folders(%s): %s", customer_path, exc)
                            continue  # preserve existing rows on scan failure

                        container_dirs = (
                            {str(Path(p).parent) for _, p in jobs}
                            if jobs else {customer_path}
                        )

                        # Also check previously indexed container dirs — a deleted
                        # job folder updates the container mtime even though it no
                        # longer appears in the new jobs list.
                        prev_containers = {
                            row[0] for row in conn.execute(
                                "SELECT dir_path FROM indexed_dirs WHERE prefix=? AND dir_path LIKE ?",
                                (prefix, os.path.join(customer_path, '%')),
                            )
                        }
                        all_containers = container_dirs | prev_containers

                        if not any(self._is_stale(conn, d, prefix) for d in all_containers):
                            continue

                        _emit(f"Indexing {customer}…")

                        # Delete after a successful scan so scan failure never
                        # leaves the customer with zero indexed rows.
                        conn.execute(
                            "DELETE FROM jobs WHERE customer=? AND prefix=?",
                            (customer, prefix),
                        )

                        for dir_name, job_docs_path in jobs:
                            if not dir_name or not dir_name[0].isdigit():
                                continue
                            job_number, desc, drawings = _parse_job_folder(dir_name)
                            try:
                                mtime = os.path.getmtime(job_docs_path)
                            except OSError:
                                mtime = time.time()
                            conn.execute(
                                """INSERT OR REPLACE INTO jobs
                                   (prefix, customer, job_number, description, drawings, path, mtime)
                                   VALUES(?,?,?,?,?,?,?)""",
                                (prefix, customer, job_number, desc,
                                 ','.join(drawings), job_docs_path, mtime),
                            )

                        for d in container_dirs:
                            self._mark_indexed(conn, d, prefix)

                # --- Blueprint / IR dirs ---
                for prefix, base_dir in bp_dirs:
                    if _cancelled():
                        return
                    if not self._is_stale(conn, base_dir, prefix):
                        continue

                    _emit(f"Indexing {prefix} files…")
                    conn.execute("DELETE FROM bp_files WHERE prefix=?", (prefix,))

                    completed = False
                    try:
                        for root, _dirs, files in os.walk(base_dir):
                            if _cancelled():
                                break
                            rel_path = os.path.relpath(root, base_dir)
                            path_parts = rel_path.split(os.sep)
                            customer = path_parts[0] if path_parts and path_parts[0] != '.' else ''
                            for filename in files:
                                file_path = os.path.join(root, filename)
                                try:
                                    mtime = os.path.getmtime(file_path)
                                except OSError:
                                    mtime = time.time()
                                conn.execute(
                                    """INSERT OR REPLACE INTO bp_files
                                       (prefix, customer, filename, name_no_ext,
                                        dir_path, rel_path, mtime)
                                       VALUES(?,?,?,?,?,?,?)""",
                                    (prefix, customer, filename,
                                     os.path.splitext(filename)[0],
                                     root, rel_path, mtime),
                                )
                        else:
                            completed = True
                    except OSError:
                        completed = True  # partial walk still worth caching

                    # Only mark indexed after a complete non-cancelled walk.
                    if completed:
                        self._mark_indexed(conn, base_dir, prefix)

        except sqlite3.OperationalError as exc:
            # Another writer holds the lock — skip this update cycle.
            logger.warning("search_index: could not acquire write lock: %s", exc)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def is_populated(self) -> bool:
        """Return True if the jobs table contains at least one row."""
        try:
            with self._connect(timeout=2.0) as conn:
                row = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
                return row[0] > 0
        except sqlite3.Error:
            return False

    def search_jobs(
        self,
        term: str,
        search_customer: bool = True,
        search_job: bool = True,
        search_desc: bool = True,
        search_drawing: bool = True,
    ) -> List[Dict]:
        """Search jobs table; returns up to _MAX_RESULTS results ordered by mtime."""
        escaped = _escape_like(term)
        like = f'%{escaped}%'
        conditions, params = [], []
        if search_customer:
            conditions.append("customer LIKE ? ESCAPE '\\' COLLATE NOCASE")
            params.append(like)
        if search_job:
            conditions.append("job_number LIKE ? ESCAPE '\\' COLLATE NOCASE")
            params.append(like)
        if search_desc:
            conditions.append("description LIKE ? ESCAPE '\\' COLLATE NOCASE")
            params.append(like)
        if search_drawing:
            conditions.append("drawings LIKE ? ESCAPE '\\' COLLATE NOCASE")
            params.append(like)
        if not conditions:
            return []

        sql = (
            f"SELECT * FROM jobs WHERE ({' OR '.join(conditions)}) "
            f"ORDER BY mtime DESC LIMIT {_MAX_RESULTS}"
        )
        try:
            with self._connect(timeout=5.0) as conn:
                rows = conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            logger.error("search_index: search_jobs failed: %s", exc)
            return []

        results = []
        for row in rows:
            drawings = [d for d in row['drawings'].split(',') if d]
            prefix = row['prefix']
            display_customer = f"[ITAR] {row['customer']}" if prefix == 'ITAR' else row['customer']
            results.append({
                'date': datetime.fromtimestamp(row['mtime']),
                'customer': display_customer,
                'job_number': row['job_number'],
                'description': row['description'],
                'drawings': drawings,
                'path': row['path'],
            })
        return results

    def search_bp(self, term: str) -> List[Dict]:
        """Search blueprint files by filename; returns up to _MAX_RESULTS results."""
        escaped = _escape_like(term)
        like = f'%{escaped}%'
        sql = (
            f"SELECT * FROM bp_files WHERE filename LIKE ? ESCAPE '\\' COLLATE NOCASE "
            f"ORDER BY mtime DESC LIMIT {_MAX_RESULTS}"
        )
        try:
            with self._connect(timeout=5.0) as conn:
                rows = conn.execute(sql, (like,)).fetchall()
        except sqlite3.Error as exc:
            logger.error("search_index: search_bp failed: %s", exc)
            return []

        results = []
        for row in rows:
            prefix = row['prefix']
            customer = row['customer']
            display_customer = f"[{prefix}] {customer}" if customer else f"[{prefix}]"
            results.append({
                'date': datetime.fromtimestamp(row['mtime']),
                'customer': display_customer,
                'job_number': row['name_no_ext'],
                'description': row['rel_path'] if row['rel_path'] != '.' else '',
                'drawings': [],
                'path': row['dir_path'],
            })
        return results

    def job_count(self) -> int:
        """Return total number of indexed job rows."""
        try:
            with self._connect(timeout=2.0) as conn:
                return conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        except sqlite3.Error:
            return 0

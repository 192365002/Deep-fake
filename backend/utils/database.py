"""
Supabase PostgreSQL database utilities with persistent JSON fallback for dev/testing.
Replaces Firebase Firestore and MongoDB with relational PostgreSQL + Supabase Client.
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None
_is_mock = False
_last_db_error: Optional[str] = None


class MockSupabaseTable:
    """In-memory simulation of Supabase PostgREST table for dev/offline testing"""
    def __init__(self, name: str, parent_db):
        self.name = name
        self.parent_db = parent_db
        self.records: Dict[str, Dict[str, Any]] = {}

    def insert(self, data: Any):
        class InsertBuilder:
            def __init__(self, table, payload):
                self.table = table
                self.payload = payload if isinstance(payload, list) else [payload]
            def execute(self):
                inserted = []
                for item in self.payload:
                    rec = dict(item)
                    rec_id = str(rec.get("id") or rec.get("user_id") or len(self.table.records) + 1)
                    rec["id"] = rec_id
                    self.table.records[rec_id] = rec
                    inserted.append(rec)
                self.table.parent_db.save_state()
                return type("Resp", (), {"data": inserted})()
        return InsertBuilder(self, data)

    def select(self, *columns):
        class SelectBuilder:
            def __init__(self, table):
                self.table = table
                self.filters = []
                self.order_col = None
                self.order_desc = False
                self.limit_val = None
                self.offset_val = 0

            def eq(self, column, value):
                self.filters.append((column, "eq", value))
                return self

            def order(self, column, desc=False):
                self.order_col = column
                self.order_desc = desc
                return self

            def limit(self, count):
                self.limit_val = count
                return self

            def range(self, start, end):
                self.offset_val = start
                self.limit_val = end - start + 1
                return self

            def execute(self):
                matched = []
                for rec in self.table.records.values():
                    ok = True
                    for col, op, val in self.filters:
                        if rec.get(col) != val:
                            ok = False
                            break
                    if ok:
                        matched.append(dict(rec))

                if self.order_col:
                    matched.sort(key=lambda r: str(r.get(self.order_col, "")), reverse=self.order_desc)

                if self.limit_val is not None:
                    matched = matched[self.offset_val:self.offset_val + self.limit_val]
                elif self.offset_val > 0:
                    matched = matched[self.offset_val:]

                return type("Resp", (), {"data": matched, "count": len(matched)})()
        return SelectBuilder(self)

    def update(self, data: Dict[str, Any]):
        class UpdateBuilder:
            def __init__(self, table, payload):
                self.table = table
                self.payload = payload
                self.filters = []

            def eq(self, column, value):
                self.filters.append((column, "eq", value))
                return self

            def execute(self):
                updated = []
                for rec_id, rec in self.table.records.items():
                    ok = True
                    for col, op, val in self.filters:
                        if rec.get(col) != val:
                            ok = False
                            break
                    if ok:
                        rec.update(self.payload)
                        updated.append(dict(rec))
                self.table.parent_db.save_state()
                return type("Resp", (), {"data": updated})()
        return UpdateBuilder(self, data)

    def delete(self):
        class DeleteBuilder:
            def __init__(self, table):
                self.table = table
                self.filters = []

            def eq(self, column, value):
                self.filters.append((column, "eq", value))
                return self

            def execute(self):
                to_delete = []
                for rec_id, rec in self.table.records.items():
                    ok = True
                    for col, op, val in self.filters:
                        if rec.get(col) != val:
                            ok = False
                            break
                    if ok:
                        to_delete.append(rec_id)
                for rid in to_delete:
                    del self.table.records[rid]
                self.table.parent_db.save_state()
                return type("Resp", (), {"data": to_delete})()
        return DeleteBuilder(self)

    def upsert(self, data: Any):
        return self.insert(data)


class MockStorageBucket:
    def __init__(self, name: str):
        self.name = name
        self.files = {}

    def upload(self, path: str, file: bytes, file_options: Optional[dict] = None):
        self.files[path] = file
        return {"Key": path}

    def create_signed_url(self, path: str, expires_in: int = 3600):
        return {"signedURL": f"https://mock-supabase.co/storage/v1/object/sign/{self.name}/{path}?token=mock"}

    def remove(self, paths: list):
        for p in paths:
            self.files.pop(p, None)
        return [{"name": p} for p in paths]


class MockStorageClient:
    def __init__(self):
        self.buckets: Dict[str, MockStorageBucket] = {}

    def from_(self, name: str) -> MockStorageBucket:
        if name not in self.buckets:
            self.buckets[name] = MockStorageBucket(name)
        return self.buckets[name]


class MockSupabaseClient:
    """Mock Supabase Client with persistent JSON storage"""
    def __init__(self, filepath="supabase_mock_store.json"):
        self.filepath = filepath
        self.tables: Dict[str, MockSupabaseTable] = {}
        self.storage = MockStorageClient()
        self.load_state()

    def table(self, name: str) -> MockSupabaseTable:
        if name not in self.tables:
            self.tables[name] = MockSupabaseTable(name, self)
        return self.tables[name]

    def from_(self, name: str) -> MockSupabaseTable:
        return self.table(name)

    def save_state(self):
        state = {tbl: t.records for tbl, t in self.tables.items()}
        try:
            with open(self.filepath, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving mock Supabase store: {e}")

    def load_state(self):
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r") as f:
                state = json.load(f)
            for tbl, recs in state.items():
                t = self.table(tbl)
                t.records = recs
        except Exception as e:
            logger.error(f"Error loading mock Supabase store: {e}")


async def init_db():
    """Initializes the Supabase client or activates the mock fallback"""
    global _supabase_client, _is_mock, _last_db_error

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if supabase_url and supabase_key and "example" not in supabase_url:
        try:
            _supabase_client = create_client(supabase_url, supabase_key)
            _is_mock = False
            _last_db_error = None
            logger.info("Connected to Supabase PostgreSQL successfully!")
            return
        except Exception as e:
            _last_db_error = str(e)
            logger.warning(f"Failed to connect to Supabase: {e}. Falling back to MockSupabaseClient.")

    logger.info("Running in Mock Supabase mode (dev/offline).")
    _supabase_client = MockSupabaseClient()
    _is_mock = True


def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key and "example" not in supabase_url:
            try:
                _supabase_client = create_client(supabase_url, supabase_key)
                return _supabase_client
            except Exception:
                pass
        _supabase_client = MockSupabaseClient()
    return _supabase_client


def is_mock_db() -> bool:
    return _is_mock


async def save_scan_result_and_update_stats(user_id: str, scan_id: str, result: dict):
    """
    Persists scan result into Supabase PostgreSQL 'scans' table and updates 'user_stats'.
    Supports bidirectional mapping between snake_case and camelCase for Android and Web.
    """
    global _last_db_error
    try:
        client = get_supabase_client()

        # Normalize media_type and verdict strings
        media_type = result.get("media_type") or result.get("mediaType") or "IMAGE"
        if hasattr(media_type, "value"):
            media_type = media_type.value
        media_type = str(media_type).upper()

        verdict = result.get("verdict") or "SAFE"
        if hasattr(verdict, "value"):
            verdict = verdict.value
        verdict = str(verdict).upper()

        scan_record = {
            "id": scan_id,
            "user_id": user_id,
            "media_type": media_type,
            "verdict": verdict,
            "confidence": float(result.get("confidence") or 100.0),
            "fake_probability": float(result.get("fake_probability") or result.get("fakeProbability") or 0.0),
            "real_probability": float(result.get("real_probability") or result.get("realProbability") or 100.0),
            "risk_level": str(result.get("risk_level") or result.get("riskLevel") or "LOW").upper(),
            "explanations": result.get("explanations") or [],
            "recommendations": result.get("recommendations") or [],
            "heatmap_base64": result.get("heatmap_base64") or result.get("heatmapBase64"),
            "storage_path": result.get("storage_path"),
            "storage_url": result.get("storage_url"),
            "metadata": result.get("metadata") or {},
            "created_at": result.get("timestamp") or datetime.utcnow().isoformat()
        }

        # 1. Insert Scan into PostgreSQL
        if hasattr(client, "table"):
            client.table("scans").insert(scan_record).execute()
        elif hasattr(client, "from_"):
            client.from_("scans").insert(scan_record).execute()

        # 2. Update user_stats in PostgreSQL (recalculates stats)
        await recalculate_and_update_stats(user_id, verdict)

        logger.info(f"Scan {scan_id} persisted to Supabase PostgreSQL for user {user_id}")

    except Exception as e:
        _last_db_error = str(e)
        logger.error(f"Error persisting scan to Supabase PostgreSQL: {e}")
        # Save to mock/local store so record is not lost
        try:
            if _mock_client:
                _mock_client.table("scans").insert(scan_record).execute()
        except Exception:
            pass


async def recalculate_and_update_stats(user_id: str, new_verdict: Optional[str] = None):
    """Calculates aggregates and updates public.user_stats"""
    try:
        client = get_supabase_client()
        # Fetch current user scans
        res = client.table("scans").select("*").eq("user_id", user_id).execute()
        scans = res.data or []

        total = len(scans)
        fake = sum(1 for s in scans if s.get("verdict") == "FAKE")
        suspicious = sum(1 for s in scans if s.get("verdict") == "SUSPICIOUS")
        safe = sum(1 for s in scans if s.get("verdict") in ("SAFE", "REAL"))

        trust = 100
        if total > 0:
            trust = int(((safe + 0.5 * suspicious) / total) * 100)

        stats_data = {
            "user_id": user_id,
            "total_scans": total,
            "fake_detected": fake,
            "suspicious_detected": suspicious,
            "safe_detected": safe,
            "trust_score": trust,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Upsert into user_stats
        if hasattr(client.table("user_stats"), "upsert"):
            client.table("user_stats").upsert(stats_data).execute()
        else:
            client.table("user_stats").insert(stats_data).execute()

    except Exception as e:
        logger.warning(f"Failed to recalculate user stats in client: {e}")


async def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Retrieve aggregate stats for user from public.user_stats"""
    try:
        client = get_supabase_client()
        res = client.table("user_stats").select("*").eq("user_id", user_id).execute()
        if res.data and len(res.data) > 0:
            row = res.data[0]
            return {
                "totalScans": row.get("total_scans", 0),
                "fakeDetected": row.get("fake_detected", 0),
                "suspiciousDetected": row.get("suspicious_detected", 0),
                "safeDetected": row.get("safe_detected", 0),
                "trustScore": row.get("trust_score", 100)
            }
        # If no row exists yet, return default
        return {"totalScans": 0, "fakeDetected": 0, "suspiciousDetected": 0, "safeDetected": 0, "trustScore": 100}
    except Exception as e:
        logger.error(f"Error fetching user stats: {e}")
        return {"totalScans": 0, "fakeDetected": 0, "suspiciousDetected": 0, "safeDetected": 0, "trustScore": 100}

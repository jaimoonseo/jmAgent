"""Comprehensive tests for audit logging system."""

import json
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
from src.audit.logger import AuditLogger, AuditRecord
from src.audit.storage import AuditStorage, AuditQuery


class TestAuditLogger:
    """Tests for AuditLogger class."""

    def test_audit_logger_init(self):
        """Test AuditLogger initialization."""
        logger = AuditLogger(user="test_user")
        assert logger.user == "test_user"

    def test_audit_logger_init_default_user(self):
        """Test AuditLogger initialization with default user."""
        logger = AuditLogger()
        assert logger.user == "anonymous"

    def test_log_action_generate(self):
        """Test logging generate action."""
        logger = AuditLogger(user="dev1")
        record = logger.log_action(
            action_type="generate",
            input_data={"prompt": "FastAPI endpoint"},
            output_data={"code": "def get(): ..."},
            status="success",
            duration=1.5,
            tokens_used={"input": 50, "output": 100}
        )

        assert record.action_type == "generate"
        assert record.user == "dev1"
        assert record.status == "success"
        assert record.input_data == {"prompt": "FastAPI endpoint"}
        assert record.output_data == {"code": "def get(): ..."}
        assert record.duration == 1.5
        assert record.tokens_used == {"input": 50, "output": 100}

    def test_log_action_refactor(self):
        """Test logging refactor action."""
        logger = AuditLogger(user="reviewer")
        record = logger.log_action(
            action_type="refactor",
            input_data={"file": "app.py", "requirements": "add type hints"},
            output_data={"refactored_code": "def func(x: int) -> str: ..."},
            status="success",
            duration=2.0
        )

        assert record.action_type == "refactor"
        assert record.status == "success"

    def test_log_action_test(self):
        """Test logging test action."""
        logger = AuditLogger()
        record = logger.log_action(
            action_type="test",
            input_data={"file": "math.py", "framework": "pytest"},
            output_data={"tests": "def test_add(): ..."},
            status="success",
            duration=1.2
        )

        assert record.action_type == "test"
        assert record.output_data == {"tests": "def test_add(): ..."}

    def test_log_action_explain(self):
        """Test logging explain action."""
        logger = AuditLogger()
        record = logger.log_action(
            action_type="explain",
            input_data={"file": "complex.py"},
            output_data={"explanation": "This code does X..."},
            status="success",
            duration=0.8
        )

        assert record.action_type == "explain"

    def test_log_action_fix(self):
        """Test logging fix action."""
        logger = AuditLogger()
        record = logger.log_action(
            action_type="fix",
            input_data={"file": "app.py", "error": "TypeError: ..."},
            output_data={"fixed_code": "def func(): ..."},
            status="success",
            duration=1.5
        )

        assert record.action_type == "fix"

    def test_log_action_chat(self):
        """Test logging chat action."""
        logger = AuditLogger()
        record = logger.log_action(
            action_type="chat",
            input_data={"message": "How to use async?"},
            output_data={"response": "Async is..."},
            status="success",
            duration=0.5
        )

        assert record.action_type == "chat"

    def test_log_action_with_failure(self):
        """Test logging failed action."""
        logger = AuditLogger(user="qa")
        record = logger.log_action(
            action_type="generate",
            input_data={"prompt": "invalid"},
            output_data=None,
            status="failure",
            error_message="Rate limit exceeded",
            duration=0.1
        )

        assert record.status == "failure"
        assert record.error_message == "Rate limit exceeded"
        assert record.output_data is None

    def test_log_action_partial_status(self):
        """Test logging partial success action."""
        logger = AuditLogger()
        record = logger.log_action(
            action_type="test",
            input_data={"file": "app.py"},
            output_data={"tests": "partial content"},
            status="partial",
            duration=1.0
        )

        assert record.status == "partial"

    def test_log_action_timestamp_is_iso_format(self):
        """Test that timestamp is in ISO 8601 format."""
        logger = AuditLogger()
        record = logger.log_action(
            action_type="generate",
            input_data={},
            output_data={},
            status="success"
        )

        # Should not raise ValueError
        datetime.fromisoformat(record.timestamp.replace('Z', '+00:00'))

    def test_log_action_with_metadata(self):
        """Test logging with custom metadata."""
        logger = AuditLogger()
        record = logger.log_action(
            action_type="generate",
            input_data={"prompt": "test"},
            output_data={"code": "test"},
            status="success",
            metadata={"model": "haiku", "temperature": 0.2}
        )

        assert record.metadata == {"model": "haiku", "temperature": 0.2}

    def test_log_action_returns_audit_record(self):
        """Test that log_action returns an AuditRecord."""
        logger = AuditLogger()
        record = logger.log_action(
            action_type="generate",
            input_data={},
            output_data={},
            status="success"
        )

        assert isinstance(record, AuditRecord)

    def test_log_action_with_nested_data(self):
        """Test logging with nested input/output data."""
        logger = AuditLogger()
        input_data = {
            "file": "app.py",
            "requirements": {
                "add_types": True,
                "add_docstrings": True
            }
        }
        output_data = {
            "code": "def func(x: int) -> str: ...",
            "changes": {
                "type_hints_added": 5,
                "docstrings_added": 2
            }
        }

        record = logger.log_action(
            action_type="refactor",
            input_data=input_data,
            output_data=output_data,
            status="success",
            duration=2.0
        )

        assert record.input_data == input_data
        assert record.output_data == output_data


class TestAuditRecord:
    """Tests for AuditRecord data class."""

    def test_audit_record_init(self):
        """Test AuditRecord initialization."""
        record = AuditRecord(
            action_type="generate",
            user="dev1",
            timestamp="2024-01-01T00:00:00Z",
            input_data={"prompt": "test"},
            output_data={"code": "test"},
            status="success",
            error_message=None,
            duration=1.0,
            tokens_used={"input": 50, "output": 100},
            metadata={}
        )

        assert record.action_type == "generate"
        assert record.user == "dev1"
        assert record.status == "success"

    def test_audit_record_to_dict(self):
        """Test AuditRecord.to_dict() method."""
        record = AuditRecord(
            action_type="generate",
            user="dev1",
            timestamp="2024-01-01T00:00:00Z",
            input_data={"prompt": "test"},
            output_data={"code": "test"},
            status="success",
            error_message=None,
            duration=1.0,
            tokens_used={"input": 50, "output": 100},
            metadata={"model": "haiku"}
        )

        data = record.to_dict()

        assert isinstance(data, dict)
        assert data["action_type"] == "generate"
        assert data["user"] == "dev1"
        assert data["input_data"] == {"prompt": "test"}
        assert data["tokens_used"] == {"input": 50, "output": 100}

    def test_audit_record_to_json_serializable(self):
        """Test AuditRecord is JSON serializable."""
        record = AuditRecord(
            action_type="generate",
            user="dev1",
            timestamp="2024-01-01T00:00:00Z",
            input_data={"prompt": "test"},
            output_data={"code": "test"},
            status="success",
            error_message=None,
            duration=1.5,
            tokens_used={"input": 50, "output": 100},
            metadata={"model": "haiku"}
        )

        # Should not raise
        json_str = json.dumps(record.to_dict())
        assert isinstance(json_str, str)

    def test_audit_record_from_dict(self):
        """Test AuditRecord.from_dict() class method."""
        data = {
            "action_type": "generate",
            "user": "dev1",
            "timestamp": "2024-01-01T00:00:00Z",
            "input_data": {"prompt": "test"},
            "output_data": {"code": "test"},
            "status": "success",
            "error_message": None,
            "duration": 1.0,
            "tokens_used": {"input": 50, "output": 100},
            "metadata": {"model": "haiku"}
        }

        record = AuditRecord.from_dict(data)

        assert record.action_type == "generate"
        assert record.user == "dev1"
        assert record.status == "success"


class TestAuditStorage:
    """Tests for AuditStorage class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "audit.db"
            yield str(db_path)

    def test_audit_storage_init(self, temp_db):
        """Test AuditStorage initialization."""
        storage = AuditStorage(db_path=temp_db)
        assert storage.db_path == temp_db

    def test_audit_storage_creates_database(self, temp_db):
        """Test that AuditStorage creates database file."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        assert Path(temp_db).exists()

    def test_audit_storage_save_record(self, temp_db):
        """Test saving audit record."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        record = AuditRecord(
            action_type="generate",
            user="dev1",
            timestamp="2024-01-01T00:00:00Z",
            input_data={"prompt": "test"},
            output_data={"code": "test"},
            status="success",
            error_message=None,
            duration=1.0,
            tokens_used={"input": 50, "output": 100},
            metadata={}
        )

        storage.save(record)

        # Verify record was saved
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

    def test_audit_storage_get_record(self, temp_db):
        """Test retrieving audit record."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        original = AuditRecord(
            action_type="generate",
            user="dev1",
            timestamp="2024-01-01T00:00:00Z",
            input_data={"prompt": "test"},
            output_data={"code": "test"},
            status="success",
            error_message=None,
            duration=1.0,
            tokens_used={"input": 50, "output": 100},
            metadata={}
        )

        storage.save(original)
        records = storage.get_all()

        assert len(records) == 1
        assert records[0].action_type == "generate"
        assert records[0].user == "dev1"

    def test_audit_storage_query_by_action_type(self, temp_db):
        """Test querying by action type."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        for action in ["generate", "refactor", "generate"]:
            record = AuditRecord(
                action_type=action,
                user="dev1",
                timestamp="2024-01-01T00:00:00Z",
                input_data={},
                output_data={},
                status="success",
                error_message=None,
                duration=1.0,
                tokens_used={},
                metadata={}
            )
            storage.save(record)

        query = AuditQuery(action_type="generate")
        results = storage.query(query)

        assert len(results) == 2
        assert all(r.action_type == "generate" for r in results)

    def test_audit_storage_query_by_user(self, temp_db):
        """Test querying by user."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        for user in ["dev1", "dev2", "dev1"]:
            record = AuditRecord(
                action_type="generate",
                user=user,
                timestamp="2024-01-01T00:00:00Z",
                input_data={},
                output_data={},
                status="success",
                error_message=None,
                duration=1.0,
                tokens_used={},
                metadata={}
            )
            storage.save(record)

        query = AuditQuery(user="dev1")
        results = storage.query(query)

        assert len(results) == 2
        assert all(r.user == "dev1" for r in results)

    def test_audit_storage_query_by_status(self, temp_db):
        """Test querying by status."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        for status in ["success", "failure", "success"]:
            record = AuditRecord(
                action_type="generate",
                user="dev1",
                timestamp="2024-01-01T00:00:00Z",
                input_data={},
                output_data={},
                status=status,
                error_message=None if status == "success" else "Error",
                duration=1.0,
                tokens_used={},
                metadata={}
            )
            storage.save(record)

        query = AuditQuery(status="success")
        results = storage.query(query)

        assert len(results) == 2
        assert all(r.status == "success" for r in results)

    def test_audit_storage_query_by_date_range(self, temp_db):
        """Test querying by date range."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        # Create records on different dates
        dates = [
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
            "2024-01-03T00:00:00Z"
        ]

        for date in dates:
            record = AuditRecord(
                action_type="generate",
                user="dev1",
                timestamp=date,
                input_data={},
                output_data={},
                status="success",
                error_message=None,
                duration=1.0,
                tokens_used={},
                metadata={}
            )
            storage.save(record)

        start_date = datetime(2024, 1, 2, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, 23, 59, 59, tzinfo=timezone.utc)

        query = AuditQuery(start_date=start_date, end_date=end_date)
        results = storage.query(query)

        assert len(results) == 1

    def test_audit_storage_query_combined(self, temp_db):
        """Test querying with combined filters."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        # Create multiple records
        records_data = [
            ("generate", "dev1", "success", "2024-01-01T00:00:00Z"),
            ("refactor", "dev1", "success", "2024-01-02T00:00:00Z"),
            ("generate", "dev2", "failure", "2024-01-03T00:00:00Z"),
            ("generate", "dev1", "failure", "2024-01-04T00:00:00Z"),
        ]

        for action, user, status, timestamp in records_data:
            record = AuditRecord(
                action_type=action,
                user=user,
                timestamp=timestamp,
                input_data={},
                output_data={},
                status=status,
                error_message="Error" if status == "failure" else None,
                duration=1.0,
                tokens_used={},
                metadata={}
            )
            storage.save(record)

        # Query: generate action by dev1 with success
        query = AuditQuery(action_type="generate", user="dev1", status="success")
        results = storage.query(query)

        assert len(results) == 1
        assert results[0].action_type == "generate"
        assert results[0].user == "dev1"
        assert results[0].status == "success"

    def test_audit_storage_get_count_by_action(self, temp_db):
        """Test getting count of records by action."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        for action in ["generate", "refactor", "generate", "test"]:
            record = AuditRecord(
                action_type=action,
                user="dev1",
                timestamp="2024-01-01T00:00:00Z",
                input_data={},
                output_data={},
                status="success",
                error_message=None,
                duration=1.0,
                tokens_used={},
                metadata={}
            )
            storage.save(record)

        counts = storage.get_count_by_action()

        assert counts.get("generate") == 2
        assert counts.get("refactor") == 1
        assert counts.get("test") == 1

    def test_audit_storage_get_count_by_user(self, temp_db):
        """Test getting count of records by user."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        for user in ["dev1", "dev2", "dev1"]:
            record = AuditRecord(
                action_type="generate",
                user=user,
                timestamp="2024-01-01T00:00:00Z",
                input_data={},
                output_data={},
                status="success",
                error_message=None,
                duration=1.0,
                tokens_used={},
                metadata={}
            )
            storage.save(record)

        counts = storage.get_count_by_user()

        assert counts.get("dev1") == 2
        assert counts.get("dev2") == 1

    def test_audit_storage_delete_old_records(self, temp_db):
        """Test deleting records older than a certain date."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        # Create records on different dates
        dates = [
            "2024-01-01T00:00:00Z",
            "2024-01-05T00:00:00Z",
            "2024-01-10T00:00:00Z"
        ]

        for date in dates:
            record = AuditRecord(
                action_type="generate",
                user="dev1",
                timestamp=date,
                input_data={},
                output_data={},
                status="success",
                error_message=None,
                duration=1.0,
                tokens_used={},
                metadata={}
            )
            storage.save(record)

        cutoff_date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        deleted_count = storage.delete_before(cutoff_date)

        assert deleted_count >= 1

        remaining = storage.get_all()
        assert len(remaining) == 2

    def test_audit_storage_multiple_saves(self, temp_db):
        """Test saving multiple records."""
        storage = AuditStorage(db_path=temp_db)
        storage._initialize_db()

        for i in range(10):
            record = AuditRecord(
                action_type="generate",
                user=f"user{i}",
                timestamp="2024-01-01T00:00:00Z",
                input_data={"index": i},
                output_data={},
                status="success",
                error_message=None,
                duration=1.0,
                tokens_used={},
                metadata={}
            )
            storage.save(record)

        all_records = storage.get_all()
        assert len(all_records) == 10


class TestAuditQuery:
    """Tests for AuditQuery class."""

    def test_audit_query_init_empty(self):
        """Test AuditQuery with no filters."""
        query = AuditQuery()
        assert query.action_type is None
        assert query.user is None
        assert query.status is None
        assert query.start_date is None
        assert query.end_date is None

    def test_audit_query_with_action_type(self):
        """Test AuditQuery with action type."""
        query = AuditQuery(action_type="generate")
        assert query.action_type == "generate"

    def test_audit_query_with_user(self):
        """Test AuditQuery with user."""
        query = AuditQuery(user="dev1")
        assert query.user == "dev1"

    def test_audit_query_with_status(self):
        """Test AuditQuery with status."""
        query = AuditQuery(status="success")
        assert query.status == "success"

    def test_audit_query_with_date_range(self):
        """Test AuditQuery with date range."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        query = AuditQuery(start_date=start, end_date=end)
        assert query.start_date == start
        assert query.end_date == end

    def test_audit_query_combined(self):
        """Test AuditQuery with multiple filters."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        query = AuditQuery(
            action_type="generate",
            user="dev1",
            status="success",
            start_date=start
        )
        assert query.action_type == "generate"
        assert query.user == "dev1"
        assert query.status == "success"
        assert query.start_date == start

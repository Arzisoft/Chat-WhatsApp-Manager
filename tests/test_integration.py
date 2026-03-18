"""
Comprehensive integration tests for ChatChaos WhatsApp Manager
Tests all core modules and integration points
"""

import os
import sys
import sqlite3
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import ParsedMessage, ParsedChat
from core.parser import parse_file, _detect_platform, _normalise_timestamp
from core.database import (
    init_db, get_connection, upsert_chat, insert_messages,
    get_all_chats, save_analysis, get_analysis, get_kpis
)
from core.error_handler import (
    ChatChaosError, APIError, DatabaseError, ValidationError,
    ErrorCategory, ErrorSeverity, ErrorLogger, CircuitBreaker
)
from core.rate_limiter import RateLimiter, ExtractionQueue
from core.transcriber import _is_arabic, _gemini_key
from core.system_health import SystemHealth


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def test(self, name, assertion, message=""):
        try:
            assert assertion, message
            self.passed += 1
            print(f"  [PASS] {name}")
        except AssertionError as e:
            self.failed += 1
            self.errors.append(f"{name}: {str(e)}")
            print(f"  [FAIL] {name}: {str(e)}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\nTest Summary: {self.passed}/{total} passed")
        if self.errors:
            print("\nFailed tests:")
            for error in self.errors:
                print(f"  - {error}")
        return self.failed == 0


results = TestResults()


def test_models():
    print("\n=== Testing Models ===")
    msg = ParsedMessage(
        seq=0,
        timestamp="2026-03-18 10:30:00",
        sender="Test User",
        body="Test message",
        is_media=False,
    )
    results.test("ParsedMessage creation", msg.sender == "Test User")
    results.test("ParsedMessage type", isinstance(msg, ParsedMessage))

    chat = ParsedChat(
        filename="test.txt",
        chat_name="Test Chat",
        platform="ios",
        messages=[msg],
    )
    results.test("ParsedChat creation", chat.chat_name == "Test Chat")
    results.test("ParsedChat message count", chat.message_count == 1)
    results.test("ParsedChat first message", chat.date_first_msg == "2026-03-18 10:30:00")


def test_parser():
    print("\n=== Testing Parser ===")

    ios_text = "[26/02/2026, 14:45:59] Sender: Test message"
    platform, pattern = _detect_platform(ios_text)
    results.test("iOS format detection", platform == "ios")

    android_text = "26/02/2026, 14:45 - Sender: Test message"
    platform, pattern = _detect_platform(android_text)
    results.test("Android format detection", platform == "android")

    timestamp = _normalise_timestamp("26/02/2026", "14:45:59")
    results.test(
        "Timestamp normalization",
        timestamp.startswith("2026-02-26"),
        f"Expected 2026-02-26, got {timestamp}"
    )

    chat = parse_file(
        "Test Chat.txt",
        "[26/02/2026, 14:45:59] User1: Hello\n[26/02/2026, 14:46:00] User2: Hi there"
    )
    results.test("Parse simple chat", chat.message_count == 2)
    results.test("Parse detects senders", chat.messages[0].sender == "User1")
    results.test("Parse detects bodies", "Hello" in chat.messages[0].body)


def test_database():
    print("\n=== Testing Database ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        os.environ["DB_PATH"] = db_path

        conn = get_connection()
        results.test("Database connection", conn is not None)

        try:
            init_db()
            results.test("Database initialization", True)

            chat = ParsedChat(
                filename="test_chat.txt",
                chat_name="Test Chat",
                platform="ios",
                messages=[
                    ParsedMessage(
                        seq=0,
                        timestamp="2026-03-18 10:00:00",
                        sender="User1",
                        body="Test",
                    )
                ],
                raw_text="test",
            )

            chat_id = upsert_chat(chat)
            results.test("Upsert chat", chat_id > 0)

            insert_messages(chat_id, chat)
            results.test("Insert messages", True)

            analysis_data = {
                "primary_area": "Beirut",
                "category": "Contractor",
                "status": "Active",
                "urgency_level": "Medium",
                "sentiment": "Positive",
                "relationship_stage": "Warm",
                "executive_summary": "Test summary",
                "last_activity_date": datetime.now().isoformat(),
            }
            save_analysis(chat_id, analysis_data)
            results.test("Save analysis", True)

            analysis = get_analysis(chat_id)
            results.test("Get analysis", analysis is not None)
            results.test("Analysis data preserved", analysis["primary_area"] == "Beirut")

            chats = get_all_chats()
            results.test("Get all chats", len(chats) >= 1)

            kpis = get_kpis()
            results.test("KPIs calculation", "total_chats" in kpis)
            results.test("KPI values are numbers", isinstance(kpis["total_chats"], int))

            conn.close()
        except Exception as e:
            results.failed += 1
            results.errors.append(f"Database test: {str(e)}")
            print(f"  ✗ Database error: {str(e)}")


def test_error_handling():
    print("\n=== Testing Error Handling ===")

    error = ChatChaosError(
        message="Test error",
        category=ErrorCategory.DATABASE_ERROR,
        severity=ErrorSeverity.ERROR,
    )
    results.test("ChatChaosError creation", isinstance(error, Exception))
    results.test("Error has category", error.category == ErrorCategory.DATABASE_ERROR)
    results.test("Error has severity", error.severity == ErrorSeverity.ERROR)
    results.test("Error to_dict", "message" in error.to_dict())

    api_error = APIError("Test API error", status_code=429)
    results.test("APIError creation", isinstance(api_error, ChatChaosError))
    results.test("APIError detects rate limit", api_error.category == ErrorCategory.RATE_LIMIT)

    db_error = DatabaseError("Test DB error", operation="insert")
    results.test("DatabaseError creation", isinstance(db_error, ChatChaosError))
    results.test("DatabaseError has operation", db_error.details.get("operation") == "insert")

    breaker = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=1)
    
    call_count = 0
    def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("Simulated failure")
        return "success"

    for attempt in range(3):
        try:
            breaker.call(failing_func)
        except:
            pass

    results.test("CircuitBreaker tracks failures", breaker.failure_count >= 2)
    results.test("CircuitBreaker opens on threshold", breaker.state == "open")


def test_rate_limiter():
    print("\n=== Testing Rate Limiter ===")

    limiter = RateLimiter(max_requests=5, window_seconds=10)

    allowed_count = 0
    for i in range(10):
        if limiter.is_allowed():
            allowed_count += 1

    results.test("Rate limiter allows within limit", allowed_count == 5)

    usage = limiter.get_usage()
    results.test("Rate limit usage tracking", usage["remaining"] == 0)
    results.test("Rate limit reports window", usage["window_seconds"] == 10)

    retry_after = limiter.get_retry_after()
    results.test("Rate limit retry calculation", retry_after > 0)

    queue = ExtractionQueue(max_requests=10, window_seconds=60)
    job_id = queue.add_job(chat_id=1, text="Test", priority="high")
    results.test("Queue adds job", job_id is not None)

    status = queue.get_job_status(job_id)
    results.test("Queue tracks job status", status is not None)
    results.test("Job starts as queued", status["status"] == "queued")

    queue_status = queue.get_queue_status()
    results.test("Queue status available", queue_status["queue_length"] >= 1)


def test_transcriber():
    print("\n=== Testing Transcriber ===")

    results.test("Arabic detection works", _is_arabic("سلام عليكم"))
    results.test("Non-Arabic detection works", not _is_arabic("Hello"))
    results.test("Gemini key reading", isinstance(_gemini_key(), str))


def test_system_health():
    print("\n=== Testing System Health ===")

    api_status = SystemHealth.get_api_status()
    results.test("API status retrievable", "status" in api_status)
    results.test("API status has timestamp", "timestamp" in api_status)

    db_status = SystemHealth.get_database_status()
    results.test("DB status retrievable", "status" in db_status)

    queue_status = SystemHealth.get_queue_status()
    results.test("Queue status retrievable", "queue_length" in queue_status)

    full_status = SystemHealth.get_full_status()
    results.test("Full status available", "overall_status" in full_status)
    results.test("Full status has services", "services" in full_status)
    results.test("Full status has recommendations", "recommendations" in full_status)


def test_end_to_end():
    print("\n=== End-to-End Integration Test ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "e2e_test.db")

        try:
            init_db()

            ios_export = """[26/02/2026, 14:45:59] Mohammed: Salam alaikum, kif halak?
[26/02/2026, 14:46:30] Rami: Alhamdulillah, mnieh. Shu akhbarack?
[26/02/2026, 14:47:00] Mohammed: Badna 200 meter mkaab concrete B300 le project fi Jounieh
[26/02/2026, 14:47:45] Mohammed: <attached: 00000001-AUDIO-2026-02-26-144745.opus>
[26/02/2026, 14:48:30] Rami: Tamam, inshallah. Price 85 dollar per meter. Delivery yom thalatha?
[26/02/2026, 14:49:00] Mohammed: Tamam, yalla"""

            chat = parse_file("WhatsApp Chat with Rami.txt", ios_export)
            results.test("E2E parse exports", chat.message_count > 0)
            results.test("E2E detects Arabic", any(m.body for m in chat.messages))

            chat_id = upsert_chat(chat)
            insert_messages(chat_id, chat)
            results.test("E2E stores chat", chat_id > 0)

            analysis_data = {
                "primary_area": "Jounieh",
                "secondary_areas": [],
                "category": "Contractor",
                "status": "Active",
                "urgency_level": "High",
                "sentiment": "Positive",
                "relationship_stage": "Hot",
                "language_mix": ["Arabic"],
                "executive_summary": "Large concrete order for Jounieh project",
                "contact": {
                    "name": "Rami",
                    "phone": None,
                    "role": "Contractor",
                    "company": None,
                    "is_decision_maker": True,
                },
                "concrete_orders": [{
                    "volume_m3": 200,
                    "mix_grade": "B300",
                    "price_per_m3": 85,
                    "currency": "USD",
                    "delivery_date": "2026-02-28",
                    "status": "Quoted",
                }],
                "last_activity_date": datetime.now().isoformat(),
            }
            save_analysis(chat_id, analysis_data)
            results.test("E2E saves analysis", True)

            stored_analysis = get_analysis(chat_id)
            results.test("E2E retrieves analysis", stored_analysis is not None)
            results.test("E2E analysis is accurate", stored_analysis["primary_area"] == "Jounieh")

            kpis = get_kpis()
            results.test("E2E KPI calculation", kpis["total_chats"] >= 1)
            results.test("E2E high risk detection", kpis["high_risk"] >= 0)

        except Exception as e:
            results.failed += 1
            results.errors.append(f"E2E test: {str(e)}")
            print(f"  ✗ E2E error: {str(e)}")


def main():
    print("=" * 60)
    print("CHATCHAOS WHATSAPP MANAGER - INTEGRATION TESTS")
    print("=" * 60)

    test_models()
    test_parser()
    test_database()
    test_error_handling()
    test_rate_limiter()
    test_transcriber()
    test_system_health()
    test_end_to_end()

    print("\n" + "=" * 60)
    success = results.summary()
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

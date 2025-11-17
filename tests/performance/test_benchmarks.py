"""
Performance benchmarks for critical paths
"""
import pytest
from app.utils.cooldown import CooldownDetector
from app.utils.smart_approval import SmartApprovalEngine
from app.services.session_service import SessionService
from datetime import datetime, timedelta


@pytest.fixture
def cooldown_detector():
    return CooldownDetector()


@pytest.fixture
def approval_engine():
    return SmartApprovalEngine()


def test_cooldown_detection_performance(benchmark, cooldown_detector):
    """Benchmark cooldown detection"""
    messages = [
        {"content": "Schedule appointment", "timestamp": datetime.now()},
        {"content": "Another request", "timestamp": datetime.now() + timedelta(minutes=1)}
    ]
    
    result = benchmark(cooldown_detector.check_cooldown, "user123", messages)
    assert result is not None


def test_smart_approval_performance(benchmark, approval_engine):
    """Benchmark smart approval decision"""
    request = {
        "type": "schedule_change",
        "child_id": "child123",
        "original_time": "14:00",
        "new_time": "15:00",
        "reason": "Want to play longer"
    }
    
    result = benchmark(approval_engine.should_auto_approve, request)
    assert isinstance(result, bool)


def test_message_parsing_performance(benchmark):
    """Benchmark message parsing"""
    from app.utils.message_parser import parse_message
    
    message = "Schedule dentist appointment for next Tuesday at 2pm for Emma"
    result = benchmark(parse_message, message)
    assert result is not None


def test_session_creation_performance(benchmark):
    """Benchmark session creation"""
    # TODO: Update this test once Session model is implemented
    # from app.models.session import Session
    pytest.skip("Session model not yet implemented")
    
    def create_session():
        pass
        # return Session(
        #     user_id="user123",
        #     channel="web",
        #     session_data={"test": "data"}
        # )
    
    result = benchmark(create_session)
    assert result.user_id == "user123"


def test_language_detection_performance(benchmark):
    """Benchmark language detection"""
    from app.utils.language_detector import detect_language
    
    texts = [
        "Hello, how are you?",
        "Bonjour, comment allez-vous?",
        "Hola, ¿cómo estás?",
        "こんにちは、元気ですか？"
    ]
    
    results = benchmark(lambda: [detect_language(text) for text in texts])
    assert len(results) == 4

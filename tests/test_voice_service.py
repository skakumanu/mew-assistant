"""
Tests for VoiceService's database write.

`VoiceService.process_voice_command` used to construct `VoiceCommand(...)`
with kwargs that don't exist on the model at all (`audio_duration`,
`transcript`, `entities`, `timestamp` — the real columns are
`audio_file_path`, `transcribed_text`, no `entities` column, and `created_at`
which defaults automatically). SQLAlchemy's default declarative `__init__`
raises `TypeError` on an unknown kwarg, so every real call to
`POST /voice/command` failed at this line. Nothing caught it: this file did
not exist, and `_mock_transcription` masked the same class of bug one layer
up in `VoiceTranscription` (Pydantic silently drops unknown constructor
kwargs rather than raising), which is why the mock path "worked" while
quietly losing `intent`/`entities`/`duration` on every transcription.

This only tests the DB-write step this fix touched. `_process_intent` (which
reads `transcription.intent` / `.entities`) hits that same upstream
`VoiceTranscription` gap and is a separate, larger, un-fixed problem —
tracked, not covered here.
"""

import pytest

from app.database.models import VoiceCommand


class TestVoiceCommandConstruction:
    """The exact construction site that used to raise TypeError."""

    def test_only_real_columns_are_used(self, db_session):
        command = VoiceCommand(
            user_id=1,
            session_id="sess-1",
            detected_language="en",
            confidence_score=1,
            transcribed_text="Schedule a doctor appointment for tomorrow at 2 PM",
            intent="schedule_appointment",
        )
        db_session.add(command)
        db_session.commit()
        db_session.refresh(command)

        assert command.id is not None
        assert command.transcribed_text.startswith("Schedule a doctor")
        assert command.intent == "schedule_appointment"
        # created_at is automatic - there is no timestamp column to set.
        assert command.created_at is not None

    def test_the_phantom_kwargs_are_rejected_by_the_model(self, db_session):
        """
        Locks the bug in place: if any of these ever become valid kwargs
        again (e.g. someone adds a migration), this test should be updated
        deliberately, not pass by accident.
        """
        for bad_kwarg in ("audio_duration", "transcript", "entities", "timestamp"):
            with pytest.raises(TypeError):
                VoiceCommand(user_id=1, **{bad_kwarg: "x"})

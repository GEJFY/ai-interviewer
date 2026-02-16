"""インタビューステートマシンのユニットテスト。

テスト対象: apps/backend/src/grc_backend/api/routes/interviews.py
"""

from unittest.mock import MagicMock

import pytest

from grc_backend.api.routes.interviews import _validate_transition
from grc_backend.core.errors import ValidationError
from grc_core.enums import InterviewStatus


class TestInterviewStateTransitions:
    """インタビューステータス遷移の検証テスト。"""

    def _mock_interview(self, status: InterviewStatus):
        interview = MagicMock()
        interview.status = status
        return interview

    # --- start ---

    def test_start_from_scheduled(self):
        """SCHEDULEDからstart可能。"""
        interview = self._mock_interview(InterviewStatus.SCHEDULED)
        _validate_transition(interview, "start")  # should not raise

    def test_start_from_paused(self):
        """PAUSEDからstart可能。"""
        interview = self._mock_interview(InterviewStatus.PAUSED)
        _validate_transition(interview, "start")

    def test_start_from_in_progress_rejected(self):
        """IN_PROGRESSからstartは不可。"""
        interview = self._mock_interview(InterviewStatus.IN_PROGRESS)
        with pytest.raises(ValidationError):
            _validate_transition(interview, "start")

    def test_start_from_completed_rejected(self):
        """COMPLETEDからstartは不可。"""
        interview = self._mock_interview(InterviewStatus.COMPLETED)
        with pytest.raises(ValidationError):
            _validate_transition(interview, "start")

    # --- pause ---

    def test_pause_from_in_progress(self):
        """IN_PROGRESSからpause可能。"""
        interview = self._mock_interview(InterviewStatus.IN_PROGRESS)
        _validate_transition(interview, "pause")

    def test_pause_from_scheduled_rejected(self):
        """SCHEDULEDからpauseは不可。"""
        interview = self._mock_interview(InterviewStatus.SCHEDULED)
        with pytest.raises(ValidationError):
            _validate_transition(interview, "pause")

    def test_pause_from_completed_rejected(self):
        """COMPLETEDからpauseは不可。"""
        interview = self._mock_interview(InterviewStatus.COMPLETED)
        with pytest.raises(ValidationError):
            _validate_transition(interview, "pause")

    # --- resume ---

    def test_resume_from_paused(self):
        """PAUSEDからresume可能。"""
        interview = self._mock_interview(InterviewStatus.PAUSED)
        _validate_transition(interview, "resume")

    def test_resume_from_in_progress_rejected(self):
        """IN_PROGRESSからresumeは不可。"""
        interview = self._mock_interview(InterviewStatus.IN_PROGRESS)
        with pytest.raises(ValidationError):
            _validate_transition(interview, "resume")

    def test_resume_from_scheduled_rejected(self):
        """SCHEDULEDからresumeは不可。"""
        interview = self._mock_interview(InterviewStatus.SCHEDULED)
        with pytest.raises(ValidationError):
            _validate_transition(interview, "resume")

    # --- complete ---

    def test_complete_from_in_progress(self):
        """IN_PROGRESSからcomplete可能。"""
        interview = self._mock_interview(InterviewStatus.IN_PROGRESS)
        _validate_transition(interview, "complete")

    def test_complete_from_paused(self):
        """PAUSEDからcomplete可能。"""
        interview = self._mock_interview(InterviewStatus.PAUSED)
        _validate_transition(interview, "complete")

    def test_complete_from_scheduled_rejected(self):
        """SCHEDULEDからcompleteは不可。"""
        interview = self._mock_interview(InterviewStatus.SCHEDULED)
        with pytest.raises(ValidationError):
            _validate_transition(interview, "complete")

    def test_complete_from_completed_rejected(self):
        """COMPLETEDからcompleteは不可（二重完了防止）。"""
        interview = self._mock_interview(InterviewStatus.COMPLETED)
        with pytest.raises(ValidationError):
            _validate_transition(interview, "complete")

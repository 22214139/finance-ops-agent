"""core/trajectory.py: the per-run audit trail the router builds up."""
from core.trajectory import Trajectory


def test_empty_trajectory_reports_no_steps():
    traj = Trajectory()
    assert traj.validator_ran_first() is False
    assert traj.first_failure() is None


def test_validator_ran_first_when_it_is_the_first_step():
    traj = Trajectory()
    traj.record("validator", "validator", True)
    traj.record("triage", "triage", True)
    assert traj.validator_ran_first() is True


def test_validator_ran_first_is_false_when_it_is_not_first():
    traj = Trajectory()
    traj.record("triage", "triage", True)
    traj.record("validator", "validator", True)
    assert traj.validator_ran_first() is False


def test_first_failure_returns_the_first_failed_step():
    traj = Trajectory()
    traj.record("validator", "validator", True)
    traj.record("audit", "anomaly_detection", False, detail="LLM timeout")
    traj.record("auditor", "audit_agent_response", False, detail="skipped after upstream failure")

    failure = traj.first_failure()
    assert failure.agent == "audit"
    assert failure.detail == "LLM timeout"


def test_summary_reports_validator_first_and_failure():
    traj = Trajectory()
    traj.record("validator", "validator", True)
    traj.record("audit", "anomaly_detection", False, detail="LLM timeout")

    summary = traj.summary()
    assert "Validator ran first: True" in summary
    assert "First failure: anomaly_detection" in summary

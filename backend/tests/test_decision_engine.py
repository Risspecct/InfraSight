from app.decision.engine import evaluate_decision
from app.decision.schemas import DecisionInput


def test_low_risk_project():
    result = evaluate_decision(
        DecisionInput(
            project_id="TEST-001",
            prediction_date="2011-01",
            cost_probability=0.20,
            schedule_probability=0.30,
        )
    )

    assert result.risk_level == "LOW"
    assert result.early_warning is False
    assert result.cost_risk.flagged is False
    assert result.schedule_risk.flagged is False


def test_cost_only_high_risk():
    result = evaluate_decision(
        DecisionInput(
            project_id="TEST-002",
            prediction_date="2011-01",
            cost_probability=0.70,
            schedule_probability=0.30,
        )
    )

    assert result.risk_level == "HIGH"
    assert result.early_warning is True
    assert result.cost_risk.flagged is True
    assert result.schedule_risk.flagged is False


def test_schedule_only_high_risk():
    result = evaluate_decision(
        DecisionInput(
            project_id="TEST-003",
            prediction_date="2011-01",
            cost_probability=0.30,
            schedule_probability=0.70,
        )
    )

    assert result.risk_level == "HIGH"
    assert result.early_warning is True
    assert result.cost_risk.flagged is False
    assert result.schedule_risk.flagged is True


def test_both_components_critical():
    result = evaluate_decision(
        DecisionInput(
            project_id="TEST-004",
            prediction_date="2011-01",
            cost_probability=0.70,
            schedule_probability=0.70,
        )
    )

    assert result.risk_level == "CRITICAL"
    assert result.early_warning is True
    assert result.cost_risk.flagged is True
    assert result.schedule_risk.flagged is True

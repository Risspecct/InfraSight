from db.database import SessionLocal

from app.services.inference import predict_project


PROJECT_ID = "PRJ_CODE_020100040"
OBSERVATION_ID = "FR_200108_001"


def test_project_inference():
    db = SessionLocal()

    try:
        result = predict_project(
            db,
            PROJECT_ID,
            OBSERVATION_ID,
        )

        assert result["project_id"] == PROJECT_ID
        assert result["observation_id"] == OBSERVATION_ID

        cost_probability = result["cost_overrun_probability"]
        schedule_probability = result["schedule_overrun_probability"]

        assert 0.0 <= cost_probability <= 1.0
        assert 0.0 <= schedule_probability <= 1.0

        print("\nInference result:")
        print(result)

    finally:
        db.close()

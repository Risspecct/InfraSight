import pandas as pd
import numpy as np

from db.database import SessionLocal
from app.services.feature_builder import MODEL_FEATURES, build_features


PROJECT_ID = "PRJ_CODE_020100040"
OBSERVATION_ID = "FR_200108_001"

ML_DATASET = "data/processed/sih_ml_master_dataset_v0.3.csv"


def test_feature_builder_matches_ml_reference():
    db = SessionLocal()

    try:
        generated = build_features(
            db,
            PROJECT_ID,
            OBSERVATION_ID,
        )

        reference_df = pd.read_csv(
            ML_DATASET,
            low_memory=False,
        )

        reference = reference_df[
            reference_df["observation_id"] == OBSERVATION_ID
        ]

        assert len(reference) == 1

        reference_row = reference.iloc[0]

        mismatches = []

        for feature in MODEL_FEATURES:
            generated_value = generated.iloc[0][feature]
            reference_value = reference_row[feature]

            if pd.isna(generated_value) and pd.isna(reference_value):
                continue

            if not np.isclose(
                float(generated_value),
                float(reference_value),
                rtol=1e-5,
                atol=1e-5,
            ):
                mismatches.append(
                    (
                        feature,
                        generated_value,
                        reference_value,
                    )
                )

        assert not mismatches, (
            "Feature mismatches found:\n"
            + "\n".join(map(str, mismatches))
        )

    finally:
        db.close()

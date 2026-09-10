import pickle
import zlib
from pathlib import Path

import lightgbm as lgb


BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_DIR = BASE_DIR / "ml" / "models"


COST_MODEL_PATH = MODEL_DIR / "cost_overrun_model.pkl"
SCHEDULE_MODEL_PATH = MODEL_DIR / "schedule_overrun_model.pkl"


def load_cost_model():
    """
    Reconstruct the existing LightGBM cost-risk model.

    The artifact contains a zlib-compressed serialized Python
    object with the LightGBM model text embedded inside it.
    """

    raw = COST_MODEL_PATH.read_bytes()
    data = zlib.decompress(raw)

    text = data.decode("utf-8", errors="ignore")

    start = text.find("tree\nversion=")

    if start == -1:
        start = text.find("version=v4")

    if start == -1:
        raise RuntimeError(
            "Could not locate LightGBM model header "
            "inside cost model artifact."
        )

    model_text = text[start:]

    booster = lgb.Booster(model_str=model_text)

    return booster


def load_schedule_model():
    """
    Load the existing XGBoost schedule-risk model.
    """

    raw = SCHEDULE_MODEL_PATH.read_bytes()
    data = zlib.decompress(raw)

    artifact = pickle.loads(data)

    return artifact

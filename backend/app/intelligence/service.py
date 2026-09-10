from sqlalchemy.orm import Session

from app.intelligence.evidence import build_project_evidence
from app.intelligence.groq_provider import GroqProvider
from app.intelligence.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.intelligence.schemas import (
    IntelligenceResponse,
)
from app.services.risk_assessment import assess_project
from app.services.explanation import explain_project


class IntelligenceService:

    def __init__(self):
        self.groq = GroqProvider()

    def analyze(
        self,
        db: Session,
        project_id: str,
        observation_id: str,
        query: str,
    ) -> dict:

        # 1. Retrieve project evidence
        evidence = build_project_evidence(
            db,
            project_id,
            observation_id,
        )

        # 2. Get ML prediction + decision
        risk = assess_project(
            db,
            project_id,
            observation_id,
        )

        # 3. Get SHAP drivers
        explanation = explain_project(
            db,
            project_id,
            observation_id,
            top_k=5,
        )

        # 4. Combine evidence
        context = {
            "project_evidence": evidence,
            "ml_risk": risk,
            "model_drivers": explanation,
        }

        # 5. Ask Groq
        result = self.groq.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                query,
                context,
            ),
            response_schema=(
                IntelligenceResponse.model_json_schema()
            ),
        )

        # 6. Validate response
        validated = IntelligenceResponse.model_validate(
            result
        )

        return validated.model_dump()
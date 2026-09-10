from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    canonical_project_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    canonical_project_name: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical_agency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    canonical_state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    canonical_sector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_report_date: Mapped[str] = mapped_column(String(20), nullable=False)
    last_report_date: Mapped[str] = mapped_column(String(20), nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    identity_confidence: Mapped[str] = mapped_column(String(50), nullable=False)

    observations: Mapped[list["ProjectObservation"]] = relationship(
        back_populates="project"
    )


class ProjectObservation(Base):
    __tablename__ = "project_observations"

    observation_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("projects.project_id"),
        nullable=False,
        index=True,
    )

    project_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    serial_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    project_name: Mapped[str] = mapped_column(String(500), nullable=False)
    agency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sector: Mapped[str] = mapped_column(String(255), nullable=False)

    report_date: Mapped[str] = mapped_column(String(20), nullable=False)
    approval_date: Mapped[str] = mapped_column(String(20), nullable=False)
    approval_date_revised: Mapped[str | None] = mapped_column(String(20), nullable=True)

    original_cost_crore: Mapped[float] = mapped_column(Float, nullable=False)
    revised_cost_crore: Mapped[float | None] = mapped_column(Float, nullable=True)
    anticipated_cost_crore: Mapped[float | None] = mapped_column(Float, nullable=True)

    cost_overrun_original_crore: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    cost_overrun_revised_crore: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    cumulative_expenditure_crore: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    original_completion_date: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    revised_completion_date: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    anticipated_completion_date: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    time_overrun_original_months: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    time_overrun_revised_months: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    additional_delay_months: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    milestones_achieved: Mapped[int] = mapped_column(Integer, nullable=False)
    milestones_total: Mapped[int] = mapped_column(Integer, nullable=False)

    physical_progress_pct: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    delay_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str | None] = mapped_column(String(255), nullable=True)

    source_report: Mapped[str] = mapped_column(String(255), nullable=False)
    source_table: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_page: Mapped[int] = mapped_column(Integer, nullable=False)
    source_serial_no: Mapped[int] = mapped_column(Integer, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="observations")

"""
updater.py

Orchestrates updates to the StudentTwin.

TwinUpdater receives already-resolved evidence and delegates
each update to the appropriate component updater.

It does not:

- create memories
- store memories
- resolve entities
- perform semantic retrieval
- decide how individual beliefs change

Those responsibilities belong to other components.
"""

from datetime import datetime

from src.twin.student import StudentTwin
from src.updater.resolver import ResolvedEvidence
from src.twin.enums import ResolutionStatus
from src.updater.base import ComponentUpdater

## TODO memory archive, and goal shit, and profile(updated by user in GUI)

class TwinUpdater:
    """
    Orchestrator responsible for evolving the StudentTwin.

    Component-specific update logic is delegated to
    ComponentUpdater implementations.
    """

    def __init__(
        self,
        component_updaters: list[ComponentUpdater],
    ) -> None:

        self._updaters: dict[str, ComponentUpdater] = {
            updater.component_name: updater
            for updater in component_updaters
        }

    # =============================================================
    # Public API
    # =============================================================

    def update(
        self,
        student: StudentTwin,
        evidence: list[ResolvedEvidence],
    ) -> str:
        """
        Apply resolved evidence to the StudentTwin.

        Only EXISTING and NEW evidence is processed.
        SKIP evidence is ignored.

        Returns:
            A human-readable update report.
        """

        reports: list[str] = []

        for item in evidence:

            if item.status == ResolutionStatus.SKIP:
                continue

            updater = self._updaters.get(
                item.component.value
            )

            if updater is None:

                reports.append(
                    f"Skipped {item.component}: "
                    "no updater is registered."
                )

                continue

            report = updater.update(
                student=student,
                evidence=item,
            )

            if report:
                reports.append(report)

        if reports:
            student.last_updated = datetime.now()

        return self._build_report(reports)

    # =============================================================
    # Private Helpers
    # =============================================================

    @staticmethod
    def _build_report(
        reports: list[str],
    ) -> str:
        """
        Combine component-level reports into one update report.
        """

        if not reports:
            return "No Twin updates were applied."

        return "\n".join(
            f"- {report}"
            for report in reports
        )
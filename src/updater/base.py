"""
component_updater.py

Defines the base interface for all Twin component updaters.

A ComponentUpdater is responsible for modifying one specific
component of the StudentTwin based on resolved evidence.

It does not perform entity resolution or memory storage.
"""

from abc import ABC, abstractmethod

from src.updater.resolver import ResolvedEvidence
from src.twin.student import StudentTwin


class ComponentUpdater(ABC):
    """
    Base class for all Twin component updaters.

    Each subclass owns the update logic for exactly one
    StudentTwin component.
    """

    component_name: str

    @abstractmethod
    def update(
        self,
        student: StudentTwin,
        evidence: ResolvedEvidence,
    ) -> str:
        """
        Apply resolved evidence to the StudentTwin.

        The component updater directly modifies the StudentTwin
        and returns a human-readable description of the change.
        """
        pass
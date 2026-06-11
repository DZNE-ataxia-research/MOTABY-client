"""Main MOTABYClient class."""
from __future__ import annotations

from typing import Any

from motaby._http import HTTPClient
from motaby.endpoints.assessments import AssessmentsEndpoint
from motaby.endpoints.batteries import BatteriesEndpoint
from motaby.endpoints.patients import PatientsEndpoint
from motaby.exceptions import MOTABYError


class MOTABYClient:
    """
    Python client for the MOTABY motor disorder assessment platform.

    Usage::

        from motaby import MOTABYClient

        client = MOTABYClient(
            base_url="https://motaby.clinic.de",
            api_key="mby_...",
        )

        # List assessments for a patient
        page = client.assessments.list(patient_id="P001", code="spiral-drawing")
        for assessment in page:
            print(assessment.assessment_code, assessment.created_at)

        # Load all data as a pandas DataFrame
        df = client.assessments.to_dataframe(patient_id="P001")
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        if not base_url:
            raise ValueError("base_url must not be empty")
        if not api_key.startswith("mby_"):
            raise ValueError("api_key must start with 'mby_'")

        self._http = HTTPClient(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.assessments = AssessmentsEndpoint(self._http)
        self.patients = PatientsEndpoint(self._http)
        self.batteries = BatteriesEndpoint(self._http)

    def ping(self) -> bool:
        """Check connectivity to the MOTABY server. Returns True if reachable."""
        try:
            self._http.get("/health")
            return True
        except MOTABYError:
            return False
        except Exception:
            return False

    def close(self) -> None:
        """Close the underlying HTTP connection."""
        self._http.close()

    def __enter__(self) -> "MOTABYClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

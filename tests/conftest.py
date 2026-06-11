"""pytest fixtures for motaby-client tests."""
from unittest.mock import MagicMock
import pytest
from motaby._http import HTTPClient


@pytest.fixture
def mock_http():
    return MagicMock(spec=HTTPClient)


@pytest.fixture
def client(mock_http):
    from motaby.client import MOTABYClient
    from motaby.endpoints.assessments import AssessmentsEndpoint
    from motaby.endpoints.patients import PatientsEndpoint
    from motaby.endpoints.batteries import BatteriesEndpoint
    c = MOTABYClient.__new__(MOTABYClient)
    c._http = mock_http
    c.assessments = AssessmentsEndpoint(mock_http)
    c.patients = PatientsEndpoint(mock_http)
    c.batteries = BatteriesEndpoint(mock_http)
    return c

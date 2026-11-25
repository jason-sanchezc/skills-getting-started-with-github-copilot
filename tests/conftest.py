import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture that provides a TestClient for making API requests."""
    return TestClient(app)


@pytest.fixture
def fresh_activities():
    """
    Fixture that saves and restores activities state between tests.
    Ensures test isolation and prevents state leakage between tests.
    """
    # Save original state
    original_state = {name: {
        "description": details["description"],
        "schedule": details["schedule"],
        "max_participants": details["max_participants"],
        "participants": details["participants"].copy()
    } for name, details in activities.items()}

    yield  # Run the test

    # Restore original state
    for name in list(activities.keys()):
        if name in original_state:
            activities[name]["participants"] = original_state[name]["participants"].copy()

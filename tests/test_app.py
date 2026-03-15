"""Backend tests for the FastAPI app.

Tests are written using pytest and structured with the Arrange/Act/Assert (AAA) pattern.
"""

import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activity store between tests.

    The app uses a module-level mutable dict for activity state.
    To make tests deterministic, restore the initial data after each test.
    """

    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


client = TestClient(app_module.app)


def test_get_activities_returns_all_activities():
    # Arrange: (no-op; state is already initialized by fixture)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json().keys() == app_module.activities.keys()


def test_signup_adds_participant_for_existing_activity():
    # Arrange
    activity_name = "Chess Club"
    email = "test_student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_returns_400_if_already_registered():
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": existing_email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_returns_404_for_unknown_activity():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "new_student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_successfully_removes_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert email not in app_module.activities[activity_name]["participants"]


def test_remove_participant_returns_404_when_missing():
    # Arrange
    activity_name = "Chess Club"
    missing_email = "not_registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": missing_email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_root_redirects_to_static_index():
    # Arrange: (no-op; state is already initialized)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "/static/index.html"

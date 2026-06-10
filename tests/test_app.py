import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Restore the in-memory activities between tests."""
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_root_redirects():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_for_activity_success():
    activity_name = "Math Club"
    email = "test_student@mergington.edu"

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate():
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_missing_activity():
    response = client.post(
        "/activities/Nonexistent/signup",
        params={"email": "missing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_success():
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_not_registered():
    activity_name = "Chess Club"
    email = "unknown@mergington.edu"

    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"


def test_remove_participant_missing_activity():
    response = client.delete(
        "/activities/Nonexistent/participants",
        params={"email": "missing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
